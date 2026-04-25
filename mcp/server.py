"""FastMCP server exposing four tools for Cascade / extension integration.

Tools
-----
1. ``run_simulation(url, personas, mode, timeout)`` → run_id
2. ``get_live_feed(run_id)`` → [AgentStatus]
3. ``get_report(run_id)`` → markdown
4. ``stop_simulation(run_id)`` → bool

Start with::

    python -m mcp.server          # stdio transport (for Cascade)
    python -m mcp.server --http   # HTTP on :8765 (for extension sidebar)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from typing import Any

from mcp.server.fastmcp import FastMCP

from agents.persona import resolve_personas
from agents.report import generate_report
from agents.runner_local import RunState, get_run, run_local, save_report

log = logging.getLogger(__name__)

mcp = FastMCP(
    "Flamboyance UX-Friction",
    description="Spawn synthetic browser agents to detect UX friction in web apps.",
)

# Background tasks keyed by run_id so we can cancel them.
_tasks: dict[str, asyncio.Task[RunState]] = {}


@mcp.tool()
async def run_simulation(
    url: str,
    personas: list[str] | None = None,
    mode: str = "local",
    timeout: int = 60,
    personas_file: str | None = None,
) -> dict[str, Any]:
    """Start a UX-friction simulation against *url*.

    Args:
        url: Target web application URL.
        personas: List of persona names (default: all built-in personas).
        mode: Execution mode — ``"local"`` (sequential) or ``"docker"`` (parallel).
        timeout: Per-agent timeout in seconds.
        personas_file: Optional path to a JSON file with custom persona definitions.

    Returns:
        ``{"run_id": "<uuid>"}``
    """
    run_id = str(uuid.uuid4())

    if mode == "docker":
        log.info("Docker mode requested — delegating to local for now (run %s)", run_id)

    task = asyncio.create_task(
        run_local(
            url,
            personas,
            timeout_s=float(timeout),
            run_id=run_id,
            personas_file=personas_file,
        )
    )
    _tasks[run_id] = task

    return {"run_id": run_id}


@mcp.tool()
async def get_live_feed(run_id: str) -> dict[str, Any]:
    """Return live status of each agent in a running simulation.

    Args:
        run_id: The simulation run ID returned by ``run_simulation``.

    Returns:
        ``{"run_id": "...", "status": "...", "agents": [...]}``
    """
    state = get_run(run_id)
    if state is None:
        return {"run_id": run_id, "status": "not_found", "agents": []}

    agents: list[dict[str, Any]] = []
    for r in state.results:
        agents.append(
            {
                "persona": r.persona,
                "status": r.status,
                "currentUrl": r.visited_urls[-1] if r.visited_urls else "",
                "frustrationEvents": [
                    e.get("description", "") for e in r.frustration_events
                ],
                "elapsedSeconds": r.elapsed_seconds,
            }
        )

    # Include personas that haven't started yet.
    finished_names = {r.persona for r in state.results}
    for p in state.personas:
        if p.name not in finished_names:
            agents.append(
                {
                    "persona": p.name,
                    "status": "pending" if state.status == "running" else "skipped",
                    "currentUrl": "",
                    "frustrationEvents": [],
                    "elapsedSeconds": 0.0,
                }
            )

    return {"run_id": run_id, "status": state.status, "agents": agents}


@mcp.tool()
async def get_report(run_id: str) -> dict[str, Any]:
    """Generate a Markdown friction report for a completed simulation.

    Args:
        run_id: The simulation run ID.

    Returns:
        ``{"run_id": "...", "markdown": "..."}``
    """
    state = get_run(run_id)
    if state is None:
        return {"run_id": run_id, "markdown": f"# Error\n\nRun `{run_id}` not found."}

    md = generate_report(state)

    try:
        path = save_report(state)
        log.info("report saved to %s", path)
    except Exception as exc:
        log.warning("could not save report: %s", exc)

    return {"run_id": run_id, "markdown": md}


@mcp.tool()
async def stop_simulation(run_id: str) -> dict[str, Any]:
    """Stop a running simulation.

    Args:
        run_id: The simulation run ID.

    Returns:
        ``{"run_id": "...", "stopped": true/false}``
    """
    state = get_run(run_id)
    if state is None:
        return {"run_id": run_id, "stopped": False}

    state.request_stop()

    task = _tasks.get(run_id)
    if task and not task.done():
        task.cancel()

    return {"run_id": run_id, "stopped": True}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Flamboyance MCP Server")
    parser.add_argument(
        "--http", action="store_true", help="Run HTTP transport on port 8765"
    )
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
