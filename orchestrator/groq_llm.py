"""Groq-backed LLM client (Llama 3.3 70B via Groq Cloud).

The API key is read from the ``GROQ_API_KEY`` environment variable only —
never commit keys or pass them on the command line (they end up in shell
history). If a key was ever pasted into chat or a ticket, rotate it in the
Groq console.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import Task

log = logging.getLogger(__name__)

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


@dataclass
class GroqLLMClient:
    """Calls Groq's OpenAI-compatible Chat Completions API.

    Uses ``response_format={"type": "json_object"}`` so the model returns a
    single JSON object: ``{ "<path>": "<full new file text>", ... }`` with
    keys exactly matching ``task.files_to_edit``.
    """

    model: str = DEFAULT_GROQ_MODEL
    temperature: float = 0.2
    max_tokens: int = 32_768
    api_key: str | None = None  # if unset, ``GROQ_API_KEY`` env var is used

    _extra_create_kwargs: dict[str, Any] = field(default_factory=dict)

    def _resolve_api_key(self) -> str:
        key = self.api_key or os.environ.get("GROQ_API_KEY", "").strip()
        if not key:
            raise ValueError(
                "GROQ_API_KEY is not set. Export it in your environment, e.g. "
                "`export GROQ_API_KEY=...` (do not pass secrets on the CLI)."
            )
        return key

    async def edit(
        self,
        *,
        task: Task,
        worktree_root: Path,
        file_contents: dict[str, str],
        context_contents: dict[str, str],
    ) -> dict[str, str]:
        _ = worktree_root  # reserved for future path-aware prompts
        key = self._resolve_api_key()

        allowed = list(task.files_to_edit)
        payload = {
            "instruction": task.instruction,
            "files_to_edit": {p: file_contents.get(p, "") for p in allowed},
            "context_files_readonly": context_contents,
        }
        user_blob = json.dumps(payload, ensure_ascii=False, indent=2)

        system = (
            "You are an expert software engineer. You will receive a JSON payload "
            "with an instruction, the current contents of files that MAY be edited, "
            "and read-only context files.\n\n"
            "Respond with a single JSON object and nothing else. Each key must be "
            "exactly one of the paths listed under \"files_to_edit\" in the input. "
            "Each value must be the complete new file contents as a string (not a "
            "diff). Include every key from files_to_edit — no omissions. "
            "Do not add keys for files that were only provided as context."
        )

        def _call_sync() -> str:
            from groq import Groq  # type: ignore[import-untyped]

            client = Groq(api_key=key)
            completion = client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_blob},
                ],
                **self._extra_create_kwargs,
            )
            choice = completion.choices[0]
            content = choice.message.content
            if not content:
                raise RuntimeError("Groq returned an empty message content")
            return content

        raw = await asyncio.to_thread(_call_sync)
        edits = _parse_json_edits(raw, allowed)
        log.debug("Groq returned %d file edit(s) for task %s", len(edits), task.task_id[:8])
        return edits


def _parse_json_edits(raw: str, allowed: list[str]) -> dict[str, str]:
    """Parse model output into a path → content map; validate allowlist."""
    text = raw.strip()
    m = _FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Groq response is not valid JSON: {e}\n---\n{text[:2000]}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Groq JSON must be an object, got {type(data).__name__}")

    allowed_set = set(allowed)
    out: dict[str, str] = {}
    for k, v in data.items():
        if k not in allowed_set:
            raise ValueError(f"Groq returned disallowed path {k!r}; allowed: {sorted(allowed_set)}")
        if not isinstance(v, str):
            raise ValueError(f"Groq value for {k!r} must be a string, got {type(v).__name__}")
        out[k] = v

    missing = allowed_set - set(out)
    if missing:
        raise ValueError(f"Groq JSON missing required paths: {sorted(missing)}")
    return out
