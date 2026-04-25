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
from .events import EventDetector
from .llm_driver import ActionDecision, ActionHistoryEntry, LLMDriver
from .persona import Persona, resolve_personas
from .validation import ValidationError, validate_url

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
    page_screenshots: dict[str, str] = field(default_factory=dict)  # URL → base64 PNG


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
            error="playwright is not installed — run `pip install playwright && playwright install chromium`",
        )

    detector = EventDetector(thresholds=persona.get_thresholds())
    visited: list[str] = []
    action_history: list[ActionHistoryEntry] = []
    page_screenshots: dict[str, str] = {}  # URL → base64 PNG
    start = time.monotonic()

    result = AgentResult(persona=persona.name, status="done", llm_mode=llm_mode)

    timeout_ms = persona.page_load_timeout_ms
    effective_max_actions = max_actions if max_actions is not None else persona.max_actions
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

            # ── Set up console error listener ──────────────────────────
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

            # ── Set up network failure listener ────────────────────────
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

            # ── Capture initial page screenshot ───────────────────────
            try:
                initial_screenshot = await page.screenshot(type="png")
                page_screenshots[url] = base64.b64encode(initial_screenshot).decode()
            except Exception as e:
                log.debug("Failed to capture initial screenshot: %s", e)

            # ── Check for broken images on initial page ────────────────
            broken_images = await _find_broken_images(page)
            for img in broken_images:
                detector.record_broken_image(url, img["src"], img["selector"])
                log.info("event: Broken image - %s", img["src"][:60])

            # ── Rage decoy detection on initial page ───────────────────
            # Only detect rage decoys for low tech_literacy personas (< 0.5)
            if persona.tech_literacy < 0.5:
                decoys = await _find_rage_decoys(page)
                for decoy in decoys:
                    decoy_evt = detector.record_rage_decoy(
                        url, decoy["selector"], decoy["reason"], x=decoy.get("x"), y=decoy.get("y")
                    )
                    log.info("event: %s", decoy_evt.description)

            # ── Run expanded page-level checks ─────────────────────────
            await _run_page_checks(page, detector, persona, url)

            actions_taken = 0
            goal_complete = False

            while actions_taken < effective_max_actions:
                elapsed = time.monotonic() - start
                if elapsed >= timeout_s:
                    break

                if persona.gives_up_early and elapsed > timeout_s * persona.early_exit_fraction:
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
                        log.info("Goal completed by LLM decision")
                        break
                    elif decision.action_type == "give_up":
                        result.status = "gave_up"
                        break

                    await page.wait_for_load_state("domcontentloaded")
                    current_url = page.url

                    # ── Heuristic goal detection ───────────────────────────
                    if not goal_complete:
                        goal_complete = await _check_goal_completion(page, persona, current_url)
                        if goal_complete:
                            result.status = "goal_complete"
                            log.info("Goal completed by heuristic detection at %s", current_url)
                            break

                    if current_url not in visited[-1:]:
                        visited.append(current_url)
                        nav_evt = detector.record_navigation(current_url)
                        if nav_evt:
                            log.info("event: %s", nav_evt.description)

                        # Capture screenshot of new page
                        if current_url not in page_screenshots:
                            try:
                                new_screenshot = await page.screenshot(type="png")
                                page_screenshots[current_url] = base64.b64encode(
                                    new_screenshot
                                ).decode()
                            except Exception as e:
                                log.debug("Failed to capture screenshot: %s", e)

                        # Check for broken images on new page
                        broken_images = await _find_broken_images(page)
                        for img in broken_images:
                            detector.record_broken_image(current_url, img["src"], img["selector"])
                            log.info("event: Broken image - %s", img["src"][:60])

                        # Run expanded page-level checks on new page
                        await _run_page_checks(page, detector, persona, current_url)

                        # Check for cart/form abandonment
                        abandon_evt = detector.check_cart_abandonment(current_url)
                        if abandon_evt:
                            log.info("event: %s", abandon_evt.description)
                        form_evt = detector.check_form_abandonment(current_url)
                        if form_evt:
                            log.info("event: %s", form_evt.description)

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
                evt = detector.record_click(selector, is_interactive=is_interactive)
                if evt:
                    log.info("event: %s", evt.description)

                await page.wait_for_load_state("domcontentloaded")
                current_url = page.url
                if current_url not in visited[-1:]:
                    visited.append(current_url)
                    nav_evt = detector.record_navigation(current_url)
                    if nav_evt:
                        log.info("event: %s", nav_evt.description)

                    # Capture screenshot of new page
                    if current_url not in page_screenshots:
                        try:
                            new_screenshot = await page.screenshot(type="png")
                            page_screenshots[current_url] = base64.b64encode(
                                new_screenshot
                            ).decode()
                        except Exception as e:
                            log.debug("Failed to capture screenshot: %s", e)

                    # Check for broken images on new page
                    broken_images = await _find_broken_images(page)
                    for img in broken_images:
                        detector.record_broken_image(current_url, img["src"], img["selector"])
                        log.info("event: Broken image - %s", img["src"][:60])

                    # Only detect rage decoys for low tech_literacy personas
                    if persona.tech_literacy < 0.5:
                        decoys = await _find_rage_decoys(page)
                        for decoy in decoys:
                            decoy_evt = detector.record_rage_decoy(
                                current_url,
                                decoy["selector"],
                                decoy["reason"],
                                x=decoy.get("x"),
                                y=decoy.get("y"),
                            )
                            log.info("event: %s", decoy_evt.description)

                    # Run expanded page-level checks on new page
                    await _run_page_checks(page, detector, persona, current_url)

                    # Check for cart/form abandonment
                    abandon_evt = detector.check_cart_abandonment(current_url)
                    if abandon_evt:
                        log.info("event: %s", abandon_evt.description)
                    form_evt = detector.check_form_abandonment(current_url)
                    if form_evt:
                        log.info("event: %s", form_evt.description)

                actions_taken += 1

            timed_out = (time.monotonic() - start) >= timeout_s
            if not goal_complete:
                detector.check_unmet_goal(persona.goal, reached=False, timed_out=timed_out)

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
            **e.details,  # Include details like selector, coordinates, etc.
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
    result.page_screenshots = page_screenshots
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
                return (
                    f"typed '{decision.target[:20]}...'"
                    if len(decision.target) > 20
                    else f"typed '{decision.target}'"
                )
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


