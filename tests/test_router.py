"""Tests for the hybrid LLM router."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.groq import GroqRateLimitError
from llm.logging import LLMCallLog, get_metrics, reset_metrics
from llm.router import FAST_TASKS, call_llm


class TestCallLLMRouting:
    """Test task-based routing logic."""

    @pytest.mark.asyncio
    async def test_summarize_routes_to_ollama(self):
        """Summarize tasks should use Ollama fast model."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "Summary result"

            result = await call_llm("summarize", "Summarize this text")

            assert result == "Summary result"
            mock_ollama.assert_called_once()
            call_kwargs = mock_ollama.call_args[1]
            assert call_kwargs["model"] == "llama3:8b"

    @pytest.mark.asyncio
    async def test_classify_routes_to_ollama(self):
        """Classify tasks should use Ollama fast model."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "positive"

            result = await call_llm("classify", "Classify sentiment")

            assert result == "positive"
            mock_ollama.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_routes_to_ollama(self):
        """Report tasks should use Ollama fast model."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "Report content"

            result = await call_llm("report", "Generate report")

            assert result == "Report content"
            mock_ollama.assert_called_once()

    @pytest.mark.asyncio
    async def test_decision_with_vision_routes_to_ollama(self):
        """Decision tasks with images should use Ollama vision model."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = '{"action": "click", "target": [100, 200]}'

            result = await call_llm(
                "decision",
                "What to click?",
                image_b64="fake_base64_image",
            )

            assert result == '{"action": "click", "target": [100, 200]}'
            mock_ollama.assert_called_once()
            call_kwargs = mock_ollama.call_args[1]
            assert call_kwargs["model"] == "llava:latest"
            assert call_kwargs["image_b64"] == "fake_base64_image"

    @pytest.mark.asyncio
    async def test_decision_text_only_tries_groq_first(self):
        """Text-only decision tasks should try Groq first."""
        with patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = "Groq decision"

            result = await call_llm("decision", "What to do?")

            assert result == "Groq decision"
            mock_groq.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_task_defaults_to_ollama(self):
        """Unknown task types should fall back to Ollama."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = "Fallback result"

            result = await call_llm("unknown_task", "Some prompt")

            assert result == "Fallback result"


class TestFallbackBehavior:
    """Test Groq to Ollama fallback logic."""

    @pytest.mark.asyncio
    async def test_groq_rate_limit_falls_back_to_ollama(self):
        """429 rate limit from Groq should trigger Ollama fallback."""
        with (
            patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq,
            patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama,
        ):
            mock_groq.side_effect = GroqRateLimitError("Rate limit exceeded", retry_after=5.0)
            mock_ollama.return_value = "Ollama fallback result"

            result = await call_llm("decision", "What to do?")

            assert result == "Ollama fallback result"
            mock_groq.assert_called_once()
            mock_ollama.assert_called_once()

    @pytest.mark.asyncio
    async def test_groq_returns_none_falls_back_to_ollama(self):
        """Groq returning None should trigger Ollama fallback."""
        with (
            patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq,
            patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama,
        ):
            mock_groq.return_value = None
            mock_ollama.return_value = "Ollama fallback result"

            result = await call_llm("decision", "What to do?")

            assert result == "Ollama fallback result"

    @pytest.mark.asyncio
    async def test_groq_exception_falls_back_to_ollama(self):
        """Generic Groq exceptions should trigger Ollama fallback."""
        with (
            patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq,
            patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama,
        ):
            mock_groq.side_effect = Exception("Network error")
            mock_ollama.return_value = "Ollama fallback result"

            result = await call_llm("decision", "What to do?")

            assert result == "Ollama fallback result"


class TestOllamaClient:
    """Test Ollama HTTP client."""

    @pytest.mark.asyncio
    async def test_call_ollama_success(self):
        """Ollama call should return response text."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Test response"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            from llm.ollama import call_ollama

            result = await call_ollama("Test prompt", model="llama3:8b")

            assert result == "Test response"

    @pytest.mark.asyncio
    async def test_call_ollama_with_image(self):
        """Ollama vision call should include image in payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Vision response"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            from llm.ollama import call_ollama

            result = await call_ollama(
                "What's in this image?",
                model="llava",
                image_b64="fake_base64",
            )

            assert result == "Vision response"
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert "images" in payload
            assert payload["images"] == ["fake_base64"]


