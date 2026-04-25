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
from typing import Any


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

    def __post_init__(self) -> None:
        if not 0.0 <= self.patience <= 1.0:
            raise ValueError(f"patience must be in [0, 1], got {self.patience}")
        if not 0.0 <= self.tech_literacy <= 1.0:
            raise ValueError(f"tech_literacy must be in [0, 1], got {self.tech_literacy}")
        if not 0.0 < self.early_exit_fraction <= 1.0:
            raise ValueError(f"early_exit_fraction must be in (0, 1], got {self.early_exit_fraction}")
        if self.max_actions < 1:
            raise ValueError(f"max_actions must be >= 1, got {self.max_actions}")
        if len(self.viewport) != 2 or self.viewport[0] < 1 or self.viewport[1] < 1:
            raise ValueError(f"viewport must be (width, height) with positive ints, got {self.viewport}")

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "patience": self.patience,
            "tech_literacy": self.tech_literacy,
            "goal": self.goal,
            "tags": list(self.tags),
            "early_exit_fraction": self.early_exit_fraction,
            "max_actions": self.max_actions,
            "viewport": list(self.viewport),
            "prefers_visible_text": self.prefers_visible_text,
            "derived": {
                "page_load_timeout_ms": self.page_load_timeout_ms,
                "click_hesitation_ms": self.click_hesitation_ms,
                "skips_hidden_menus": self.skips_hidden_menus,
                "gives_up_early": self.gives_up_early,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Persona:
        viewport = data.get("viewport", [1280, 720])
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
        )


# ── Built-in persona defaults ──────────────────────────────────────────

FRUSTRATED_EXEC = Persona(
    name="frustrated_exec",
    patience=0.2,
    tech_literacy=0.8,
    goal="Complete a purchase flow quickly",
    tags=("executive", "impatient"),
    early_exit_fraction=0.3,
)

NON_TECH_SENIOR = Persona(
    name="non_tech_senior",
    patience=0.5,
    tech_literacy=0.2,
    goal="Find and read account settings",
    tags=("senior", "low-tech"),
)

POWER_USER = Persona(
    name="power_user",
    patience=0.9,
    tech_literacy=0.9,
    goal="Navigate all features and check edge cases",
    tags=("expert", "thorough"),
)

CASUAL_BROWSER = Persona(
    name="casual_browser",
    patience=0.5,
    tech_literacy=0.5,
    goal="Browse around and see what's available",
    tags=("casual", "explorer"),
)

ANXIOUS_NEWBIE = Persona(
    name="anxious_newbie",
    patience=0.3,
    tech_literacy=0.3,
    goal="Sign up for an account without getting confused",
    tags=("newbie", "anxious", "low-tech"),
)

METHODICAL_TESTER = Persona(
    name="methodical_tester",
    patience=0.95,
    tech_literacy=0.6,
    goal="Systematically check every link and form",
    tags=("qa", "thorough", "slow"),
    max_actions=100,
)

MOBILE_COMMUTER = Persona(
    name="mobile_commuter",
    patience=0.25,
    tech_literacy=0.85,
    goal="Quickly check order status while on the go",
    tags=("mobile", "rushed", "tech-savvy"),
    early_exit_fraction=0.3,
    viewport=(375, 667),
)

ACCESSIBILITY_USER = Persona(
    name="accessibility_user",
    patience=0.7,
    tech_literacy=0.35,
    goal="Navigate using visible labels and clear affordances",
    tags=("a11y", "needs-clarity"),
    prefers_visible_text=True,
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
}


def resolve_personas(names: list[str] | None = None) -> list[Persona]:
    """Return a list of Persona instances, falling back to all defaults."""
    if not names:
        return list(DEFAULT_PERSONAS.values())
    result: list[Persona] = []
    for n in names:
        persona = DEFAULT_PERSONAS.get(n)
        if persona is None:
            raise ValueError(
                f"Unknown persona {n!r}. Available: {sorted(DEFAULT_PERSONAS)}"
            )
        result.append(persona)
    return result