async def _check_goal_completion(page: object, persona: Persona, current_url: str) -> bool:
    """Check if the current page indicates goal completion using heuristic patterns.

    Uses persona's success_url_patterns and success_text_patterns to detect
    when a goal has been achieved, even if the LLM doesn't recognize it.

    Returns:
        True if goal appears to be complete, False otherwise.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    # Check URL patterns - match against URL path only
    if persona.success_url_patterns:
        from urllib.parse import urlparse
        parsed = urlparse(current_url)
        url_path = parsed.path.lower()
        for pattern in persona.success_url_patterns:
            pattern_lower = pattern.lower()
            # Check if pattern matches the path (not just substring)
            if url_path == pattern_lower or url_path.startswith(pattern_lower):
                log.debug("Goal URL pattern matched: %s in path %s", pattern, url_path)
                return True

    # Check page text patterns
    if persona.success_text_patterns:
        try:
            # Get visible text from the page body
            body_text = await page.evaluate("() => document.body?.innerText?.toLowerCase() || ''")
            for pattern in persona.success_text_patterns:
                if pattern.lower() in body_text:
                    log.debug("Goal text pattern matched: %s", pattern)
                    return True
        except Exception as e:
            log.debug("Failed to check page text for goal completion: %s", e)

    return False


async def _find_clickables(page: object, persona: Persona) -> list[dict[str, object]]:
    """Discover clickable elements on the page, respecting persona limitations.

    Returns empty list if page context is destroyed (e.g., during navigation).
    """
    # Import types inline to keep the function signature simple when playwright
    # is not installed.
    from playwright.async_api import Page

    assert isinstance(page, Page)

    elements: list[dict[str, object]] = []

    try:
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

            try:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                role = await el.evaluate("el => el.getAttribute('role') || ''")
            except Exception:
                continue

            interactive = tag in INTERACTIVE_TAGS or role in INTERACTIVE_ROLES

            if persona.skips_hidden_menus:
                try:
                    aria_expanded = await el.evaluate("el => el.getAttribute('aria-expanded')")
                    if aria_expanded == "false":
                        continue
                except Exception:
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

    except Exception as e:
        # Page context destroyed during navigation - this is expected
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping clickables check - page navigating")
            return []
        raise

    return elements


async def _find_broken_images(page: object) -> list[dict[str, str]]:
    """Find images that failed to load on the page.

    Detects images with src attributes that have naturalWidth of 0 (failed to load).
    Returns empty list if page context is destroyed (e.g., during navigation).
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        broken = await page.evaluate("""
        () => {
            const results = [];
            const images = document.querySelectorAll('img[src]');

            for (const img of images) {
                // Skip tiny images (likely tracking pixels)
                if (img.width < 10 && img.height < 10) continue;

                // Check if image failed to load
                if (!img.complete || img.naturalWidth === 0) {
                    let selector = 'img';
                    if (img.id) {
                        selector = `#${img.id}`;
                    } else if (img.alt) {
                        selector = `img[alt="${img.alt.slice(0, 30).replace(/"/g, '\\"')}"]`;
                    } else if (img.className) {
                        const firstClass = img.className.split(' ')[0];
                        if (firstClass) selector = `img.${firstClass}`;
                    }

                    results.push({
                        src: img.src,
                        selector: selector
                    });
                }

                if (results.length >= 10) break;
            }
            return results;
        }
    """)
    except Exception as e:
        # Page context destroyed during navigation - this is expected
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping broken image check - page navigating")
            return []
        raise

    return broken


