"""Tests for LLM driver with mocked API responses."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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
    def test_init_no_api_key_required(self):
        """LLMDriver no longer requires API key (uses local Ollama by default)."""
        driver = LLMDriver()
        assert driver.call_count == 0
        assert driver.total_tokens_used == 0


class TestBuildSystemPrompt:
    def test_frustrated_exec_prompt(self):
        driver = LLMDriver()
        prompt = driver._build_system_prompt(FRUSTRATED_EXEC)

        assert "frustrated_exec" in prompt
        assert "Complete a purchase flow quickly" in prompt
        assert "impatient" in prompt.lower()

    def test_power_user_prompt(self):
        driver = LLMDriver()
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
        driver = LLMDriver()
        prompt = driver._build_system_prompt(persona)

        assert "labeled" in prompt.lower()


class TestBuildHistoryContext:
    def test_empty_history(self):
        driver = LLMDriver()
        context = driver._build_history_context([])
        assert "first action" in context.lower()

    def test_with_history(self):
        driver = LLMDriver()
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
        driver = LLMDriver()
        raw = '{"action": "click", "target": [150, 300], "reasoning": "clicking login"}'

        decision = driver._parse_response(raw)

        assert decision.action_type == "click"
        assert decision.target == (150, 300)
        assert decision.reasoning == "clicking login"

    def test_parse_type_response(self):
        driver = LLMDriver()
        raw = '{"action": "type", "target": "hello", "reasoning": "typing text"}'

        decision = driver._parse_response(raw)

        assert decision.action_type == "type"
        assert decision.target == "hello"

    def test_parse_done_response(self):
        driver = LLMDriver()
        raw = '{"action": "done", "target": null, "reasoning": "goal complete"}'

        decision = driver._parse_response(raw)

        assert decision.action_type == "done"
        assert decision.target is None

    def test_parse_give_up_response(self):
        driver = LLMDriver()
        raw = '{"action": "give_up", "target": "stuck on login", "reasoning": "cannot proceed"}'

        decision = driver._parse_response(raw)

        assert decision.action_type == "give_up"
        assert decision.target == "stuck on login"

    def test_parse_with_surrounding_text(self):
        driver = LLMDriver()
        raw = 'Here is my decision:\n{"action": "scroll", "target": "down", "reasoning": "looking for more"}\nThat should work.'

        decision = driver._parse_response(raw)

        assert decision.action_type == "scroll"
        assert decision.target == "down"

    def test_parse_invalid_json(self):
        driver = LLMDriver()
        raw = "This is not valid JSON at all"

        decision = driver._parse_response(raw)

        assert decision.action_type == "give_up"
        assert "Invalid" in decision.target or "parse" in decision.reasoning.lower()

    def test_parse_unknown_action(self):
        driver = LLMDriver()
        raw = '{"action": "dance", "target": null, "reasoning": "party time"}'

        decision = driver._parse_response(raw)

        assert decision.action_type == "give_up"


class TestDecideAction:
    @pytest.mark.asyncio
    async def test_decide_action_success(self):
        LLMDriver.clear_cache()
        driver = LLMDriver()

        with patch("llm.router.call_ollama", new_callable=AsyncMock) as mock_ollama:
            mock_ollama.return_value = (
                '{"action": "click", "target": [100, 200], "reasoning": "clicking button"}'
            )

            decision = await driver.decide_action(
                screenshot_b64="fake_base64_data",
                persona=FRUSTRATED_EXEC,
                history=[],
                current_url="http://example.com",
            )

        assert decision.action_type == "click"
        assert decision.target == (100, 200)
        assert driver.call_count == 1

    @pytest.mark.asyncio
    async def test_decide_action_uses_router_for_vision(self):
        """Vision-based decisions should go through the router to Ollama."""
        LLMDriver.clear_cache()
        driver = LLMDriver()

        with patch("llm.call_llm", new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = (
                '{"action": "scroll", "target": "down", "reasoning": "looking for more"}'
            )

            decision = await driver.decide_action(
                screenshot_b64="fake_base64_data",
                persona=FRUSTRATED_EXEC,
                history=[],
                current_url="http://example.com",
            )

        assert decision.action_type == "scroll"
        mock_call_llm.assert_called_once()
        call_kwargs = mock_call_llm.call_args[1]
        assert call_kwargs["task_type"] == "decision"
        assert call_kwargs["image_b64"] == "fake_base64_data"

    @pytest.mark.asyncio
    async def test_decide_action_error_gives_up(self):
        LLMDriver.clear_cache()
        driver = LLMDriver()

        with patch("llm.call_llm", new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.side_effect = Exception("Connection failed")

            decision = await driver.decide_action(
                screenshot_b64="fake_base64_data",
                persona=FRUSTRATED_EXEC,
                history=[],
            )

        assert decision.action_type == "give_up"
        assert "LLM error" in str(decision.target)


class TestGetUsageStats:
    def test_initial_stats(self):
        LLMDriver.clear_cache()
        driver = LLMDriver()
        stats = driver.get_usage_stats()

        assert stats["call_count"] == 0
        assert stats["total_tokens"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_size"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_calls(self):
        LLMDriver.clear_cache()
        driver = LLMDriver()

        with patch("llm.call_llm", new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = '{"action": "done", "target": null, "reasoning": "done"}'

            await driver.decide_action("fake1", FRUSTRATED_EXEC, [])
            await driver.decide_action("fake2", FRUSTRATED_EXEC, [])

        stats = driver.get_usage_stats()
        assert stats["call_count"] == 2

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        LLMDriver.clear_cache()
        driver = LLMDriver()

        with patch("llm.call_llm", new_callable=AsyncMock) as mock_call_llm:
            mock_call_llm.return_value = (
                '{"action": "click", "target": [100, 200], "reasoning": "test"}'
            )

            await driver.decide_action("same_screenshot", FRUSTRATED_EXEC, [], "http://test.com")
            await driver.decide_action("same_screenshot", FRUSTRATED_EXEC, [], "http://test.com")

        stats = driver.get_usage_stats()
        assert stats["call_count"] == 1
        assert stats["cache_hits"] == 1
        assert mock_call_llm.call_count == 1


class TestValidation:
    def test_validates_click_coords_in_viewport(self):
        driver = LLMDriver(viewport=(1280, 720))
        decision = ActionDecision(
            action_type="click",
            target=(1500, 200),  # x outside viewport
            reasoning="clicking button",
        )
        validated = driver._validate_decision(decision)
        assert validated.action_type == "click"
        assert validated.target == (1279, 200)  # clamped to viewport
        assert "clamped" in validated.reasoning

    def test_validates_click_negative_coords(self):
        driver = LLMDriver(viewport=(1280, 720))
        decision = ActionDecision(
            action_type="click",
            target=(-10, -20),
            reasoning="clicking button",
        )
        validated = driver._validate_decision(decision)
        assert validated.action_type == "click"
        assert validated.target == (0, 0)  # clamped to 0,0

    def test_validates_click_invalid_target(self):
        driver = LLMDriver()
        decision = ActionDecision(
            action_type="click",
            target="not coordinates",
            reasoning="clicking button",
        )
        validated = driver._validate_decision(decision)
        assert validated.action_type == "give_up"
        assert "coordinates" in validated.reasoning.lower()

    def test_validates_type_empty_string(self):
        driver = LLMDriver()
        decision = ActionDecision(
            action_type="type",
            target="",
            reasoning="typing text",
        )
        validated = driver._validate_decision(decision)
        assert validated.action_type == "give_up"
        assert "non-empty" in validated.reasoning.lower()

    def test_validates_type_non_string(self):
        driver = LLMDriver()
        decision = ActionDecision(
            action_type="type",
            target=123,
            reasoning="typing text",
        )
        validated = driver._validate_decision(decision)
        assert validated.action_type == "give_up"

    def test_validates_scroll_invalid_direction(self):
        driver = LLMDriver()
        decision = ActionDecision(
            action_type="scroll",
            target="left",  # invalid
            reasoning="scrolling",
        )
        validated = driver._validate_decision(decision)
        assert validated.action_type == "scroll"
        assert validated.target == "down"  # defaulted

    def test_valid_decisions_pass_through(self):
        driver = LLMDriver(viewport=(1280, 720))

        # Valid click
        decision = ActionDecision(action_type="click", target=(100, 200), reasoning="test")
        validated = driver._validate_decision(decision)
        assert validated.target == (100, 200)

        # Valid type
        decision = ActionDecision(action_type="type", target="hello", reasoning="test")
        validated = driver._validate_decision(decision)
        assert validated.target == "hello"

        # Valid scroll
        decision = ActionDecision(action_type="scroll", target="up", reasoning="test")
        validated = driver._validate_decision(decision)
        assert validated.target == "up"


class TestNestedJsonParsing:
    def test_parse_nested_json(self):
        driver = LLMDriver()
        raw = '{"action": "click", "target": [100, 200], "reasoning": "clicking button", "metadata": {"confidence": 0.9}}'
        decision = driver._parse_response(raw)
        assert decision.action_type == "click"
        assert decision.target == (100, 200)

    def test_parse_json_with_nested_braces_in_string(self):
        driver = LLMDriver()
        raw = '{"action": "type", "target": "test{}", "reasoning": "typing text with braces"}'
        decision = driver._parse_response(raw)
        assert decision.action_type == "type"
        assert decision.target == "test{}"

    def test_extract_json_object(self):
        driver = LLMDriver()

        # Simple object
        assert driver._extract_json_object('{"a": 1}') == '{"a": 1}'

        # Nested object
        assert driver._extract_json_object('{"a": {"b": 2}}') == '{"a": {"b": 2}}'

        # With surrounding text
        result = driver._extract_json_object('Here is the result: {"action": "done"} That is all.')
        assert result == '{"action": "done"}'

        # No JSON
        assert driver._extract_json_object("No JSON here") is None


class TestHistoryContext:
    def test_history_truncates_to_limit(self):
        driver = LLMDriver()
        history = [
            ActionHistoryEntry(
                action="click", target=(i * 10, i * 10), result=f"result{i}", url="http://test.com"
            )
            for i in range(10)
        ]
        context = driver._build_history_context(history)

        # Should mention older actions were omitted
        assert "omitted" in context.lower()
        # Should contain recent actions
        assert "result9" in context

    def test_history_hash_changes_with_history(self):
        driver = LLMDriver()
        history1 = [ActionHistoryEntry(action="click", target=(100, 200), result="ok", url="")]
        history2 = [ActionHistoryEntry(action="type", target="text", result="ok", url="")]

        hash1 = driver._history_hash(history1)
        hash2 = driver._history_hash(history2)

        assert hash1 != hash2

    def test_history_hash_empty(self):
        driver = LLMDriver()
        assert driver._history_hash([]) == "empty"
