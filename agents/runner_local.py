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
import os
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

# Directory for persisting run state to disk
_STATE_DIR = Path("results/.runs")


def _get_state_path(run_id: str) -> Path:
    """Get the path to the state file for a run."""
    return _STATE_DIR / f"{run_id}.json"


def _serialize_persona(persona: "Persona") -> dict[str, Any]:
    """Serialize a Persona to a JSON-compatible dict."""
    return {
        "name": persona.name,
        "patience": persona.patience,
        "tech_literacy": persona.tech_literacy,
        "goal": persona.goal,
        "tags": list(persona.tags),
        "early_exit_fraction": persona.early_exit_fraction,
        "max_actions": persona.max_actions,
        "viewport": list(persona.viewport),
        "prefers_visible_text": persona.prefers_visible_text,
        "slow_load_threshold_ms": persona.slow_load_threshold_ms,
        "long_dwell_threshold_s": persona.long_dwell_threshold_s,
        "rage_click_threshold": persona.rage_click_threshold,
        "focus_areas": list(persona.focus_areas),
        "frustration_triggers": list(persona.frustration_triggers),
        "detection_weights": list(persona.detection_weights),
        "success_url_patterns": list(persona.success_url_patterns),
        "success_text_patterns": list(persona.success_text_patterns),
    }


def _deserialize_persona(data: dict[str, Any]) -> "Persona":
    """Deserialize a Persona from a JSON-compatible dict."""
    return Persona(
        name=data["name"],
        patience=data["patience"],
        tech_literacy=data["tech_literacy"],
        goal=data["goal"],
        tags=tuple(data.get("tags", [])),
        early_exit_fraction=data.get("early_exit_fraction", 0.4),
        max_actions=data.get("max_actions", 50),
        viewport=tuple(data.get("viewport", [1280, 720])),
        prefers_visible_text=data.get("prefers_visible_text", False),
        slow_load_threshold_ms=data.get("slow_load_threshold_ms"),
        long_dwell_threshold_s=data.get("long_dwell_threshold_s"),
        rage_click_threshold=data.get("rage_click_threshold"),
        focus_areas=tuple(data.get("focus_areas", [])),
        frustration_triggers=tuple(data.get("frustration_triggers", [])),
        detection_weights=tuple(tuple(x) for x in data.get("detection_weights", [])),
        success_url_patterns=tuple(data.get("success_url_patterns", [])),
        success_text_patterns=tuple(data.get("success_text_patterns", [])),
    )


def _serialize_result(result: AgentResult) -> dict[str, Any]:
    """Serialize an AgentResult to a JSON-compatible dict."""
    return {
        "persona": result.persona,
        "status": result.status,
        "visited_urls": result.visited_urls,
        "frustration_events": result.frustration_events,
        "elapsed_seconds": result.elapsed_seconds,
        "error": result.error,
        "llm_mode": result.llm_mode,
        "llm_calls": result.llm_calls,
        "llm_tokens": result.llm_tokens,
        "action_history": result.action_history,
        # Skip page_screenshots to keep state files small
    }


def _deserialize_result(data: dict[str, Any]) -> AgentResult:
    """Deserialize an AgentResult from a JSON-compatible dict."""
    return AgentResult(
        persona=data["persona"],
        status=data["status"],
        visited_urls=data.get("visited_urls", []),
        frustration_events=data.get("frustration_events", []),
        elapsed_seconds=data.get("elapsed_seconds", 0.0),
        error=data.get("error"),
        llm_mode=data.get("llm_mode", False),
        llm_calls=data.get("llm_calls", 0),
        llm_tokens=data.get("llm_tokens", 0),
        action_history=data.get("action_history", []),
        page_screenshots={},  # Not persisted
    )


