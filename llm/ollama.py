"""Ollama HTTP client for local LLM inference.

Supports both text and vision models via the Ollama REST API.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from agents.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_FAST,
    OLLAMA_MODEL_QUALITY,
    OLLAMA_TIMEOUT_S,
)

log = logging.getLogger(__name__)


class OllamaError(Exception):
    """Raised when Ollama API call fails."""

    pass


class OllamaConnectionError(OllamaError):
    """Raised when unable to connect to Ollama server."""

    pass


async def call_ollama(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 512,
    image_b64: str | None = None,
    system_prompt: str | None = None,
    temperature: float = 0.3,
) -> str:
    """Call local Ollama model.

    Args:
        prompt: The user prompt/question.
        model: Model name (defaults to OLLAMA_MODEL_FAST from config).
        max_tokens: Maximum tokens in response.
        image_b64: Optional base64-encoded image for vision models.
        system_prompt: Optional system prompt.
        temperature: Sampling temperature (0.0-1.0).

    Returns:
        Generated text response.

    Raises:
        OllamaConnectionError: If unable to connect to Ollama server.
        OllamaError: If the API call fails.
    """
    if model is None:
        model = OLLAMA_MODEL_QUALITY if image_b64 else OLLAMA_MODEL_FAST

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        },
    }

    if system_prompt:
        payload["system"] = system_prompt

    if image_b64:
        payload["images"] = [image_b64]

    url = f"{OLLAMA_BASE_URL}/api/generate"

    try:
        import httpx
    except ImportError:
        return await _call_ollama_urllib(url, payload)

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_S) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.ConnectError as e:
        log.error("Failed to connect to Ollama at %s: %s", OLLAMA_BASE_URL, e)
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
            "Is Ollama running? Start with: ollama serve"
        ) from e
    except httpx.TimeoutException as e:
        log.error("Ollama request timed out after %ss", OLLAMA_TIMEOUT_S)
        raise OllamaError(f"Ollama request timed out after {OLLAMA_TIMEOUT_S}s") from e
    except httpx.HTTPStatusError as e:
        log.error("Ollama API error: %s", e.response.text)
        raise OllamaError(f"Ollama API error: {e.response.status_code}") from e
    except Exception as e:
        log.error("Unexpected error calling Ollama: %s", e)
        raise OllamaError(f"Ollama error: {e}") from e


async def _call_ollama_urllib(url: str, payload: dict[str, Any]) -> str:
    """Fallback implementation using urllib (no httpx dependency)."""
    import urllib.error
    import urllib.request

    def do_request() -> str:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")
        except urllib.error.URLError as e:
            if "Connection refused" in str(e):
                raise OllamaConnectionError(
                    f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                    "Is Ollama running? Start with: ollama serve"
                ) from e
            raise OllamaError(f"Ollama error: {e}") from e

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, do_request)


async def check_ollama_available() -> bool:
    """Check if Ollama server is available."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def list_ollama_models() -> list[str]:
    """List available models on the Ollama server."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []
