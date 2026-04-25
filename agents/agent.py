"""Playwright-based synthetic browser agent driven by a Persona.

The agent navigates a target URL, clicks interactable elements, and records
frustration events. Timing (page-load timeout, click hesitation) is governed
by the persona's ``patience`` and ``tech_literacy`` values.

Usage (standalone)::

    python -m agents.agent --url http://localhost:3000 --persona frustrated_exec

The module can also be imported and driven programmatically via ``run_agent``.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import random
import sys
import time
from dataclasses import dataclass, field

from .config import MAX_LLM_CALLS_PER_SESSION
from .events import EventDetector, FrustrationEvent
from .llm_driver import ActionDecision, ActionHistoryEntry, LLMDriver
from .persona import Persona, resolve_personas

log = logging.getLogger(__name__)

INTERACTIVE_ROLES = frozenset(
    {"button", "link", "menuitem", "tab", "checkbox", "radio", "textbox", "combobox"}
)
INTERACTIVE_TAGS = frozenset({"a", "button", "input", "select", "textarea"})


@dataclass
class AgentResult:
    persona: str
    status: str  # "done" | "gave_up" | "error" | "goal_complete"
    visited_urls: list[str] = field(default_factory=list)
    frustration_events: list[dict[str, object]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: str | None = None
    llm_mode: bool = False
    llm_calls: int = 0
    llm_tokens: int = 0
    action_history: list[dict[str, object]] = field(default_factory=list)


async def run_agent(
    url: str,
    persona: Persona,
    *,
    timeout_s: float = 60.0,
    headless: bool = True,
    max_actions: int | None = None,
    llm_mode: bool = False,
    max_llm_calls: int | None = None,
) -> AgentResult:
    """Launch a Playwright browser and simulate the persona navigating *url*.

    Args:
        url: Target URL to navigate.
        persona: Persona controlling behavior (timeouts, viewport, action limits).
        timeout_s: Overall session timeout in seconds.
        headless: Run browser without visible UI.
        max_actions: Override persona.max_actions if specified.
        llm_mode: If True, use LLM vision model to decide actions instead of random.
        max_llm_calls: Maximum LLM API calls per session (default from config).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return AgentResult(
            persona=persona.name,
            status="error",
            error="playwright is not installed — run `pip install playwright && playwright install chromium`",
        )

    detector = EventDetector()
    visited: list[str] = []
    action_history: list[ActionHistoryEntry] = []
    start = time.monotonic()

    result = AgentResult(persona=persona.name, status="done", llm_mode=llm_mode)

    timeout_ms = persona.page_load_timeout_ms
    effective_max_actions = max_actions if max_actions is not None else persona.max_actions
    effective_max_llm_calls = max_llm_calls if max_llm_calls is not None else MAX_LLM_CALLS_PER_SESSION

    llm_driver: LLMDriver | None = None
    if llm_mode:
        try:
            llm_driver = LLMDriver()
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

            # ── Initial navigation with slow_load detection ──────────
            nav_start = time.monotonic()
            try:
                await page.goto(url, wait_until="domcontentloaded")
            except Exception as exc:
                result.status = "error"
                result.error = f"Failed to load {url}: {exc}"
                await browser.close()
                result.elapsed_seconds = time.monotonic() - start
                return result

            load_ms = (time.monotonic() - nav_start) * 1000
            slow_evt = detector.record_slow_load(url, load_ms)
            if slow_evt:
                log.info("event: %s", slow_evt.description)

            visited.append(url)
            detector.record_navigation(url)
            detector.touch()

            # ── Rage decoy detection on initial page ───────────────────
            decoys = await _find_rage_decoys(page)
            for decoy in decoys:
                decoy_evt = detector.record_rage_decoy(url, decoy["selector"], decoy["reason"])
                log.info("event: %s", decoy_evt.description)

            actions_taken = 0
            gave_up = False
            goal_complete = False

            while actions_taken < effective_max_actions:
                elapsed = time.monotonic() - start
                if elapsed >= timeout_s:
                    break

                if persona.gives_up_early and elapsed > timeout_s * persona.early_exit_fraction:
                    gave_up = True
                    result.status = "gave_up"
                    break

                # ── LLM Mode: Vision-based decision making ──────────────
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
                    action_history.append(ActionHistoryEntry(
                        action=decision.action_type,
                        target=decision.target,
                        result=action_result,
                        url=page.url,
                    ))
                    detector.touch()

                    if decision.action_type == "done":
                        goal_complete = True
                        result.status = "goal_complete"
                        break
                    elif decision.action_type == "give_up":
                        gave_up = True
                        result.status = "gave_up"
                        break

                    await page.wait_for_load_state("domcontentloaded")
                    current_url = page.url
                    if current_url not in visited[-1:]:
                        visited.append(current_url)
                        nav_evt = detector.record_navigation(current_url)
                        if nav_evt:
                            log.info("event: %s", nav_evt.description)

                    actions_taken += 1
                    continue

                # ── Random Mode: Original random click behavior ─────────
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
                    detector.record_click(selector, is_interactive=False)
                    actions_taken += 1
                    continue

                detector.touch()
                evt = detector.record_click(
                    selector, is_interactive=is_interactive
                )
                if evt:
                    log.info("event: %s", evt.description)

                await page.wait_for_load_state("domcontentloaded")
                current_url = page.url
                if current_url not in visited[-1:]:
                    visited.append(current_url)
                    nav_evt = detector.record_navigation(current_url)
                    if nav_evt:
                        log.info("event: %s", nav_evt.description)

                    decoys = await _find_rage_decoys(page)
                    for decoy in decoys:
                        decoy_evt = detector.record_rage_decoy(
                            current_url, decoy["selector"], decoy["reason"]
                        )
                        log.info("event: %s", decoy_evt.description)

                actions_taken += 1

            timed_out = (time.monotonic() - start) >= timeout_s
            if not goal_complete:
                detector.check_unmet_goal(
                    persona.goal, reached=False, timed_out=timed_out
                )

            if llm_driver:
                stats = llm_driver.get_usage_stats()
                result.llm_calls = stats["call_count"]
                result.llm_tokens = stats["total_tokens"]

            await browser.close()

    except Exception as exc:
        result.status = "error"
        result.error = str(exc)

    result.visited_urls = visited
    result.frustration_events = [
        {
            "kind": e.kind,
            "description": e.description,
            "url": e.url,
            "timestamp": e.timestamp,
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


async def _execute_llm_action(page: object, decision: ActionDecision) -> str:
    """Execute an LLM-decided action and return a result description."""
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        if decision.action_type == "click":
            if isinstance(decision.target, tuple) and len(decision.target) == 2:
                x, y = decision.target
                await page.mouse.click(x, y)
                return f"clicked at ({x}, {y})"
            return "invalid click coordinates"

        elif decision.action_type == "type":
            if isinstance(decision.target, str):
                await page.keyboard.type(decision.target)
                return f"typed '{decision.target[:20]}...'" if len(decision.target) > 20 else f"typed '{decision.target}'"
            return "invalid type target"

        elif decision.action_type == "scroll":
            direction = decision.target if isinstance(decision.target, str) else "down"
            delta = -300 if direction == "up" else 300
            await page.mouse.wheel(0, delta)
            return f"scrolled {direction}"

        elif decision.action_type == "back":
            await page.go_back()
            return "navigated back"

        elif decision.action_type == "done":
            return "goal completed"

        elif decision.action_type == "give_up":
            reason = decision.target if isinstance(decision.target, str) else "unknown reason"
            return f"gave up: {reason}"

        else:
            return f"unknown action: {decision.action_type}"

    except Exception as e:
        log.warning("Action execution failed: %s", e)
        return f"action failed: {e}"


async def _find_clickables(
    page: object, persona: Persona
) -> list[dict[str, object]]:
    """Discover clickable elements on the page, respecting persona limitations."""
    # Import types inline to keep the function signature simple when playwright
    # is not installed.
    from playwright.async_api import Page

    assert isinstance(page, Page)

    elements: list[dict[str, object]] = []

    locator = page.locator(
        "a, button, input[type='submit'], input[type='button'], "
        "[role='button'], [role='link'], [role='menuitem'], [role='tab']"
    )
    count = await locator.count()

    for i in range(min(count, 30)):
        el = locator.nth(i)
        try:
            if not await el.is_visible():
                continue
        except Exception:
            continue

        tag = await el.evaluate("el => el.tagName.toLowerCase()")
        role = await el.evaluate("el => el.getAttribute('role') || ''")
        interactive = tag in INTERACTIVE_TAGS or role in INTERACTIVE_ROLES

        if persona.skips_hidden_menus:
            aria_expanded = await el.evaluate(
                "el => el.getAttribute('aria-expanded')"
            )
            if aria_expanded == "false":
                continue

        selector = f"{tag}:nth-of-type({i + 1})"
        text = ""
        try:
            text = (await el.inner_text())[:40].strip()
            if text:
                selector = f"{tag}:has-text('{text}')"
        except Exception:
            pass

        # Personas who prefer visible text skip icon-only / unlabeled controls.
        if persona.prefers_visible_text and not text:
            continue

        elements.append({"selector": selector, "interactive": interactive})

    return elements


async def _find_rage_decoys(page: object) -> list[dict[str, str]]:
    """Find elements that look clickable but are not actual buttons or links.

    Detects elements with visual affordances (cursor:pointer, button-like styling)
    that are not semantic interactive elements.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    decoys: list[dict[str, str]] = []

    # Find non-interactive elements that have cursor:pointer or button-like styling
    candidates = await page.evaluate("""
        () => {
            const results = [];
            const interactiveTags = new Set(['a', 'button', 'input', 'select', 'textarea']);
            const interactiveRoles = new Set([
                'button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'textbox', 'combobox'
            ]);

            // Query common decoy patterns: divs/spans with pointer cursor or button-like appearance
            const candidates = document.querySelectorAll(
                'div, span, p, li, img, label, td, th, h1, h2, h3, h4, h5, h6'
            );

            for (const el of candidates) {
                const tag = el.tagName.toLowerCase();
                const role = el.getAttribute('role') || '';

                // Skip if it's actually interactive
                if (interactiveTags.has(tag) || interactiveRoles.has(role)) continue;

                // Skip if it has an onclick handler via attribute (JS handlers harder to detect)
                if (el.hasAttribute('onclick')) continue;

                // Skip if it's inside an interactive element
                if (el.closest('a, button, input, select, textarea, [role="button"], [role="link"]')) continue;

                const style = window.getComputedStyle(el);
                const reasons = [];

                // Check for cursor:pointer
                if (style.cursor === 'pointer') {
                    reasons.push('cursor:pointer');
                }

                // Check for hover class patterns (limited detection)
                if (el.className && /hover|clickable|btn|button/i.test(el.className)) {
                    reasons.push('clickable class name');
                }

                if (reasons.length > 0) {
                    // Build a selector
                    let selector = tag;
                    const text = (el.innerText || '').trim().slice(0, 30);
                    if (text) {
                        selector = `${tag}:has-text('${text.replace(/'/g, "\\'")}')`;
                    } else if (el.id) {
                        selector = `#${el.id}`;
                    } else if (el.className) {
                        const firstClass = el.className.split(' ')[0];
                        if (firstClass) selector = `${tag}.${firstClass}`;
                    }

                    results.push({
                        selector: selector,
                        reason: reasons.join(', ')
                    });
                }

                // Limit to avoid flooding
                if (results.length >= 10) break;
            }
            return results;
        }
    """)

    return candidates


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run a single UX-friction agent")
    parser.add_argument("--url", required=True, help="Target URL to test")
    parser.add_argument("--persona", default="frustrated_exec", help="Persona name")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.add_argument("--llm", action="store_true", help="Use LLM vision model for navigation")
    parser.add_argument("--max-llm-calls", type=int, default=None, help="Max LLM API calls per session")
    args = parser.parse_args()

    persona = resolve_personas([args.persona])[0]
    result = asyncio.run(
        run_agent(
            args.url,
            persona,
            timeout_s=args.timeout,
            headless=args.headless,
            llm_mode=args.llm,
            max_llm_calls=args.max_llm_calls,
        )
    )
    output = {
        "persona": result.persona,
        "status": result.status,
        "visited_urls": result.visited_urls,
        "frustration_events": result.frustration_events,
        "elapsed_seconds": result.elapsed_seconds,
        "error": result.error,
    }
    if result.llm_mode:
        output["llm_mode"] = True
        output["llm_calls"] = result.llm_calls
        output["llm_tokens"] = result.llm_tokens
        output["action_history"] = result.action_history
    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