async def _find_accessibility_issues(
    page: object, min_contrast: float = 4.5
) -> list[dict[str, object]]:
    """Find accessibility issues on the page.

    Detects:
    - Images without alt text
    - Elements with poor contrast (if detectable via computed styles)
    - Potential keyboard traps (elements with tabindex but no visible focus)

    Returns empty list if page context is destroyed.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        issues = await page.evaluate("""
        () => {
            const results = [];

            // Check for images without alt text
            const images = document.querySelectorAll('img');
            for (const img of images) {
                if (!img.alt && !img.getAttribute('aria-label') && !img.getAttribute('aria-labelledby')) {
                    // Skip tiny images (tracking pixels)
                    if (img.width < 10 && img.height < 10) continue;

                    let selector = 'img';
                    if (img.id) selector = `#${img.id}`;
                    else if (img.src) selector = `img[src*="${img.src.slice(-30)}"]`;

                    results.push({
                        issue_type: 'missing_alt',
                        selector: selector,
                        details: { src: img.src?.slice(0, 100) }
                    });
                }
                if (results.length >= 5) break;
            }

            // Check for buttons/links without accessible names
            const interactives = document.querySelectorAll('button, a, [role="button"], [role="link"]');
            for (const el of interactives) {
                const text = (el.innerText || '').trim();
                const ariaLabel = el.getAttribute('aria-label');
                const ariaLabelledBy = el.getAttribute('aria-labelledby');
                const title = el.getAttribute('title');

                if (!text && !ariaLabel && !ariaLabelledBy && !title) {
                    let selector = el.tagName.toLowerCase();
                    if (el.id) selector = `#${el.id}`;
                    else if (el.className && typeof el.className === 'string') {
                        const firstClass = el.className.split(' ')[0];
                        if (firstClass) selector = `${el.tagName.toLowerCase()}.${firstClass}`;
                    }

                    results.push({
                        issue_type: 'missing_accessible_name',
                        selector: selector,
                        details: {}
                    });
                }
                if (results.length >= 10) break;
            }

            // Check for form inputs without labels
            const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select');
            for (const input of inputs) {
                const id = input.id;
                const ariaLabel = input.getAttribute('aria-label');
                const ariaLabelledBy = input.getAttribute('aria-labelledby');
                const placeholder = input.getAttribute('placeholder');

                let hasLabel = false;
                if (id) {
                    hasLabel = !!document.querySelector(`label[for="${id}"]`);
                }
                if (!hasLabel) {
                    hasLabel = !!input.closest('label');
                }

                if (!hasLabel && !ariaLabel && !ariaLabelledBy) {
                    let selector = input.tagName.toLowerCase();
                    if (id) selector = `#${id}`;
                    else if (input.name) selector = `${input.tagName.toLowerCase()}[name="${input.name}"]`;

                    results.push({
                        issue_type: 'missing_label',
                        selector: selector,
                        details: { placeholder: placeholder || '' }
                    });
                }
                if (results.length >= 15) break;
            }

            return results;
        }
    """)
    except Exception as e:
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping accessibility check - page navigating")
            return []
        raise

    return issues


async def _find_mobile_issues(
    page: object, viewport: tuple[int, int], min_tap_target: int = 44
) -> list[dict[str, object]]:
    """Find mobile UX issues on the page.

    Detects:
    - Tap targets smaller than minimum size
    - Horizontal scroll (content wider than viewport)
    - Text too small for mobile

    Returns empty list if page context is destroyed.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)
    viewport_width = viewport[0]

    try:
        issues = await page.evaluate(
            """
        (args) => {
            const { viewportWidth, minTapTarget } = args;
            const results = [];

            // Check for horizontal scroll
            if (document.documentElement.scrollWidth > viewportWidth + 10) {
                results.push({
                    issue_type: 'horizontal_scroll',
                    selector: 'body',
                    details: {
                        content_width: document.documentElement.scrollWidth,
                        viewport_width: viewportWidth
                    }
                });
            }

            // Check tap target sizes
            const tappables = document.querySelectorAll('a, button, input, select, textarea, [role="button"], [role="link"]');
            for (const el of tappables) {
                if (!el.offsetParent) continue; // Skip hidden elements

                const rect = el.getBoundingClientRect();
                const width = rect.width;
                const height = rect.height;

                if ((width < minTapTarget || height < minTapTarget) && width > 0 && height > 0) {
                    let selector = el.tagName.toLowerCase();
                    const text = (el.innerText || '').trim().slice(0, 20);
                    if (text) {
                        selector = `${el.tagName.toLowerCase()}:has-text('${text.replace(/'/g, "\\'")}')`;
                    } else if (el.id) {
                        selector = `#${el.id}`;
                    }

                    results.push({
                        issue_type: 'small_tap_target',
                        selector: selector,
                        details: {
                            width: Math.round(width),
                            height: Math.round(height),
                            min_required: minTapTarget
                        },
                        x: Math.round(rect.left + width / 2),
                        y: Math.round(rect.top + height / 2)
                    });
                }
                if (results.length >= 10) break;
            }

            return results;
        }
    """,
            {"viewportWidth": viewport_width, "minTapTarget": min_tap_target},
        )
    except Exception as e:
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping mobile check - page navigating")
            return []
        raise

    return issues


