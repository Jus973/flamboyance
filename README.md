# Flamboyance

A Spark-style **master / worker / reducer** orchestrator for parallelizing
LLM coding tasks against a single git repo. Built on `asyncio` and
`git worktree` — no external runtime dependencies.

The design follows [`orchestrator_spec.md`](./orchestrator_spec.md):

```
                  ┌──────────────────────────────────────┐
                  │            Master (Driver)           │
                  │  scan → build DAG → check deps       │
                  └──────────────┬───────────────────────┘
                                 │ asyncio.gather
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
   │ Worktree A      │  │ Worktree B      │  │ Worktree C      │
   │ Worker (LLM)    │  │ Worker (LLM)    │  │ Worker (LLM)    │
   │ files_to_edit ⊂ │  │ files_to_edit ⊂ │  │ files_to_edit ⊂ │
   │ context_files   │  │ context_files   │  │ context_files   │
   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
            └────────────────────┼────────────────────┘
                                 ▼
                    ┌─────────────────────────────┐
                    │      Reducer (Integrator)   │
                    │  merge --no-ff each branch  │
                    │  auto-resolve safe hunks    │
                    └─────────────────────────────┘
```

## Components

| Module | Role |
| --- | --- |
| `orchestrator/master.py` | Asyncio driver. Plans → Prepares → Executes → Reduces. |
| `orchestrator/worktree.py` | Async wrapper around `git worktree` for parallel isolation. |
| `orchestrator/context_mapper.py` | AST-based import graph + per-task minimum context set. |
| `orchestrator/worker.py` | Mock LLM worker loop with §4 sandbox enforcement. |
| `orchestrator/reducer.py` | Merges branches; auto-resolves disjoint additive conflicts. |
| `orchestrator/cli.py` | `discover`, `prepare`, `run`, `clean` subcommands. |

## Install

```bash
git clone <this-repo>
cd flamboyance
python3 -m pip install -e .
# or, without install:
PYTHONPATH=. python3 -m orchestrator --help
```

## CLI

```bash
# Print 3 independent refactor tasks the mapper finds in ./my-repo
flamboyance --root ./my-repo discover -n 3

# Just create the 3 worktrees and the per-task JSON manifests, then exit
flamboyance --root ./my-repo prepare -n 3 --keep

# Full pipeline: plan → 3 parallel worktrees → 3 parallel mock-LLM workers → reduce
flamboyance --root ./my-repo run -n 3 --output report.json

# Tear down every flamboyance/* worktree git knows about in the repo
flamboyance --root ./my-repo clean
```

## End-to-end smoke test

```bash
./examples/smoke_test.sh
```

This stages the demo project under `examples/sample_project/` (which contains
three `# REFACTOR:`-marked, mutually-independent modules) into a fresh tmp
git repo and runs the full pipeline. You should see three commits land on
`main`, one per Worker.

## How "minimum context" works

`ContextMapper.context_for(graph, files_to_edit)` returns the smallest set of
files a Worker needs to safely edit `files_to_edit`. It is the union of:

1. **Direct importers** of any edited file — so the LLM sees how its symbols
   are called and won't break callsites.
2. **Direct imports** of any edited file — so the LLM doesn't invent
   signatures that don't exist.
3. **Shared core context** — files in `types/`, `models/`, `schemas/`, etc.,
   *or* highly-imported across the repo (top-N by in-degree).

The result is capped (default 12 files) so the prompt stays small.

## Independence guarantee (spec §4)

`ContextMapper.select_independent` picks a maximal set of candidates whose
`files_to_edit` are (a) pairwise disjoint and (b) connected by no import
edge. Anything else is dropped from the parallel batch — the Master refuses
to race overlapping work.

## Plugging in a real LLM

`worker.LLMClient` is a `Protocol`. Drop in any class with this signature:

```python
async def edit(self, *, task, worktree_root, file_contents, context_contents) -> dict[str, str]: ...
```

…and pass it to `Orchestrator(repo_root, llm=YourClient())`. The Worker
sandbox will still reject any file outside `task.files_to_edit`.
