"""The Worker: stateless executor for a single Task inside a worktree.

The real implementation would shell out to an LLM (Claude, GPT, etc.). We
keep the interface around an `LLMClient` Protocol so swapping in a real
provider is a one-class change. The default `MockLLMClient` writes a
deterministic, parsable diff so we can exercise the full pipeline (Master
→ Worktree → Worker → Reducer) end-to-end without API keys.

Spec §4 sandbox: a Worker MUST NOT touch any file outside its
`files_to_edit` allowlist. We enforce this *after* the LLM call by
diffing the worktree and rejecting any extra modifications.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import Task, WorkerResult
from .worktree import Worktree, _run_git

log = logging.getLogger(__name__)


class LLMClient(Protocol):
    async def edit(
        self,
        *,
        task: Task,
        worktree_root: Path,
        file_contents: dict[str, str],
        context_contents: dict[str, str],
    ) -> dict[str, str]:
        """Return a mapping of {relative_path: new_content} for files to rewrite."""
        ...


@dataclass
class MockLLMClient:
    """Deterministic stand-in for a real LLM.

    For every file in `files_to_edit` we prepend a header comment recording
    which Worker touched it and append a sentinel function. This is enough to
    produce real, mergeable diffs that exercise the Reducer's conflict
    handler without requiring network calls.
    """

    latency_seconds: tuple[float, float] = (0.05, 0.15)
    seed: int | None = None

    async def edit(
        self,
        *,
        task: Task,
        worktree_root: Path,
        file_contents: dict[str, str],
        context_contents: dict[str, str],
    ) -> dict[str, str]:
        rng = random.Random(self.seed if self.seed is not None else hash(task.task_id))
        await asyncio.sleep(rng.uniform(*self.latency_seconds))

        rewritten: dict[str, str] = {}
        for rel, src in file_contents.items():
            header = (
                f"# flamboyance: refactored by worker for task {task.task_id[:8]}\n"
                f"# instruction: {task.instruction}\n"
            )
            footer = (
                f"\n\ndef _flamboyance_marker_{task.task_id.replace('-', '_')}() -> str:\n"
                f"    return {task.task_id!r}\n"
            )
            # Prepend header (idempotent) and append footer.
            new_src = src
            if header.splitlines()[0] not in new_src:
                new_src = header + new_src
            new_src = new_src.rstrip() + footer
            rewritten[rel] = new_src
        return rewritten


async def _read_files(root: Path, rels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in rels:
        p = root / rel
        if p.exists() and p.is_file():
            out[rel] = p.read_text(encoding="utf-8", errors="replace")
    return out


async def _git_modified_files(root: Path) -> list[str]:
    """Files with staged or unstaged changes inside `root`."""
    _, stdout, _ = await _run_git("status", "--porcelain", cwd=root)
    modified: list[str] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain v1: "XY path" or "XY orig -> path" for renames.
        path = line[3:]
        if "->" in path:
            path = path.split("->", 1)[1].strip()
        modified.append(path.strip())
    return modified


async def run_worker(
    task: Task,
    worktree: Worktree,
    llm: LLMClient,
    *,
    auto_commit: bool = True,
) -> WorkerResult:
    """Execute one Task inside its worktree. Returns a WorkerResult."""
    root = worktree.path
    log.info("worker[%s] start in %s", task.task_id[:8], root)

    file_contents = await _read_files(root, list(task.files_to_edit))
    context_contents = await _read_files(root, list(task.context_files))

    try:
        edits = await llm.edit(
            task=task,
            worktree_root=root,
            file_contents=file_contents,
            context_contents=context_contents,
        )
    except Exception as e:  # the LLM itself crashed
        return WorkerResult(
            task_id=task.task_id,
            branch=worktree.branch,
            worktree_path=str(root),
            status="failed",
            error=f"LLM error: {e!r}",
        )

    # Sandbox enforcement (spec §4): refuse to write outside the allowlist.
    allowed = set(task.files_to_edit)
    illegal = sorted(set(edits.keys()) - allowed)
    if illegal:
        return WorkerResult(
            task_id=task.task_id,
            branch=worktree.branch,
            worktree_path=str(root),
            status="violation",
            error=f"LLM tried to modify disallowed files: {illegal}",
        )

    # Apply the edits.
    for rel, new_src in edits.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_src, encoding="utf-8")

    # Double-check after applying — paranoid second pass against the working tree.
    modified = await _git_modified_files(root)
    surprise = sorted(set(modified) - allowed)
    if surprise:
        return WorkerResult(
            task_id=task.task_id,
            branch=worktree.branch,
            worktree_path=str(root),
            status="violation",
            modified_files=modified,
            error=f"Worktree modifications outside allowlist: {surprise}",
        )

    if auto_commit and modified:
        await _run_git("add", "--", *modified, cwd=root)
        msg = f"flamboyance: {task.label} ({task.task_id[:8]})\n\n{task.instruction}"
        await _run_git("commit", "-m", msg, cwd=root)

    log.info("worker[%s] done; modified=%s", task.task_id[:8], modified)
    return WorkerResult(
        task_id=task.task_id,
        branch=worktree.branch,
        worktree_path=str(root),
        status="success",
        modified_files=modified,
        log=f"applied {len(edits)} file edits",
    )
