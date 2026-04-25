"""Markdown report generator for UX-friction simulation results."""

from __future__ import annotations

import base64
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .runner_local import RunState

log = logging.getLogger(__name__)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

FIX_RECOMMENDATIONS: dict[str, str] = {
    "slow_load": "Optimize page load performance: compress images, minify JS/CSS, enable caching, use lazy loading.",
    "dead_end": "Add navigation options or call-to-action buttons to this page.",
    "long_dwell": "Simplify the page content or add clearer guidance for user actions.",
    "rage_decoy": "Either make this element interactive or remove clickable styling (cursor:pointer, hover effects).",
    "js_error": "Fix the JavaScript error. Check the browser console for stack traces.",
    "broken_image": "Fix broken image src URLs or add appropriate fallback images.",
    "network_error": "Ensure API endpoints are available and returning correct responses.",
    "circular_navigation": "Improve navigation flow to prevent users from going in circles.",
    "rage_click": "Ensure the element responds to clicks or remove interactive affordances.",
    "unmet_goal": "Review the user flow for this goal and remove friction points.",
}


def _save_screenshot(
    screenshot_b64: str,
    run_id: str,
    persona: str,
    url: str,
    index: int,
    results_dir: str = "results",
) -> str | None:
    """Save a base64 screenshot to disk and return the relative path.

    Args:
        screenshot_b64: Base64-encoded PNG screenshot
        run_id: Unique run identifier
        persona: Persona name for organizing screenshots
        url: Page URL (used for filename)
        index: Screenshot index for ordering
        results_dir: Base results directory

    Returns:
        Relative path to saved screenshot, or None if save failed
    """
    try:
        screenshots_dir = Path(results_dir) / "screenshots" / run_id / persona
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Create safe filename from URL
        safe_url = url.replace("://", "_").replace("/", "_").replace("?", "_")[:50]
        filename = f"{index:02d}_{safe_url}.png"
        filepath = screenshots_dir / filename

        # Decode and save
        image_data = base64.b64decode(screenshot_b64)
        filepath.write_bytes(image_data)

        # Return relative path from results dir (report is saved inside results_dir)
        return str(filepath.relative_to(Path(results_dir)))
    except Exception as e:
        log.warning("Failed to save screenshot: %s", e)
        return None


def _annotate_and_save_screenshot(
    screenshot_b64: str,
    events: list[dict],
    run_id: str,
    persona: str,
    url: str,
    index: int,
    results_dir: str = "results",
) -> str | None:
    """Annotate a screenshot with frustration events and save to disk.

    Args:
        screenshot_b64: Base64-encoded PNG screenshot
        events: Frustration events that occurred on this page
        run_id: Unique run identifier
        persona: Persona name
        url: Page URL
        index: Screenshot index
        results_dir: Base results directory

    Returns:
        Relative path to saved annotated screenshot, or None if failed
    """
    try:
        from .screenshot_annotator import AnnotationMarker, annotate_screenshot
    except ImportError:
        log.warning("screenshot_annotator not available, saving unannotated")
        return _save_screenshot(screenshot_b64, run_id, persona, url, index, results_dir)

    # Create markers from events
    markers: list[AnnotationMarker] = []
    severity_colors = {
        "critical": "red",
        "high": "orange",
        "medium": "yellow",
        "low": "green",
    }

    for event in events:
        # Try to extract coordinates from event
        coords = None
        if "x" in event and "y" in event:
            try:
                coords = (int(event["x"]), int(event["y"]))
            except (ValueError, TypeError):
                pass
        elif "target" in event:
            target = event["target"]
            if isinstance(target, (list, tuple)) and len(target) == 2:
                try:
                    coords = (int(target[0]), int(target[1]))
                except (ValueError, TypeError):
                    pass

        if coords:
            severity = event.get("severity", "medium")
            markers.append(
                AnnotationMarker(
                    x=coords[0],
                    y=coords[1],
                    label=event.get("kind", "event"),
                    color=severity_colors.get(severity, "yellow"),
                )
            )

    # Annotate if we have markers
    if markers:
        annotated_b64 = annotate_screenshot(screenshot_b64, markers)
    else:
        annotated_b64 = screenshot_b64

    return _save_screenshot(annotated_b64, run_id, persona, url, index, results_dir)


def _escape_markdown(text: str) -> str:
    """Escape special markdown characters in text for safe table/list rendering."""
    if not text:
        return text
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    text = text.replace("\r", "")
    return text