class TestGroqClient:
    """Test Groq API client."""

    @pytest.mark.asyncio
    async def test_call_groq_success(self):
        """Groq call should return response content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Groq response"))]

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("llm.groq._get_client", return_value=mock_client):
            from llm.groq import call_groq

            result = await call_groq("Test prompt")

            assert result == "Groq response"

    @pytest.mark.asyncio
    async def test_call_groq_rate_limit_error(self):
        """Groq 429 should raise GroqRateLimitError."""
        mock_client = AsyncMock()

        try:
            from openai import RateLimitError

            mock_client.chat.completions.create.side_effect = RateLimitError(
                "Rate limit exceeded, try again in 5s",
                response=MagicMock(status_code=429),
                body=None,
            )
        except ImportError:
            pytest.skip("openai package not installed")

        with patch("llm.groq._get_client", return_value=mock_client):
            from llm.groq import GroqRateLimitError, call_groq

            with pytest.raises(GroqRateLimitError):
                await call_groq("Test prompt")


class TestLLMMetrics:
    """Test metrics collection."""

    def test_metrics_record_call(self):
        """Metrics should track call counts by provider."""
        reset_metrics()
        metrics = get_metrics()

        call_log = LLMCallLog(
            task_type="decision",
            provider="ollama",
            model="llama3:70b",
            latency_ms=150.0,
        )
        metrics.record(call_log)

        assert metrics.total_calls == 1
        assert metrics.ollama_calls == 1
        assert metrics.groq_calls == 0

    def test_metrics_track_fallbacks(self):
        """Metrics should track fallback events."""
        reset_metrics()
        metrics = get_metrics()

        call_log = LLMCallLog(
            task_type="decision",
            provider="ollama",
            model="llama3:70b",
            latency_ms=200.0,
            fallback=True,
        )
        metrics.record(call_log)

        assert metrics.fallback_count == 1

    def test_metrics_track_errors(self):
        """Metrics should track error counts."""
        reset_metrics()
        metrics = get_metrics()

        call_log = LLMCallLog(
            task_type="decision",
            provider="groq",
            model="llama-3.1-8b-instant",
            latency_ms=50.0,
            success=False,
            error="Rate limit",
        )
        metrics.record(call_log)

        assert metrics.errors == 1

    def test_metrics_summary(self):
        """Metrics summary should include key stats."""
        reset_metrics()
        metrics = get_metrics()

        metrics.record(LLMCallLog("decision", "ollama", "llama3:70b", latency_ms=100))
        metrics.record(LLMCallLog("summarize", "ollama", "llama3:8b", latency_ms=50))
        metrics.record(LLMCallLog("decision", "groq", "llama-3.1-8b-instant", latency_ms=80))

        summary = metrics.summary()
        assert "3 calls" in summary
        assert "ollama=2" in summary
        assert "groq=1" in summary


class TestFastTasks:
    """Test fast task identification."""

    def test_fast_tasks_set(self):
        """Fast tasks should be correctly identified."""
        assert "summarize" in FAST_TASKS
        assert "classify" in FAST_TASKS
        assert "report" in FAST_TASKS
        assert "decision" not in FAST_TASKS


class TestModelConfiguration:
    """Test model configuration from environment."""

    def test_default_vision_model(self):
        """Default vision model should be llava:latest."""
        from agents.config import OLLAMA_MODEL_VISION

        assert OLLAMA_MODEL_VISION == "llava:latest"

    def test_default_fast_model(self):
        """Default fast model should be llama3:8b."""
        from agents.config import OLLAMA_MODEL_FAST

        assert OLLAMA_MODEL_FAST == "llama3:8b"

    def test_default_quality_model(self):
        """Default quality model should be llama3:8b."""
        from agents.config import OLLAMA_MODEL_QUALITY

        assert OLLAMA_MODEL_QUALITY == "llama3:8b"

    def test_vision_model_used_for_image_tasks(self):
        """Vision model should be distinct from quality model for image tasks."""
        from agents.config import OLLAMA_MODEL_VISION

        # Vision model should be a vision-capable model
        assert "llava" in OLLAMA_MODEL_VISION.lower() or "vision" in OLLAMA_MODEL_VISION.lower()

    @pytest.mark.asyncio
    async def test_vision_task_uses_vision_model_not_quality(self):
        """Vision tasks should use OLLAMA_MODEL_VISION, not OLLAMA_MODEL_QUALITY."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = '{"action": "scroll", "target": "down"}'

            await call_llm(
                "decision",
                "Analyze this screenshot",
                image_b64="base64_screenshot_data",
            )

            call_kwargs = mock_ollama.call_args[1]
            # Should use vision model, not quality model
            assert call_kwargs["model"] == "llava:latest"
            assert call_kwargs["model"] != "llama3:8b"

    @pytest.mark.asyncio
    async def test_text_decision_uses_quality_model_on_fallback(self):
        """Text-only decisions falling back to Ollama should use quality model."""
        with (
            patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq,
            patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama,
        ):
            mock_groq.side_effect = Exception("API error")
            mock_ollama.return_value = '{"action": "click", "target": [50, 50]}'

            await call_llm("decision", "What should I click?")

            call_kwargs = mock_ollama.call_args[1]
            # Should use quality model for text fallback
            assert call_kwargs["model"] == "llama3:8b"


class TestVisionRouting:
    """Test vision-specific routing behavior."""

    @pytest.mark.asyncio
    async def test_image_passed_to_ollama(self):
        """Image data should be passed through to Ollama."""
        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = '{"action": "type", "target": "hello"}'
            test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            await call_llm(
                "decision",
                "What text should I type?",
                image_b64=test_image,
            )

            call_kwargs = mock_ollama.call_args[1]
            assert call_kwargs["image_b64"] == test_image

    @pytest.mark.asyncio
    async def test_no_image_does_not_use_vision_model(self):
        """Tasks without images should not use vision model."""
        with patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = '{"action": "done"}'

            await call_llm("decision", "Are we done?")

            # Should try Groq first for text-only decisions
            mock_groq.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_image_string_treated_as_no_image(self):
        """Empty image string should be treated as no image."""
        with patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = '{"action": "scroll", "target": "up"}'

            # Empty string should not trigger vision path
            await call_llm(
                "decision",
                "Should I scroll?",
                image_b64="",
            )

            # Empty string is falsy, so should use text path (Groq first)
            mock_groq.assert_called_once()

    @pytest.mark.asyncio
    async def test_none_image_treated_as_no_image(self):
        """None image should be treated as no image."""
        with patch("llm.router.call_groq", new_callable=AsyncMock) as mock_groq:
            mock_groq.return_value = '{"action": "back"}'

            await call_llm(
                "decision",
                "Should I go back?",
                image_b64=None,
            )

            mock_groq.assert_called_once()
