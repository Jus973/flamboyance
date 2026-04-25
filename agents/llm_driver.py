"""LLM-driven decision engine for vision-based web navigation.

Uses the LLM router to analyze screenshots and decide which action to take
next based on the persona's goal. Supports local Ollama and cloud Groq.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from typing import ClassVar, Literal

from .config import LLM_MAX_TOKENS
from .persona import Persona

log = logging.getLogger(__name__)

ActionType = Literal["click", "type", "scroll", "back", "done", "give_up"]


@dataclass
class ActionDecision:
    """Structured action decision from the LLM."""

    action_type: ActionType
    target: tuple[int, int] | str | None = None
    reasoning: str = ""
    raw_response: str = ""


@dataclass
class ActionHistoryEntry:
    """Record of an action taken and its result."""

    action: str
    target: tuple[int, int] | str | None
    result: str
    url: str = ""


class LLMDriver:
    """Vision-based LLM driver for web navigation decisions.

    Uses the hybrid LLM router which routes vision-based decisions to local
    Ollama by default, with optional Groq fallback for text-only decisions.
    """

    _response_cache: ClassVar[dict[str, "ActionDecision"]] = {}
    _cache_hits: ClassVar[int] = 0

    def __init__(self):
        """Initialize the LLM driver.

        No API key required for Ollama-based vision decisions.
        Groq API key is only needed for text-based decision fallback.
        """
        self.total_tokens_used: int = 0
        self.call_count: int = 0

    @classmethod
    def _cache_key(cls, screenshot_b64: str, persona_name: str, url: str) -> str:
        """Generate cache key from screenshot hash, persona, and URL."""
        content = f"{persona_name}:{url}:{screenshot_b64[:2000]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the response cache (useful for testing)."""
        cls._response_cache.clear()
        cls._cache_hits = 0

    def _build_system_prompt(self, persona: Persona) -> str:
        """Convert persona traits into compact LLM system instructions."""
        patience_desc = (
            "impatient, give up quickly"
            if persona.patience < 0.3
            else "somewhat impatient"
            if persona.patience < 0.5
            else "moderately patient"
            if persona.patience < 0.7
            else "very patient, thorough"
        )

        tech_desc = (
            "low-tech, needs obvious UI"
            if persona.tech_literacy < 0.3
            else "moderate tech skills"
            if persona.tech_literacy < 0.7
            else "tech-savvy"
        )

        pref = " | Prefers labeled elements only" if persona.prefers_visible_text else ""

        return f"""Simulate a user browsing a website to achieve a goal.

PERSONA: {persona.name} | GOAL: {persona.goal}
PATIENCE: {patience_desc} | TECH: {tech_desc}{pref}

ACTIONS: click([x,y]), type("text"), scroll("up"|"down"), back(), done(), give_up("reason")

Click element centers. Click input first, then type. Use done() when goal complete, give_up() if stuck.

Respond with JSON only: {{"action":"...", "target":..., "reasoning":"brief explanation"}}"""

    def _build_history_context(self, history: list[ActionHistoryEntry]) -> str:
        """Format recent action history for context (last 2 actions for token efficiency)."""
        if not history:
            return "First action."

        parts = []
        for entry in history[-2:]:
            target_str = (
                f"({entry.target[0]},{entry.target[1]})"
                if isinstance(entry.target, tuple)
                else repr(entry.target)
            )
            parts.append(f"{entry.action}({target_str})->{entry.result}")

        return "Recent: " + "; ".join(parts)

    async def decide_action(
        self,
        screenshot_b64: str,
        persona: Persona,
        history: list[ActionHistoryEntry],
        current_url: str = "",
    ) -> ActionDecision:
        """Analyze screenshot and decide next action.

        Uses the hybrid LLM router which routes vision decisions to local Ollama.

        Args:
            screenshot_b64: Base64-encoded PNG screenshot
            persona: Persona controlling behavior
            history: Recent action history for context
            current_url: Current page URL for context

        Returns:
            ActionDecision with the chosen action
        """
        cache_key = self._cache_key(screenshot_b64, persona.name, current_url)
        if cache_key in self._response_cache:
            LLMDriver._cache_hits += 1
            log.debug("Cache hit for %s (total hits: %d)", cache_key, self._cache_hits)
            return self._response_cache[cache_key]

        from llm import call_llm

        system_prompt = self._build_system_prompt(persona)
        history_context = self._build_history_context(history)
        user_content = f"URL: {current_url}\n{history_context}\nDecide next action:"

        try:
            raw_content = await call_llm(
                task_type="decision",
                prompt=user_content,
                max_tokens=LLM_MAX_TOKENS,
                image_b64=screenshot_b64,
                system_prompt=system_prompt,
                temperature=0.3,
            )

            self.call_count += 1
            self.total_tokens_used += len(raw_content) // 4

            decision = self._parse_response(raw_content)

            if decision.action_type not in ("give_up",):
                self._response_cache[cache_key] = decision

            return decision

        except Exception as e:
            log.error("LLM call failed: %s", e)
            return ActionDecision(
                action_type="give_up",
                target=f"LLM error: {e}",
                reasoning="Could not get response from LLM",
            )

    def _parse_response(self, raw_content: str) -> ActionDecision:
        """Parse LLM response into ActionDecision."""
        json_match = re.search(r"\{[^{}]*\}", raw_content, re.DOTALL)
        if not json_match:
            log.warning("No JSON found in LLM response: %s", raw_content[:200])
            return ActionDecision(
                action_type="give_up",
                target="Invalid LLM response format",
                reasoning="Could not parse LLM response",
                raw_response=raw_content,
            )

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            log.warning("Invalid JSON in LLM response: %s", e)
            return ActionDecision(
                action_type="give_up",
                target="Invalid JSON in response",
                reasoning="Could not parse LLM response",
                raw_response=raw_content,
            )

        action = data.get("action", "give_up")
        target = data.get("target")
        reasoning = data.get("reasoning", "")

        if action not in ("click", "type", "scroll", "back", "done", "give_up"):
            log.warning("Unknown action type: %s", action)
            action = "give_up"
            target = f"Unknown action: {data.get('action')}"

        if action == "click" and isinstance(target, list) and len(target) == 2:
            target = (int(target[0]), int(target[1]))

        return ActionDecision(
            action_type=action,
            target=target,
            reasoning=reasoning,
            raw_response=raw_content,
        )

    def get_usage_stats(self) -> dict[str, int]:
        """Return usage statistics for cost tracking."""
        return {
            "call_count": self.call_count,
            "total_tokens": self.total_tokens_used,
            "cache_hits": self._cache_hits,
            "cache_size": len(self._response_cache),
        }
