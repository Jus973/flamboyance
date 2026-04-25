"""Flamboyance CLI.

Subcommands:
    discover   Scan a repo and print the auto-detected refactor tasks.
    prepare    Plan + create the parallel worktrees (no LLM calls).
    run        Full pipeline: plan → prepare → execute → reduce.
    clean      Tear down any flamboyance worktrees left behind.

Examples:
    flamboyance discover --root ./my-project --num-tasks 3
    flamboyance run      --root ./my-project --num-tasks 3 --output report.json
    flamboyance prepare  --root ./my-project --keep
    flamboyance clean    --root ./my-project
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from .context_mapper import ContextMapper
from .groq_llm import DEFAULT_GROQ_MODEL, GroqLLMClient
from .master import Orchestrator
from .worker import MockLLMClient
from .worktree import WorktreeManager


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flamboyance",
        description="Spark-style master/worker/reducer for parallel LLM coding tasks.",
    )
    p.add_argument("--root", type=Path, default=Path.cwd(),
                   help="Path to the target git repo (default: cwd).")
    p.add_argument("--trunk", default="main",
                   help="Trunk branch to merge into (default: main).")
    p.add_argument("-v", "--verbose", action="count", default=0)

    sub = p.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("discover", help="Print auto-detected independent tasks.")
    pd.add_argument("--num-tasks", "-n", type=int, default=3)

    pp = sub.add_parser("prepare", help="Create worktrees, but don't run workers.")
    pp.add_argument("--num-tasks", "-n", type=int, default=3)
    pp.add_argument("--keep", action="store_true",
                    help="Leave worktrees on disk after this command exits.")

    pr = sub.add_parser("run", help="Full pipeline.")
    pr.add_argument("--num-tasks", "-n", type=int, default=3)
    pr.add_argument(
        "--llm",
        choices=("mock", "groq"),
        default="mock",
        help="Worker backend: local mock (default) or Groq (Llama 3.3 70B).",
    )
    pr.add_argument(
        "--groq-model",
        default=DEFAULT_GROQ_MODEL,
        help=f"Groq model id (default: {DEFAULT_GROQ_MODEL}).",
    )
    pr.add_argument("--keep", action="store_true",
                    help="Don't tear down worktrees after the run.")
    pr.add_argument("--skip-reduce", action="store_true",
                    help="Stop after Workers finish; don't merge back.")
    pr.add_argument("--output", "-o", type=Path,
                    help="Write the JSON RunReport to this path.")
    pr.add_argument("--concurrency", type=int, default=8)

    sub.add_parser("clean", help="Remove any flamboyance worktrees in the repo.")

    return p


def _setup_logging(verbose: int) -> None:
    level = logging.WARNING - 10 * min(verbose, 2)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------- commands

async def _cmd_discover(args: argparse.Namespace) -> int:
    mapper = ContextMapper(args.root)
    graph, tasks = mapper.build_tasks(n=args.num_tasks)
    payload = {
        "root": str(args.root),
        "scanned_files": len(graph.files),
        "shared_context": mapper.shared_context(graph),
        "tasks": [t.to_dict() for t in tasks],
    }
    print(json.dumps(payload, indent=2))
    return 0


async def _cmd_prepare(args: argparse.Namespace) -> int:
    orch = Orchestrator(args.root, trunk_branch=args.trunk)
    try:
        tasks = await orch.plan(n=args.num_tasks)
        jobs = await orch.prepare(tasks)
        print(json.dumps([
            {
                "task_id": j.task.task_id,
                "label": j.task.label,
                "branch": j.worktree.branch,
                "worktree": str(j.worktree.path),
                "files_to_edit": list(j.task.files_to_edit),
                "context_files": list(j.task.context_files),
            }
            for j in jobs
        ], indent=2))
        return 0
    finally:
        if not args.keep:
            await orch.worktrees.cleanup_all()


async def _cmd_run(args: argparse.Namespace) -> int:
    if args.llm == "groq":
        llm = GroqLLMClient(model=args.groq_model)
    else:
        llm = MockLLMClient()

    orch = Orchestrator(
        args.root,
        trunk_branch=args.trunk,
        llm=llm,
        max_concurrency=args.concurrency,
    )
    report = await orch.run(
        n=args.num_tasks,
        keep_worktrees=args.keep,
        skip_reduce=args.skip_reduce,
    )
    payload = report.to_dict()
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"Wrote report to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(payload, indent=2))

    failed = sum(1 for w in report.worker_results if w.status != "success")
    conflicts = sum(1 for m in report.merge_results if m.status == "conflict")
    return 0 if (failed == 0 and conflicts == 0) else 1


async def _cmd_clean(args: argparse.Namespace) -> int:
    # We don't keep state across processes, so the safest thing is to ask
    # git for every worktree it knows about and remove the ones whose
    # branch lives under the `flamboyance/` namespace.
    from .worktree import _run_git
    _, stdout, _ = await _run_git(
        "worktree", "list", "--porcelain", cwd=args.root,
    )
    removed = 0
    cur: dict[str, str] = {}
    for line in stdout.splitlines() + [""]:
        if not line.strip():
            if cur and cur.get("branch", "").startswith("refs/heads/flamboyance/"):
                wt_path = cur.get("worktree", "")
                branch = cur["branch"].removeprefix("refs/heads/")
                await _run_git("worktree", "remove", "--force", wt_path,
                               cwd=args.root, check=False)
                await _run_git("branch", "-D", branch,
                               cwd=args.root, check=False)
                removed += 1
            cur = {}
            continue
        key, _, value = line.partition(" ")
        cur[key] = value
    await _run_git("worktree", "prune", cwd=args.root, check=False)
    print(f"Removed {removed} flamboyance worktree(s).")
    return 0


# ---------------------------------------------------------------- entry

def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    _setup_logging(args.verbose)

    cmds = {
        "discover": _cmd_discover,
        "prepare": _cmd_prepare,
        "run": _cmd_run,
        "clean": _cmd_clean,
    }
    return asyncio.run(cmds[args.cmd](args))


if __name__ == "__main__":
    raise SystemExit(main())
