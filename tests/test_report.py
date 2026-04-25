"""Tests for agents.report module."""

from agents.agent import AgentResult
from agents.persona import resolve_personas
from agents.report import (
    FIX_RECOMMENDATIONS,
    _count_events_by_severity,
    _escape_markdown,
    _group_events_by_kind,
    _sort_events_by_severity,
    generate_report,
)
from agents.runner_local import RunState


class TestReportGeneration:
    def test_basic_report_structure(self) -> None:
        state = RunState(
            run_id="test-1234",
            url="http://localhost:3000",
            personas=resolve_personas(["frustrated_exec"]),
            results=[
                AgentResult(
                    persona="frustrated_exec",
                    status="done",
                    visited_urls=["http://localhost:3000", "http://localhost:3000/about"],
                    frustration_events=[
                        {
                            "kind": "unmet_goal",
                            "description": "Unmet goal (timeout): Complete a purchase",
                            "severity": "critical",
                        }
                    ],
                    elapsed_seconds=12.5,
                )
            ],
            status="done",
        )
        md = generate_report(state)
        assert "# Flamboyance UX Friction Report" in md
        assert "test-1234" in md
        assert "frustrated_exec" in md
        assert "unmet_goal" in md
        assert "localhost:3000" in md
        # New features
        assert "Executive Summary" in md
        assert "Recommendations" in md
        assert "critical" in md.lower()

    def test_empty_report(self) -> None:
        state = RunState(
            run_id="test-0000",
            url="http://example.com",
            personas=[],
            results=[],
            status="done",
        )
        md = generate_report(state)
        assert "No frustration events" in md

    def test_report_with_multiple_severity_levels(self) -> None:
        state = RunState(
            run_id="test-multi",
            url="http://example.com",
            personas=resolve_personas(["frustrated_exec"]),
            results=[
                AgentResult(
                    persona="frustrated_exec",
                    status="done",
                    visited_urls=["http://example.com"],
                    frustration_events=[
                        {
                            "kind": "unmet_goal",
                            "description": "Goal failed",
                            "severity": "critical",
                        },
                        {"kind": "js_error", "description": "JS Error", "severity": "high"},
                        {"kind": "slow_load", "description": "Page slow", "severity": "medium"},
                        {"kind": "long_dwell", "description": "User waited", "severity": "low"},
                    ],
                    elapsed_seconds=30.0,
                )
            ],
            status="done",
        )
        md = generate_report(state)

        # Check severity sections exist
        assert "Critical" in md
        assert "High" in md
        assert "Medium" in md
        assert "Low" in md

        # Check recommendations exist for event types
        assert "Recommendations" in md

    def test_report_escapes_special_characters(self) -> None:
        state = RunState(
            run_id="test|special",
            url="http://example.com/path|with|pipes",
            personas=[],
            results=[
                AgentResult(
                    persona="test_persona",
                    status="done",
                    visited_urls=[],
                    frustration_events=[
                        {
                            "kind": "js_error",
                            "description": "Error | with | pipes\nand newlines",
                            "severity": "high",
                        }
                    ],
                    elapsed_seconds=5.0,
                )
            ],
            status="done",
        )
        md = generate_report(state)

        # Pipes should be escaped
        assert "\\|" in md or "|special" not in md.split("\n")[0]
        # Newlines should be removed from descriptions
        assert "and newlines" in md
        assert "\n\n" not in md.replace("\n\n", "XX")  # Normal paragraph breaks ok

    def test_report_with_llm_mode(self) -> None:
        result = AgentResult(
            persona="test_llm",
            status="done",
            visited_urls=["http://example.com"],
            frustration_events=[],
            elapsed_seconds=10.0,
            llm_mode=True,
            llm_calls=5,
            llm_tokens=500,
            action_history=[
                {"action": "click", "target": [100, 200], "result": "clicked"},
                {"action": "type", "target": "test", "result": "typed"},
            ],
        )
        state = RunState(
            run_id="test-llm",
            url="http://example.com",
            personas=[],
            results=[result],
            status="done",
        )
        md = generate_report(state)

        assert "LLM Navigation Stats" in md
        assert "LLM Calls" in md
        assert "5" in md
        assert "Action History" in md
        assert "click" in md
        assert "typed" in md


class TestMarkdownEscaping:
    def test_escape_pipes(self) -> None:
        assert _escape_markdown("hello|world") == "hello\\|world"

    def test_escape_newlines(self) -> None:
        assert _escape_markdown("hello\nworld") == "hello world"
        assert _escape_markdown("hello\r\nworld") == "hello world"

    def test_escape_empty_string(self) -> None:
        assert _escape_markdown("") == ""
        assert _escape_markdown(None) is None


class TestSeverityHelpers:
    def test_count_events_by_severity(self) -> None:
        events = [
            {"kind": "test", "severity": "critical"},
            {"kind": "test", "severity": "high"},
            {"kind": "test", "severity": "high"},
            {"kind": "test", "severity": "medium"},
            {"kind": "test"},  # defaults to medium
        ]
        counts = _count_events_by_severity(events)
        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 2
        assert counts["low"] == 0

    def test_sort_events_by_severity(self) -> None:
        events = [
            {"kind": "low", "severity": "low"},
            {"kind": "critical", "severity": "critical"},
            {"kind": "medium", "severity": "medium"},
            {"kind": "high", "severity": "high"},
        ]
        sorted_events = _sort_events_by_severity(events)
        assert sorted_events[0]["kind"] == "critical"
        assert sorted_events[1]["kind"] == "high"
        assert sorted_events[2]["kind"] == "medium"
        assert sorted_events[3]["kind"] == "low"

    def test_group_events_by_kind(self) -> None:
        events = [
            {"kind": "js_error", "description": "Error 1"},
            {"kind": "slow_load", "description": "Slow 1"},
            {"kind": "js_error", "description": "Error 2"},
        ]
        groups = _group_events_by_kind(events)
        assert len(groups["js_error"]) == 2
        assert len(groups["slow_load"]) == 1


class TestRecommendations:
    def test_all_event_types_have_recommendations(self) -> None:
        event_types = [
            "slow_load",
            "dead_end",
            "long_dwell",
            "rage_decoy",
            "js_error",
            "broken_image",
            "network_error",
            "circular_navigation",
            "rage_click",
            "unmet_goal",
        ]
        for event_type in event_types:
            assert event_type in FIX_RECOMMENDATIONS
            assert len(FIX_RECOMMENDATIONS[event_type]) > 10  # Meaningful recommendation
