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

Frustration tier (active user struggle):
8. **Circular navigation** — visiting A → B → A in the URL history.
9. **Rage clicks** — ≥3 clicks on the same non-interactive element within 1.5 s.
10. **Unmet goal** — the agent's goal was not reached before timeout / give-up.
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
    "slow_load": EventSeverity.MEDIUM,
    "dead_end": EventSeverity.HIGH,
    "long_dwell": EventSeverity.LOW,
    "rage_decoy": EventSeverity.MEDIUM,
    "js_error": EventSeverity.HIGH,
    "broken_image": EventSeverity.MEDIUM,
    "network_error": EventSeverity.HIGH,
    "circular_navigation": EventSeverity.MEDIUM,
    "rage_click": EventSeverity.HIGH,
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
        self, url: str, selector: str, reason: str
    ) -> FrustrationEvent:
        """Emit a *rage_decoy* event for elements that look clickable but aren't.

        Args:
            url: Page URL where the decoy was found.
            selector: CSS selector or description of the decoy element.
            reason: Why the element appears clickable (e.g., "cursor:pointer",
                    "button-like styling", "hover effect").
        """
        evt = FrustrationEvent(
            kind="rage_decoy",
            timestamp=time.time(),
            description=f"Rage decoy: element '{selector}' looks clickable ({reason}) but is not interactive",
            url=url,
            details={"selector": selector, "reason": reason},
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

    def all_events(self) -> list[FrustrationEvent]:
        return list(self.events)
