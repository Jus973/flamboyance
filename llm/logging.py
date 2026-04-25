"""Structured logging for LLM calls.

Provides consistent logging format for debugging and monitoring LLM usage.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class LLMCallLog:
    """Record of an LLM call for logging and metrics."""

    task_type: str
    provider: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float = 0.0
    fallback: bool = False
    error: str | None = None
    success: bool = True

    def __str__(self) -> str:
        status = "OK" if self.success else f"FAILED {self.error or ''}"
        tokens = ""
        if self.prompt_tokens or self.completion_tokens:
            tokens = f" tokens={self.prompt_tokens or 0}+{self.completion_tokens or 0}"
        fallback_str = " fallback=true" if self.fallback else ""
        return (
            f"LLM [{self.task_type}] {self.provider}/{self.model} "
            f"{self.latency_ms:.0f}ms{tokens}{fallback_str} {status}"
        )


@dataclass
class LLMMetrics:
    """Aggregated metrics for LLM usage."""

    total_calls: int = 0
    ollama_calls: int = 0
    groq_calls: int = 0
    fallback_count: int = 0
    total_latency_ms: float = 0.0
    errors: int = 0
    calls_by_task: dict[str, int] = field(default_factory=dict)

    def record(self, call_log: LLMCallLog) -> None:
        """Record a call log into metrics."""
        self.total_calls += 1
        if call_log.provider == "ollama":
            self.ollama_calls += 1
        elif call_log.provider == "groq":
            self.groq_calls += 1
        if call_log.fallback:
            self.fallback_count += 1
        if not call_log.success:
            self.errors += 1
        self.total_latency_ms += call_log.latency_ms
        self.calls_by_task[call_log.task_type] = (
            self.calls_by_task.get(call_log.task_type, 0) + 1
        )

    def summary(self) -> str:
        """Return a summary string of metrics."""
        avg_latency = (
            self.total_latency_ms / self.total_calls if self.total_calls > 0 else 0
        )
        return (
            f"LLM Metrics: {self.total_calls} calls "
            f"(ollama={self.ollama_calls}, groq={self.groq_calls}), "
            f"fallbacks={self.fallback_count}, errors={self.errors}, "
            f"avg_latency={avg_latency:.0f}ms"
        )


_metrics = LLMMetrics()


def get_metrics() -> LLMMetrics:
    """Get the global metrics instance."""
    return _metrics


def reset_metrics() -> None:
    """Reset global metrics (useful for testing)."""
    global _metrics
    _metrics = LLMMetrics()


@contextmanager
def timed_call(
    task_type: str,
    provider: str,
    model: str,
) -> Generator[LLMCallLog, None, None]:
    """Context manager for timing and logging LLM calls.

    Usage:
        with timed_call("decision", "ollama", "llama3:70b") as call_log:
            result = await call_ollama(...)
            call_log.completion_tokens = len(result) // 4  # rough estimate

    The call is automatically logged on exit.
    """
    call_log = LLMCallLog(
        task_type=task_type,
        provider=provider,
        model=model,
    )
    start_time = time.perf_counter()

    try:
        yield call_log
    except Exception as e:
        call_log.success = False
        call_log.error = str(e)[:100]
        raise
    finally:
        call_log.latency_ms = (time.perf_counter() - start_time) * 1000
        _metrics.record(call_log)
        log.info("%s", call_log)


def log_fallback(
    task_type: str,
    from_provider: str,
    to_provider: str,
    reason: str,
) -> None:
    """Log a fallback event."""
    log.warning(
        "LLM [%s] %s FAILED (%s), fallback to %s",
        task_type,
        from_provider,
        reason,
        to_provider,
    )
