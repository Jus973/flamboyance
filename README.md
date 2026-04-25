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
| `agents/` | Personas, `runner_local`, `runner_mutation`, single-agent `agent` module, event detection, Markdown reports. |
| `mcp/` | `python -m mcp` — FastMCP server (`run_simulation`, `get_live_feed`, `get_report`, `stop_simulation`, `run_mutation_test_tool`). |
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

| Name | Patience | Tech Literacy | Special Behavior | Goal |
|------|----------|---------------|------------------|------|
| `frustrated_exec` | 0.2 | 0.8 | Early exit (30%) | Complete a purchase flow quickly |
| `non_tech_senior` | 0.5 | 0.2 | Skips hidden menus | Find and read account settings |
| `power_user` | 0.9 | 0.9 | — | Navigate all features and check edge cases |
| `casual_browser` | 0.5 | 0.5 | — | Browse around and see what's available |
| `anxious_newbie` | 0.3 | 0.3 | Early exit, skips hidden | Sign up without getting confused |
| `methodical_tester` | 0.95 | 0.6 | 100 max actions | Systematically check every link and form |
| `mobile_commuter` | 0.25 | 0.85 | Mobile viewport (375x667) | Quickly check order status on the go |
| `accessibility_user` | 0.7 | 0.35 | Prefers visible text | Navigate using clear labels and affordances |

**Derived behaviors:**
- **Patience < 0.4** triggers early give-up (exits after `early_exit_fraction` of timeout)
- **Tech literacy < 0.5** skips elements with `aria-expanded="false"` (collapsed menus)
- **`prefers_visible_text`** skips icon-only / unlabeled buttons

## Custom Personas

Load personas from a JSON file without editing code:

```bash
python -m agents.runner_local --url http://localhost:3000 --personas-file my_personas.json
```

File format:

```json
{
  "personas": [
    {
      "name": "my_custom",
      "patience": 0.4,
      "tech_literacy": 0.7,
      "goal": "Test the checkout flow",
      "viewport": [375, 667],
      "prefers_visible_text": true
    }
  ]
}
```

Custom personas merge with built-ins; same-name entries override.

## Mutation Testing

Test how personas behave when UI elements are broken, hidden, or degraded:

```bash
# Use a built-in mutation scenario
python -m agents.runner_mutation --url http://localhost:3000 --mutation broken_checkout

# Use a custom mutation scenario (JSON)
python -m agents.runner_mutation --url http://localhost:3000 \
  --mutation '{"name": "custom", "hide": ["#checkout-btn"], "disable": [".nav"]}'
```

### Built-in Mutation Scenarios

| Name | Effect |
|------|--------|
| `broken_checkout` | Hides checkout buttons |
| `no_nav` | Removes navigation elements |
| `slow_submit` | Adds 3s delay to form submissions |
| `disabled_forms` | Disables all form inputs |
| `hidden_cta` | Hides call-to-action buttons |

### MCP Tool

The `run_mutation_test_tool` MCP tool allows mutation testing via Cascade:

```python
# Example: Test with hidden checkout button
await run_mutation_test_tool(
    url="http://localhost:3000",
    mutations={"name": "test", "hide": ["#checkout-btn"]},
    personas=["frustrated_exec"],
    llm_mode=True,
)
```

### Mutation Schema

```python
MutationScenario(
    name="example",
    hide=["#selector"],           # visibility: hidden
    disable=[".selector"],        # pointer-events: none
    remove=["nav"],               # remove from DOM
    delay_clicks={"button": 3000} # delay clicks by ms
)
```

---

## Testing

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest tests/ -v
```

Tests cover report shape, persona validation, frustration event detection, custom persona loading, and mutation scenarios (`tests/test_report.py`, `tests/test_persona.py`, `tests/test_events.py`, `tests/test_persona_loader.py`, `tests/test_mutations.py`).
