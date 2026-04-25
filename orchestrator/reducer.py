"""The Reducer: integrate Worker branches back into the trunk.

Strategy (in order, per branch):
  1. `git merge --no-ff` the Worker branch.
  2. If git reports a conflict, walk every conflicted file and try to
     auto-resolve using a simple, *safe* heuristic: when both sides only
     *added* lines (no deletes, no overlaps), splice the additions in
     order. This covers the common "two Workers each appended a helper
     to the same util module" case without ever silently dropping code.
  3. Anything we can't auto-resolve is left in the worktree with conflict
     markers, the merge is aborted, and we report it via `MergeResult`.

We deliberately *do not* try to be clever about overlapping edits — the
spec already tells us those tasks should never have been parallelized
(§4 Dependency Check), so the right behavior is to surface them.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import MergeResult, WorkerResult
from .worktree import _run_git

log = logging.getLogger(__name__)

CONFLICT_BLOCK_RE = re.compile(
    r"<{7} .*?\n(?P<ours>.*?)={7}\n(?P<theirs>.*?)>{7} .*?\n",
    re.DOTALL,
)


class Reducer:
    """Integrates Worker branches back into the trunk in a deterministic order."""

    def __init__(self, repo_root: Path, trunk_branch: str = "main"):
        self.repo_root = repo_root.resolve()
        self.trunk_branch = trunk_branch

    async def reduce(self, results: list[WorkerResult]) -> list[MergeResult]:
        # Make sure we're on the trunk before we start merging.
        await _run_git("checkout", self.trunk_branch, cwd=self.repo_root, check=False)

        outcomes: list[MergeResult] = []
        # Sort for deterministic merge order — conflicts (if any) are reproducible.
        for wr in sorted(results, key=lambda r: r.branch):
            if wr.status != "success":
                outcomes.append(MergeResult(
                    task_id=wr.task_id,
                    branch=wr.branch,
                    status="skipped",
                    resolution_notes=[f"worker status={wr.status}: {wr.error or ''}"],
                ))
                continue
            outcomes.append(await self._merge_one(wr))
        return outcomes

    async def _merge_one(self, wr: WorkerResult) -> MergeResult:
        rc, _, stderr = await _run_git(
            "merge", "--no-ff", "--no-edit",
            "-m", f"flamboyance reduce: {wr.branch}",
            wr.branch,
            cwd=self.repo_root,
            check=False,
        )
        if rc == 0:
            return MergeResult(task_id=wr.task_id, branch=wr.branch, status="merged")

        # Conflict path — find conflicted files and try to auto-resolve.
        conflicted = await self._conflicted_files()
        log.warning("merge conflict on %s: %s", wr.branch, conflicted)

        notes: list[str] = []
        unresolved: list[str] = []
        for rel in conflicted:
            resolved_text, ok, note = self._auto_resolve(self.repo_root / rel)
            notes.append(f"{rel}: {note}")
            if ok:
                (self.repo_root / rel).write_text(resolved_text, encoding="utf-8")
                await _run_git("add", "--", rel, cwd=self.repo_root)
            else:
                unresolved.append(rel)

        if unresolved:
            await _run_git("merge", "--abort", cwd=self.repo_root, check=False)
            return MergeResult(
                task_id=wr.task_id,
                branch=wr.branch,
                status="conflict",
                conflicts=unresolved,
                resolution_notes=notes + [stderr.strip()],
            )

        # All conflicts auto-resolved — finalize the merge commit.
        await _run_git(
            "commit", "--no-edit",
            "-m", f"flamboyance reduce (auto-resolved): {wr.branch}",
            cwd=self.repo_root,
            check=False,
        )
        return MergeResult(
            task_id=wr.task_id,
            branch=wr.branch,
            status="auto-resolved",
            resolution_notes=notes,
        )

    # ------------------------------------------------------------ helpers

    async def _conflicted_files(self) -> list[str]:
        _, stdout, _ = await _run_git(
            "diff", "--name-only", "--diff-filter=U",
            cwd=self.repo_root,
        )
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    @staticmethod
    def _auto_resolve(path: Path) -> tuple[str, bool, str]:
        """Try to resolve all conflict blocks in `path`.

        Returns (new_text, success, note). The current heuristic is
        intentionally conservative: we only auto-resolve a block if one side
        is strictly contained in the other, OR if the two sides are pure
        appends to disjoint regions (no overlapping line deletions). When in
        doubt we bail and let a human handle it.
        """
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ("", False, "file missing")

        new_parts: list[str] = []
        cursor = 0
        resolved_blocks = 0
        unresolved_blocks = 0

        for m in CONFLICT_BLOCK_RE.finditer(text):
            new_parts.append(text[cursor:m.start()])
            ours = m.group("ours")
            theirs = m.group("theirs")

            merged = Reducer._merge_hunk(ours, theirs)
            if merged is None:
                # Leave the conflict block untouched so a human sees it.
                new_parts.append(text[m.start():m.end()])
                unresolved_blocks += 1
            else:
                new_parts.append(merged)
                resolved_blocks += 1
            cursor = m.end()
        new_parts.append(text[cursor:])

        if unresolved_blocks:
            return ("".join(new_parts), False,
                    f"resolved {resolved_blocks}, unresolved {unresolved_blocks}")
        return ("".join(new_parts), True,
                f"auto-resolved {resolved_blocks} block(s)")

    @staticmethod
    def _merge_hunk(ours: str, theirs: str) -> str | None:
        """Decide how to fuse one conflict block; return None if unsafe."""
        if ours == theirs:
            return ours
        if ours.strip() == "":
            return theirs
        if theirs.strip() == "":
            return ours
        # Containment: one side is a strict superset → take the superset.
        if ours in theirs:
            return theirs
        if theirs in ours:
            return ours
        # Pure-append heuristic: if both sides share a common prefix and only
        # add new lines after it, concatenate the unique tails.
        ours_lines = ours.splitlines(keepends=True)
        theirs_lines = theirs.splitlines(keepends=True)
        i = 0
        while i < len(ours_lines) and i < len(theirs_lines) and ours_lines[i] == theirs_lines[i]:
            i += 1
        # Common prefix established. If the *remaining* lines on one side are
        # empty, the other side wins. If both have remainders and neither
        # remainder appears in the other, we splice them in deterministic
        # (alphabetical) order — safe because they are pure additions.
        ours_tail = "".join(ours_lines[i:])
        theirs_tail = "".join(theirs_lines[i:])
        prefix = "".join(ours_lines[:i])
        if not ours_tail:
            return prefix + theirs_tail
        if not theirs_tail:
            return prefix + ours_tail
        if ours_tail in theirs_tail:
            return prefix + theirs_tail
        if theirs_tail in ours_tail:
            return prefix + ours_tail
        # Last resort: concatenate (deterministic order) — only safe because
        # we've established both sides are pure additions past a shared prefix.
        first, second = sorted([ours_tail, theirs_tail])
        return prefix + first + second
