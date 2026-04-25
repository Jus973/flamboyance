"""Tests for agents.persona module."""

import pytest

from agents.persona import (
    ACCESSIBILITY_USER,
    ANXIOUS_NEWBIE,
    CASUAL_BROWSER,
    DEFAULT_PERSONAS,
    FRUSTRATED_EXEC,
    METHODICAL_TESTER,
    MOBILE_COMMUTER,
    NON_TECH_SENIOR,
    POWER_USER,
    Persona,
    resolve_personas,
)


class TestPersonaSchema:
    def test_defaults_exist(self) -> None:
        # Original three personas must remain
        assert "frustrated_exec" in DEFAULT_PERSONAS
        assert "non_tech_senior" in DEFAULT_PERSONAS
        assert "power_user" in DEFAULT_PERSONAS
        # New personas added in Phase A
        assert "casual_browser" in DEFAULT_PERSONAS
        assert "anxious_newbie" in DEFAULT_PERSONAS
        assert "methodical_tester" in DEFAULT_PERSONAS
        assert "mobile_commuter" in DEFAULT_PERSONAS
        assert "accessibility_user" in DEFAULT_PERSONAS
        # Total count (allow for future additions)
        assert len(DEFAULT_PERSONAS) >= 8

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


class TestPhaseBFields:
    """Phase B: new behavioral fields added to Persona."""

    def test_default_values(self) -> None:
        p = Persona(name="t", patience=0.5, tech_literacy=0.5, goal="test")
        assert p.early_exit_fraction == 0.4
        assert p.max_actions == 50
        assert p.viewport == (1280, 720)
        assert p.prefers_visible_text is False

    def test_custom_values(self) -> None:
        p = Persona(
            name="custom",
            patience=0.5,
            tech_literacy=0.5,
            goal="test",
            early_exit_fraction=0.25,
            max_actions=100,
            viewport=(375, 667),
            prefers_visible_text=True,
        )
        assert p.early_exit_fraction == 0.25
        assert p.max_actions == 100
        assert p.viewport == (375, 667)
        assert p.prefers_visible_text is True

    def test_frustrated_exec_early_exit(self) -> None:
        assert FRUSTRATED_EXEC.early_exit_fraction == 0.3

    def test_methodical_tester_max_actions(self) -> None:
        assert METHODICAL_TESTER.max_actions == 100

    def test_mobile_commuter_viewport(self) -> None:
        assert MOBILE_COMMUTER.viewport == (375, 667)
        assert MOBILE_COMMUTER.early_exit_fraction == 0.3

    def test_accessibility_user_prefers_visible_text(self) -> None:
        assert ACCESSIBILITY_USER.prefers_visible_text is True

    def test_validation_early_exit_fraction_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="early_exit_fraction"):
            Persona(name="bad", patience=0.5, tech_literacy=0.5, goal="x", early_exit_fraction=0.0)
        with pytest.raises(ValueError, match="early_exit_fraction"):
            Persona(name="bad", patience=0.5, tech_literacy=0.5, goal="x", early_exit_fraction=1.5)

    def test_validation_max_actions_invalid(self) -> None:
        with pytest.raises(ValueError, match="max_actions"):
            Persona(name="bad", patience=0.5, tech_literacy=0.5, goal="x", max_actions=0)

    def test_validation_viewport_invalid(self) -> None:
        with pytest.raises(ValueError, match="viewport"):
            Persona(name="bad", patience=0.5, tech_literacy=0.5, goal="x", viewport=(0, 720))

    def test_round_trip_dict_with_phase_b_fields(self) -> None:
        p = MOBILE_COMMUTER
        d = p.to_dict()
        p2 = Persona.from_dict(d)
        assert p.early_exit_fraction == p2.early_exit_fraction
        assert p.max_actions == p2.max_actions
        assert p.viewport == p2.viewport
        assert p.prefers_visible_text == p2.prefers_visible_text

    def test_from_dict_with_missing_phase_b_fields(self) -> None:
        # Older dict formats should still work with defaults
        d = {
            "name": "legacy",
            "patience": 0.5,
            "tech_literacy": 0.5,
            "goal": "test",
        }
        p = Persona.from_dict(d)
        assert p.early_exit_fraction == 0.4
        assert p.max_actions == 50
        assert p.viewport == (1280, 720)
        assert p.prefers_visible_text is False


class TestNewPersonasBehavior:
    """Verify new personas have expected derived properties."""

    def test_casual_browser_mid_range(self) -> None:
        p = CASUAL_BROWSER
        assert p.patience == 0.5
        assert p.tech_literacy == 0.5
        assert p.gives_up_early is False
        assert p.skips_hidden_menus is False

    def test_anxious_newbie_struggles(self) -> None:
        p = ANXIOUS_NEWBIE
        assert p.patience == 0.3
        assert p.tech_literacy == 0.3
        assert p.gives_up_early is True
        assert p.skips_hidden_menus is True

    def test_methodical_tester_patient_mid_literacy(self) -> None:
        p = METHODICAL_TESTER
        assert p.patience == 0.95
        assert p.tech_literacy == 0.6
        assert p.gives_up_early is False
        assert p.skips_hidden_menus is False

    def test_mobile_commuter_rushed_but_capable(self) -> None:
        p = MOBILE_COMMUTER
        assert p.patience == 0.25
        assert p.tech_literacy == 0.85
        assert p.gives_up_early is True
        assert p.skips_hidden_menus is False

    def test_accessibility_user_patient_low_literacy(self) -> None:
        p = ACCESSIBILITY_USER
        assert p.patience == 0.7
        assert p.tech_literacy == 0.35
        assert p.gives_up_early is False
        assert p.skips_hidden_menus is True


class TestResolvePersonas:
    def test_resolve_all(self) -> None:
        result = resolve_personas(None)
        assert len(result) == len(DEFAULT_PERSONAS)

    def test_resolve_specific(self) -> None:
        result = resolve_personas(["power_user"])
        assert len(result) == 1
        assert result[0].name == "power_user"

    def test_resolve_multiple(self) -> None:
        result = resolve_personas(["anxious_newbie", "mobile_commuter"])
        assert len(result) == 2
        names = {r.name for r in result}
        assert names == {"anxious_newbie", "mobile_commuter"}

    def test_resolve_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown persona"):
            resolve_personas(["nonexistent"])
