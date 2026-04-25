# Flamboyance

**Playwright-driven synthetic personas** that browse a web app, record UX friction, and expose tools via **MCP** plus a **VS Code / Windsurf** sidebar.

```
┌─────────────────────────────────────────────────────────────────┐
│  agents/           Playwright personas · local runner · reports │
│  mcp/              FastMCP tools (stdio or HTTP)               │
│  extension/        VS Code webview + MCP client                │
│  docker/           Agent + MCP images (compose)                │
└─────────────────────────────────────────────────────────────────┘
```

## Layout

| Path | Purpose |
| --- | --- |
| `agents/` | Personas, `runner_local`, single-agent `agent` module, event detection, Markdown reports. |
| `mcp/` | `python -m mcp` — FastMCP server (`run_simulation`, `get_live_feed`, `get_report`, `stop_simulation`). |
| `extension/` | TypeScript VS Code extension ("UX Friction Monitor"). |
| `docker/` | `Dockerfile.agent` + `docker-compose.yml` for containerized agents / MCP HTTP. |
| `tests/` | `pytest` for agent report/persona/events. |

**Python dependencies** are declared in [`pyproject.toml`](./pyproject.toml) (`playwright`, `mcp[cli]`, `pydantic`). **`requirements.txt`** only points at that file.

---

## Install

```bash
git clone <this-repo>
cd flamboyance
python3 -m pip install -e .
```

## Local runner (sequential)

```bash
python -m agents.runner_local --url http://localhost:3000
```

## Single agent (one persona)

```bash
python -m agents.agent --url http://localhost:3000 --persona frustrated_exec
```

## MCP server

```bash
python -m mcp.server              # stdio (e.g. Cascade)
python -m mcp.server --http --port 8765   # HTTP for the extension sidebar
```

## VS Code extension

```bash
cd extension
npm install
npm run compile
# Load the folder in VS Code; use "Run Simulation" from the command palette.
```

## Docker

From `docker/`:

```bash
TARGET_URL=http://host.docker.internal:3000 docker compose up
```

Build context must include `agents/` and `mcp/` (see `Dockerfile.agent`). Compose defines several agent services plus an `mcp-server` on port **8765**.

---

## Built-in Personas

| Name | Patience | Tech Literacy | Goal |
|------|----------|---------------|------|
| `frustrated_exec` | 0.2 | 0.8 | Complete a purchase flow quickly |
| `non_tech_senior` | 0.5 | 0.2 | Find and read account settings |
| `power_user` | 0.9 | 0.9 | Navigate all features and check edge cases |

## Testing

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -v
```

Tests cover report shape, persona validation, and frustration event detection (`tests/test_report.py`, `tests/test_persona.py`, `tests/test_events.py`).
