"""LLM-driven decision engine for vision-based web navigation.

Uses the LLM router to analyze screenshots and decide which action to take
next based on the persona's goal. Supports local Ollama and cloud Groq.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import ClassVar, Literal

from .config import LLM_MAX_TOKENS
from .persona import Persona

log = logging.getLogger(__name__)

ActionType = Literal["click", "type", "scroll", "back", "done", "give_up"]

HISTORY_CONTEXT_SIZE = 5

FEW_SHOT_EXAMPLES = '''
Examples of good decisions:

1. Login form visible, goal is to sign in:
   {"action": "click", "target": [320, 180], "reasoning": "Click email input field to enter credentials"}

2. After clicking email field:
   {"action": "type", "target": "user@example.com", "reasoning": "Enter email address in focused input"}

3. Content below fold, need to see more:
   {"action": "scroll", "target": "down", "reasoning": "Scroll to find the checkout button"}

4. Wrong page, need to go back:
   {"action": "back", "target": null, "reasoning": "Return to previous page, this is not the settings page"}

5. Goal achieved (e.g., order confirmation visible):
   {"action": "done", "target": null, "reasoning": "Order confirmation shown, purchase complete"}

6. Stuck after multiple attempts:
   {"action": "give_up", "target": "Cannot find login button after scrolling entire page", "reasoning": "Element not present"}
'''


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

    _response_cache: ClassVar[dict[str, ActionDecision]] = {}
    _cache_hits: ClassVar[int] = 0

    def __init__(self, viewport: tuple[int, int] = (1280, 720)):
        """Initialize the LLM driver.

        Args:
            viewport: Browser viewport dimensions (width, height) for validation.

        No API key required for Ollama-based vision decisions.
        Groq API key is only needed for text-based decision fallback.
        """
        self.total_tokens_used: int = 0
        self.call_count: int = 0
        self.viewport = viewport

    @classmethod
    def _cache_key(cls, screenshot_b64: str, persona_name: str, url: str, history_hash: str) -> str:
        """Generate cache key from screenshot hash, persona, URL, and history.

        Uses full screenshot hash to avoid collisions on similar pages.
        """
        screenshot_hash = hashlib.sha256(screenshot_b64.encode()).hexdigest()[:12]
        content = f"{persona_name}:{url}:{screenshot_hash}:{history_hash}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the response cache (useful for testing)."""
        cls._response_cache.clear()
        cls._cache_hits = 0

    def _build_system_prompt(self, persona: Persona) -> str:
        """Convert persona traits into detailed LLM system instructions with UX guidance."""
        patience_desc = (
            "impatient, give up quickly if confused or frustrated"
            if persona.patience < 0.3
            else "somewhat impatient, may abandon complex flows"
            if persona.patience < 0.5
            else "moderately patient, will try a few approaches"
            if persona.patience < 0.7
            else "very patient, will systematically explore options"
        )

        tech_desc = (
            "low technical literacy - needs obvious UI, large buttons, clear labels"
            if persona.tech_literacy < 0.3
            else "moderate tech skills - can use standard web patterns"
            if persona.tech_literacy < 0.7
            else "tech-savvy - comfortable with complex interfaces and shortcuts"
        )

        behavior_notes = []
        if persona.prefers_visible_text:
            behavior_notes.append("- Only interact with clearly labeled elements (avoid icon-only buttons)")
        if persona.patience < 0.4:
            behavior_notes.append("- Give up if stuck for more than 2-3 attempts on same goal")
        if persona.tech_literacy < 0.4:
            behavior_notes.append("- Avoid dropdown menus and hidden navigation")
            behavior_notes.append("- Look for large, obvious buttons and links")

        behavior_section = "\n".join(behavior_notes) if behavior_notes else "- Standard browsing behavior"

        # Build persona-specific focus section
        focus_section = ""
        if persona.focus_areas:
            focus_section = f"\n## WHAT TO LOOK FOR\nThis persona specifically focuses on: {', '.join(persona.focus_areas)}\n"
            focus_section += "Pay extra attention to issues in these areas when navigating.\n"

        # Build frustration triggers section
        frustration_section = ""
        if persona.frustration_triggers:
            frustration_section = f"\n## FRUSTRATION TRIGGERS\nThis persona gets frustrated by: {', '.join(persona.frustration_triggers)}\n"
            frustration_section += "Report these issues when encountered and consider giving up if they block progress.\n"

        return f"""You are simulating a user browsing a website to achieve a specific goal.
Analyze the screenshot and decide the next action based on the persona's characteristics.

## PERSONA PROFILE
- Name: {persona.name}
- Goal: {persona.goal}
- Patience: {patience_desc}
- Tech Level: {tech_desc}

## PERSONA BEHAVIORS
{behavior_section}
{focus_section}{frustration_section}
## AVAILABLE ACTIONS
- click([x,y]): Click at coordinates. Always click element centers. For inputs, click first then type.
- type("text"): Type text into the currently focused input field.
- scroll("up"|"down"): Scroll the page to reveal more content.
- back(): Navigate to the previous page.
- done(): Goal has been achieved - use when you see clear confirmation (order complete, settings saved, etc.)
- give_up("reason"): Cannot proceed - use when stuck, blocked, or goal seems impossible.

## DECISION GUIDELINES
1. Look for elements related to the goal before taking action
2. Prefer clicking buttons/links with text matching the goal over generic navigation
3. If a form is visible, fill it out step by step (click field, type, click next field)
4. If content might be below the fold, scroll to check before giving up
5. Avoid clicking the same element repeatedly if it doesn't produce results
6. Consider the persona's patience - impatient users give up faster

{FEW_SHOT_EXAMPLES}

## RESPONSE FORMAT
Respond with ONLY a JSON object (no markdown, no explanation):
{{"action": "...", "target": ..., "reasoning": "brief explanation"}}"""

    def _build_history_context(self, history: list[ActionHistoryEntry]) -> str:
        """Format recent action history for context.

        Uses last HISTORY_CONTEXT_SIZE actions to provide better context for decisions.
        Summarizes older actions if history is longer.
        """
        if not history:
            return "This is your first action on this page."

        recent = history[-HISTORY_CONTEXT_SIZE:]

        parts = []
        for i, entry in enumerate(recent, 1):
            if isinstance(entry.target, tuple):
                target_str = f"({entry.target[0]},{entry.target[1]})"
            elif entry.target:
                target_str = f'"{entry.target}"' if isinstance(entry.target, str) else str(entry.target)
            else:
                target_str = "null"

            parts.append(f"{i}. {entry.action}({target_str}) -> {entry.result}")

        # Add summary if there's older history
        older_count = len(history) - len(recent)
        prefix = f"[{older_count} earlier actions omitted]\n" if older_count > 0 else ""

        return f"{prefix}Recent actions:\n" + "\n".join(parts)

    def _history_hash(self, history: list[ActionHistoryEntry]) -> str:
        """Generate a hash of action history for cache key."""
        if not history:
            return "empty"
        recent = history[-HISTORY_CONTEXT_SIZE:]
        content = "|".join(f"{e.action}:{e.result}" for e in recent)
        return hashlib.md5(content.encode()).hexdigest()[:8]

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
        # Update viewport from persona if available
        if hasattr(persona, 'viewport'):
            self.viewport = persona.viewport

        history_hash = self._history_hash(history)
        cache_key = self._cache_key(screenshot_b64, persona.name, current_url, history_hash)
        if cache_key in self._response_cache:
            LLMDriver._cache_hits += 1
            log.debug("Cache hit for %s (total hits: %d)", cache_key, self._cache_hits)
            return self._response_cache[cache_key]

        from llm import call_llm

        system_prompt = self._build_system_prompt(persona)
        history_context = self._build_history_context(history)
        user_content = f"Current URL: {current_url}\nViewport: {self.viewport[0]}x{self.viewport[1]}\n\n{history_context}\n\nAnalyze the screenshot and decide the next action:"

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

            # Validate the decision
            decision = self._validate_decision(decision)

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
        """Parse LLM response into ActionDecision.

        Handles both simple and nested JSON structures by finding
        the outermost balanced braces.
        """
        # Try to find balanced JSON object (handles nested structures)
        json_str = self._extract_json_object(raw_content)
        if not json_str:
            log.warning("No JSON found in LLM response: %s", raw_content[:200])
            return ActionDecision(
                action_type="give_up",
                target="Invalid LLM response format",
                reasoning="Could not parse LLM response",
                raw_response=raw_content,
            )

        try:
            data = json.loads(json_str)
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
            try:
                target = (int(target[0]), int(target[1]))
            except (ValueError, TypeError):
                log.warning("Invalid click coordinates: %s", target)
                action = "give_up"
                target = "Invalid click coordinates"

        return ActionDecision(
            action_type=action,
            target=target,
            reasoning=reasoning,
            raw_response=raw_content,
        )

    def _extract_json_object(self, text: str) -> str | None:
        """Extract the first balanced JSON object from text.

        Handles nested braces correctly, unlike simple regex.
        """
        start = text.find('{')
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False

        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue

            if char == '\\' and in_string:
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

        return None

    def _validate_decision(self, decision: ActionDecision) -> ActionDecision:
        """Validate and potentially fix a decision.

        Checks:
        - Click coordinates are within viewport bounds
        - Type target is a non-empty string
        - Scroll direction is valid
        """
        if decision.action_type == "click":
            if isinstance(decision.target, tuple) and len(decision.target) == 2:
                x, y = decision.target
                width, height = self.viewport

                # Check bounds with small margin
                if x < 0 or x > width or y < 0 or y > height:
                    log.warning("Click coordinates (%d, %d) outside viewport %dx%d",
                               x, y, width, height)
                    # Clamp to viewport bounds
                    x = max(0, min(x, width - 1))
                    y = max(0, min(y, height - 1))
                    decision = ActionDecision(
                        action_type="click",
                        target=(x, y),
                        reasoning=decision.reasoning + " (coords clamped to viewport)",
                        raw_response=decision.raw_response,
                    )
            else:
                log.warning("Invalid click target: %s", decision.target)
                return ActionDecision(
                    action_type="give_up",
                    target="Invalid click coordinates",
                    reasoning="Click action requires [x, y] coordinates",
                    raw_response=decision.raw_response,
                )

        elif decision.action_type == "type":
            if not isinstance(decision.target, str) or not decision.target:
                log.warning("Invalid type target: %s", decision.target)
                return ActionDecision(
                    action_type="give_up",
                    target="Invalid type target",
                    reasoning="Type action requires non-empty string",
                    raw_response=decision.raw_response,
                )

        elif decision.action_type == "scroll" and decision.target not in ("up", "down", None):
            log.warning("Invalid scroll direction: %s, defaulting to down", decision.target)
            decision = ActionDecision(
                action_type="scroll",
                target="down",
                reasoning=decision.reasoning,
                raw_response=decision.raw_response,
            )

        return decision

    def get_usage_stats(self) -> dict[str, int]:
        """Return usage statistics for cost tracking."""
        return {
            "call_count": self.call_count,
            "total_tokens": self.total_tokens_used,
            "cache_hits": self._cache_hits,
            "cache_size": len(self._response_cache),
        }
