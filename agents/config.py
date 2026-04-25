"""Environment-based configuration for LLM-driven agents.

Configuration is read from environment variables with sensible defaults.
Set these before running with --llm mode:

    export FLAMBOYANCE_LLM_API_KEY="your-api-key"
    export FLAMBOYANCE_LLM_BASE_URL="https://api.groq.com/openai/v1"  # optional
    export FLAMBOYANCE_LLM_MODEL="meta-llama/llama-4-scout-17b-16e-instruct"  # optional

For local Ollama:

    export FLAMBOYANCE_OLLAMA_URL="http://localhost:11434"  # optional
    export FLAMBOYANCE_OLLAMA_MODEL_FAST="llama3:8b"  # optional, for text tasks
    export FLAMBOYANCE_OLLAMA_MODEL_QUALITY="llama3:8b"  # optional, for complex text
    export FLAMBOYANCE_OLLAMA_MODEL_VISION="llava:latest"  # optional, for vision tasks

Event detection thresholds:

    export FLAMBOYANCE_SLOW_LOAD_THRESHOLD_MS="3000"  # Page load time threshold
    export FLAMBOYANCE_LONG_DWELL_THRESHOLD_S="10"    # Time without action threshold
    export FLAMBOYANCE_RAGE_CLICK_THRESHOLD="3"       # Number of clicks
    export FLAMBOYANCE_RAGE_CLICK_WINDOW_S="1.5"      # Time window for rage clicks

Threshold profiles (set FLAMBOYANCE_THRESHOLD_PROFILE):
    - "strict": Lower thresholds, more sensitive detection
    - "balanced": Default thresholds (same as not setting profile)
    - "lenient": Higher thresholds, only major issues detected
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

# Groq / OpenAI-compatible API settings
LLM_API_KEY: str | None = os.environ.get("FLAMBOYANCE_LLM_API_KEY")
LLM_BASE_URL: str = os.environ.get("FLAMBOYANCE_LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL: str = os.environ.get("FLAMBOYANCE_LLM_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# Ollama local model settings
OLLAMA_BASE_URL: str = os.environ.get("FLAMBOYANCE_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL_FAST: str = os.environ.get("FLAMBOYANCE_OLLAMA_MODEL_FAST", "llama3:8b")
OLLAMA_MODEL_QUALITY: str = os.environ.get("FLAMBOYANCE_OLLAMA_MODEL_QUALITY", "llama3:8b")
OLLAMA_MODEL_VISION: str = os.environ.get("FLAMBOYANCE_OLLAMA_MODEL_VISION", "llava:latest")
OLLAMA_TIMEOUT_S: float = float(os.environ.get("FLAMBOYANCE_OLLAMA_TIMEOUT", "60.0"))

MAX_LLM_CALLS_PER_SESSION: int = int(os.environ.get("FLAMBOYANCE_MAX_LLM_CALLS", "30"))

# Groq rate limit retry settings (not used for local Ollama)
LLM_RETRY_ATTEMPTS: int = int(os.environ.get("FLAMBOYANCE_LLM_RETRY_ATTEMPTS", "3"))
LLM_RETRY_DELAY_S: float = float(os.environ.get("FLAMBOYANCE_LLM_RETRY_DELAY", "2.0"))

# Image detail mode for vision API: "low" (85 tokens), "high" (~1100 tokens), or "auto"
# "auto" balances accuracy and cost; "high" for maximum accuracy on small UI elements
LLM_IMAGE_DETAIL: str = os.environ.get("FLAMBOYANCE_LLM_IMAGE_DETAIL", "auto")

# Maximum tokens for LLM response (actual JSON response is ~50-80 tokens)
LLM_MAX_TOKENS: int = int(os.environ.get("FLAMBOYANCE_LLM_MAX_TOKENS", "150"))


# ── Event Detection Thresholds ─────────────────────────────────────────

ThresholdProfile = Literal["strict", "balanced", "lenient"]


@dataclass
class EventThresholds:
    """Configurable thresholds for frustration event detection."""

    slow_load_threshold_ms: float = 3000.0
    long_dwell_threshold_s: float = 10.0
    rage_click_threshold: int = 3
    rage_click_window_s: float = 1.5

    @classmethod
    def from_profile(cls, profile: ThresholdProfile) -> EventThresholds:
        """Create thresholds from a named profile."""
        if profile == "strict":
            return cls(
                slow_load_threshold_ms=2000.0,
                long_dwell_threshold_s=5.0,
                rage_click_threshold=2,
                rage_click_window_s=2.0,
            )
        elif profile == "lenient":
            return cls(
                slow_load_threshold_ms=5000.0,
                long_dwell_threshold_s=20.0,
                rage_click_threshold=5,
                rage_click_window_s=1.0,
            )
        else:  # balanced
            return cls()

    @classmethod
    def from_env(cls) -> EventThresholds:
        """Create thresholds from environment variables.

        Environment variables override profile defaults.
        """
        profile = os.environ.get("FLAMBOYANCE_THRESHOLD_PROFILE", "balanced")
        thresholds = cls.from_profile(profile)  # type: ignore

        if "FLAMBOYANCE_SLOW_LOAD_THRESHOLD_MS" in os.environ:
            thresholds.slow_load_threshold_ms = float(
                os.environ["FLAMBOYANCE_SLOW_LOAD_THRESHOLD_MS"]
            )

        if "FLAMBOYANCE_LONG_DWELL_THRESHOLD_S" in os.environ:
            thresholds.long_dwell_threshold_s = float(
                os.environ["FLAMBOYANCE_LONG_DWELL_THRESHOLD_S"]
            )

        if "FLAMBOYANCE_RAGE_CLICK_THRESHOLD" in os.environ:
            thresholds.rage_click_threshold = int(
                os.environ["FLAMBOYANCE_RAGE_CLICK_THRESHOLD"]
            )

        if "FLAMBOYANCE_RAGE_CLICK_WINDOW_S" in os.environ:
            thresholds.rage_click_window_s = float(
                os.environ["FLAMBOYANCE_RAGE_CLICK_WINDOW_S"]
            )

        return thresholds


# Default thresholds loaded from environment
DEFAULT_THRESHOLDS: EventThresholds = EventThresholds.from_env()
