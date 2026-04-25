"""Tests for the UI mutation layer."""

from agents.mutations import (
    COMMON_SCENARIOS,
    MutationScenario,
    _build_mutation_script,
    get_scenario,
)


class TestMutationScenario:
    """Tests for MutationScenario dataclass."""

    def test_create_empty_scenario(self):
        """Empty scenario should have no mutations."""
        scenario = MutationScenario(name="empty")
        assert scenario.name == "empty"
        assert scenario.hide == []
        assert scenario.disable == []
        assert scenario.remove == []
        assert scenario.delay_clicks == {}
        assert scenario.is_empty()

    def test_create_scenario_with_hide(self):
        """Scenario with hide selectors."""
        scenario = MutationScenario(
            name="test_hide",
            hide=["#checkout-btn", ".submit-button"],
        )
        assert scenario.name == "test_hide"
        assert scenario.hide == ["#checkout-btn", ".submit-button"]
        assert not scenario.is_empty()

    def test_create_scenario_with_all_mutations(self):
        """Scenario with all mutation types."""
        scenario = MutationScenario(
            name="full_test",
            hide=["#hidden"],
            disable=[".disabled"],
            remove=[".removed"],
            delay_clicks={"button": 1000},
        )
        assert scenario.name == "full_test"
        assert scenario.hide == ["#hidden"]
        assert scenario.disable == [".disabled"]
        assert scenario.remove == [".removed"]
        assert scenario.delay_clicks == {"button": 1000}
        assert not scenario.is_empty()

    def test_from_dict(self):
        """Create scenario from dictionary."""
        data = {
            "name": "from_dict_test",
            "hide": ["#btn"],
            "disable": [".form"],
            "remove": ["nav"],
            "delay_clicks": {"input": 500},
        }
        scenario = MutationScenario.from_dict(data)
        assert scenario.name == "from_dict_test"
        assert scenario.hide == ["#btn"]
        assert scenario.disable == [".form"]
        assert scenario.remove == ["nav"]
        assert scenario.delay_clicks == {"input": 500}

    def test_from_dict_minimal(self):
        """Create scenario from minimal dictionary."""
        data = {"name": "minimal"}
        scenario = MutationScenario.from_dict(data)
        assert scenario.name == "minimal"
        assert scenario.is_empty()

    def test_from_dict_missing_name(self):
        """Missing name defaults to 'unnamed'."""
        data = {"hide": ["#btn"]}
        scenario = MutationScenario.from_dict(data)
        assert scenario.name == "unnamed"
        assert scenario.hide == ["#btn"]

    def test_to_dict(self):
        """Convert scenario to dictionary."""
        scenario = MutationScenario(
            name="to_dict_test",
            hide=["#btn"],
            disable=[".form"],
        )
        data = scenario.to_dict()
        assert data == {
            "name": "to_dict_test",
            "hide": ["#btn"],
            "disable": [".form"],
            "remove": [],
            "delay_clicks": {},
        }

    def test_roundtrip(self):
        """Roundtrip through dict and back."""
        original = MutationScenario(
            name="roundtrip",
            hide=["#a", "#b"],
            disable=[".c"],
            remove=[".d"],
            delay_clicks={"e": 100, "f": 200},
        )
        data = original.to_dict()
        restored = MutationScenario.from_dict(data)
        assert restored.name == original.name
        assert restored.hide == original.hide
        assert restored.disable == original.disable
        assert restored.remove == original.remove
        assert restored.delay_clicks == original.delay_clicks