async def _find_error_messages(page: object) -> list[dict[str, str]]:
    """Find visible error messages on the page.

    Detects elements with error styling or ARIA invalid state.
    Returns empty list if page context is destroyed.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        errors = await page.evaluate("""
        () => {
            const results = [];

            // Check for elements with error classes or aria-invalid
            const errorSelectors = [
                '[aria-invalid="true"]',
                '.error',
                '.error-message',
                '.field-error',
                '.validation-error',
                '.has-error',
                '.is-invalid',
                '[class*="error"]',
                '[class*="invalid"]'
            ];

            for (const selector of errorSelectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        if (!el.offsetParent) continue; // Skip hidden

                        const text = (el.innerText || el.textContent || '').trim();
                        if (!text && !el.matches('[aria-invalid]')) continue;

                        let elSelector = el.tagName.toLowerCase();
                        if (el.id) elSelector = `#${el.id}`;
                        else if (el.className && typeof el.className === 'string') {
                            const firstClass = el.className.split(' ')[0];
                            if (firstClass) elSelector = `${el.tagName.toLowerCase()}.${firstClass}`;
                        }

                        results.push({
                            selector: elSelector,
                            message: text.slice(0, 200)
                        });

                        if (results.length >= 10) return results;
                    }
                } catch (e) {
                    // Invalid selector, skip
                }
            }

            return results;
        }
    """)
    except Exception as e:
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping error message check - page navigating")
            return []
        raise

    return errors


async def _find_modal_overlays(page: object) -> list[dict[str, str]]:
    """Find intrusive modal overlays on the page.

    Detects modals, popups, and overlays that may frustrate users.
    Returns empty list if page context is destroyed.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        modals = await page.evaluate("""
        () => {
            const results = [];

            // Common modal selectors
            const modalSelectors = [
                '[role="dialog"]',
                '[role="alertdialog"]',
                '.modal',
                '.popup',
                '.overlay',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="overlay"]',
                '[class*="lightbox"]'
            ];

            for (const selector of modalSelectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        if (!el.offsetParent) continue; // Skip hidden

                        const style = window.getComputedStyle(el);
                        // Check if it's actually overlaying content
                        if (style.position !== 'fixed' && style.position !== 'absolute') continue;
                        if (style.zIndex && parseInt(style.zIndex) < 100) continue;

                        // Check for close button
                        const hasCloseButton = !!el.querySelector('[aria-label*="close"], [aria-label*="Close"], .close, [class*="close"], button:has-text("×"), button:has-text("X")');

                        let elSelector = el.tagName.toLowerCase();
                        if (el.id) elSelector = `#${el.id}`;
                        else if (el.className && typeof el.className === 'string') {
                            const firstClass = el.className.split(' ')[0];
                            if (firstClass) elSelector = `${el.tagName.toLowerCase()}.${firstClass}`;
                        }

                        const modalType = hasCloseButton ? 'dismissible_modal' : 'intrusive_modal';

                        results.push({
                            selector: elSelector,
                            modal_type: modalType,
                            has_close_button: hasCloseButton
                        });

                        if (results.length >= 5) return results;
                    }
                } catch (e) {
                    // Invalid selector, skip
                }
            }

            return results;
        }
    """)
    except Exception as e:
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping modal check - page navigating")
            return []
        raise

    return modals


