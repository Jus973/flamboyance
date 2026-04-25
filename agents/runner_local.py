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
from .persona import DEFAULT_PERSONAS, Persona
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
    llm_mode: bool = False
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
    llm_mode: bool = False,
    max_llm_calls: int | None = None,
    parallel: bool = False,
) -> RunState:
    """Run agents sequentially and return the completed RunState.

    Args:
        url: Target URL to test.
        persona_names: Names of personas to run (None = all available).
        timeout_s: Per-agent session timeout.
        headless: Run browser without visible UI.
        run_id: Optional run identifier (generated if not provided).
        personas_file: Optional JSON file with custom persona definitions.
        llm_mode: If True, use LLM vision model for navigation decisions.
        max_llm_calls: Maximum LLM API calls per agent session.
        parallel: If True, run heuristic agents in parallel for speed.
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
    state = RunState(run_id=rid, url=url, personas=personas, status="running", llm_mode=llm_mode)
    _runs[rid] = state

    if parallel and not llm_mode:
        # Run heuristic agents in parallel for speed
        log.info("running %d agents in parallel (heuristic mode)", len(personas))
        tasks = [
            run_agent(url, persona, timeout_s=timeout_s, headless=headless, llm_mode=False)
            for persona in personas
            if not state.stopped
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for persona, result in zip(personas, results, strict=True):
            if isinstance(result, Exception):
                log.error("agent %s failed: %s", persona.name, result)
                state.results.append(AgentResult(
                    persona=persona.name, status="error", error=str(result)
                ))
            else:
                state.results.append(result)
                log.info(
                    "agent %s finished: status=%s events=%d",
                    persona.name, result.status, len(result.frustration_events)
                )
    else:
        # Sequential execution (required for LLM mode due to rate limits)
        for persona in personas:
            if state.stopped:
                break
            log.info("starting agent: %s%s", persona.name, " (LLM mode)" if llm_mode else "")
            result = await run_agent(
                url,
                persona,
                timeout_s=timeout_s,
                headless=headless,
                llm_mode=llm_mode,
                max_llm_calls=max_llm_calls,
            )
            state.results.append(result)
            log.info(
                "agent %s finished: status=%s events=%d%s",
                persona.name,
                result.status,
                len(result.frustration_events),
                f" llm_calls={result.llm_calls}" if llm_mode else "",
            )

    state.status = "stopped" if state.stopped else "done"
    return state


async def run_full(
    url: str,
    persona_names: list[str] | None = None,
    *,
    timeout_s: float = 60.0,
    headless: bool = True,
    run_id: str | None = None,
    personas_file: str | Path | None = None,
    max_llm_calls: int | None = None,
    heuristic_parallel: bool = True,
) -> tuple[RunState, RunState]:
    """Run both heuristic and LLM modes for all personas.

    Heuristic checks run in parallel (fast), LLM checks run sequentially (rate-limited).

    Args:
        url: Target URL to test.
        persona_names: Names of personas to run (None = all available).
        timeout_s: Per-agent session timeout.
        headless: Run browser without visible UI.
        run_id: Optional base run identifier.
        personas_file: Optional JSON file with custom persona definitions.
        max_llm_calls: Maximum LLM API calls per agent session.
        heuristic_parallel: If True, run heuristic agents in parallel.

    Returns:
        Tuple of (heuristic_state, llm_state).
    """
    base_id = run_id or str(uuid.uuid4())[:8]

    # Phase 1: Heuristic checks (parallel for speed)
    log.info("=== Phase 1: Heuristic checks (parallel=%s) ===", heuristic_parallel)
    heuristic_state = await run_local(
        url,
        persona_names,
        timeout_s=timeout_s,
        headless=headless,
        run_id=f"{base_id}-heuristic",
        personas_file=personas_file,
        llm_mode=False,
        parallel=heuristic_parallel,
    )

    # Phase 2: LLM checks (sequential due to rate limits)
    log.info("=== Phase 2: LLM checks (sequential) ===")
    llm_state = await run_local(
        url,
        persona_names,
        timeout_s=timeout_s,
        headless=headless,
        run_id=f"{base_id}-llm",
        personas_file=personas_file,
        llm_mode=True,
        max_llm_calls=max_llm_calls,
        parallel=False,
    )

    return heuristic_state, llm_state


def save_report(state: RunState, output_dir: str | Path = "reports") -> Path:
    """Generate and save a Markdown report to disk."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = generate_report(state)
    # Use full run_id to preserve suffixes like "-heuristic" or "-llm"
    # Truncate UUID part to 8 chars but keep any suffix
    if "-" in state.run_id[8:]:
        # Format: "uuid-suffix" -> "uuid[:8]-suffix"
        parts = state.run_id.split("-", 1)
        if len(parts) == 2 and len(parts[0]) >= 8:
            filename = f"report-{parts[0][:8]}-{parts[1]}.md"
        else:
            filename = f"report-{state.run_id}.md"
    else:
        filename = f"report-{state.run_id[:8]}.md"
    path = out / filename
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
    parser.add_argument("--llm", action="store_true", help="Use LLM vision model for navigation")
    parser.add_argument("--max-llm-calls", type=int, default=None, help="Max LLM API calls per agent")
    parser.add_argument(
        "--parallel", action="store_true",
        help="Run heuristic agents in parallel for speed"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Run both heuristic (parallel) and LLM (sequential) modes"
    )
    args = parser.parse_args()

    if args.full:
        # Run both modes
        heuristic_state, llm_state = asyncio.run(
            run_full(
                args.url,
                args.personas,
                timeout_s=args.timeout,
                headless=args.headless,
                personas_file=args.personas_file,
                max_llm_calls=args.max_llm_calls,
                heuristic_parallel=True,
            )
        )

        heuristic_report = save_report(heuristic_state, args.output)
        llm_report = save_report(llm_state, args.output)

        summary = {
            "mode": "full",
            "heuristic": {
                "run_id": heuristic_state.run_id,
                "status": heuristic_state.status,
                "agents": len(heuristic_state.results),
                "total_events": sum(len(r.frustration_events) for r in heuristic_state.results),
                "report": str(heuristic_report),
            },
            "llm": {
                "run_id": llm_state.run_id,
                "status": llm_state.status,
                "agents": len(llm_state.results),
                "total_events": sum(len(r.frustration_events) for r in llm_state.results),
                "total_llm_calls": sum(r.llm_calls for r in llm_state.results),
                "report": str(llm_report),
            },
        }
    else:
        state = asyncio.run(
            run_local(
                args.url,
                args.personas,
                timeout_s=args.timeout,
                headless=args.headless,
                personas_file=args.personas_file,
                llm_mode=args.llm,
                max_llm_calls=args.max_llm_calls,
                parallel=args.parallel,
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
