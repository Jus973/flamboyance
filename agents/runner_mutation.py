"""Mutation test runner for UX-friction agents.

Applies UI mutations (hide/disable/remove elements) before running persona agents
to simulate broken or degraded UX scenarios.

Usage::

    python -m agents.runner_mutation --url http://localhost:3000 --mutation broken_checkout

Or programmatically::

    from agents.runner_mutation import run_mutation_test
    from agents.mutations import MutationScenario

    scenario = MutationScenario(name="test", hide=["#checkout-btn"])
    result = asyncio.run(run_mutation_test("http://localhost:3000", scenario))
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agent import AgentResult
from .config import MAX_LLM_CALLS_PER_SESSION
from .events import EventDetector
from .llm_driver import ActionHistoryEntry, LLMDriver
from .mutations import COMMON_SCENARIOS, MutationScenario, apply_mutations
from .persona import DEFAULT_PERSONAS, Persona
from .persona_loader import load_personas_file, merge_personas
from .validation import ValidationError, validate_url

log = logging.getLogger(__name__)


@dataclass
class MutationTestResult:
    """Result of running mutation tests across personas."""

    scenario: str
    url: str
    persona_results: list[AgentResult] = field(default_factory=list)
    status: str = "done"  # "done" | "stopped" | "error"
    elapsed_seconds: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scenario": self.scenario,
            "url": self.url,
            "status": self.status,
            "elapsed_seconds": self.elapsed_seconds,
            "error": self.error,
            "persona_results": [
                {
                    "persona": r.persona,
                    "status": r.status,
                    "visited_urls": r.visited_urls,
                    "frustration_events": r.frustration_events,
                    "elapsed_seconds": r.elapsed_seconds,
                    "error": r.error,
                    "llm_mode": r.llm_mode,
                    "llm_calls": r.llm_calls,
                    "llm_tokens": r.llm_tokens,
                }
                for r in self.persona_results
            ],
        }

    def summary(self) -> dict[str, Any]:
        """Generate a summary of which personas failed under this mutation."""
        failed = []
        succeeded = []
        for r in self.persona_results:
            events_by_kind: dict[str, int] = {}
            for e in r.frustration_events:
                kind = e.get("kind", "unknown")
                events_by_kind[kind] = events_by_kind.get(kind, 0) + 1

            info = {
                "persona": r.persona,
                "status": r.status,
                "event_count": len(r.frustration_events),
                "events_by_kind": events_by_kind,
            }

            # Consider "failed" if goal was unmet or agent gave up
            if r.status in ("gave_up", "error") or any(
                e.get("kind") == "unmet_goal" for e in r.frustration_events
            ):
                failed.append(info)
            else:
                succeeded.append(info)

        return {
            "scenario": self.scenario,
            "url": self.url,
            "total_personas": len(self.persona_results),
            "failed_count": len(failed),
            "succeeded_count": len(succeeded),
            "failed_personas": failed,
            "succeeded_personas": succeeded,
        }


async def _run_agent_with_mutations(
    url: str,
    persona: Persona,
    scenario: MutationScenario,
    *,
    timeout_s: float = 60.0,
    headless: bool = True,
    llm_mode: bool = False,
    max_llm_calls: int | None = None,
) -> AgentResult:
    """Run a single agent with mutations applied to the page.

    This is a modified version of run_agent that applies mutations after page load.
    """
    try:
        url = validate_url(url, allow_localhost=True)
    except ValidationError as e:
        return AgentResult(
            persona=persona.name,
            status="error",
            error=f"Invalid URL: {e}",
        )

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return AgentResult(
            persona=persona.name,
            status="error",
            error="playwright is not installed",
        )

    from .agent import (
        _execute_llm_action,
        _find_broken_images,
        _find_clickables,
        _find_rage_decoys,
    )

    detector = EventDetector(thresholds=persona.get_thresholds())
    visited: list[str] = []
    action_history: list[ActionHistoryEntry] = []
    start = time.monotonic()

    result = AgentResult(persona=persona.name, status="done", llm_mode=llm_mode)

    timeout_ms = persona.page_load_timeout_ms
    effective_max_actions = persona.max_actions
    effective_max_llm_calls = (
        max_llm_calls if max_llm_calls is not None else MAX_LLM_CALLS_PER_SESSION
    )

    llm_driver: LLMDriver | None = None
    if llm_mode:
        try:
            llm_driver = LLMDriver(viewport=persona.viewport)
        except (ImportError, ValueError) as e:
            return AgentResult(
                persona=persona.name,
                status="error",
                error=f"LLM mode initialization failed: {e}",
                llm_mode=True,
            )

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": persona.viewport[0], "height": persona.viewport[1]}
            )
            page = await context.new_page()
            page.set_default_timeout(timeout_ms)

            # Set up console error listener
            def on_console_message(msg):
                if msg.type == "error":
                    location = msg.location
                    detector.record_js_error(
                        url=page.url,
                        message=msg.text,
                        source=location.get("url", "") if location else "",
                        line=location.get("lineNumber", 0) if location else 0,
                    )
                    log.info("event: JS error - %s", msg.text[:100])

            page.on("console", on_console_message)

            # Set up network failure listener
            def on_response(response):
                if response.status >= 400:
                    detector.record_network_error(
                        url=page.url,
                        request_url=response.url,
                        status_code=response.status,
                        error_text=response.status_text,
                        method=response.request.method,
                    )
                    log.info("event: Network error - %s %d", response.url[:60], response.status)

            page.on("response", on_response)

            def on_request_failed(request):
                failure = request.failure
                detector.record_network_error(
                    url=page.url,
                    request_url=request.url,
                    status_code=0,
                    error_text=failure if failure else "request failed",
                    method=request.method,
                )
                log.info("event: Request failed - %s", request.url[:60])

            page.on("requestfailed", on_request_failed)

            # Initial navigation
            nav_start = time.monotonic()
            try:
                await page.goto(url, wait_until="domcontentloaded")
            except Exception as exc:
                result.status = "error"
                result.error = f"Failed to load {url}: {exc}"
                await browser.close()
                result.elapsed_seconds = time.monotonic() - start
                return result

            # ── APPLY MUTATIONS after page load ──────────────────────────
            log.info("applying mutation scenario: %s", scenario.name)
            await apply_mutations(page, scenario)

            load_ms = (time.monotonic() - nav_start) * 1000
            slow_evt = detector.record_slow_load(url, load_ms)
            if slow_evt:
                log.info("event: %s", slow_evt.description)

            visited.append(url)
            detector.record_navigation(url)
            detector.touch()

            # Check for broken images on initial page
            broken_images = await _find_broken_images(page)
            for img in broken_images:
                detector.record_broken_image(url, img["src"], img["selector"])
                log.info("event: Broken image - %s", img["src"][:60])

            # Rage decoy detection on initial page (only for low tech_literacy personas)
            if persona.tech_literacy < 0.5:
                decoys = await _find_rage_decoys(page)
                for decoy in decoys:
                    decoy_evt = detector.record_rage_decoy(url, decoy["selector"], decoy["reason"])
                    log.info("event: %s", decoy_evt.description)

            actions_taken = 0
            goal_complete = False
            import random

            while actions_taken < effective_max_actions:
                elapsed = time.monotonic() - start
                if elapsed >= timeout_s:
                    break

                if persona.gives_up_early and elapsed > timeout_s * persona.early_exit_fraction:
                    result.status = "gave_up"
                    break

                # LLM Mode: Vision-based decision making
                if llm_mode and llm_driver is not None:
                    if llm_driver.call_count >= effective_max_llm_calls:
                        log.warning("Max LLM calls reached (%d)", effective_max_llm_calls)
                        result.status = "gave_up"
                        break

                    screenshot = await page.screenshot(type="png")
                    screenshot_b64 = base64.b64encode(screenshot).decode()

                    decision = await llm_driver.decide_action(
                        screenshot_b64,
                        persona,
                        action_history,
                        current_url=page.url,
                    )

                    log.info("LLM decision: %s - %s", decision.action_type, decision.reasoning)

                    action_result = await _execute_llm_action(page, decision)
                    action_history.append(
                        ActionHistoryEntry(
                            action=decision.action_type,
                            target=decision.target,
                            result=action_result,
                            url=page.url,
                        )
                    )
                    detector.touch()

                    if decision.action_type == "done":
                        goal_complete = True
                        result.status = "goal_complete"
                        break
                    elif decision.action_type == "give_up":
                        result.status = "gave_up"
                        break

                    await page.wait_for_load_state("domcontentloaded")

                    # Re-apply mutations after navigation
                    await apply_mutations(page, scenario)

                    current_url = page.url
                    if current_url not in visited[-1:]:
                        visited.append(current_url)
                        nav_evt = detector.record_navigation(current_url)
                        if nav_evt:
                            log.info("event: %s", nav_evt.description)

                        broken_images = await _find_broken_images(page)
                        for img in broken_images:
                            detector.record_broken_image(current_url, img["src"], img["selector"])
                            log.info("event: Broken image - %s", img["src"][:60])

                    actions_taken += 1
                    continue

                # Random Mode: Original random click behavior
                await asyncio.sleep(persona.click_hesitation_ms / 1000.0)

                dwell_s = time.time() - detector.last_action_time
                dwell_evt = detector.record_long_dwell(page.url, dwell_s)
                if dwell_evt:
                    log.info("event: %s", dwell_evt.description)

                clickables = await _find_clickables(page, persona)
                if not clickables:
                    dead_evt = detector.record_dead_end(page.url)
                    log.info("event: %s", dead_evt.description)
                    break

                target = random.choice(clickables)
                selector = target["selector"]
                is_interactive = target["interactive"]

                try:
                    await page.click(selector, timeout=5000)
                except Exception:
                    detector.record_click(selector, is_interactive=False, url=page.url)
                    actions_taken += 1
                    continue

                detector.touch()
                evt = detector.record_click(selector, is_interactive=is_interactive, url=page.url)
                if evt:
                    log.info("event: %s", evt.description)

                await page.wait_for_load_state("domcontentloaded")

                # Re-apply mutations after navigation
                await apply_mutations(page, scenario)

                current_url = page.url
                if current_url not in visited[-1:]:
                    visited.append(current_url)
                    nav_evt = detector.record_navigation(current_url)
                    if nav_evt:
                        log.info("event: %s", nav_evt.description)

                    broken_images = await _find_broken_images(page)
                    for img in broken_images:
                        detector.record_broken_image(current_url, img["src"], img["selector"])
                        log.info("event: Broken image - %s", img["src"][:60])

                    # Only detect rage decoys for low tech_literacy personas
                    if persona.tech_literacy < 0.5:
                        decoys = await _find_rage_decoys(page)
                        for decoy in decoys:
                            decoy_evt = detector.record_rage_decoy(
                                current_url, decoy["selector"], decoy["reason"]
                            )
                            log.info("event: %s", decoy_evt.description)

                actions_taken += 1

            timed_out = (time.monotonic() - start) >= timeout_s
            if not goal_complete:
                final_url = visited[-1] if visited else url
                detector.check_unmet_goal(persona.goal, reached=False, timed_out=timed_out, url=final_url)

            if llm_driver:
                stats = llm_driver.get_usage_stats()
                result.llm_calls = stats["call_count"]
                result.llm_tokens = stats["total_tokens"]

            await browser.close()

    except asyncio.CancelledError:
        log.info("Agent run cancelled for %s", persona.name)
        result.status = "error"
        result.error = "Agent run was cancelled"
    except TimeoutError as exc:
        log.warning("Timeout during agent run: %s", exc)
        result.status = "error"
        result.error = f"Timeout: {exc}"
    except ConnectionError as exc:
        log.error("Connection error during agent run: %s", exc)
        result.status = "error"
        result.error = f"Connection error: {exc}"
    except Exception as exc:
        log.error("Unexpected error during agent run: %s", exc, exc_info=True)
        result.status = "error"
        result.error = str(exc)

    result.visited_urls = visited
    result.frustration_events = [
        {
            "kind": e.kind,
            "description": e.description,
            "url": e.url,
            "timestamp": e.timestamp,
            "severity": e.severity.value,
        }
        for e in detector.all_events()
    ]
    result.action_history = [
        {
            "action": h.action,
            "target": h.target if not isinstance(h.target, tuple) else list(h.target),
            "result": h.result,
            "url": h.url,
        }
        for h in action_history
    ]
    result.elapsed_seconds = time.monotonic() - start
    return result


async def run_mutation_test(
    url: str,
    scenario: MutationScenario,
    persona_names: list[str] | None = None,
    *,
    timeout_s: float = 60.0,
    headless: bool = True,
    llm_mode: bool = False,
    max_llm_calls: int | None = None,
    personas_file: str | Path | None = None,
) -> MutationTestResult:
    """Run persona agents against a page with UI elements mutated.

    Args:
        url: Target URL to test.
        scenario: MutationScenario defining what elements to mutate.
        persona_names: Names of personas to run (None = all available).
        timeout_s: Per-agent session timeout.
        headless: Run browser without visible UI.
        llm_mode: If True, use LLM vision model for navigation.
        max_llm_calls: Maximum LLM API calls per agent session.
        personas_file: Optional JSON file with custom persona definitions.

    Returns:
        MutationTestResult with results for each persona.
    """
    start = time.monotonic()

    try:
        validated_url = validate_url(url, allow_localhost=True)
    except ValidationError as e:
        return MutationTestResult(
            scenario=scenario.name,
            url=url,
            status="error",
            error=str(e),
        )

    # Resolve personas
    available = dict(DEFAULT_PERSONAS)
    if personas_file:
        custom = load_personas_file(personas_file)
        available = merge_personas(custom, base=available, custom_overrides=True)

    if persona_names:
        personas = []
        for name in persona_names:
            if name not in available:
                return MutationTestResult(
                    scenario=scenario.name,
                    url=url,
                    status="error",
                    error=f"Unknown persona {name!r}. Available: {sorted(available)}",
                )
            personas.append(available[name])
    else:
        personas = list(available.values())

    result = MutationTestResult(scenario=scenario.name, url=validated_url)

    log.info(
        "starting mutation test: scenario=%s personas=%d llm_mode=%s",
        scenario.name,
        len(personas),
        llm_mode,
    )

    for persona in personas:
        log.info(
            "running persona %s with mutation %s%s",
            persona.name,
            scenario.name,
            " (LLM mode)" if llm_mode else "",
        )
        agent_result = await _run_agent_with_mutations(
            validated_url,
            persona,
            scenario,
            timeout_s=timeout_s,
            headless=headless,
            llm_mode=llm_mode,
            max_llm_calls=max_llm_calls,
        )
        result.persona_results.append(agent_result)
        log.info(
            "persona %s finished: status=%s events=%d",
            persona.name,
            agent_result.status,
            len(agent_result.frustration_events),
        )

    result.elapsed_seconds = time.monotonic() - start
    return result


def generate_mutation_report(result: MutationTestResult) -> str:
    """Generate a Markdown report for mutation test results."""
    lines = [
        f"# Mutation Test Report: {result.scenario}",
        "",
        f"**URL:** {result.url}",
        f"**Status:** {result.status}",
        f"**Duration:** {result.elapsed_seconds:.1f}s",
        "",
    ]

    if result.error:
        lines.extend([f"**Error:** {result.error}", ""])

    summary = result.summary()

    lines.extend(
        [
            "## Summary",
            "",
            f"- **Total personas tested:** {summary['total_personas']}",
            f"- **Failed:** {summary['failed_count']}",
            f"- **Succeeded:** {summary['succeeded_count']}",
            "",
        ]
    )

    if summary["failed_personas"]:
        lines.extend(["## Failed Personas", ""])
        for p in summary["failed_personas"]:
            lines.append(f"### {p['persona']}")
            lines.append(f"- Status: {p['status']}")
            lines.append(f"- Events: {p['event_count']}")
            if p["events_by_kind"]:
                lines.append("- Event breakdown:")
                for kind, count in p["events_by_kind"].items():
                    lines.append(f"  - {kind}: {count}")
            lines.append("")

    if summary["succeeded_personas"]:
        lines.extend(["## Succeeded Personas", ""])
        for p in summary["succeeded_personas"]:
            lines.append(f"- **{p['persona']}**: {p['event_count']} events")
        lines.append("")

    lines.extend(["## Detailed Results", ""])
    for r in result.persona_results:
        lines.append(f"### {r.persona}")
        lines.append(f"- **Status:** {r.status}")
        lines.append(f"- **Duration:** {r.elapsed_seconds:.1f}s")
        lines.append(f"- **URLs visited:** {len(r.visited_urls)}")

        if r.frustration_events:
            lines.append("- **Frustration events:**")
            for e in r.frustration_events:
                lines.append(
                    f"  - [{e.get('severity', 'unknown')}] {e.get('description', 'No description')}"
                )

        if r.error:
            lines.append(f"- **Error:** {r.error}")

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run mutation tests on UX-friction agents")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument(
        "--mutation",
        required=True,
        help=f"Mutation scenario name or JSON. Built-in: {list(COMMON_SCENARIOS.keys())}",
    )
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
    parser.add_argument("--llm", action="store_true", help="Use LLM vision model for navigation")
    parser.add_argument(
        "--max-llm-calls", type=int, default=None, help="Max LLM API calls per agent"
    )
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of Markdown")
    args = parser.parse_args()

    # Parse mutation scenario
    if args.mutation in COMMON_SCENARIOS:
        scenario = COMMON_SCENARIOS[args.mutation]
    else:
        try:
            mutation_dict = json.loads(args.mutation)
            scenario = MutationScenario.from_dict(mutation_dict)
        except json.JSONDecodeError:
            print(f"Error: Unknown mutation '{args.mutation}' and not valid JSON", file=sys.stderr)
            print(f"Available built-in mutations: {list(COMMON_SCENARIOS.keys())}", file=sys.stderr)
            sys.exit(1)

    result = asyncio.run(
        run_mutation_test(
            args.url,
            scenario,
            args.personas,
            timeout_s=args.timeout,
            headless=args.headless,
            llm_mode=args.llm,
            max_llm_calls=args.max_llm_calls,
            personas_file=args.personas_file,
        )
    )

    if args.json:
        json.dump(result.to_dict(), sys.stdout, indent=2)
        print()
    else:
        report = generate_mutation_report(result)
        print(report)

        # Save report
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"mutation-{scenario.name}-{uuid.uuid4().hex[:8]}.md"
        path.write_text(report, encoding="utf-8")
        log.info("report saved: %s", path)


if __name__ == "__main__":
    main()
