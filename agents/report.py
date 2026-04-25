"""Markdown report generator for UX-friction simulation results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runner_local import RunState


def generate_report(state: "RunState") -> str:
    """Produce a Markdown friction report from a completed RunState."""
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_events = sum(len(r.frustration_events) for r in state.results)

    lines.append(f"# Flamboyance UX Friction Report")
    lines.append("")
    lines.append(f"- **Run ID:** `{state.run_id}`")
    lines.append(f"- **Target URL:** {state.url}")
    lines.append(f"- **Status:** {state.status}")
    lines.append(f"- **Agents:** {len(state.results)}")
    lines.append(f"- **Total frustration events:** {total_events}")
    lines.append(f"- **Generated:** {now}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Persona | Status | Events | Elapsed |")
    lines.append("|---------|--------|--------|---------|")
    for r in state.results:
        lines.append(
            f"| {r.persona} | {r.status} | {len(r.frustration_events)} "
            f"| {r.elapsed_seconds:.1f}s |"
        )
    lines.append("")

    for r in state.results:
        lines.append(f"## Agent: {r.persona}")
        lines.append("")
        lines.append(f"- **Status:** {r.status}")
        lines.append(f"- **Elapsed:** {r.elapsed_seconds:.1f}s")
        if r.error:
            lines.append(f"- **Error:** {r.error}")
        lines.append("")

        if r.visited_urls:
            lines.append("### Navigation Path")
            lines.append("")
            for i, u in enumerate(r.visited_urls, 1):
                lines.append(f"{i}. {u}")
            lines.append("")

        if r.frustration_events:
            lines.append("### Frustration Events")
            lines.append("")
            for ev in r.frustration_events:
                kind = ev.get("kind", "unknown")
                desc = ev.get("description", "")
                lines.append(f"- **{kind}**: {desc}")
            lines.append("")

    if total_events == 0:
        lines.append("---")
        lines.append("")
        lines.append("*No frustration events detected during this simulation.*")
        lines.append("")

    return "\n".join(lines)
