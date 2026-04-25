"""Environment-based configuration for LLM-driven agents.

Configuration is read from environment variables with sensible defaults.
Set these before running with --llm mode:

    export FLAMBOYANCE_LLM_API_KEY="your-api-key"
    export FLAMBOYANCE_LLM_BASE_URL="https://api.groq.com/openai/v1"  # optional
    export FLAMBOYANCE_LLM_MODEL="meta-llama/llama-4-scout-17b-16e-instruct"  # optional
"""

from __future__ import annotations

import os

LLM_API_KEY: str | None = os.environ.get("FLAMBOYANCE_LLM_API_KEY")
LLM_BASE_URL: str = os.environ.get("FLAMBOYANCE_LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL: str = os.environ.get("FLAMBOYANCE_LLM_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

MAX_LLM_CALLS_PER_SESSION: int = int(os.environ.get("FLAMBOYANCE_MAX_LLM_CALLS", "30"))
LLM_RETRY_ATTEMPTS: int = int(os.environ.get("FLAMBOYANCE_LLM_RETRY_ATTEMPTS", "3"))
LLM_RETRY_DELAY_S: float = float(os.environ.get("FLAMBOYANCE_LLM_RETRY_DELAY", "2.0"))

# Minimum delay between LLM requests to avoid rate limiting (seconds)
# Groq free tier: ~30 requests/min, so 3s delay is conservative
LLM_REQUEST_DELAY_S: float = float(os.environ.get("FLAMBOYANCE_LLM_REQUEST_DELAY", "3.0"))
