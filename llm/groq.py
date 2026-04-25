"""Groq API client wrapper.

Uses the OpenAI-compatible API for Groq cloud inference.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from agents.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_RETRY_DELAY_S,
)

log = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TIMEOUT_S = 30.0


class GroqError(Exception):
    """Raised when Groq API call fails."""

    pass


class GroqRateLimitError(GroqError):
    """Raised on 429 rate limit errors."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


_client: Any = None


def _get_client() -> Any:
    """Lazily initialize the OpenAI client for Groq."""
    global _client
    if _client is None:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai package required for Groq. Install with: pip install openai"
            )

        if not LLM_API_KEY:
            raise GroqError(
                "Groq API key required. Set FLAMBOYANCE_LLM_API_KEY environment variable."
            )

        _client = AsyncOpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            timeout=GROQ_TIMEOUT_S,
        )
    return _client


async def call_groq(
    prompt: str,
    max_tokens: int = 512,
    model: str = GROQ_MODEL,
    system_prompt: str | None = None,
    temperature: float = 0.3,
) -> str | None:
    """Call Groq API via OpenAI-compatible endpoint.

    Args:
        prompt: The user prompt/question.
        max_tokens: Maximum tokens in response.
        model: Model name (default: llama-3.1-8b-instant).
        system_prompt: Optional system prompt.
        temperature: Sampling temperature (0.0-1.0).

    Returns:
        Generated text response, or None if the call fails (signaling fallback).

    Raises:
        GroqRateLimitError: On 429 rate limit (includes retry_after if available).
        GroqError: On other API errors.
    """
    try:
        client = _get_client()
    except (ImportError, GroqError) as e:
        log.warning("Groq client unavailable: %s", e)
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    except Exception as e:
        error_str = str(e)

        try:
            from openai import RateLimitError

            if isinstance(e, RateLimitError):
                retry_after = _parse_retry_after(error_str)
                log.warning(
                    "Groq rate limited (429), retry_after=%s",
                    f"{retry_after}s" if retry_after else "unknown",
                )
                raise GroqRateLimitError(error_str, retry_after) from e
        except ImportError:
            pass

        if "429" in error_str or "rate limit" in error_str.lower():
            retry_after = _parse_retry_after(error_str)
            raise GroqRateLimitError(error_str, retry_after) from e

        if "timeout" in error_str.lower():
            log.warning("Groq request timed out")
            return None

        log.warning("Groq API error: %s", e)
        return None


def _parse_retry_after(error_message: str) -> float | None:
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
            return float(match.group(1)) + 0.5
    return None


async def call_groq_with_retry(
    prompt: str,
    max_tokens: int = 512,
    model: str = GROQ_MODEL,
    system_prompt: str | None = None,
    temperature: float = 0.3,
    max_retries: int = 2,
) -> str | None:
    """Call Groq with automatic retry on rate limits.

    Returns None if all retries are exhausted or on non-retryable errors.
    """
    for attempt in range(max_retries + 1):
        try:
            return await call_groq(
                prompt=prompt,
                max_tokens=max_tokens,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
            )
        except GroqRateLimitError as e:
            if attempt < max_retries:
                delay = e.retry_after or (LLM_RETRY_DELAY_S * (2**attempt))
                log.info("Groq rate limited, retrying in %.1fs (attempt %d/%d)",
                         delay, attempt + 1, max_retries + 1)
                await asyncio.sleep(delay)
            else:
                log.warning("Groq rate limit exceeded after %d retries", max_retries + 1)
                return None

    return None