async def _find_copy_paste_blocks(page: object) -> list[dict[str, str]]:
    """Find elements that block text selection/copy.

    Detects user-select: none on content elements.
    Returns empty list if page context is destroyed.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        blocks = await page.evaluate("""
        () => {
            const results = [];

            // Check content elements for user-select: none
            const contentElements = document.querySelectorAll('p, article, section, div, span, li, td, th');

            for (const el of contentElements) {
                const style = window.getComputedStyle(el);
                if (style.userSelect === 'none' || style.webkitUserSelect === 'none') {
                    // Skip if it's a button or interactive element
                    if (el.closest('button, a, input, select, textarea')) continue;

                    // Only flag if it has meaningful text content
                    const text = (el.innerText || '').trim();
                    if (text.length < 20) continue;

                    let selector = el.tagName.toLowerCase();
                    if (el.id) selector = `#${el.id}`;
                    else if (el.className && typeof el.className === 'string') {
                        const firstClass = el.className.split(' ')[0];
                        if (firstClass) selector = `${el.tagName.toLowerCase()}.${firstClass}`;
                    }

                    results.push({
                        selector: selector,
                        text_preview: text.slice(0, 50)
                    });

                    if (results.length >= 5) return results;
                }
            }

            return results;
        }
    """)
    except Exception as e:
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping copy/paste check - page navigating")
            return []
        raise

    return blocks


async def _find_infinite_scroll_issues(page: object) -> list[dict[str, object]]:
    """Find infinite scroll issues on the page.

    Detects pages where footer is unreachable or scroll position may be lost.
    Returns empty list if page context is destroyed.
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        issues = await page.evaluate("""
        () => {
            const results = [];

            // Check if page has infinite scroll indicators
            const infiniteScrollIndicators = [
                '[data-infinite-scroll]',
                '.infinite-scroll',
                '[class*="infinite"]',
                '[class*="lazy-load"]'
            ];

            let hasInfiniteScroll = false;
            for (const selector of infiniteScrollIndicators) {
                if (document.querySelector(selector)) {
                    hasInfiniteScroll = true;
                    break;
                }
            }

            // Check if footer exists and is reachable
            const footer = document.querySelector('footer, [role="contentinfo"], .footer');
            if (footer && hasInfiniteScroll) {
                const rect = footer.getBoundingClientRect();
                const viewportHeight = window.innerHeight;
                const docHeight = document.documentElement.scrollHeight;

                // If footer is way below viewport and page has infinite scroll
                if (rect.top > viewportHeight * 3) {
                    results.push({
                        issue_type: 'footer_unreachable',
                        details: {
                            footer_position: Math.round(rect.top),
                            viewport_height: viewportHeight,
                            doc_height: docHeight
                        }
                    });
                }
            }

            return results;
        }
    """)
    except Exception as e:
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping infinite scroll check - page navigating")
            return []
        raise

    return issues


