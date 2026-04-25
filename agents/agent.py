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
import json
import logging
import random
import sys
import time
from dataclasses import dataclass, field

from .events import EventDetector, FrustrationEvent
from .persona import Persona, resolve_personas

log = logging.getLogger(__name__)

INTERACTIVE_ROLES = frozenset(
    {"button", "link", "menuitem", "tab", "checkbox", "radio", "textbox", "combobox"}
)
INTERACTIVE_TAGS = frozenset({"a", "button", "input", "select", "textarea"})


@dataclass
class AgentResult:
    persona: str
    status: str  # "done" | "gave_up" | "error"
    visited_urls: list[str] = field(default_factory=list)
    frustration_events: list[dict[str, object]] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: str | None = None


async def run_agent(
    url: str,
    persona: Persona,
    *,
    timeout_s: float = 60.0,
    headless: bool = True,
    max_actions: int = 50,
) -> AgentResult:
    """Launch a Playwright browser and simulate the persona navigating *url*."""
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
    start = time.monotonic()

    result = AgentResult(persona=persona.name, status="done")

    timeout_ms = persona.page_load_timeout_ms

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            page = await context.new_page()
            page.set_default_timeout(timeout_ms)

            try:
                await page.goto(url, wait_until="domcontentloaded")
            except Exception as exc:
                result.status = "error"
                result.error = f"Failed to load {url}: {exc}"
                await browser.close()
                result.elapsed_seconds = time.monotonic() - start
                return result

            visited.append(url)
            detector.record_navigation(url)

            actions_taken = 0
            gave_up = False

            while actions_taken < max_actions:
                elapsed = time.monotonic() - start
                if elapsed >= timeout_s:
                    break

                if persona.gives_up_early and elapsed > timeout_s * 0.4:
                    gave_up = True
                    result.status = "gave_up"
                    break

                await asyncio.sleep(persona.click_hesitation_ms / 1000.0)

                clickables = await _find_clickables(page, persona)
                if not clickables:
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

                actions_taken += 1

            timed_out = (time.monotonic() - start) >= timeout_s
            detector.check_unmet_goal(
                persona.goal, reached=False, timed_out=timed_out
            )

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
    result.elapsed_seconds = time.monotonic() - start
    return result


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
        try:
            text = (await el.inner_text())[:40]
            if text.strip():
                selector = f"{tag}:has-text('{text.strip()}')"
        except Exception:
            pass

        elements.append({"selector": selector, "interactive": interactive})

    return elements


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single UX-friction agent")
    parser.add_argument("--url", required=True, help="Target URL to test")
    parser.add_argument("--persona", default="frustrated_exec", help="Persona name")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    args = parser.parse_args()

    persona = resolve_personas([args.persona])[0]
    result = asyncio.run(
        run_agent(args.url, persona, timeout_s=args.timeout, headless=args.headless)
    )
    json.dump(
        {
            "persona": result.persona,
            "status": result.status,
            "visited_urls": result.visited_urls,
            "frustration_events": result.frustration_events,
            "elapsed_seconds": result.elapsed_seconds,
            "error": result.error,
        },
        sys.stdout,
        indent=2,
    )
    print()


if __name__ == "__main__":
    main()
