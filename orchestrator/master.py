"""Master Orchestrator — the asyncio driver.

Pipeline:
    scan ──▶ discover ──▶ select-independent ──▶ prepare (parallel) ──▶
        execute (parallel) ──▶ reduce (sequential, deterministic)

Every "fan-out" stage uses `asyncio.gather` so N Workers prepare/run in
true wall-clock parallel; the only sequential stage is the Reducer,
because git's index is itself single-writer.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .context_mapper import ContextMapper
from .models import MergeResult, Task, WorkerResult, dump_json
from .reducer import Reducer
from .worker import LLMClient, MockLLMClient, run_worker
from .worktree import Worktree, WorktreeManager

log = logging.getLogger(__name__)


@dataclass
class PreparedJob:
    """A Task bound to its isolated worktree, ready for a Worker to pick up."""

    task: Task
    worktree: Worktree


@dataclass
class RunReport:
    tasks: list[Task]
    worker_results: list[WorkerResult]
    merge_results: list[MergeResult]

    def to_dict(self) -> dict:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "worker_results": [w.to_dict() for w in self.worker_results],
            "merge_results": [m.to_dict() for m in self.merge_results],
        }


class Orchestrator:
    """Top-level driver. Construct once per pipeline run."""

    def __init__(
        self,
        repo_root: Path,
        *,
        trunk_branch: str = "main",
        llm: LLMClient | None = None,
        max_concurrency: int = 8,
    ):
        self.repo_root = repo_root.resolve()
        self.trunk_branch = trunk_branch
        self.llm = llm or MockLLMClient()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.worktrees = WorktreeManager(self.repo_root)
        self.mapper = ContextMapper(self.repo_root)
        self.reducer = Reducer(self.repo_root, trunk_branch=trunk_branch)

    # ------------------------------------------------------------ planning

    async def plan(self, n: int = 3) -> list[Task]:
        """Build the task plan from the repo (no worktrees yet)."""
        await self.worktrees.ensure_repo()
        _, tasks = self.mapper.build_tasks(n=n)
        log.info("Planned %d independent task(s)", len(tasks))
        for t in tasks:
            log.info("  • %s  files=%s  ctx=%d",
                     t.label, list(t.files_to_edit), len(t.context_files))
        return tasks

    # ---------------------------------------------------- worker preparation

    async def prepare(self, tasks: Sequence[Task]) -> list[PreparedJob]:
        """Create one worktree per task, *in parallel*. This is the step the
        spec asks us to make truly simultaneous."""
        head = await self.worktrees.ensure_repo()

        async def _prep(task: Task) -> PreparedJob:
            async with self.semaphore:
                wt = await self.worktrees.create(task.branch_name, base_ref=head)
                # Persist the task manifest as a *sibling* of the worktree so
                # it never appears in `git status` (otherwise the Worker's
                # sandbox check would flag it as an unauthorized modification).
                # An out-of-process Worker can still recover its task by
                # reading <worktree_path>.task.json.
                manifest = wt.path.with_suffix(wt.path.suffix + ".task.json")
                dump_json(task.to_dict(), manifest)
                return PreparedJob(task=task, worktree=wt)

        jobs = await asyncio.gather(*(_prep(t) for t in tasks))
        log.info("Prepared %d worktree(s) in parallel", len(jobs))
        return list(jobs)

    # -------------------------------------------------------- worker execution

    async def execute(self, jobs: Sequence[PreparedJob]) -> list[WorkerResult]:
        async def _run(job: PreparedJob) -> WorkerResult:
            async with self.semaphore:
                return await run_worker(job.task, job.worktree, self.llm)
        return list(await asyncio.gather(*(_run(j) for j in jobs)))

    # --------------------------------------------------------------- reduce

    async def reduce(self, results: Sequence[WorkerResult]) -> list[MergeResult]:
        return await self.reducer.reduce(list(results))

    # ----------------------------------------------------------------- run

    async def run(
        self,
        n: int = 3,
        *,
        keep_worktrees: bool = False,
        skip_reduce: bool = False,
    ) -> RunReport:
        try:
            tasks = await self.plan(n=n)
            if not tasks:
                return RunReport(tasks=[], worker_results=[], merge_results=[])

            jobs = await self.prepare(tasks)
            worker_results = await self.execute(jobs)
            merge_results = (
                [] if skip_reduce else await self.reduce(worker_results)
            )
            return RunReport(
                tasks=tasks,
                worker_results=worker_results,
                merge_results=merge_results,
            )
        finally:
            if not keep_worktrees:
                await self.worktrees.cleanup_all()