def _save_state(state: RunState, created_at: str | None = None) -> None:
    """Persist run state to disk using atomic write."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    data = {
        "run_id": state.run_id,
        "url": state.url,
        "status": state.status,
        "llm_mode": state.llm_mode,
        "personas": [_serialize_persona(p) for p in state.personas],
        "results": [_serialize_result(r) for r in state.results],
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Check for error attribute
    if hasattr(state, "_error"):
        data["error"] = state._error
    
    state_path = _get_state_path(state.run_id)
    
    # Atomic write: write to temp file, then rename
    fd, tmp_path = tempfile.mkstemp(dir=_STATE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, state_path)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _load_state(run_id: str) -> RunState | None:
    """Load run state from disk."""
    state_path = _get_state_path(run_id)
    if not state_path.exists():
        return None
    
    try:
        with open(state_path, encoding="utf-8") as f:
            data = json.load(f)
        
        personas = [_deserialize_persona(p) for p in data.get("personas", [])]
        results = [_deserialize_result(r) for r in data.get("results", [])]
        
        state = RunState(
            run_id=data["run_id"],
            url=data["url"],
            personas=personas,
            results=results,
            status=data.get("status", "done"),
            llm_mode=data.get("llm_mode", False),
        )
        
        # Restore error attribute if present
        if "error" in data:
            state._error = data["error"]
        
        return state
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.warning("Failed to load state for %s: %s", run_id, e)
        return None


def get_run(run_id: str) -> RunState | None:
    """Get run state, checking memory first then disk."""
    # Check in-memory cache first
    if run_id in _runs:
        return _runs[run_id]
    
    # Try loading from disk
    state = _load_state(run_id)
    if state is not None:
        # Cache in memory for future lookups
        _runs[run_id] = state
    return state


def all_runs() -> dict[str, RunState]:
    return dict(_runs)


def cleanup_old_state_files(max_age_hours: int = 24) -> int:
    """Remove state files older than max_age_hours.
    
    Also marks any 'running' state files as 'interrupted' since they
    represent orphaned runs from a previous server instance.
    
    Returns:
        Number of files cleaned up.
    """
    if not _STATE_DIR.exists():
        return 0
    
    cleaned = 0
    cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
    
    for state_file in _STATE_DIR.glob("*.json"):
        try:
            # Check file modification time
            mtime = state_file.stat().st_mtime
            if mtime < cutoff:
                state_file.unlink()
                cleaned += 1
                log.info("Cleaned up old state file: %s", state_file.name)
                continue
            
            # Check for orphaned running states
            with open(state_file, encoding="utf-8") as f:
                data = json.load(f)
            
            if data.get("status") == "running":
                # Mark as interrupted since server restarted
                data["status"] = "interrupted"
                data["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Atomic write
                fd, tmp_path = tempfile.mkstemp(dir=_STATE_DIR, suffix=".tmp")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    os.replace(tmp_path, state_file)
                    log.info("Marked orphaned run as interrupted: %s", data.get("run_id"))
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
                    
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Error processing state file %s: %s", state_file.name, e)
    
    return cleaned


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
    batch_size: int | None = None,
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
        batch_size: If set, run agents in batches of this size (parallel within batch).
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
    created_at = datetime.now(timezone.utc).isoformat()
    _save_state(state, created_at=created_at)

    if batch_size and batch_size > 1:
        # Run agents in batches (parallel within each batch)
        log.info("running %d agents in batches of %d", len(personas), batch_size)
        for i in range(0, len(personas), batch_size):
            if state.stopped:
                break
            batch = personas[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(personas) + batch_size - 1) // batch_size
            log.info("=== Batch %d/%d: %s ===", batch_num, total_batches, [p.name for p in batch])

            tasks = [
                run_agent(
                    url,
                    persona,
                    timeout_s=timeout_s,
                    headless=headless,
                    llm_mode=llm_mode,
                    max_llm_calls=max_llm_calls,
                )
                for persona in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for persona, result in zip(batch, results, strict=True):
                if isinstance(result, Exception):
                    log.error("agent %s failed: %s", persona.name, result)
                    state.results.append(
                        AgentResult(persona=persona.name, status="error", error=str(result))
                    )
                else:
                    state.results.append(result)
                    log.info(
                        "agent %s finished: status=%s events=%d%s",
                        persona.name,
                        result.status,
                        len(result.frustration_events),
                        f" llm_calls={result.llm_calls}" if llm_mode else "",
                    )
            # Save state after each batch
            _save_state(state, created_at=created_at)
    elif parallel and not llm_mode:
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
                state.results.append(
                    AgentResult(persona=persona.name, status="error", error=str(result))
                )
            else:
                state.results.append(result)
                log.info(
                    "agent %s finished: status=%s events=%d",
                    persona.name,
                    result.status,
                    len(result.frustration_events),
                )
        # Save state after parallel execution
        _save_state(state, created_at=created_at)
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
            # Save state after each agent in sequential mode
            _save_state(state, created_at=created_at)

    state.status = "stopped" if state.stopped else "done"
    _save_state(state, created_at=created_at)
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


def save_report(state: RunState, output_dir: str | Path = "results") -> Path:
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
    parser.add_argument("--personas", nargs="*", default=None, help="Persona names (default: all)")
    parser.add_argument(
        "--personas-file",
        type=Path,
        default=None,
        help="JSON file with custom persona definitions",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument("--llm", action="store_true", help="Use LLM vision model for navigation")
    parser.add_argument(
        "--max-llm-calls", type=int, default=None, help="Max LLM API calls per agent"
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Run heuristic agents in parallel for speed"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Run agents in parallel batches of N (e.g., --batch-size 3)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run both heuristic (parallel) and LLM (sequential) modes",
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
                batch_size=args.batch_size,
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