class TestBuildMutationScript:
    """Tests for JavaScript mutation script generation."""

    def test_empty_scenario_script(self):
        """Empty scenario produces minimal script."""
        scenario = MutationScenario(name="empty")
        script = _build_mutation_script(scenario)
        assert "(function() {" in script
        assert "})();" in script

    def test_hide_script(self):
        """Hide mutation generates visibility:hidden."""
        scenario = MutationScenario(name="test", hide=["#btn"])
        script = _build_mutation_script(scenario)
        assert "visibility" in script
        assert "hidden" in script
        assert "#btn" in script
        assert "data-flamboyance-mutation" in script

    def test_disable_script(self):
        """Disable mutation generates pointer-events:none."""
        scenario = MutationScenario(name="test", disable=[".form"])
        script = _build_mutation_script(scenario)
        assert "pointerEvents" in script
        assert "none" in script
        assert ".form" in script
        assert "opacity" in script

    def test_remove_script(self):
        """Remove mutation generates el.remove()."""
        scenario = MutationScenario(name="test", remove=["nav"])
        script = _build_mutation_script(scenario)
        assert ".remove()" in script
        assert "nav" in script

    def test_delay_clicks_script(self):
        """Delay clicks mutation generates event listener."""
        scenario = MutationScenario(name="test", delay_clicks={"button": 1500})
        script = _build_mutation_script(scenario)
        assert "addEventListener" in script
        assert "click" in script
        assert "setTimeout" in script
        assert "1500" in script
        assert "_flamboyanceDelayed" in script

    def test_selector_escaping(self):
        """Selectors with quotes are escaped."""
        scenario = MutationScenario(name="test", hide=["[data-test='value']"])
        script = _build_mutation_script(scenario)
        assert "[data-test=\\'value\\']" in script


class TestCommonScenarios:
    """Tests for pre-defined common scenarios."""

    def test_broken_checkout_exists(self):
        """broken_checkout scenario is defined."""
        scenario = COMMON_SCENARIOS.get("broken_checkout")
        assert scenario is not None
        assert scenario.name == "broken_checkout"
        assert len(scenario.hide) > 0

    def test_no_nav_exists(self):
        """no_nav scenario is defined."""
        scenario = COMMON_SCENARIOS.get("no_nav")
        assert scenario is not None
        assert scenario.name == "no_nav"
        assert len(scenario.remove) > 0

    def test_slow_submit_exists(self):
        """slow_submit scenario is defined."""
        scenario = COMMON_SCENARIOS.get("slow_submit")
        assert scenario is not None
        assert scenario.name == "slow_submit"
        assert len(scenario.delay_clicks) > 0

    def test_disabled_forms_exists(self):
        """disabled_forms scenario is defined."""
        scenario = COMMON_SCENARIOS.get("disabled_forms")
        assert scenario is not None
        assert scenario.name == "disabled_forms"
        assert len(scenario.disable) > 0

    def test_hidden_cta_exists(self):
        """hidden_cta scenario is defined."""
        scenario = COMMON_SCENARIOS.get("hidden_cta")
        assert scenario is not None
        assert scenario.name == "hidden_cta"
        assert len(scenario.hide) > 0

    def test_get_scenario_found(self):
        """get_scenario returns scenario when found."""
        scenario = get_scenario("broken_checkout")
        assert scenario is not None
        assert scenario.name == "broken_checkout"

    def test_get_scenario_not_found(self):
        """get_scenario returns None when not found."""
        scenario = get_scenario("nonexistent")
        assert scenario is None


class TestMutationTestResult:
    """Tests for MutationTestResult dataclass."""

    def test_import_mutation_test_result(self):
        """MutationTestResult can be imported."""
        from agents.runner_mutation import MutationTestResult

        result = MutationTestResult(
            scenario="test",
            url="http://example.com",
        )
        assert result.scenario == "test"
        assert result.url == "http://example.com"
        assert result.status == "done"
        assert result.persona_results == []

    def test_to_dict(self):
        """MutationTestResult.to_dict() works."""
        from agents.runner_mutation import MutationTestResult

        result = MutationTestResult(
            scenario="test",
            url="http://example.com",
            elapsed_seconds=5.0,
        )
        data = result.to_dict()
        assert data["scenario"] == "test"
        assert data["url"] == "http://example.com"
        assert data["elapsed_seconds"] == 5.0
        assert data["persona_results"] == []

    def test_summary_empty(self):
        """Summary with no results."""
        from agents.runner_mutation import MutationTestResult

        result = MutationTestResult(
            scenario="test",
            url="http://example.com",
        )
        summary = result.summary()
        assert summary["scenario"] == "test"
        assert summary["total_personas"] == 0
        assert summary["failed_count"] == 0
        assert summary["succeeded_count"] == 0
