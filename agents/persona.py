"""Persona schema and built-in defaults for UX-friction agents.

Each persona controls how the synthetic browser agent behaves:
- ``patience`` (0-1): lower values cause shorter timeouts and earlier give-ups.
- ``tech_literacy`` (0-1): lower values add click hesitation and miss hidden menus.
- ``goal``: free-text description of what the persona is trying to accomplish.
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

    def __post_init__(self) -> None:
        if not 0.0 <= self.patience <= 1.0:
            raise ValueError(f"patience must be in [0, 1], got {self.patience}")
        if not 0.0 <= self.tech_literacy <= 1.0:
            raise ValueError(f"tech_literacy must be in [0, 1], got {self.tech_literacy}")

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
            "derived": {
                "page_load_timeout_ms": self.page_load_timeout_ms,
                "click_hesitation_ms": self.click_hesitation_ms,
                "skips_hidden_menus": self.skips_hidden_menus,
                "gives_up_early": self.gives_up_early,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Persona:
        return cls(
            name=data["name"],
            patience=data["patience"],
            tech_literacy=data["tech_literacy"],
            goal=data["goal"],
            tags=tuple(data.get("tags", [])),
        )


# ── Built-in persona defaults ──────────────────────────────────────────

FRUSTRATED_EXEC = Persona(
    name="frustrated_exec",
    patience=0.2,
    tech_literacy=0.8,
    goal="Complete a purchase flow quickly",
    tags=("executive", "impatient"),
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

DEFAULT_PERSONAS: dict[str, Persona] = {
    "frustrated_exec": FRUSTRATED_EXEC,
    "non_tech_senior": NON_TECH_SENIOR,
    "power_user": POWER_USER,
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