def _get_severity(event: dict) -> str:
    """Get severity from event, defaulting to medium if not present."""
    return event.get("severity", "medium")


def _sort_events_by_severity(events: list[dict]) -> list[dict]:
    """Sort events by severity (critical first, then high, medium, low)."""
    return sorted(events, key=lambda e: SEVERITY_ORDER.get(_get_severity(e), 2))


def _group_events_by_kind(events: list[dict]) -> dict[str, list[dict]]:
    """Group events by their kind for aggregated reporting."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        kind = event.get("kind", "unknown")
        groups[kind].append(event)
    return dict(groups)


def _count_events_by_severity(events: list[dict]) -> dict[str, int]:
    """Count events by severity level."""
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for event in events:
        severity = _get_severity(event)
        if severity in counts:
            counts[severity] += 1
    return counts


def _generate_executive_summary(all_events: list[dict]) -> list[str]:
    """Generate executive summary highlighting top issues."""
    lines: list[str] = []

    if not all_events:
        lines.append("No issues detected. The user experience appears smooth.")
        return lines

    severity_counts = _count_events_by_severity(all_events)
    sorted_events = _sort_events_by_severity(all_events)

    # Severity breakdown
    severity_parts = []
    for sev in ["critical", "high", "medium", "low"]:
        count = severity_counts[sev]
        if count > 0:
            emoji = SEVERITY_EMOJI.get(sev, "")
            severity_parts.append(f"{emoji} {count} {sev}")

    lines.append(f"**Issues found:** {' | '.join(severity_parts)}")
    lines.append("")

    # Top 3 issues
    lines.append("**Top issues to address:**")
    lines.append("")
    for i, event in enumerate(sorted_events[:3], 1):
        kind = event.get("kind", "unknown")
        desc = _escape_markdown(event.get("description", "")[:100])
        severity = _get_severity(event)
        emoji = SEVERITY_EMOJI.get(severity, "")
        lines.append(f"{i}. {emoji} **{kind}**: {desc}")

    return lines


def _generate_recommendations(grouped_events: dict[str, list[dict]]) -> list[str]:
    """Generate actionable recommendations based on event types."""
    lines: list[str] = []

    # Sort by count (most frequent first)
    sorted_kinds = sorted(grouped_events.items(), key=lambda x: -len(x[1]))

    for kind, events in sorted_kinds:
        count = len(events)
        recommendation = FIX_RECOMMENDATIONS.get(kind, "Review and address this issue.")
        lines.append(f"- **{kind}** ({count}x): {recommendation}")

    return lines


def generate_report(state: RunState) -> str:
    """Produce a Markdown friction report from a completed RunState."""
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Collect all events from all agents
    all_events: list[dict] = []
    for r in state.results:
        for ev in r.frustration_events:
            ev_copy = dict(ev)
            ev_copy["persona"] = r.persona
            all_events.append(ev_copy)

    total_events = len(all_events)

    # Header
    lines.append("# Flamboyance UX Friction Report")
    lines.append("")
    lines.append(f"- **Run ID:** `{_escape_markdown(state.run_id)}`")
    lines.append(f"- **Target URL:** {_escape_markdown(state.url)}")
    lines.append(f"- **Status:** {state.status}")
    lines.append(f"- **Agents:** {len(state.results)}")
    lines.append(f"- **Total friction events:** {total_events}")
    lines.append(f"- **Generated:** {now}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.extend(_generate_executive_summary(all_events))
    lines.append("")

    # Recommendations (if any events)
    if all_events:
        lines.append("## Recommendations")
        lines.append("")
        grouped_events = _group_events_by_kind(all_events)
        lines.extend(_generate_recommendations(grouped_events))
        lines.append("")

    # Events by Severity
    if all_events:
        lines.append("## Issues by Severity")
        lines.append("")

        for severity in ["critical", "high", "medium", "low"]:
            sev_events = [e for e in all_events if _get_severity(e) == severity]
            if not sev_events:
                continue

            emoji = SEVERITY_EMOJI.get(severity, "")
            lines.append(f"### {emoji} {severity.title()} ({len(sev_events)})")
            lines.append("")
            lines.append("| Event | Description | URL | Persona |")
            lines.append("|-------|-------------|-----|---------|")
            for ev in sev_events:
                kind = ev.get("kind", "unknown")
                desc = _escape_markdown(ev.get("description", ""))[:80]
                url = _escape_markdown(ev.get("url", ""))[:40]
                persona = ev.get("persona", "")
                lines.append(f"| {kind} | {desc} | {url} | {persona} |")
            lines.append("")

    # Agent Summary Table
    lines.append("## Agent Summary")
    lines.append("")
    lines.append("| Persona | Status | Events | Critical | High | Elapsed |")
    lines.append("|---------|--------|--------|----------|------|---------|")
    for r in state.results:
        agent_severity = _count_events_by_severity(r.frustration_events)
        lines.append(
            f"| {r.persona} | {r.status} | {len(r.frustration_events)} "
            f"| {agent_severity['critical']} | {agent_severity['high']} "
            f"| {r.elapsed_seconds:.1f}s |"
        )
    lines.append("")

    # Detailed Agent Reports
    for r in state.results:
        lines.append(f"## Agent: {r.persona}")
        lines.append("")
        lines.append(f"- **Status:** {r.status}")
        lines.append(f"- **Elapsed:** {r.elapsed_seconds:.1f}s")
        if r.error:
            lines.append(f"- **Error:** {_escape_markdown(r.error)}")
        lines.append("")

        # LLM mode stats
        if getattr(r, 'llm_mode', False):
            lines.append("### LLM Navigation Stats")
            lines.append("")
            lines.append(f"- **LLM Calls:** {getattr(r, 'llm_calls', 0)}")
            lines.append(f"- **Tokens Used:** {getattr(r, 'llm_tokens', 0)}")
            lines.append("")

        if r.visited_urls:
            lines.append("### Navigation Path")
            lines.append("")
            for i, u in enumerate(r.visited_urls, 1):
                lines.append(f"{i}. {_escape_markdown(u)}")
            lines.append("")

        if r.frustration_events:
            sorted_events = _sort_events_by_severity(r.frustration_events)
            lines.append("### Frustration Events")
            lines.append("")
            for ev in sorted_events:
                kind = ev.get("kind", "unknown")
                desc = _escape_markdown(ev.get("description", ""))
                severity = _get_severity(ev)
                emoji = SEVERITY_EMOJI.get(severity, "")
                lines.append(f"- {emoji} **{kind}** ({severity}): {desc}")
            lines.append("")

        # LLM Action History (if available)
        action_history = getattr(r, 'action_history', [])
        if action_history:
            lines.append("### Action History")
            lines.append("")
            lines.append("| # | Action | Target | Result |")
            lines.append("|---|--------|--------|--------|")
            for i, action in enumerate(action_history[:20], 1):  # Limit to 20
                act = action.get("action", "")
                target = str(action.get("target", ""))[:30]
                result = _escape_markdown(str(action.get("result", "")))[:40]
                lines.append(f"| {i} | {act} | {target} | {result} |")
            if len(action_history) > 20:
                lines.append(f"| ... | ({len(action_history) - 20} more actions) | | |")
            lines.append("")

        # Visual Evidence (screenshots)
        page_screenshots = getattr(r, 'page_screenshots', {})
        if page_screenshots:
            lines.append("### Visual Evidence")
            lines.append("")

            # Group events by URL for annotation
            events_by_url: dict[str, list[dict]] = defaultdict(list)
            for ev in r.frustration_events:
                ev_url = ev.get("url", "")
                if ev_url:
                    events_by_url[ev_url].append(ev)

            for idx, (url, screenshot_b64) in enumerate(page_screenshots.items()):
                # Get events for this page
                page_events = events_by_url.get(url, [])

                # Save annotated screenshot
                screenshot_path = _annotate_and_save_screenshot(
                    screenshot_b64,
                    page_events,
                    state.run_id,
                    r.persona,
                    url,
                    idx,
                )

                if screenshot_path:
                    short_url = _escape_markdown(url[:60])
                    event_count = len(page_events)
                    event_note = f" ({event_count} issue{'s' if event_count != 1 else ''})" if event_count else ""
                    lines.append(f"**Page {idx + 1}:** {short_url}{event_note}")
                    lines.append("")
                    lines.append(f"![Screenshot]({screenshot_path})")
                    lines.append("")

    if total_events == 0:
        lines.append("---")
        lines.append("")
        lines.append("*No frustration events detected during this simulation.*")
        lines.append("")

    return "\n".join(lines)
