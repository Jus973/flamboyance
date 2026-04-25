"""Test that the Worker enforces spec §4: never modify files outside the allowlist."""

import asyncio
from pathlib import Path

import pytest

from orchestrator.models import Task
from orchestrator.worker import LLMClient, run_worker
from orchestrator.worktree import Worktree


class EvilLLM:
    """Pretends to be an LLM that 'helpfully' rewrites unrelated files."""
    async def edit(self, *, task, worktree_root, file_contents, context_contents):
        return {
            "allowed.py": "# rewritten\n",
            "../escape.py": "# attack\n",
            "context.py": "# I shouldn't touch this\n",
        }


@pytest.mark.asyncio
async def test_worker_rejects_writes_outside_allowlist(tmp_path: Path):
    # We don't need a real worktree to exercise the sandbox check — the
    # `_git_modified_files` call would fail without git, so we instead
    # validate the *first* sandbox gate (illegal keys in the LLM response).
    task = Task.new(
        files_to_edit=["allowed.py"],
        context_files=["context.py"],
        instruction="noop",
    )
    (tmp_path / "allowed.py").write_text("orig\n")
    (tmp_path / "context.py").write_text("ctx\n")

    wt = Worktree(path=tmp_path, branch="x", base_ref="HEAD")
    result = await run_worker(task, wt, EvilLLM(), auto_commit=False)
    assert result.status == "violation"
    assert "context.py" in result.error
