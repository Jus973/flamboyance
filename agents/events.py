"""Frustration event detection for UX-friction agents.

Detects multiple categories of frustration:

Notice tier (passive UX friction):
1. **slow_load** — page load time exceeds a threshold (default 3 000 ms).
2. **dead_end** — no clickable elements found on a page after load.
3. **long_dwell** — agent stays on a page without acting for too long (default 10 s).
4. **rage_decoy** — elements that look clickable but are not buttons/links.
5. **js_error** — JavaScript console errors detected on the page.
6. **broken_image** — images that failed to load (404 or broken src).
7. **network_error** — failed network requests (API errors, timeouts).
8. **error_message_visible** — visible error states on the page.
9. **accessibility_failure** — missing alt text, poor contrast, keyboard traps.
10. **mobile_tap_target** — tap targets <44px, horizontal scroll, viewport issues.
11. **confusing_navigation** — breadcrumb depth >4, unclear CTAs.
12. **modal_frustration** — intrusive overlays, hard-to-dismiss modals.
13. **copy_paste_failure** — disabled text selection on content.
14. **infinite_scroll_trap** — can't reach footer, scroll position lost.

Frustration tier (active user struggle):
15. **Circular navigation** — visiting A → B → A in the URL history.
16. **Rage clicks** — ≥3 clicks on the same non-interactive element within 1.5 s.
17. **scroll_rage** — rapid up/down scroll events (>5 direction changes in 3s).
18. **form_abandonment** — form focus → page exit without submit.
19. **session_timeout** — session expiry modals/redirects detected.
20. **slow_interaction** — button click → DOM change latency >500ms.
21. **search_frustration** — zero results, repeated searches, no feedback.
22. **cart_abandonment** — cart page → exit without checkout.
23. **back_button_abuse** — >3 back navigations in sequence.
24. **Unmet goal** — the agent's goal was not reached before timeout / give-up.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import EventThresholds


class EventSeverity(Enum):
    """Severity levels for frustration events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


EVENT_SEVERITY: dict[str, EventSeverity] = {
    # Notice tier
    "slow_load": EventSeverity.MEDIUM,
    "dead_end": EventSeverity.HIGH,
    "long_dwell": EventSeverity.LOW,
    "rage_decoy": EventSeverity.MEDIUM,
    "js_error": EventSeverity.HIGH,
    "broken_image": EventSeverity.MEDIUM,
    "network_error": EventSeverity.HIGH,
    "error_message_visible": EventSeverity.MEDIUM,
    "accessibility_failure": EventSeverity.HIGH,
    "mobile_tap_target": EventSeverity.MEDIUM,
    "confusing_navigation": EventSeverity.MEDIUM,
    "modal_frustration": EventSeverity.MEDIUM,
    "copy_paste_failure": EventSeverity.LOW,
    "infinite_scroll_trap": EventSeverity.MEDIUM,
    # Frustration tier
    "circular_navigation": EventSeverity.MEDIUM,
    "rage_click": EventSeverity.HIGH,
    "scroll_rage": EventSeverity.MEDIUM,
    "form_abandonment": EventSeverity.HIGH,
    "session_timeout": EventSeverity.HIGH,
    "slow_interaction": EventSeverity.MEDIUM,
    "search_frustration": EventSeverity.MEDIUM,
    "cart_abandonment": EventSeverity.HIGH,
    "back_button_abuse": EventSeverity.MEDIUM,
    "unmet_goal": EventSeverity.CRITICAL,
}


@dataclass
class FrustrationEvent:
    kind: str
    timestamp: float
    description: str
    url: str = ""
    details: dict[str, object] = field(default_factory=dict)

    @property
    def severity(self) -> EventSeverity:
        """Get the severity level for this event type."""
        return EVENT_SEVERITY.get(self.kind, EventSeverity.MEDIUM)


