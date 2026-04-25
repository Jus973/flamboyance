"""Async wrapper around `git worktree` for ephemeral parallel workspaces.

Each Worker gets its own checkout on its own branch. Worktrees share the
underlying object store with the parent repo (cheap to create, cheap to
destroy) and give us hard filesystem-level isolation between concurrent
Workers — no race conditions on `os.chdir`, no shared mutable index.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


class GitError(RuntimeError):
    """Raised when a git subprocess returns non-zero."""


@dataclass
class Worktree:
    path: Path
    branch: str
    base_ref: str


async def _run_git(
    *args: str,
    cwd: Path,
    check: bool = True,
) -> tuple[int, str, str]:
    """Run a git command asynchronously and capture its output."""
    log.debug("git %s  (cwd=%s)", " ".join(args), cwd)
    proc = await asyncio.create_subprocess_exec(
        "git",
        *args,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_b, stderr_b = await proc.communicate()
    stdout = stdout_b.decode(errors="replace")
    stderr = stderr_b.decode(errors="replace")
    if check and proc.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed ({proc.returncode}):\n{stderr.strip()}"
        )
    return proc.returncode or 0, stdout, stderr


class WorktreeManager:
    """Lifecycle manager for a pool of `git worktree`s rooted at one repo."""

    def __init__(self, repo_root: Path, workspace_root: Path | None = None):
        self.repo_root = repo_root.resolve()
        # Default to a sibling `.flamboyance/worktrees/` so we never pollute
        # the user's source tree with checkouts that get committed by accident.
        self.workspace_root = (
            workspace_root or self.repo_root / ".flamboyance" / "worktrees"
        ).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self._created: list[Worktree] = []

    async def ensure_repo(self) -> str:
        """Verify we're inside a git repo and return the current HEAD ref."""
        _, stdout, _ = await _run_git("rev-parse", "--show-toplevel", cwd=self.repo_root)
        if Path(stdout.strip()).resolve() != self.repo_root:
            raise GitError(f"{self.repo_root} is not the toplevel of a git repo")
        _, head, _ = await _run_git("rev-parse", "HEAD", cwd=self.repo_root)
        return head.strip()

    async def create(self, branch: str, base_ref: str | None = None) -> Worktree:
        """Create a fresh worktree on a new branch derived from `base_ref`.

        If the worktree directory already exists it is removed first — Workers
        always get a clean slate.
        """
        base = base_ref or await self.ensure_repo()
        # Use the branch's last segment as a directory name to keep paths sane.
        dir_name = branch.replace("/", "_")
        wt_path = self.workspace_root / dir_name
        if wt_path.exists():
            await self.remove(Worktree(path=wt_path, branch=branch, base_ref=base))

        # Delete any stale branch with the same name first; ignore failures.
        await _run_git("branch", "-D", branch, cwd=self.repo_root, check=False)

        await _run_git(
            "worktree",
            "add",
            "-b",
            branch,
            str(wt_path),
            base,
            cwd=self.repo_root,
        )
        wt = Worktree(path=wt_path, branch=branch, base_ref=base)
        self._created.append(wt)
        log.info("Created worktree %s @ %s", branch, wt_path)
        return wt

    async def remove(self, wt: Worktree) -> None:
        """Tear down a worktree and its branch."""
        await _run_git(
            "worktree", "remove", "--force", str(wt.path),
            cwd=self.repo_root, check=False,
        )
        # `worktree remove` may leave the directory if git lost track of it.
        if wt.path.exists():
            shutil.rmtree(wt.path, ignore_errors=True)
        await _run_git("branch", "-D", wt.branch, cwd=self.repo_root, check=False)
        log.info("Removed worktree %s", wt.branch)

    async def cleanup_all(self) -> None:
        """Remove every worktree this manager created in this process."""
        await asyncio.gather(*(self.remove(wt) for wt in self._created))
        self._created.clear()
        # `git worktree prune` cleans up any administrative leftovers.
        await _run_git("worktree", "prune", cwd=self.repo_root, check=False)
