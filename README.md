# Flamboyance

This repository is a **monorepo** with two related tracks:

1. **Parallel coding orchestrator** (`orchestrator/`) — Spark-style master / worker / reducer over **git worktrees** and **asyncio**, with optional **Groq** (Llama 3.3 70B). Spec: [`orchestrator_spec.md`](./orchestrator_spec.md).
2. **UX friction agents** (`agents/`, `mcp/`, `extension/`, `docker/`) — **Playwright**-driven synthetic personas that browse a web app, record friction, and expose tools via **MCP** plus a **VS Code** sidebar.

```
┌─────────────────────────────────────────────────────────────────┐
│  orchestrator/     git worktrees · context mapper · merge back  │
├─────────────────────────────────────────────────────────────────┤
│  agents/           Playwright personas · local runner · reports   │
│  mcp/              FastMCP tools (stdio or HTTP)                  │
│  extension/        VS Code webview + MCP client                  │
│  docker/           Agent + MCP images (compose)                   │
└─────────────────────────────────────────────────────────────────┘
```

## Layout

| Path | Purpose |
| --- | --- |
| `orchestrator/` | CLI (`flamboyance`), master, worktrees, context mapper, worker + Groq, reducer. |
| `agents/` | Personas, `runner_local`, single-agent `agent` module, event detection, Markdown reports. |
| `mcp/` | `python -m mcp` — FastMCP server (`run_simulation`, `get_live_feed`, `get_report`, `stop_simulation`). |
| `extension/` | TypeScript VS Code extension (“UX Friction Monitor”). |
| `docker/` | `Dockerfile.agent` + `docker-compose.yml` for containerized agents / MCP HTTP. |
| `examples/` | `sample_project/` (Python demo repo) and `smoke_test.sh` for the orchestrator. |
| `tests/` | `pytest` for orchestrator helpers + agent report/persona/events. |

**Python dependencies** are declared in [`pyproject.toml`](./pyproject.toml) (`groq`, `playwright`, `mcp[cli]`, `pydantic`). **`requirements.txt`** only points at that file.

---

## 1. Parallel coding orchestrator

High-level flow (see diagram in [`orchestrator_spec.md`](./orchestrator_spec.md)):

- **Master** scans Python files, builds an import graph, finds refactor tasks (`# REFACTOR:` / `# TASK:` markers or fallbacks), and keeps only **independent** tasks (disjoint files, no import edge between edit sets).
- **Workers** run in separate **git worktrees**; each receives `files_to_edit`, `context_files`, and an instruction. Edits outside the allowlist are rejected.
- **Reducer** merges worker branches into the trunk with `git merge --no-ff` and **limited** programmatic conflict resolution.

**Spec note:** the spec calls for a global linter/test step after merge; the current **reducer does not run** those commands — run your own CI or local `pytest` / `npm test` after a run.

### Install

```bash
git clone <this-repo>
cd flamboyance
python3 -m pip install -e .
# or without install:
PYTHONPATH=. python3 -m orchestrator --help
```

### CLI

```bash
flamboyance --root ./my-repo discover -n 3
flamboyance --root ./my-repo prepare -n 3 --keep
flamboyance --root ./my-repo run -n 3 --output report.json

export GROQ_API_KEY="your-key-here"   # never commit; rotate if exposed
flamboyance --root ./my-repo run -n 3 --llm groq --output report.json
flamboyance --root ./my-repo run --llm groq --groq-model llama-3.3-70b-versatile

flamboyance --root ./my-repo clean
```

### Orchestrator smoke test

```bash
./examples/smoke_test.sh
```

Copies `examples/sample_project/` into a temp git repo and runs **mock** workers (default). Expect three worker commits merged into `main` when independence holds.

### Minimum context & independence

- **Context:** direct importers + direct imports of edited files, plus a small “shared core” set (directory hints + high in-degree modules), capped (~12 files).
- **Independence:** `ContextMapper.select_independent` enforces disjoint `files_to_edit` and **no Python import edge** between tasks (see spec §4).

### Custom LLM

Implement `orchestrator.worker.LLMClient` and pass `Orchestrator(repo_root, llm=YourClient())`. **Groq** is implemented in `orchestrator/groq_llm.py` (JSON object mode; full file contents per path).

---

## 2. UX friction agents

Synthetic browser “personas” probe a URL (timeouts, dead ends, unmet goals) and emit a Markdown report.

### Local runner (sequential)

```bash
python -m agents.runner_local --url http://localhost:3000
```

### Single agent (one persona)

```bash
python -m agents.agent --url http://localhost:3000 --persona frustrated_exec
```

### MCP server

```bash
python -m mcp.server              # stdio (e.g. Cascade)
python -m mcp.server --http --port 8765   # HTTP for the extension sidebar
```

### VS Code extension

```bash
cd extension
npm install
npm run compile
# Load the folder in VS Code; use “Run Simulation” from the command palette.
```

### Docker

From `docker/`:

```bash
TARGET_URL=http://host.docker.internal:3000 docker compose up
```

Build context must include `orchestrator/`, `agents/`, and `mcp/` (see `Dockerfile.agent`). Compose defines several agent services plus an `mcp-server` on port **8765**.

---

## Testing

```bash
python3 -m pip install -e ".[dev]"
PYTHONPATH=. python3 -m pytest tests/ -q
```

- **Orchestrator:** reducer merge helpers, context independence, worker sandbox, Groq JSON parsing.
- **Agents:** report shape, persona/events helpers (`tests/test_report.py`, `tests/test_persona.py`, `tests/test_events.py`).

End-to-end orchestration without API keys: `./examples/smoke_test.sh` (mock LLM). With Groq, set `GROQ_API_KEY` and add `--llm groq` to a `run` invocation against your own git repo.
