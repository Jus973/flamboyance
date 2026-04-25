"""Persona schema and built-in defaults for UX-friction agents.

Each persona controls how the synthetic browser agent behaves:

Primary fields (required):
    patience (0-1): Lower values cause shorter page-load timeouts and trigger
        early give-up behavior (exits after ``early_exit_fraction`` of timeout).
    tech_literacy (0-1): Lower values add click hesitation and skip hidden menus
        (elements with ``aria-expanded="false"``).
    goal: Free-text description of what the persona is trying to accomplish.
        Used in the ``unmet_goal`` frustration event at session end.

Metadata:
    tags: Optional tuple of labels for filtering/grouping personas.

Behavioral overrides (Phase B, with backward-compatible defaults):
    early_exit_fraction (0-1, default 0.4): When ``gives_up_early`` is True,
        the agent exits after this fraction of the total timeout has elapsed.
    max_actions (int, default 50): Maximum click/navigation actions before stopping.
    viewport (width, height, default 1280x720): Browser viewport dimensions.
        Use smaller values like (375, 667) to simulate mobile devices.
    prefers_visible_text (bool, default False): When True, skip clickable elements
        that have no visible inner text (icon-only buttons, etc.).

Derived properties (read-only, computed from primary fields):
    page_load_timeout_ms: ``10_000 * (1.5 - patience)``
    click_hesitation_ms: ``500 * (2.0 - tech_literacy)``
    skips_hidden_menus: ``tech_literacy < 0.5``
    gives_up_early: ``patience < 0.4``

See also ``persona_loader.py`` for loading custom personas from JSON files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import EventThresholds


@dataclass(frozen=True)
class Persona:
    name: str
    patience: float
    tech_literacy: float
    goal: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    # Phase B fields with backward-compatible defaults:
    early_exit_fraction: float = 0.4
    max_actions: int = 50
    viewport: tuple[int, int] = (1280, 720)
    prefers_visible_text: bool = False
    # Threshold overrides (None = use global defaults)
    slow_load_threshold_ms: float | None = None
    long_dwell_threshold_s: float | None = None
    rage_click_threshold: int | None = None
    # Persona-specific focus for differentiated LLM behavior
    focus_areas: tuple[str, ...] = field(default_factory=tuple)
    frustration_triggers: tuple[str, ...] = field(default_factory=tuple)
    # Detection weights: friction_type -> weight multiplier (1.0 = normal, 2.0 = prioritized)
    detection_weights: tuple[tuple[str, float], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.patience <= 1.0:
            raise ValueError(f"patience must be in [0, 1], got {self.patience}")
        if not 0.0 <= self.tech_literacy <= 1.0:
            raise ValueError(f"tech_literacy must be in [0, 1], got {self.tech_literacy}")
        if not 0.0 < self.early_exit_fraction <= 1.0:
            raise ValueError(
                f"early_exit_fraction must be in (0, 1], got {self.early_exit_fraction}"
            )
        if self.max_actions < 1:
            raise ValueError(f"max_actions must be >= 1, got {self.max_actions}")
        if len(self.viewport) != 2 or self.viewport[0] < 1 or self.viewport[1] < 1:
            raise ValueError(
                f"viewport must be (width, height) with positive ints, got {self.viewport}"
            )

    def get_thresholds(self) -> EventThresholds:
        """Get event detection thresholds, applying any persona-specific overrides.

        Returns a new EventThresholds instance with persona overrides applied
        on top of the global defaults.
        """
        from .config import DEFAULT_THRESHOLDS, EventThresholds

        return EventThresholds(
            slow_load_threshold_ms=(
                self.slow_load_threshold_ms
                if self.slow_load_threshold_ms is not None
                else DEFAULT_THRESHOLDS.slow_load_threshold_ms
            ),
            long_dwell_threshold_s=(
                self.long_dwell_threshold_s
                if self.long_dwell_threshold_s is not None
                else DEFAULT_THRESHOLDS.long_dwell_threshold_s
            ),
            rage_click_threshold=(
                self.rage_click_threshold
                if self.rage_click_threshold is not None
                else DEFAULT_THRESHOLDS.rage_click_threshold
            ),
            rage_click_window_s=DEFAULT_THRESHOLDS.rage_click_window_s,
        )

    @property
    def page_load_timeout_ms(self) -> float:
        """Timeout = base * (1.5 - patience). Lower patience => shorter wait."""
        base_ms = 10_000
        return base_ms * (1.5 - self.patience)

    @property
    def click_hesitation_ms(self) -> float:
        """Hesitation = base * (2.0 - tech_literacy). Lower literacy => longer pause."""
        base_ms = 500
        return base_ms * (2.0 - self.tech_literacy)

    @property
    def skips_hidden_menus(self) -> bool:
        return self.tech_literacy < 0.5

    @property
    def gives_up_early(self) -> bool:
        return self.patience < 0.4

    def get_detection_weights(self) -> dict[str, float]:
        """Get detection weights as a dict for easy lookup."""
        return dict(self.detection_weights)

    def get_weighted_severity(self, event_kind: str, base_severity: float) -> float:
        """Apply persona-specific weight to an event's severity score.

        Args:
            event_kind: The type of friction event.
            base_severity: The base severity score (0-1).

        Returns:
            Weighted severity score.
        """
        weights = self.get_detection_weights()
        multiplier = weights.get(event_kind, 1.0)
        return min(base_severity * multiplier, 1.0)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "patience": self.patience,
            "tech_literacy": self.tech_literacy,
            "goal": self.goal,
            "tags": list(self.tags),
            "early_exit_fraction": self.early_exit_fraction,
            "max_actions": self.max_actions,
            "viewport": list(self.viewport),
            "prefers_visible_text": self.prefers_visible_text,
            "focus_areas": list(self.focus_areas),
            "frustration_triggers": list(self.frustration_triggers),
            "detection_weights": dict(self.detection_weights),
            "derived": {
                "page_load_timeout_ms": self.page_load_timeout_ms,
                "click_hesitation_ms": self.click_hesitation_ms,
                "skips_hidden_menus": self.skips_hidden_menus,
                "gives_up_early": self.gives_up_early,
            },
        }
        # Include threshold overrides if set
        if self.slow_load_threshold_ms is not None:
            result["slow_load_threshold_ms"] = self.slow_load_threshold_ms
        if self.long_dwell_threshold_s is not None:
            result["long_dwell_threshold_s"] = self.long_dwell_threshold_s
        if self.rage_click_threshold is not None:
            result["rage_click_threshold"] = self.rage_click_threshold
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Persona:
        viewport = data.get("viewport", [1280, 720])
        # Handle detection_weights as dict or list of tuples
        weights_data = data.get("detection_weights", {})
        if isinstance(weights_data, dict):
            detection_weights = tuple(weights_data.items())
        else:
            detection_weights = tuple(tuple(w) for w in weights_data)
        return cls(
            name=data["name"],
            patience=data["patience"],
            tech_literacy=data["tech_literacy"],
            goal=data["goal"],
            tags=tuple(data.get("tags", [])),
            early_exit_fraction=data.get("early_exit_fraction", 0.4),
            max_actions=data.get("max_actions", 50),
            viewport=(viewport[0], viewport[1]),
            prefers_visible_text=data.get("prefers_visible_text", False),
            slow_load_threshold_ms=data.get("slow_load_threshold_ms"),
            long_dwell_threshold_s=data.get("long_dwell_threshold_s"),
            rage_click_threshold=data.get("rage_click_threshold"),
            focus_areas=tuple(data.get("focus_areas", [])),
            frustration_triggers=tuple(data.get("frustration_triggers", [])),
            detection_weights=detection_weights,
        )

    def to_llm_prompt(self) -> str:
        """Generate a description of this persona for LLM system prompts."""
        patience_desc = (
            "very impatient and will give up quickly"
            if self.patience < 0.3
            else "somewhat impatient"
            if self.patience < 0.5
            else "moderately patient"
            if self.patience < 0.7
            else "very patient and thorough"
        )

        tech_desc = (
            "struggles with technology and needs obvious UI"
            if self.tech_literacy < 0.3
            else "has basic tech skills"
            if self.tech_literacy < 0.5
            else "comfortable with standard web interfaces"
            if self.tech_literacy < 0.7
            else "highly tech-savvy and can navigate complex UIs"
        )

        lines = [
            f"Persona: {self.name}",
            f"Goal: {self.goal}",
            f"Patience: {patience_desc} ({self.patience:.1f}/1.0)",
            f"Tech literacy: {tech_desc} ({self.tech_literacy:.1f}/1.0)",
        ]

        if self.focus_areas:
            lines.append(f"Focus areas: {', '.join(self.focus_areas)}")

        if self.frustration_triggers:
            lines.append(f"Gets frustrated by: {', '.join(self.frustration_triggers)}")

        if self.detection_weights:
            weights = self.get_detection_weights()
            prioritized = [k for k, v in weights.items() if v > 1.0]
            if prioritized:
                lines.append(f"Prioritizes detecting: {', '.join(prioritized)}")

        if self.prefers_visible_text:
            lines.append("Preference: Only uses clearly labeled, visible elements")

        if self.gives_up_early:
            lines.append(f"Behavior: May give up after {self.early_exit_fraction:.0%} of timeout")

        if self.skips_hidden_menus:
            lines.append("Behavior: Avoids collapsed menus and hidden UI")

        return "\n".join(lines)


# ── Built-in persona defaults ──────────────────────────────────────────

FRUSTRATED_EXEC = Persona(
    name="frustrated_exec",
    patience=0.2,
    tech_literacy=0.8,
    goal="Complete a purchase flow quickly",
    tags=("executive", "impatient"),
    early_exit_fraction=0.3,
    max_actions=15,
    focus_areas=("speed", "checkout", "forms"),
    frustration_triggers=(
        "slow loading",
        "unnecessary steps",
        "loading spinners",
        "required fields",
    ),
    detection_weights=(
        ("slow_interaction", 2.0),
        ("session_timeout", 1.5),
        ("slow_load", 1.5),
        ("modal_frustration", 1.5),
    ),
)

NON_TECH_SENIOR = Persona(
    name="non_tech_senior",
    patience=0.5,
    tech_literacy=0.2,
    goal="Find and read account settings",
    tags=("senior", "low-tech"),
    focus_areas=("labels", "text size", "navigation"),
    frustration_triggers=("small text", "confusing labels", "icon-only buttons", "jargon"),
    detection_weights=(
        ("confusing_navigation", 2.0),
        ("scroll_rage", 1.5),
        ("back_button_abuse", 1.5),
    ),
)

POWER_USER = Persona(
    name="power_user",
    patience=0.9,
    tech_literacy=0.9,
    goal="Navigate all features and check edge cases",
    tags=("expert", "thorough"),
    focus_areas=("keyboard shortcuts", "advanced features", "edge cases"),
    frustration_triggers=("missing features", "inconsistent behavior", "no keyboard navigation"),
    detection_weights=(
        ("copy_paste_failure", 1.5),
        ("js_error", 1.5),
    ),
)

CASUAL_BROWSER = Persona(
    name="casual_browser",
    patience=0.5,
    tech_literacy=0.5,
    goal="Browse around and see what's available",
    tags=("casual", "explorer"),
    max_actions=25,
    focus_areas=("content", "navigation", "visual appeal"),
    frustration_triggers=("popups", "aggressive CTAs", "cluttered layout"),
    detection_weights=(
        ("modal_frustration", 2.0),
        ("scroll_rage", 1.5),
        ("infinite_scroll_trap", 1.5),
    ),
)

ANXIOUS_NEWBIE = Persona(
    name="anxious_newbie",
    patience=0.3,
    tech_literacy=0.3,
    goal="Sign up for an account without getting confused",
    tags=("newbie", "anxious", "low-tech"),
    focus_areas=("signup", "forms", "error messages"),
    frustration_triggers=(
        "unclear errors",
        "too many fields",
        "no progress indicator",
        "unexpected behavior",
    ),
    detection_weights=(
        ("form_abandonment", 2.0),
        ("error_message_visible", 2.0),
        ("back_button_abuse", 1.5),
    ),
)

METHODICAL_TESTER = Persona(
    name="methodical_tester",
    patience=0.95,
    tech_literacy=0.6,
    goal="Systematically check every link and form",
    tags=("qa", "thorough", "slow"),
    max_actions=100,
    focus_areas=("links", "forms", "validation", "error states"),
    frustration_triggers=("broken links", "missing validation", "inconsistent states"),
    detection_weights=(
        ("error_message_visible", 1.5),
        ("infinite_scroll_trap", 1.5),
    ),
)

MOBILE_COMMUTER = Persona(
    name="mobile_commuter",
    patience=0.25,
    tech_literacy=0.85,
    goal="Quickly check order status while on the go",
    tags=("mobile", "rushed", "tech-savvy"),
    early_exit_fraction=0.3,
    max_actions=20,
    viewport=(375, 667),
    focus_areas=("mobile layout", "touch targets", "quick actions"),
    frustration_triggers=(
        "small tap targets",
        "horizontal scroll",
        "desktop-only features",
        "slow mobile load",
    ),
    detection_weights=(
        ("mobile_tap_target", 2.0),
        ("slow_interaction", 1.5),
        ("slow_load", 1.5),
    ),
)

ACCESSIBILITY_USER = Persona(
    name="accessibility_user",
    patience=0.7,
    tech_literacy=0.35,
    goal="Navigate using visible labels and clear affordances",
    tags=("a11y", "needs-clarity"),
    prefers_visible_text=True,
    focus_areas=("labels", "contrast", "focus indicators", "screen reader"),
    frustration_triggers=(
        "missing labels",
        "icon-only buttons",
        "poor contrast",
        "no focus visible",
    ),
    detection_weights=(
        ("accessibility_failure", 2.0),
        ("copy_paste_failure", 1.5),
    ),
)

# ── New personas for expanded friction coverage ────────────────────────

FORM_FILLER = Persona(
    name="form_filler",
    patience=0.4,
    tech_literacy=0.5,
    goal="Complete a multi-step form without errors",
    tags=("forms", "data-entry"),
    focus_areas=("form validation", "error messages", "field labels", "progress indicators"),
    frustration_triggers=(
        "unclear errors",
        "lost form data",
        "confusing field labels",
        "no progress indicator",
    ),
    detection_weights=(
        ("form_abandonment", 2.0),
        ("error_message_visible", 2.0),
        ("session_timeout", 1.5),
    ),
)

SEARCH_USER = Persona(
    name="search_user",
    patience=0.35,
    tech_literacy=0.6,
    goal="Find a specific product or information using search",
    tags=("search", "goal-oriented"),
    focus_areas=("search functionality", "filters", "results relevance"),
    frustration_triggers=(
        "zero results",
        "irrelevant results",
        "no search feedback",
        "broken filters",
    ),
    detection_weights=(
        ("search_frustration", 2.0),
        ("confusing_navigation", 1.5),
        ("infinite_scroll_trap", 1.5),
    ),
)

CHECKOUT_USER = Persona(
    name="checkout_user",
    patience=0.3,
    tech_literacy=0.7,
    goal="Complete a purchase from cart to confirmation",
    tags=("checkout", "purchase", "goal-oriented"),
    focus_areas=("cart", "checkout flow", "payment forms", "order confirmation"),
    frustration_triggers=("cart issues", "payment errors", "session timeout", "unclear totals"),
    detection_weights=(
        ("cart_abandonment", 2.0),
        ("form_abandonment", 1.5),
        ("slow_interaction", 1.5),
        ("session_timeout", 2.0),
    ),
)

DEFAULT_PERSONAS: dict[str, Persona] = {
    "frustrated_exec": FRUSTRATED_EXEC,
    "non_tech_senior": NON_TECH_SENIOR,
    "power_user": POWER_USER,
    "casual_browser": CASUAL_BROWSER,
    "anxious_newbie": ANXIOUS_NEWBIE,
    "methodical_tester": METHODICAL_TESTER,
    "mobile_commuter": MOBILE_COMMUTER,
    "accessibility_user": ACCESSIBILITY_USER,
    "form_filler": FORM_FILLER,
    "search_user": SEARCH_USER,
    "checkout_user": CHECKOUT_USER,
}


def resolve_personas(names: list[str] | None = None) -> list[Persona]:
    """Return a list of Persona instances, falling back to all defaults."""
    if not names:
        return list(DEFAULT_PERSONAS.values())
    result: list[Persona] = []
    for n in names:
        persona = DEFAULT_PERSONAS.get(n)
        if persona is None:
            raise ValueError(f"Unknown persona {n!r}. Available: {sorted(DEFAULT_PERSONAS)}")
        result.append(persona)
    return result