async def _find_rage_decoys(page: object) -> list[dict[str, str]]:
    """Find elements that look clickable but are not actual buttons or links.

    Detects elements with visual affordances (cursor:pointer, button-like styling,
    box shadows, transforms, hover effects) that are not semantic interactive elements.
    Returns empty list if page context is destroyed (e.g., during navigation).
    """
    from playwright.async_api import Page

    assert isinstance(page, Page)

    try:
        candidates = await page.evaluate("""
        () => {
            const results = [];
            const interactiveTags = new Set(['a', 'button', 'input', 'select', 'textarea']);
            const interactiveRoles = new Set([
                'button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'textbox', 'combobox'
            ]);

            // Query common decoy patterns: divs/spans with pointer cursor or button-like appearance
            const candidates = document.querySelectorAll(
                'div, span, p, li, img, label, td, th, h1, h2, h3, h4, h5, h6, article, section, figure'
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

                // Check for explicit button/clickable class patterns (tightened to reduce false positives)
                if (el.className && /\b(btn|button|clickable)\b/i.test(String(el.className))) {
                    reasons.push('clickable class name');
                }

                // Check for box shadow (often indicates clickable cards)
                if (style.boxShadow && style.boxShadow !== 'none') {
                    const hasShadow = !/^0px 0px 0px/.test(style.boxShadow);
                    if (hasShadow && style.cursor === 'pointer') {
                        reasons.push('box-shadow with pointer');
                    }
                }

                // Check for border-radius with background (button-like appearance)
                if (style.borderRadius && style.borderRadius !== '0px') {
                    const hasBackground = style.backgroundColor !== 'rgba(0, 0, 0, 0)' &&
                                         style.backgroundColor !== 'transparent';
                    if (hasBackground && parseFloat(style.borderRadius) >= 4) {
                        reasons.push('button-like styling');
                    }
                }

                // Check for transform or transition (often indicates interactive elements)
                if (style.transition && /transform|scale|translate/i.test(style.transition)) {
                    if (style.cursor === 'pointer') {
                        reasons.push('interactive transition');
                    }
                }

                // Check for tabindex (suggests keyboard navigation expectation)
                if (el.hasAttribute('tabindex') && el.getAttribute('tabindex') !== '-1') {
                    reasons.push('has tabindex');
                }

                // Require 2+ visual affordances to reduce false positives
                if (reasons.length >= 2) {
                    // Build a selector
                    let selector = tag;
                    const text = (el.innerText || '').trim().slice(0, 30);
                    if (text) {
                        selector = `${tag}:has-text('${text.replace(/'/g, "\\'")}')`;
                    } else if (el.id) {
                        selector = `#${el.id}`;
                    } else if (el.className && typeof el.className === 'string') {
                        const firstClass = el.className.split(' ')[0];
                        if (firstClass) selector = `${tag}.${firstClass}`;
                    }

                    // Get bounding box for annotation
                    const rect = el.getBoundingClientRect();
                    const x = Math.round(rect.left + rect.width / 2);
                    const y = Math.round(rect.top + rect.height / 2);

                    results.push({
                        selector: selector,
                        reason: reasons.join(', '),
                        x: x,
                        y: y
                    });
                }

                // Limit to avoid flooding
                if (results.length >= 10) break;
            }
            return results;
        }
    """)
    except Exception as e:
        # Page context destroyed during navigation - this is expected
        if "context was destroyed" in str(e) or "navigation" in str(e).lower():
            log.debug("Skipping rage decoy check - page navigating")
            return []
        raise

    return candidates


