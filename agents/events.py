"""Frustration event detection for UX-friction agents.

Detects three categories of frustration:
1. **Circular navigation** — visiting A → B → A in the URL history.
2. **Rage clicks** — ≥3 clicks on the same non-interactive element within 1.5 s.
3. **Unmet goal** — the agent's goal was not reached before timeout / give-up.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class FrustrationEvent:
    kind: str  # "circular_navigation" | "rage_click" | "unmet_goal"
    timestamp: float
    description: str
    url: str = ""
    details: dict[str, object] = field(default_factory=dict)


class EventDetector:
    """Stateful detector that accumulates navigation/click history and emits events."""

    RAGE_CLICK_THRESHOLD: int = 3
    RAGE_CLICK_WINDOW_S: float = 1.5

    def __init__(self) -> None:
        self.url_history: list[str] = []
        self.click_log: list[tuple[float, str]] = []  # (timestamp, selector)
        self.events: list[FrustrationEvent] = []

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
