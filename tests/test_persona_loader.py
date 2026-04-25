"""Tests for agents.persona_loader module — Phase C file-based personas."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.persona import DEFAULT_PERSONAS, Persona
from agents.persona_loader import (
    PersonaSchema,
    PersonasFile,
    load_personas_file,
    merge_personas,
)


class TestPersonaSchema:
    def test_valid_minimal(self) -> None:
        data = {
            "name": "test",
            "patience": 0.5,
            "tech_literacy": 0.6,
            "goal": "do stuff",
        }
        ps = PersonaSchema.model_validate(data)
        assert ps.name == "test"
        assert ps.early_exit_fraction == 0.4  # default
        assert ps.viewport == (1280, 720)  # default

    def test_valid_full(self) -> None:
        data = {
            "name": "custom",
            "patience": 0.3,
            "tech_literacy": 0.8,
            "goal": "test goal",
            "tags": ["fast", "mobile"],
            "early_exit_fraction": 0.25,
            "max_actions": 75,
            "viewport": [375, 667],
            "prefers_visible_text": True,
        }
        ps = PersonaSchema.model_validate(data)
        assert ps.viewport == (375, 667)
        assert ps.prefers_visible_text is True

    def test_to_persona(self) -> None:
        ps = PersonaSchema(
            name="x", patience=0.4, tech_literacy=0.5, goal="g", tags=["a"]
        )
        p = ps.to_persona()
        assert isinstance(p, Persona)
        assert p.name == "x"
        assert p.tags == ("a",)

    def test_invalid_patience(self) -> None:
        with pytest.raises(ValidationError):
            PersonaSchema(name="bad", patience=1.5, tech_literacy=0.5, goal="x")

    def test_invalid_viewport(self) -> None:
        with pytest.raises(ValidationError):
            PersonaSchema(
                name="bad", patience=0.5, tech_literacy=0.5, goal="x", viewport=[0, 720]
            )


class TestLoadPersonasFile:
    def test_load_valid_file(self, tmp_path: Path) -> None:
        data = {
            "personas": [
                {"name": "a", "patience": 0.5, "tech_literacy": 0.5, "goal": "A"},
                {"name": "b", "patience": 0.2, "tech_literacy": 0.9, "goal": "B"},
            ]
        }
        path = tmp_path / "test.json"
        path.write_text(json.dumps(data))

        result = load_personas_file(path)
        assert len(result) == 2
        assert "a" in result
        assert "b" in result
        assert result["a"].goal == "A"

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_personas_file(tmp_path / "nonexistent.json")

    def test_invalid_json_schema(self, tmp_path: Path) -> None:
        data = {"personas": [{"name": "bad"}]}  # missing required fields
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(data))

        with pytest.raises(ValidationError):
            load_personas_file(path)


class TestMergePersonas:
    def test_merge_adds_custom(self) -> None:
        custom = {
            "new_one": Persona(
                name="new_one", patience=0.5, tech_literacy=0.5, goal="test"
            )
        }
        merged = merge_personas(custom)
        assert "new_one" in merged
        assert "frustrated_exec" in merged  # built-in still present

    def test_custom_overrides_builtin(self) -> None:
        custom = {
            "frustrated_exec": Persona(
                name="frustrated_exec",
                patience=0.99,  # different from built-in
                tech_literacy=0.5,
                goal="custom",
            )
        }
        merged = merge_personas(custom, custom_overrides=True)
        assert merged["frustrated_exec"].patience == 0.99

    def test_builtin_takes_precedence_when_disabled(self) -> None:
        custom = {
            "frustrated_exec": Persona(
                name="frustrated_exec",
                patience=0.99,
                tech_literacy=0.5,
                goal="custom",
            )
        }
        merged = merge_personas(custom, custom_overrides=False)
        # Built-in should win
        assert merged["frustrated_exec"].patience == DEFAULT_PERSONAS["frustrated_exec"].patience

    def test_merge_with_custom_base(self) -> None:
        base = {"only_base": Persona(name="only_base", patience=0.5, tech_literacy=0.5, goal="x")}
        custom = {"only_custom": Persona(name="only_custom", patience=0.5, tech_literacy=0.5, goal="y")}
        merged = merge_personas(custom, base=base)
        assert "only_base" in merged
        assert "only_custom" in merged
        assert "frustrated_exec" not in merged  # not using DEFAULT_PERSONAS