async def _run_page_checks(
    page: object,
    detector: EventDetector,
    persona: Persona,
    url: str,
) -> None:
    """Run all page-level friction detection checks.

    This consolidates the various detection functions and records events
    based on persona preferences.
    """
    weights = persona.get_detection_weights()

    # Check for error messages (prioritized for form_filler, anxious_newbie)
    if weights.get("error_message_visible", 1.0) >= 1.0:
        errors = await _find_error_messages(page)
        for err in errors:
            detector.record_error_message(url, err.get("message", ""), err.get("selector", ""))
            log.info("event: Error message - %s", err.get("message", "")[:60])

    # Check for modal frustration (prioritized for casual_browser, frustrated_exec)
    if weights.get("modal_frustration", 1.0) >= 1.0:
        modals = await _find_modal_overlays(page)
        for modal in modals:
            if modal.get("modal_type") == "intrusive_modal":
                detector.record_modal_frustration(
                    url, modal.get("modal_type", ""), modal.get("selector", "")
                )
                log.info("event: Modal frustration - %s", modal.get("modal_type", ""))

    # Check for accessibility issues (prioritized for accessibility_user)
    if weights.get("accessibility_failure", 1.0) >= 1.0:
        a11y_issues = await _find_accessibility_issues(page)
        for issue in a11y_issues:
            detector.record_accessibility_failure(
                url,
                issue.get("issue_type", "unknown"),
                issue.get("selector", ""),
                issue.get("details"),
            )
            log.info("event: Accessibility issue - %s", issue.get("issue_type", ""))

    # Check for mobile issues (prioritized for mobile_commuter, only on mobile viewport)
    is_mobile = persona.viewport[0] < 768
    if is_mobile and weights.get("mobile_tap_target", 1.0) >= 1.0:
        mobile_issues = await _find_mobile_issues(
            page,
            persona.viewport,
            detector.thresholds.tap_target_min_px,
        )
        for issue in mobile_issues:
            detector.record_mobile_issue(
                url,
                issue.get("issue_type", "unknown"),
                issue.get("selector", ""),
                issue.get("details"),
            )
            log.info("event: Mobile issue - %s", issue.get("issue_type", ""))

    # Check for copy/paste blocks (prioritized for power_user, accessibility_user)
    if weights.get("copy_paste_failure", 1.0) >= 1.0:
        blocks = await _find_copy_paste_blocks(page)
        for block in blocks:
            detector.record_copy_paste_failure(url, block.get("selector", ""))
            log.info("event: Copy/paste blocked - %s", block.get("selector", ""))

    # Check for infinite scroll issues (prioritized for methodical_tester, casual_browser)
    if weights.get("infinite_scroll_trap", 1.0) >= 1.0:
        scroll_issues = await _find_infinite_scroll_issues(page)
        for issue in scroll_issues:
            detector.record_infinite_scroll_trap(url, issue.get("issue_type", "unknown"))
            log.info("event: Infinite scroll issue - %s", issue.get("issue_type", ""))

    # Track cart visits for cart_abandonment detection
    if detector._is_cart_url(url):
        detector.record_cart_visit()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run a single UX-friction agent")
    parser.add_argument("--url", required=True, help="Target URL to test")
    parser.add_argument("--persona", default="frustrated_exec", help="Persona name")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.add_argument("--llm", action="store_true", help="Use LLM vision model for navigation")
    parser.add_argument(
        "--max-llm-calls", type=int, default=None, help="Max LLM API calls per session"
    )
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
