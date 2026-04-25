"""Tests for agents.persona module."""

import pytest

from agents.persona import (
    DEFAULT_PERSONAS,
    FRUSTRATED_EXEC,
    NON_TECH_SENIOR,
    POWER_USER,
    Persona,
    resolve_personas,
)


class TestPersonaSchema:
    def test_defaults_exist(self) -> None:
        assert len(DEFAULT_PERSONAS) == 3
        assert "frustrated_exec" in DEFAULT_PERSONAS
        assert "non_tech_senior" in DEFAULT_PERSONAS
        assert "power_user" in DEFAULT_PERSONAS

    def test_frustrated_exec_values(self) -> None:
        p = FRUSTRATED_EXEC
        assert p.patience == 0.2
        assert p.tech_literacy == 0.8
        assert p.gives_up_early is True
        assert p.skips_hidden_menus is False

    def test_non_tech_senior_values(self) -> None:
        p = NON_TECH_SENIOR
        assert p.patience == 0.5
        assert p.tech_literacy == 0.2
        assert p.skips_hidden_menus is True
        assert p.gives_up_early is False

    def test_power_user_values(self) -> None:
        p = POWER_USER
        assert p.patience == 0.9
        assert p.tech_literacy == 0.9
        assert p.gives_up_early is False
        assert p.skips_hidden_menus is False

    def test_page_load_timeout(self) -> None:
        p = Persona(name="t", patience=0.2, tech_literacy=0.5, goal="test")
        assert p.page_load_timeout_ms == 10_000 * (1.5 - 0.2)

    def test_click_hesitation(self) -> None:
        p = Persona(name="t", patience=0.5, tech_literacy=0.2, goal="test")
        assert p.click_hesitation_ms == 500 * (2.0 - 0.2)

    def test_validation_patience_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="patience"):
            Persona(name="bad", patience=1.5, tech_literacy=0.5, goal="x")

    def test_validation_tech_literacy_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="tech_literacy"):
            Persona(name="bad", patience=0.5, tech_literacy=-0.1, goal="x")

    def test_round_trip_dict(self) -> None:
        p = FRUSTRATED_EXEC
        d = p.to_dict()
        p2 = Persona.from_dict(d)
        assert p.name == p2.name
        assert p.patience == p2.patience
        assert p.tech_literacy == p2.tech_literacy
        assert p.goal == p2.goal


class TestResolvePersonas:
    def test_resolve_all(self) -> None:
        result = resolve_personas(None)
        assert len(result) == 3

    def test_resolve_specific(self) -> None:
        result = resolve_personas(["power_user"])
        assert len(result) == 1
        assert result[0].name == "power_user"

    def test_resolve_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            resolve_personas(["nonexistent"])
