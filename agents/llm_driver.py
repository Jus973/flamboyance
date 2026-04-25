"""LLM-driven decision engine for vision-based web navigation.

Uses an OpenAI-compatible vision model to analyze screenshots and decide
which action to take next based on the persona's goal.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from .config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_REQUEST_DELAY_S,
    LLM_RETRY_ATTEMPTS,
    LLM_RETRY_DELAY_S,
)
from .persona import Persona
from .rate_limiter import GlobalRateLimiter

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
    """Vision-based LLM driver for web navigation decisions."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or LLM_API_KEY
        self.base_url = base_url or LLM_BASE_URL
        self.model = model or LLM_MODEL

        if not self.api_key:
            raise ValueError(
                "LLM API key required. Set FLAMBOYANCE_LLM_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self._client: Any = None
        self.total_tokens_used: int = 0
        self.call_count: int = 0

    def _get_client(self) -> Any:
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "openai package required for LLM mode. "
                    "Install with: pip install openai"
                )
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def _build_system_prompt(self, persona: Persona) -> str:
        """Convert persona traits into LLM system instructions."""
        patience_desc = (
            "very impatient - give up quickly if things are confusing"
            if persona.patience < 0.3
            else "somewhat impatient - don't spend too long on unclear UI"
            if persona.patience < 0.5
            else "moderately patient - willing to explore a bit"
            if persona.patience < 0.7
            else "very patient - thorough and methodical"
        )

        tech_desc = (
            "low tech literacy - prefer obvious, clearly labeled buttons"
            if persona.tech_literacy < 0.3
            else "moderate tech literacy - can handle standard web patterns"
            if persona.tech_literacy < 0.7
            else "high tech literacy - comfortable with complex interfaces"
        )

        return f"""You are simulating a real user browsing a website. Act naturally as this persona would.

PERSONA: {persona.name}
GOAL: {persona.goal}
PATIENCE: {patience_desc}
TECH LEVEL: {tech_desc}
{f"PREFERENCE: Only interact with clearly labeled, visible elements" if persona.prefers_visible_text else ""}

You see a screenshot of the current webpage. Decide what action to take next to achieve your goal.

AVAILABLE ACTIONS:
- click(x, y) - Click at the specified pixel coordinates
- type("text") - Type text into the currently focused input field
- scroll("up" | "down") - Scroll the page
- back() - Go back to the previous page
- done() - Goal has been accomplished
- give_up("reason") - Cannot complete the goal, explain why

GUIDELINES:
1. Look at the screenshot carefully to understand the current page state
2. Click on buttons, links, or interactive elements that help achieve the goal
3. For click coordinates, estimate the CENTER of the element you want to click
4. If you see a form field that needs input, click it first, then type
5. If the goal appears complete, use done()
6. If stuck or frustrated (matching your patience level), use give_up()

Respond with ONLY a JSON object in this exact format:
{{"action": "click", "target": [x, y], "reasoning": "clicking the login button to sign in"}}
{{"action": "type", "target": "search query", "reasoning": "typing search term"}}
{{"action": "scroll", "target": "down", "reasoning": "looking for more content"}}
{{"action": "back", "target": null, "reasoning": "returning to previous page"}}
{{"action": "done", "target": null, "reasoning": "successfully completed the goal"}}
{{"action": "give_up", "target": "cannot find the settings page", "reasoning": "no clear path to settings"}}"""

    def _build_history_context(self, history: list[ActionHistoryEntry]) -> str:
        """Format recent action history for context."""
        if not history:
            return "This is your first action on this site."

        lines = ["Recent actions taken:"]
        for i, entry in enumerate(history[-5:], 1):
            target_str = (
                f"({entry.target[0]}, {entry.target[1]})"
                if isinstance(entry.target, tuple)
                else repr(entry.target)
            )
            lines.append(f"{i}. {entry.action}({target_str}) -> {entry.result}")

        return "\n".join(lines)

    async def decide_action(
        self,
        screenshot_b64: str,
        persona: Persona,
        history: list[ActionHistoryEntry],
        current_url: str = "",
    ) -> ActionDecision:
        """Analyze screenshot and decide next action.

        Args:
            screenshot_b64: Base64-encoded PNG screenshot
            persona: Persona controlling behavior
            history: Recent action history for context
            current_url: Current page URL for context

        Returns:
            ActionDecision with the chosen action
        """
        client = self._get_client()

        system_prompt = self._build_system_prompt(persona)
        history_context = self._build_history_context(history)
        user_content = f"Current URL: {current_url}\n\n{history_context}\n\nAnalyze this screenshot and decide your next action:"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_b64}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ]

        last_error: Exception | None = None
        for attempt in range(LLM_RETRY_ATTEMPTS + 1):
            try:
                # Global rate limiting: ensure minimum delay between requests across all drivers
                await GlobalRateLimiter.acquire(LLM_REQUEST_DELAY_S)

                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.3,
                )

                self.call_count += 1
                if response.usage:
                    self.total_tokens_used += response.usage.total_tokens

                raw_content = response.choices[0].message.content or ""
                return self._parse_response(raw_content)

            except Exception as e:
                last_error = e
                retry_delay = self._get_retry_delay(e, attempt)
                log.warning(
                    "LLM API call failed (attempt %d/%d): %s, retrying in %.1fs",
                    attempt + 1,
                    LLM_RETRY_ATTEMPTS + 1,
                    e,
                    retry_delay,
                )
                if attempt < LLM_RETRY_ATTEMPTS:
                    await asyncio.sleep(retry_delay)

        log.error("LLM API failed after retries: %s", last_error)
        return ActionDecision(
            action_type="give_up",
            target=f"LLM API error: {last_error}",
            reasoning="Could not get response from LLM",
        )

    def _get_retry_delay(self, error: Exception, attempt: int) -> float:
        """Calculate retry delay, respecting Retry-After for rate limit errors.

        For 429 rate limit errors, parses the retry delay from the error message
        (Groq returns "try again in X seconds" format). Falls back to exponential
        backoff for other errors.
        """
        try:
            from openai import RateLimitError
        except ImportError:
            RateLimitError = type(None)  # type: ignore

        if isinstance(error, RateLimitError):
            retry_after = self._parse_retry_after(str(error))
            if retry_after is not None:
                log.info("Rate limited (429), waiting %.1fs as requested by API", retry_after)
                return retry_after

        return LLM_RETRY_DELAY_S * (2**attempt)

    def _parse_retry_after(self, error_message: str) -> float | None:
        """Extract retry delay from rate limit error message.

        Groq API returns messages like: "try again in 7.123s" or "try again in 7 seconds"
        """
        patterns = [
            r"try again in (\d+(?:\.\d+)?)\s*s(?:econds?)?",
            r"retry.after[:\s]+(\d+(?:\.\d+)?)",
            r"wait (\d+(?:\.\d+)?)\s*s(?:econds?)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return float(match.group(1)) + 0.5  # Add buffer
        return None

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
        }