class EventDetector:
    """Stateful detector that accumulates navigation/click history and emits events.

    Thresholds can be configured via:
    1. Environment variables (FLAMBOYANCE_SLOW_LOAD_THRESHOLD_MS, etc.)
    2. Threshold profiles ("strict", "balanced", "lenient")
    3. Direct constructor argument for per-instance customization

    Example:
        # Use default thresholds from environment
        detector = EventDetector()

        # Use strict profile
        from agents.config import EventThresholds
        detector = EventDetector(thresholds=EventThresholds.from_profile("strict"))

        # Custom thresholds
        detector = EventDetector(thresholds=EventThresholds(
            slow_load_threshold_ms=2000.0,
            long_dwell_threshold_s=5.0,
        ))
    """

    def __init__(self, thresholds: EventThresholds | None = None) -> None:
        from .config import DEFAULT_THRESHOLDS

        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.url_history: list[str] = []
        self.click_log: list[tuple[float, str]] = []  # (timestamp, selector)
        self.events: list[FrustrationEvent] = []
        self.last_action_time: float = time.time()
        # New tracking state for expanded friction patterns
        self.scroll_log: list[tuple[float, str]] = []  # (timestamp, direction)
        self.back_nav_count: int = 0  # Sequential back navigations
        self.form_focus_url: str | None = None  # URL where form was focused
        self.search_queries: list[str] = []  # Recent search queries
        self.cart_visited: bool = False  # Whether cart page was visited

    @property
    def RAGE_CLICK_THRESHOLD(self) -> int:
        """Number of clicks to trigger rage click detection."""
        return self.thresholds.rage_click_threshold

    @property
    def RAGE_CLICK_WINDOW_S(self) -> float:
        """Time window for rage click detection in seconds."""
        return self.thresholds.rage_click_window_s

    @property
    def SLOW_LOAD_THRESHOLD_MS(self) -> float:
        """Page load time threshold in milliseconds."""
        return self.thresholds.slow_load_threshold_ms

    @property
    def LONG_DWELL_THRESHOLD_S(self) -> float:
        """Time without action threshold in seconds."""
        return self.thresholds.long_dwell_threshold_s

    @property
    def SCROLL_RAGE_THRESHOLD(self) -> int:
        """Number of direction changes to trigger scroll rage."""
        return self.thresholds.scroll_rage_direction_changes

    @property
    def SCROLL_RAGE_WINDOW_S(self) -> float:
        """Time window for scroll rage detection in seconds."""
        return self.thresholds.scroll_rage_window_s

    @property
    def SLOW_INTERACTION_THRESHOLD_MS(self) -> float:
        """Click to DOM change latency threshold in milliseconds."""
        return self.thresholds.slow_interaction_threshold_ms

    @property
    def BACK_BUTTON_ABUSE_THRESHOLD(self) -> int:
        """Number of sequential back navigations to trigger abuse detection."""
        return self.thresholds.back_button_abuse_threshold

    # ── Notice-tier detectors ──────────────────────────────────────────

    def record_slow_load(
        self, url: str, load_time_ms: float
    ) -> FrustrationEvent | None:
        """Emit a *slow_load* event if page load exceeded the threshold."""
        if load_time_ms <= self.SLOW_LOAD_THRESHOLD_MS:
            return None
        evt = FrustrationEvent(
            kind="slow_load",
            timestamp=time.time(),
            description=(
                f"Slow page load: {load_time_ms:.0f}ms "
                f"(threshold {self.SLOW_LOAD_THRESHOLD_MS:.0f}ms)"
            ),
            url=url,
            details={"load_time_ms": load_time_ms},
        )
        self.events.append(evt)
        return evt

    def record_dead_end(self, url: str) -> FrustrationEvent:
        """Emit a *dead_end* event when no clickable elements are found."""
        evt = FrustrationEvent(
            kind="dead_end",
            timestamp=time.time(),
            description="Dead end: no clickable elements found on page",
            url=url,
        )
        self.events.append(evt)
        return evt

    def record_long_dwell(
        self, url: str, dwell_s: float
    ) -> FrustrationEvent | None:
        """Emit a *long_dwell* event if dwell time exceeds the threshold."""
        if dwell_s <= self.LONG_DWELL_THRESHOLD_S:
            return None
        evt = FrustrationEvent(
            kind="long_dwell",
            timestamp=time.time(),
            description=(
                f"Long dwell: {dwell_s:.1f}s without action "
                f"(threshold {self.LONG_DWELL_THRESHOLD_S:.1f}s)"
            ),
            url=url,
            details={"dwell_seconds": dwell_s},
        )
        self.events.append(evt)
        self.touch()
        return evt

    def touch(self) -> None:
        """Reset the dwell timer (call after every meaningful agent action)."""
        self.last_action_time = time.time()

    def record_rage_decoy(
        self, url: str, selector: str, reason: str, x: int | None = None, y: int | None = None
    ) -> FrustrationEvent:
        """Emit a *rage_decoy* event for elements that look clickable but aren't.

        Args:
            url: Page URL where the decoy was found.
            selector: CSS selector or description of the decoy element.
            reason: Why the element appears clickable (e.g., "cursor:pointer",
                    "button-like styling", "hover effect").
            x: X coordinate of element center (for screenshot annotation).
            y: Y coordinate of element center (for screenshot annotation).
        """
        details: dict[str, object] = {"selector": selector, "reason": reason}
        if x is not None and y is not None:
            details["x"] = x
            details["y"] = y
        evt = FrustrationEvent(
            kind="rage_decoy",
            timestamp=time.time(),
            description=f"Rage decoy: element '{selector}' looks clickable ({reason}) but is not interactive",
            url=url,
            details=details,
        )
        self.events.append(evt)
        return evt

    def record_js_error(
        self, url: str, message: str, source: str = "", line: int = 0
    ) -> FrustrationEvent:
        """Emit a *js_error* event when a JavaScript error is detected.

        Args:
            url: Page URL where the error occurred.
            message: The error message from the console.
            source: Source file or script that caused the error.
            line: Line number where the error occurred.
        """
        desc = f"JavaScript error: {message[:100]}"
        if source:
            desc += f" (source: {source}"
            if line:
                desc += f":{line}"
            desc += ")"

        evt = FrustrationEvent(
            kind="js_error",
            timestamp=time.time(),
            description=desc,
            url=url,
            details={"message": message, "source": source, "line": line},
        )
        self.events.append(evt)
        return evt

    def record_broken_image(
        self, url: str, image_src: str, selector: str = ""
    ) -> FrustrationEvent:
        """Emit a *broken_image* event when an image fails to load.

        Args:
            url: Page URL where the broken image was found.
            image_src: The src attribute of the broken image.
            selector: CSS selector for the image element.
        """
        evt = FrustrationEvent(
            kind="broken_image",
            timestamp=time.time(),
            description=f"Broken image: failed to load '{image_src[:80]}'",
            url=url,
            details={"image_src": image_src, "selector": selector},
        )
        self.events.append(evt)
        return evt

    def record_network_error(
        self,
        url: str,
        request_url: str,
        status_code: int = 0,
        error_text: str = "",
        method: str = "GET",
    ) -> FrustrationEvent:
        """Emit a *network_error* event when a network request fails.

        Args:
            url: Page URL where the error occurred.
            request_url: The URL of the failed request.
            status_code: HTTP status code (0 for connection failures).
            error_text: Error description or response text.
            method: HTTP method (GET, POST, etc.).
        """
        if status_code >= 400:
            desc = f"Network error: {method} {request_url[:60]} returned {status_code}"
        else:
            desc = f"Network error: {method} {request_url[:60]} failed"
            if error_text:
                desc += f" ({error_text[:40]})"

        evt = FrustrationEvent(
            kind="network_error",
            timestamp=time.time(),
            description=desc,
            url=url,
            details={
                "request_url": request_url,
                "status_code": status_code,
                "error_text": error_text,
                "method": method,
            },
        )
        self.events.append(evt)
        return evt

    # ── Frustration-tier detectors ─────────────────────────────────────

    def record_navigation(self, url: str) -> FrustrationEvent | None:
        """Record a URL visit; returns a FrustrationEvent if circular nav detected."""
        self.url_history.append(url)
        if len(self.url_history) >= 3:
            a, b, c = (
                self.url_history[-3],
                self.url_history[-2],
                self.url_history[-1],
            )
            if a == c and a != b:
                evt = FrustrationEvent(
                    kind="circular_navigation",
                    timestamp=time.time(),
                    description=f"Circular navigation detected: {a} → {b} → {a}",
                    url=url,
                    details={"sequence": [a, b, c]},
                )
                self.events.append(evt)
                return evt
        return None

    def record_click(
        self, selector: str, *, is_interactive: bool = True
    ) -> FrustrationEvent | None:
        """Record a click; returns a FrustrationEvent if rage-click detected."""
        now = time.time()
        self.click_log.append((now, selector))

        if is_interactive:
            return None

        cutoff = now - self.RAGE_CLICK_WINDOW_S
        recent = [
            (t, s) for t, s in self.click_log if t >= cutoff and s == selector
        ]
        if len(recent) >= self.RAGE_CLICK_THRESHOLD:
            evt = FrustrationEvent(
                kind="rage_click",
                timestamp=now,
                description=(
                    f"Rage click: {len(recent)} clicks on '{selector}' "
                    f"within {self.RAGE_CLICK_WINDOW_S}s"
                ),
                details={"selector": selector, "count": len(recent)},
            )
            self.events.append(evt)
            # Clear to avoid duplicate firing on the next click.
            self.click_log = [
                (t, s) for t, s in self.click_log if s != selector
            ]
            return evt
        return None

    def check_unmet_goal(
        self, goal: str, *, reached: bool, timed_out: bool
    ) -> FrustrationEvent | None:
        """Call at end of agent run. Returns event if goal was not reached."""
        if reached:
            return None
        reason = "timeout" if timed_out else "gave up"
        evt = FrustrationEvent(
            kind="unmet_goal",
            timestamp=time.time(),
            description=f"Unmet goal ({reason}): {goal}",
            details={"goal": goal, "reason": reason},
        )
        self.events.append(evt)
        return evt

    # ── New friction pattern detectors ────────────────────────────────────

    def record_form_abandonment(
        self, url: str, form_selector: str = ""
    ) -> FrustrationEvent:
        """Emit a *form_abandonment* event when user leaves page with focused form."""
        evt = FrustrationEvent(
            kind="form_abandonment",
            timestamp=time.time(),
            description=f"Form abandonment: user left page without submitting form",
            url=url,
            details={"form_selector": form_selector},
        )
        self.events.append(evt)
        self.form_focus_url = None
        return evt

    def record_form_focus(self, url: str) -> None:
        """Track that a form field was focused on this URL."""
        self.form_focus_url = url

    def check_form_abandonment(self, new_url: str) -> FrustrationEvent | None:
        """Check if navigating away from a page with focused form."""
        if self.form_focus_url and self.form_focus_url != new_url:
            return self.record_form_abandonment(self.form_focus_url)
        return None

    def record_scroll_rage(
        self, url: str, direction: str
    ) -> FrustrationEvent | None:
        """Record a scroll event; returns event if scroll rage detected.

        Args:
            url: Current page URL.
            direction: "up" or "down".
        """
        now = time.time()
        self.scroll_log.append((now, direction))

        cutoff = now - self.SCROLL_RAGE_WINDOW_S
        recent = [(t, d) for t, d in self.scroll_log if t >= cutoff]

        # Count direction changes
        direction_changes = 0
        for i in range(1, len(recent)):
            if recent[i][1] != recent[i - 1][1]:
                direction_changes += 1

        if direction_changes >= self.SCROLL_RAGE_THRESHOLD:
            evt = FrustrationEvent(
                kind="scroll_rage",
                timestamp=now,
                description=(
                    f"Scroll rage: {direction_changes} direction changes "
                    f"within {self.SCROLL_RAGE_WINDOW_S}s"
                ),
                url=url,
                details={"direction_changes": direction_changes},
            )
            self.events.append(evt)
            self.scroll_log = []  # Reset to avoid duplicate firing
            return evt
        return None

    def record_error_message(
        self, url: str, message: str, selector: str = ""
    ) -> FrustrationEvent:
        """Emit an *error_message_visible* event when error state is detected."""
        evt = FrustrationEvent(
            kind="error_message_visible",
            timestamp=time.time(),
            description=f"Error message visible: {message[:100]}",
            url=url,
            details={"message": message, "selector": selector},
        )
        self.events.append(evt)
        return evt

    def record_session_timeout(
        self, url: str, reason: str = "session expired"
    ) -> FrustrationEvent:
        """Emit a *session_timeout* event when session expiry is detected."""
        evt = FrustrationEvent(
            kind="session_timeout",
            timestamp=time.time(),
            description=f"Session timeout: {reason}",
            url=url,
            details={"reason": reason},
        )
        self.events.append(evt)
        return evt

    def record_accessibility_failure(
        self,
        url: str,
        issue_type: str,
        element_selector: str = "",
        details: dict[str, object] | None = None,
    ) -> FrustrationEvent:
        """Emit an *accessibility_failure* event.

        Args:
            url: Page URL.
            issue_type: Type of issue (e.g., "missing_alt", "poor_contrast", "keyboard_trap").
            element_selector: CSS selector for the problematic element.
            details: Additional details about the issue.
        """
        evt = FrustrationEvent(
            kind="accessibility_failure",
            timestamp=time.time(),
            description=f"Accessibility issue: {issue_type}",
            url=url,
            details={
                "issue_type": issue_type,
                "selector": element_selector,
                **(details or {}),
            },
        )
        self.events.append(evt)
        return evt

    def record_mobile_issue(
        self,
        url: str,
        issue_type: str,
        element_selector: str = "",
        details: dict[str, object] | None = None,
    ) -> FrustrationEvent:
        """Emit a *mobile_tap_target* event for mobile UX issues.

        Args:
            url: Page URL.
            issue_type: Type of issue (e.g., "small_tap_target", "horizontal_scroll", "viewport").
            element_selector: CSS selector for the problematic element.
            details: Additional details (e.g., actual size).
        """
        evt = FrustrationEvent(
            kind="mobile_tap_target",
            timestamp=time.time(),
            description=f"Mobile issue: {issue_type}",
            url=url,
            details={
                "issue_type": issue_type,
                "selector": element_selector,
                **(details or {}),
            },
        )
        self.events.append(evt)
        return evt

    def record_slow_interaction(
        self, url: str, latency_ms: float, action: str = "click"
    ) -> FrustrationEvent | None:
        """Emit a *slow_interaction* event if action latency exceeds threshold."""
        if latency_ms <= self.SLOW_INTERACTION_THRESHOLD_MS:
            return None
        evt = FrustrationEvent(
            kind="slow_interaction",
            timestamp=time.time(),
            description=(
                f"Slow interaction: {action} took {latency_ms:.0f}ms "
                f"(threshold {self.SLOW_INTERACTION_THRESHOLD_MS:.0f}ms)"
            ),
            url=url,
            details={"latency_ms": latency_ms, "action": action},
        )
        self.events.append(evt)
        return evt

    def record_confusing_navigation(
        self, url: str, reason: str, details: dict[str, object] | None = None
    ) -> FrustrationEvent:
        """Emit a *confusing_navigation* event for navigation UX issues."""
        evt = FrustrationEvent(
            kind="confusing_navigation",
            timestamp=time.time(),
            description=f"Confusing navigation: {reason}",
            url=url,
            details={"reason": reason, **(details or {})},
        )
        self.events.append(evt)
        return evt

    def record_modal_frustration(
        self, url: str, modal_type: str, selector: str = ""
    ) -> FrustrationEvent:
        """Emit a *modal_frustration* event for intrusive modals."""
        evt = FrustrationEvent(
            kind="modal_frustration",
            timestamp=time.time(),
            description=f"Modal frustration: {modal_type}",
            url=url,
            details={"modal_type": modal_type, "selector": selector},
        )
        self.events.append(evt)
        return evt

    def record_search_frustration(
        self, url: str, reason: str, query: str = ""
    ) -> FrustrationEvent:
        """Emit a *search_frustration* event for search UX issues."""
        if query:
            self.search_queries.append(query)
        evt = FrustrationEvent(
            kind="search_frustration",
            timestamp=time.time(),
            description=f"Search frustration: {reason}",
            url=url,
            details={"reason": reason, "query": query, "recent_queries": self.search_queries[-5:]},
        )
        self.events.append(evt)
        return evt

    def record_cart_abandonment(self, url: str) -> FrustrationEvent:
        """Emit a *cart_abandonment* event when user leaves cart without checkout."""
        evt = FrustrationEvent(
            kind="cart_abandonment",
            timestamp=time.time(),
            description="Cart abandonment: user left cart page without completing checkout",
            url=url,
            details={},
        )
        self.events.append(evt)
        self.cart_visited = False
        return evt

    def record_cart_visit(self) -> None:
        """Track that the cart page was visited."""
        self.cart_visited = True

    def check_cart_abandonment(self, new_url: str) -> FrustrationEvent | None:
        """Check if leaving cart page without checkout."""
        if self.cart_visited and not self._is_checkout_url(new_url):
            # Only trigger if not going to checkout
            if not self._is_cart_url(new_url):
                return self.record_cart_abandonment(new_url)
        return None

    def _is_cart_url(self, url: str) -> bool:
        """Check if URL appears to be a cart page."""
        cart_patterns = ["cart", "basket", "bag", "shopping-cart"]
        url_lower = url.lower()
        return any(p in url_lower for p in cart_patterns)

    def _is_checkout_url(self, url: str) -> bool:
        """Check if URL appears to be a checkout page."""
        checkout_patterns = ["checkout", "payment", "order", "purchase", "pay"]
        url_lower = url.lower()
        return any(p in url_lower for p in checkout_patterns)

    def record_back_button(self, url: str) -> FrustrationEvent | None:
        """Record a back navigation; returns event if abuse detected."""
        self.back_nav_count += 1
        if self.back_nav_count >= self.BACK_BUTTON_ABUSE_THRESHOLD:
            evt = FrustrationEvent(
                kind="back_button_abuse",
                timestamp=time.time(),
                description=(
                    f"Back button abuse: {self.back_nav_count} sequential back navigations"
                ),
                url=url,
                details={"count": self.back_nav_count},
            )
            self.events.append(evt)
            self.back_nav_count = 0  # Reset
            return evt
        return None

    def reset_back_button_count(self) -> None:
        """Reset back button counter (call on forward navigation)."""
        self.back_nav_count = 0

    def record_copy_paste_failure(
        self, url: str, selector: str = ""
    ) -> FrustrationEvent:
        """Emit a *copy_paste_failure* event when text selection is blocked."""
        evt = FrustrationEvent(
            kind="copy_paste_failure",
            timestamp=time.time(),
            description="Copy/paste blocked: text selection disabled on content",
            url=url,
            details={"selector": selector},
        )
        self.events.append(evt)
        return evt

    def record_infinite_scroll_trap(
        self, url: str, reason: str = "footer unreachable"
    ) -> FrustrationEvent:
        """Emit an *infinite_scroll_trap* event."""
        evt = FrustrationEvent(
            kind="infinite_scroll_trap",
            timestamp=time.time(),
            description=f"Infinite scroll trap: {reason}",
            url=url,
            details={"reason": reason},
        )
        self.events.append(evt)
        return evt

    def all_events(self) -> list[FrustrationEvent]:
        return list(self.events)
