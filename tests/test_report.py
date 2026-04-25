"""Tests for agents.report module."""

from agents.agent import AgentResult
from agents.persona import resolve_personas
from agents.report import generate_report
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
