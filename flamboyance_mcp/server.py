"""FastMCP server exposing tools for Cascade / extension integration.

Primary Tools (recommended)
---------------------------
1. ``run_flamboyance(url, ...)`` → Start a UX friction test with sensible defaults
2. ``get_status(run_id)`` → Poll for progress/completion with concise summary

Legacy Tools
------------
3. ``run_simulation(url, personas, mode, timeout)`` → run_id
4. ``get_live_feed(run_id)`` → [AgentStatus]
5. ``get_report(run_id)`` → full markdown report
6. ``stop_simulation(run_id)`` → bool

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

from agents.mutations import COMMON_SCENARIOS, MutationScenario
from agents.report import generate_concise_summary, generate_report
from agents.runner_local import RunState, get_run, run_local, save_report
from agents.runner_mutation import generate_mutation_report, run_mutation_test
from agents.validation import ValidationError, validate_timeout, validate_url
from mcp.server.fastmcp import FastMCP

log = logging.getLogger(__name__)

def create_mcp(host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    return FastMCP(
        "Flamboyance UX-Friction",
        instructions="Spawn synthetic browser agents to detect UX friction in web apps.",
        host=host,
        port=port,
    )

mcp = create_mcp()

# Background tasks keyed by run_id so we can cancel them.
_tasks: dict[str, asyncio.Task[RunState]] = {}


@mcp.tool()
async def run_simulation(
    url: str,
    personas: list[str] | None = None,
    mode: str = "local",
    timeout: int = 60,
    personas_file: str | None = None,
    llm_mode: bool = False,
    max_llm_calls: int | None = None,
) -> dict[str, Any]:
    """Start a UX-friction simulation against *url*.

    Args:
        url: Target web application URL.
        personas: List of persona names (default: all built-in personas).
        mode: Execution mode — ``"local"`` (sequential) or ``"docker"`` (parallel).
        timeout: Per-agent timeout in seconds.
        personas_file: Optional path to a JSON file with custom persona definitions.
        llm_mode: If True, use LLM vision model for intelligent navigation instead of random clicks.
        max_llm_calls: Maximum LLM API calls per agent session (default: 30).

    Returns:
        ``{"run_id": "<uuid>", "llm_mode": bool}`` on success, or
        ``{"error": "message"}`` on validation failure.
    """
    try:
        validated_url = validate_url(url, allow_localhost=True)
        validated_timeout = validate_timeout(timeout)
    except ValidationError as e:
        log.warning("Validation failed: %s", e)
        return {"error": str(e)}

    run_id = str(uuid.uuid4())

    if mode == "docker":
        log.info("Docker mode requested — delegating to local for now (run %s)", run_id)

    task = asyncio.create_task(
        run_local(
            validated_url,
            personas,
            timeout_s=validated_timeout,
            run_id=run_id,
            personas_file=personas_file,
            llm_mode=llm_mode,
            max_llm_calls=max_llm_calls,
        )
    )
    _tasks[run_id] = task

    return {"run_id": run_id, "llm_mode": llm_mode}


@mcp.tool()
async def run_flamboyance(
    url: str,
    personas: list[str] | None = None,
    timeout: int = 60,
    llm_mode: bool = True,
    batch_size: int | None = 3,
    headless: bool = True,
    max_llm_calls: int | None = 30,
    personas_file: str | None = None,
) -> dict[str, Any]:
    """Run a UX friction test on a website.
    
    This is the primary tool for running Flamboyance tests. It provides
    sensible defaults and returns a run_id for status polling.
    
    Args:
        url: Target web application URL.
        personas: List of persona names (default: all built-in personas).
        timeout: Per-agent timeout in seconds (default: 60).
        llm_mode: If True (default), use LLM vision model for intelligent
            navigation. Set to False for fast heuristic-only mode (no API costs).
        batch_size: Run agents in parallel batches of N (default: 3).
            Set to None or 1 for sequential execution.
        headless: If True (default), run browser without visible UI.
            Set to False to show browser windows for debugging.
        max_llm_calls: Maximum LLM API calls per agent (default: 30).
            Only applies when llm_mode=True.
        personas_file: Optional path to JSON file with custom persona definitions.
    
    Returns:
        ``{"run_id": "<uuid>", "status": "running", "config": {...}}`` on success,
        or ``{"error": "message"}`` on validation failure.
    
    Examples:
        - Default (LLM mode, batched): run_flamboyance(url="http://localhost:5173")
        - Fast heuristic mode: run_flamboyance(url="...", llm_mode=False, batch_size=4)
        - Debug mode: run_flamboyance(url="...", headless=False)
    """
    try:
        validated_url = validate_url(url, allow_localhost=True)
        validated_timeout = validate_timeout(timeout)
    except ValidationError as e:
        log.warning("Validation failed: %s", e)
        return {"error": str(e)}

    run_id = str(uuid.uuid4())

    task = asyncio.create_task(
        run_local(
            validated_url,
            personas,
            timeout_s=validated_timeout,
            run_id=run_id,
            personas_file=personas_file,
            llm_mode=llm_mode,
            max_llm_calls=max_llm_calls,
            headless=headless,
            batch_size=batch_size,
        )
    )
    _tasks[run_id] = task

    config = {
        "llm_mode": llm_mode,
        "batch_size": batch_size,
        "headless": headless,
        "timeout": validated_timeout,
    }
    if llm_mode:
        config["max_llm_calls"] = max_llm_calls

    return {"run_id": run_id, "status": "running", "config": config}


@mcp.tool()
async def get_status(run_id: str) -> dict[str, Any]:
    """Get the status of a running or completed simulation.
    
    Returns progress while running, or a concise summary when done.
    Use this to poll for completion after calling run_flamboyance.
    
    Args:
        run_id: The simulation run ID returned by run_flamboyance or run_simulation.
    
    Returns:
        While running: ``{"run_id": "...", "status": "running", "progress": "3/8 agents complete"}``
        On completion: ``{"run_id": "...", "status": "done", "summary": "<concise markdown>"}``
        If not found: ``{"run_id": "...", "status": "not_found"}``
    """
    state = get_run(run_id)
    if state is None:
        return {"run_id": run_id, "status": "not_found"}

    if state.status == "running":
        completed = len(state.results)
        total = len(state.personas)
        return {
            "run_id": run_id,
            "status": "running",
            "progress": f"{completed}/{total} agents complete",
        }

    # Done or stopped - generate concise summary
    summary = generate_concise_summary(state)
    
    # Also save the full report
    try:
        path = save_report(state)
        log.info("report saved to %s", path)
    except Exception as exc:
        log.warning("could not save report: %s", exc)

    return {
        "run_id": run_id,
        "status": state.status,
        "summary": summary,
    }


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
        agent_info: dict[str, Any] = {
            "persona": r.persona,
            "status": r.status,
            "currentUrl": r.visited_urls[-1] if r.visited_urls else "",
            "frustrationEvents": [e.get("description", "") for e in r.frustration_events],
            "elapsedSeconds": r.elapsed_seconds,
        }
        if r.llm_mode:
            agent_info["llmCalls"] = r.llm_calls
            agent_info["llmTokens"] = r.llm_tokens
        agents.append(agent_info)

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


@mcp.tool()
async def run_mutation_test_tool(
    url: str,
    mutations: dict[str, Any],
    personas: list[str] | None = None,
    timeout: int = 60,
    llm_mode: bool = False,
    max_llm_calls: int | None = None,
) -> dict[str, Any]:
    """Run persona agents against a page with UI elements mutated.

    This tool applies mutations (hide/disable/remove elements) to simulate
    broken or degraded UX scenarios, then runs persona agents to detect
    frustration events caused by the mutations.

    Args:
        url: Target web application URL.
        mutations: Mutation scenario as dict with keys:
            - name (str): Scenario identifier
            - hide (list[str]): CSS selectors to hide (visibility: hidden)
            - disable (list[str]): Selectors to disable (pointer-events: none)
            - remove (list[str]): Selectors to remove from DOM
            - delay_clicks (dict[str, int]): Selector -> ms delay before click
        personas: List of persona names (default: all built-in personas).
        timeout: Per-agent timeout in seconds.
        llm_mode: If True, use LLM vision model for intelligent navigation.
        max_llm_calls: Maximum LLM API calls per agent session.

    Returns:
        Dict with mutation test results including:
        - scenario: Name of the mutation scenario
        - status: "done" | "error"
        - summary: Which personas failed/succeeded
        - markdown: Full report in Markdown format

    Example mutations:
        - {"name": "broken_checkout", "hide": ["#checkout-btn"]}
        - {"name": "no_nav", "remove": [".main-nav", "nav"]}
        - {"name": "slow_submit", "delay_clicks": {"button[type=submit]": 3000}}

    Built-in scenarios: broken_checkout, no_nav, slow_submit, disabled_forms, hidden_cta
    """
    try:
        validated_url = validate_url(url, allow_localhost=True)
        validated_timeout = validate_timeout(timeout)
    except ValidationError as e:
        log.warning("Validation failed: %s", e)
        return {"error": str(e)}

    # Handle built-in scenario names
    if isinstance(mutations, str):
        if mutations in COMMON_SCENARIOS:
            scenario = COMMON_SCENARIOS[mutations]
        else:
            return {
                "error": f"Unknown built-in scenario: {mutations}. Available: {list(COMMON_SCENARIOS.keys())}"
            }
    else:
        scenario = MutationScenario.from_dict(mutations)

    log.info("starting mutation test: scenario=%s url=%s", scenario.name, validated_url)

    result = await run_mutation_test(
        validated_url,
        scenario,
        personas,
        timeout_s=validated_timeout,
        headless=True,
        llm_mode=llm_mode,
        max_llm_calls=max_llm_calls,
    )

    markdown = generate_mutation_report(result)

    return {
        "scenario": result.scenario,
        "url": result.url,
        "status": result.status,
        "elapsed_seconds": result.elapsed_seconds,
        "error": result.error,
        "summary": result.summary(),
        "markdown": markdown,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Flamboyance MCP Server")
    parser.add_argument("--http", action="store_true", help="Run HTTP transport on port 8765")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    if args.http:
        # Reconfigure the module-level mcp instance for HTTP
        mcp._host = args.host
        mcp._port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
