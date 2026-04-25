"""LLM routing layer.

Routes calls to appropriate providers based on task type:
- summarize, classify, report: Ollama (fast local model)
- decision with vision: Ollama (quality local model)
- decision text-only: Groq with Ollama fallback
"""

from __future__ import annotations

import logging
from typing import Literal

from agents.config import (
    OLLAMA_MODEL_FAST,
    OLLAMA_MODEL_QUALITY,
)
from .groq import call_groq, GroqRateLimitError
from .ollama import call_ollama, OllamaError
from .logging import timed_call, log_fallback

log = logging.getLogger(__name__)

TaskType = Literal["summarize", "classify", "report", "decision"]

FAST_TASKS = frozenset({"summarize", "classify", "report"})


async def call_llm(
    task_type: str,
    prompt: str,
    max_tokens: int = 512,
    image_b64: str | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.3,
) -> str:
    """Unified LLM interface with automatic routing.

    Routes calls based on task type:
    - "summarize", "classify", "report": Uses local Ollama (fast model)
    - "decision" with image: Uses local Ollama (quality model, vision)
    - "decision" text-only: Tries Groq first, falls back to Ollama on failure

    Args:
        task_type: Type of task (summarize, classify, report, decision).
        prompt: The user prompt/question.
        max_tokens: Maximum tokens in response.
        image_b64: Optional base64-encoded image (for vision tasks).
        system_prompt: Optional system prompt.
        temperature: Sampling temperature (0.0-1.0).

    Returns:
        Generated text response.

    Raises:
        Exception: If all providers fail.
    """
    if task_type in FAST_TASKS:
        return await _call_ollama_fast(
            task_type=task_type,
            prompt=prompt,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    if task_type == "decision":
        if image_b64:
            return await _call_ollama_vision(
                task_type=task_type,
                prompt=prompt,
                max_tokens=max_tokens,
                image_b64=image_b64,
                system_prompt=system_prompt,
                temperature=temperature,
            )
        else:
            return await _call_decision_with_fallback(
                prompt=prompt,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                temperature=temperature,
            )

    log.warning("Unknown task type '%s', defaulting to Ollama", task_type)
    return await _call_ollama_fast(
        task_type=task_type,
        prompt=prompt,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        temperature=temperature,
    )


async def _call_ollama_fast(
    task_type: str,
    prompt: str,
    max_tokens: int,
    system_prompt: str | None,
    temperature: float,
) -> str:
    """Call Ollama with fast model for lightweight tasks."""
    model = OLLAMA_MODEL_FAST

    with timed_call(task_type, "ollama", model) as call_log:
        result = await call_ollama(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        call_log.completion_tokens = len(result) // 4
        return result


async def _call_ollama_vision(
    task_type: str,
    prompt: str,
    max_tokens: int,
    image_b64: str,
    system_prompt: str | None,
    temperature: float,
) -> str:
    """Call Ollama with quality model for vision-based decisions."""
    model = OLLAMA_MODEL_QUALITY

    with timed_call(task_type, "ollama", model) as call_log:
        result = await call_ollama(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            image_b64=image_b64,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        call_log.completion_tokens = len(result) // 4
        return result


async def _call_decision_with_fallback(
    prompt: str,
    max_tokens: int,
    system_prompt: str | None,
    temperature: float,
) -> str:
    """Call Groq for text-based decisions, fall back to Ollama on failure."""
    task_type = "decision"

    try:
        with timed_call(task_type, "groq", "llama-3.1-8b-instant") as call_log:
            result = await call_groq(
                prompt=prompt,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            if result is not None:
                call_log.completion_tokens = len(result) // 4
                return result
            call_log.success = False
            call_log.error = "returned None"

    except GroqRateLimitError as e:
        log_fallback(task_type, "groq", "ollama", f"429 rate limit: {e}")
    except Exception as e:
        log_fallback(task_type, "groq", "ollama", str(e))

    model = OLLAMA_MODEL_QUALITY
    with timed_call(task_type, "ollama", model) as call_log:
        call_log.fallback = True
        result = await call_ollama(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        call_log.completion_tokens = len(result) // 4
        return result
