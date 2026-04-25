"""Local sequential runner for UX-friction agents.

Runs each persona agent one after another in a single process.
Produces a Markdown friction report when all agents finish.

Usage::

    python -m agents.runner_local --url http://localhost:3000

Or programmatically::

    from agents.runner_local import run_local
    results = asyncio.run(run_local("http://localhost:3000"))
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .agent import AgentResult, run_agent
from .persona import DEFAULT_PERSONAS, Persona, resolve_personas
from .persona_loader import load_personas_file, merge_personas
from .report import generate_report

log = logging.getLogger(__name__)


@dataclass
class RunState:
    run_id: str
    url: str
    personas: list[Persona]
    results: list[AgentResult] = field(default_factory=list)
    status: str = "pending"  # "pending" | "running" | "done" | "stopped"
    _stop_flag: bool = field(default=False, repr=False)

    def request_stop(self) -> None:
        self._stop_flag = True

    @property
    def stopped(self) -> bool:
        return self._stop_flag


# Global registry so the MCP server can track active/completed runs.
_runs: dict[str, RunState] = {}


def get_run(run_id: str) -> RunState | None:
    return _runs.get(run_id)


def all_runs() -> dict[str, RunState]:
    return dict(_runs)


async def run_local(
    url: str,
    persona_names: list[str] | None = None,
    *,
    timeout_s: float = 60.0,
    headless: bool = True,
    run_id: str | None = None,
    personas_file: str | Path | None = None,
) -> RunState:
    """Run agents sequentially and return the completed RunState.

    Args:
        url: Target URL to test.
        persona_names: Names of personas to run (None = all available).
        timeout_s: Per-agent session timeout.
        headless: Run browser without visible UI.
        run_id: Optional run identifier (generated if not provided).
        personas_file: Optional JSON file with custom persona definitions.
    """
    available = dict(DEFAULT_PERSONAS)
    if personas_file:
        custom = load_personas_file(personas_file)
        available = merge_personas(custom, base=available, custom_overrides=True)

    if persona_names:
        personas = []
        for name in persona_names:
            if name not in available:
                raise ValueError(f"Unknown persona {name!r}. Available: {sorted(available)}")
            personas.append(available[name])
    else:
        personas = list(available.values())
    rid = run_id or str(uuid.uuid4())
    state = RunState(run_id=rid, url=url, personas=personas, status="running")
    _runs[rid] = state

    for persona in personas:
        if state.stopped:
            break
        log.info("starting agent: %s", persona.name)
        result = await run_agent(
            url, persona, timeout_s=timeout_s, headless=headless
        )
        state.results.append(result)
        log.info(
            "agent %s finished: status=%s events=%d",
            persona.name,
            result.status,
            len(result.frustration_events),
        )

    state.status = "stopped" if state.stopped else "done"
    return state


def save_report(state: RunState, output_dir: str | Path = "reports") -> Path:
    """Generate and save a Markdown report to disk."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = generate_report(state)
    path = out / f"report-{state.run_id[:8]}.md"
    path.write_text(md, encoding="utf-8")
    log.info("report saved: %s", path)
    return path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run UX-friction agents locally")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument(
        "--personas", nargs="*", default=None, help="Persona names (default: all)"
    )
    parser.add_argument(
        "--personas-file",
        type=Path,
        default=None,
        help="JSON file with custom persona definitions",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.add_argument("--output", default="reports", help="Output directory")
    args = parser.parse_args()

    state = asyncio.run(
        run_local(
            args.url,
            args.personas,
            timeout_s=args.timeout,
            headless=args.headless,
            personas_file=args.personas_file,
        )
    )

    report_path = save_report(state, args.output)

    summary = {
        "run_id": state.run_id,
        "status": state.status,
        "agents": len(state.results),
        "total_events": sum(len(r.frustration_events) for r in state.results),
        "report": str(report_path),
    }
    json.dump(summary, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
