"""Tests for LLM driver with mocked API responses."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.llm_driver import ActionDecision, ActionHistoryEntry, LLMDriver
from agents.persona import FRUSTRATED_EXEC, POWER_USER, Persona


class TestActionDecision:
    def test_click_decision(self):
        decision = ActionDecision(
            action_type="click",
            target=(100, 200),
            reasoning="clicking button",
        )
        assert decision.action_type == "click"
        assert decision.target == (100, 200)
        assert decision.reasoning == "clicking button"

    def test_type_decision(self):
        decision = ActionDecision(
            action_type="type",
            target="hello world",
            reasoning="typing search query",
        )
        assert decision.action_type == "type"
        assert decision.target == "hello world"

    def test_done_decision(self):
        decision = ActionDecision(
            action_type="done",
            target=None,
            reasoning="goal achieved",
        )
        assert decision.action_type == "done"


class TestLLMDriverInit:
    def test_init_with_api_key(self):
        driver = LLMDriver(api_key="test-key", base_url="https://api.test.com")
        assert driver.api_key == "test-key"
        assert driver.base_url == "https://api.test.com"
        assert driver.call_count == 0
        assert driver.total_tokens_used == 0

    def test_init_without_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("agents.llm_driver.LLM_API_KEY", None):
                with pytest.raises(ValueError, match="LLM API key required"):
                    LLMDriver(api_key=None)


class TestBuildSystemPrompt:
    def test_frustrated_exec_prompt(self):
        driver = LLMDriver(api_key="test-key")
        prompt = driver._build_system_prompt(FRUSTRATED_EXEC)
        
        assert "frustrated_exec" in prompt
        assert "Complete a purchase flow quickly" in prompt
        assert "impatient" in prompt.lower()

    def test_power_user_prompt(self):
        driver = LLMDriver(api_key="test-key")
        prompt = driver._build_system_prompt(POWER_USER)
        
        assert "power_user" in prompt
        assert "patient" in prompt.lower()
        assert "tech-savvy" in prompt.lower()

    def test_prefers_visible_text_in_prompt(self):
        persona = Persona(
            name="test",
            patience=0.5,
            tech_literacy=0.5,
            goal="test goal",
            prefers_visible_text=True,
        )
        driver = LLMDriver(api_key="test-key")
        prompt = driver._build_system_prompt(persona)
        
        assert "labeled" in prompt.lower()


class TestBuildHistoryContext:
    def test_empty_history(self):
        driver = LLMDriver(api_key="test-key")
        context = driver._build_history_context([])
        assert "first action" in context.lower()

    def test_with_history(self):
        driver = LLMDriver(api_key="test-key")
        history = [
            ActionHistoryEntry(
                action="click",
                target=(100, 200),
                result="clicked button",
                url="http://example.com",
            ),
            ActionHistoryEntry(
                action="type",
                target="search",
                result="typed 'search'",
                url="http://example.com",
            ),
        ]
        context = driver._build_history_context(history)
        
        assert "Recent" in context
        assert "click" in context
        assert "100,200" in context
        assert "type" in context


class TestParseResponse:
    def test_parse_click_response(self):
        driver = LLMDriver(api_key="test-key")
        raw = '{"action": "click", "target": [150, 300], "reasoning": "clicking login"}'
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "click"
        assert decision.target == (150, 300)
        assert decision.reasoning == "clicking login"

    def test_parse_type_response(self):
        driver = LLMDriver(api_key="test-key")
        raw = '{"action": "type", "target": "hello", "reasoning": "typing text"}'
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "type"
        assert decision.target == "hello"

    def test_parse_done_response(self):
        driver = LLMDriver(api_key="test-key")
        raw = '{"action": "done", "target": null, "reasoning": "goal complete"}'
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "done"
        assert decision.target is None

    def test_parse_give_up_response(self):
        driver = LLMDriver(api_key="test-key")
        raw = '{"action": "give_up", "target": "stuck on login", "reasoning": "cannot proceed"}'
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "give_up"
        assert decision.target == "stuck on login"

    def test_parse_with_surrounding_text(self):
        driver = LLMDriver(api_key="test-key")
        raw = 'Here is my decision:\n{"action": "scroll", "target": "down", "reasoning": "looking for more"}\nThat should work.'
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "scroll"
        assert decision.target == "down"

    def test_parse_invalid_json(self):
        driver = LLMDriver(api_key="test-key")
        raw = "This is not valid JSON at all"
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "give_up"
        assert "Invalid" in decision.target or "parse" in decision.reasoning.lower()

    def test_parse_unknown_action(self):
        driver = LLMDriver(api_key="test-key")
        raw = '{"action": "dance", "target": null, "reasoning": "party time"}'
        
        decision = driver._parse_response(raw)
        
        assert decision.action_type == "give_up"


class TestDecideAction:
    @pytest.mark.asyncio
    async def test_decide_action_success(self):
        LLMDriver.clear_cache()
        driver = LLMDriver(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"action": "click", "target": [100, 200], "reasoning": "clicking button"}'
                )
            )
        ]
        mock_response.usage = MagicMock(total_tokens=150)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(driver, "_get_client", return_value=mock_client):
            decision = await driver.decide_action(
                screenshot_b64="fake_base64_data",
                persona=FRUSTRATED_EXEC,
                history=[],
                current_url="http://example.com",
            )
        
        assert decision.action_type == "click"
        assert decision.target == (100, 200)
        assert driver.call_count == 1
        assert driver.total_tokens_used == 150

    @pytest.mark.asyncio
    async def test_decide_action_api_error_retries(self):
        LLMDriver.clear_cache()
        driver = LLMDriver(api_key="test-key")
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        with patch.object(driver, "_get_client", return_value=mock_client):
            with patch("agents.llm_driver.LLM_RETRY_ATTEMPTS", 1):
                with patch("agents.llm_driver.LLM_RETRY_DELAY_S", 0.01):
                    decision = await driver.decide_action(
                        screenshot_b64="fake_base64_data",
                        persona=FRUSTRATED_EXEC,
                        history=[],
                    )
        
        assert decision.action_type == "give_up"
        assert "API error" in str(decision.target)
        assert mock_client.chat.completions.create.call_count == 2


class TestGetUsageStats:
    def test_initial_stats(self):
        LLMDriver.clear_cache()
        driver = LLMDriver(api_key="test-key")
        stats = driver.get_usage_stats()
        
        assert stats["call_count"] == 0
        assert stats["total_tokens"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_size"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_calls(self):
        LLMDriver.clear_cache()
        driver = LLMDriver(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"action": "done", "target": null, "reasoning": "done"}'))
        ]
        mock_response.usage = MagicMock(total_tokens=100)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(driver, "_get_client", return_value=mock_client):
            await driver.decide_action("fake1", FRUSTRATED_EXEC, [])
            await driver.decide_action("fake2", FRUSTRATED_EXEC, [])
        
        stats = driver.get_usage_stats()
        assert stats["call_count"] == 2
        assert stats["total_tokens"] == 200

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        LLMDriver.clear_cache()
        driver = LLMDriver(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"action": "click", "target": [100, 200], "reasoning": "test"}'))
        ]
        mock_response.usage = MagicMock(total_tokens=100)
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(driver, "_get_client", return_value=mock_client):
            await driver.decide_action("same_screenshot", FRUSTRATED_EXEC, [], "http://test.com")
            await driver.decide_action("same_screenshot", FRUSTRATED_EXEC, [], "http://test.com")
        
        stats = driver.get_usage_stats()
        assert stats["call_count"] == 1
        assert stats["cache_hits"] == 1
        assert mock_client.chat.completions.create.call_count == 1
