"""Load persona definitions from JSON files with Pydantic validation.

This enables non-developers to define custom personas without editing Python.

Usage::

    from agents.persona_loader import load_personas_file, merge_personas

    custom = load_personas_file("my_personas.json")
    all_personas = merge_personas(custom)  # merges with DEFAULT_PERSONAS
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .persona import DEFAULT_PERSONAS, Persona

log = logging.getLogger(__name__)


class PersonaSchema(BaseModel):
    """Pydantic model mirroring the Persona dataclass for validation."""

    name: str
    patience: float = Field(ge=0.0, le=1.0)
    tech_literacy: float = Field(ge=0.0, le=1.0)
    goal: str
    tags: list[str] = Field(default_factory=list)
    early_exit_fraction: float = Field(default=0.4, gt=0.0, le=1.0)
    max_actions: int = Field(default=50, ge=1)
    viewport: tuple[int, int] = Field(default=(1280, 720))
    prefers_visible_text: bool = False

    @field_validator("viewport", mode="before")
    @classmethod
    def coerce_viewport(cls, v: Any) -> tuple[int, int]:
        if isinstance(v, (list, tuple)) and len(v) == 2:
            w, h = v
            if w < 1 or h < 1:
                raise ValueError("viewport dimensions must be >= 1")
            return (int(w), int(h))
        raise ValueError("viewport must be [width, height]")

    def to_persona(self) -> Persona:
        return Persona(
            name=self.name,
            patience=self.patience,
            tech_literacy=self.tech_literacy,
            goal=self.goal,
            tags=tuple(self.tags),
            early_exit_fraction=self.early_exit_fraction,
            max_actions=self.max_actions,
            viewport=self.viewport,
            prefers_visible_text=self.prefers_visible_text,
        )


class PersonasFile(BaseModel):
    """Root schema for a personas JSON file."""

    personas: list[PersonaSchema]


def load_personas_file(path: str | Path) -> dict[str, Persona]:
    """Load personas from a JSON file.

    File format::

        {
          "personas": [
            {"name": "my_persona", "patience": 0.5, "tech_literacy": 0.6, "goal": "..."},
            ...
          ]
        }

    Returns:
        Dict mapping persona name -> Persona instance.

    Raises:
        FileNotFoundError: if path does not exist.
        pydantic.ValidationError: if JSON fails schema validation.
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    validated = PersonasFile.model_validate(data)
    result: dict[str, Persona] = {}
    for ps in validated.personas:
        persona = ps.to_persona()
        if persona.name in result:
            log.warning("Duplicate persona name %r in %s; last definition wins", persona.name, path)
        result[persona.name] = persona
    log.info("Loaded %d persona(s) from %s", len(result), path)
    return result


def merge_personas(
    custom: dict[str, Persona],
    *,
    base: dict[str, Persona] | None = None,
    custom_overrides: bool = True,
) -> dict[str, Persona]:
    """Merge custom personas with built-in defaults.

    Args:
        custom: Personas loaded from file.
        base: Base personas to merge with (default: DEFAULT_PERSONAS).
        custom_overrides: If True, custom personas override built-ins with same name.
                          If False, built-ins take precedence.

    Returns:
        Merged dict of name -> Persona.
    """
    if base is None:
        base = dict(DEFAULT_PERSONAS)
    else:
        base = dict(base)

    if custom_overrides:
        base.update(custom)
    else:
        for name, persona in custom.items():
            if name not in base:
                base[name] = persona
    return base
