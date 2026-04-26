"""Tests for MCP server tools and error handling."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flamboyance_mcp.server import (
    create_mcp,
    get_live_feed,
    get_report,
    get_status,
    mcp,
    run_flamboyance,
    run_mutation_test_tool,
    run_simulation,
    stop_simulation,
)


class TestMCPServerSetup:
    """Test MCP server initialization and tool registration."""

    def test_create_mcp_default_config(self):
        """MCP server creates with correct name."""
        server = create_mcp()
        assert server.name == "Flamboyance UX-Friction"

    def test_create_mcp_has_instructions(self):
        """MCP server has instructions for Cascade."""
        server = create_mcp()
        assert "browser agents" in server.instructions.lower()

    def test_all_tools_registered(self):
        """All 7 expected tools are registered."""
        tool_names = {tool.name for tool in mcp._tool_manager._tools.values()}
        expected_tools = {
            "run_simulation",
            "run_flamboyance",
            "get_status",
            "get_live_feed",
            "get_report",
            "stop_simulation",
            "run_mutation_test_tool",
        }
        assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


class TestRunFlamboyance:
    """Test the primary run_flamboyance tool."""

    @pytest.mark.asyncio
    async def test_run_flamboyance_invalid_url(self):
        """Invalid URL returns error dict."""
        result = await run_flamboyance(url="not-a-url")
        assert "error" in result
        assert "url" in result["error"].lower() or "invalid" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_flamboyance_invalid_timeout(self):
        """Invalid timeout returns error dict."""
        result = await run_flamboyance(url="http://localhost:3000", timeout=-5)
        assert "error" in result
        assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_flamboyance_success_returns_run_id(self):
        """Valid request returns run_id and config."""
        with patch("flamboyance_mcp.server.run_local", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = MagicMock()
            result = await run_flamboyance(url="http://localhost:3000")

        assert "run_id" in result
        assert result["status"] == "running"
        assert "config" in result
        assert result["config"]["llm_mode"] is True  # default

    @pytest.mark.asyncio
    async def test_run_flamboyance_heuristic_mode(self):
        """Heuristic mode config is reflected in response."""
        with patch("flamboyance_mcp.server.run_local", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = MagicMock()
            result = await run_flamboyance(url="http://localhost:3000", llm_mode=False)

        assert result["config"]["llm_mode"] is False
        assert "max_llm_calls" not in result["config"]


class TestRunSimulation:
    """Test the legacy run_simulation tool."""

    @pytest.mark.asyncio
    async def test_run_simulation_invalid_url(self):
        """Invalid URL returns error dict."""
        result = await run_simulation(url="javascript:alert(1)")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_simulation_success(self):
        """Valid request returns run_id."""
        with patch("flamboyance_mcp.server.run_local", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = MagicMock()
            result = await run_simulation(url="http://localhost:8080")

        assert "run_id" in result
        assert "llm_mode" in result


class TestGetStatus:
    """Test the get_status polling tool."""

    @pytest.mark.asyncio
    async def test_get_status_not_found(self):
        """Unknown run_id returns not_found status."""
        result = await get_status(run_id="nonexistent-id")
        assert result["status"] == "not_found"
        assert result["run_id"] == "nonexistent-id"

    @pytest.mark.asyncio
    async def test_get_status_running(self):
        """Running simulation returns progress."""
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS

        mock_state = RunState(
            run_id="test-run-123",
            url="http://localhost:3000",
            personas=list(DEFAULT_PERSONAS.values())[:3],
            status="running",
        )

        with patch("flamboyance_mcp.server.get_run", return_value=mock_state):
            result = await get_status(run_id="test-run-123")

        assert result["status"] == "running"
        assert "progress" in result
        assert "0/3" in result["progress"]

    @pytest.mark.asyncio
    async def test_get_status_done_returns_summary(self):
        """Completed simulation returns concise summary."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS

        mock_result = AgentResult(
            persona="frustrated_exec",
            status="done",
            frustration_events=[{"kind": "slow_load", "description": "Page took 5s", "url": "http://test.com"}],
        )
        mock_state = RunState(
            run_id="test-run-456",
            url="http://localhost:3000",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="done",
            results=[mock_result],
        )

        with patch("flamboyance_mcp.server.get_run", return_value=mock_state):
            with patch("flamboyance_mcp.server.save_report", return_value="results/report.md"):
                result = await get_status(run_id="test-run-456")

        assert result["status"] == "done"
        assert "summary" in result
        assert isinstance(result["summary"], str)


class TestGetLiveFeed:
    """Test the get_live_feed tool."""

    @pytest.mark.asyncio
    async def test_get_live_feed_not_found(self):
        """Unknown run_id returns empty agents list."""
        result = await get_live_feed(run_id="nonexistent")
        assert result["status"] == "not_found"
        assert result["agents"] == []

    @pytest.mark.asyncio
    async def test_get_live_feed_with_results(self):
        """Returns agent status for each persona."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import Persona

        personas = [
            Persona(name="test1", patience=0.5, tech_literacy=0.5, goal="test"),
            Persona(name="test2", patience=0.5, tech_literacy=0.5, goal="test"),
        ]
        mock_result = AgentResult(
            persona="test1",
            status="done",
            visited_urls=["http://test.com"],
            frustration_events=[{"description": "test event"}],
            elapsed_seconds=5.0,
        )
        mock_state = RunState(
            run_id="feed-test",
            url="http://localhost:3000",
            personas=personas,
            status="running",
            results=[mock_result],
        )

        with patch("flamboyance_mcp.server.get_run", return_value=mock_state):
            result = await get_live_feed(run_id="feed-test")

        assert result["status"] == "running"
        assert len(result["agents"]) == 2
        # First agent completed
        assert result["agents"][0]["persona"] == "test1"
        assert result["agents"][0]["status"] == "done"
        # Second agent pending
        assert result["agents"][1]["persona"] == "test2"
        assert result["agents"][1]["status"] == "pending"


class TestGetReport:
    """Test the get_report tool."""

    @pytest.mark.asyncio
    async def test_get_report_not_found(self):
        """Unknown run_id returns error markdown."""
        result = await get_report(run_id="nonexistent")
        assert "Error" in result["markdown"]
        assert "not found" in result["markdown"]

    @pytest.mark.asyncio
    async def test_get_report_generates_markdown(self):
        """Valid run_id returns markdown report."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS

        mock_result = AgentResult(persona="frustrated_exec", status="done")
        mock_state = RunState(
            run_id="report-test",
            url="http://localhost:3000",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="done",
            results=[mock_result],
        )

        with patch("flamboyance_mcp.server.get_run", return_value=mock_state):
            with patch("flamboyance_mcp.server.save_report", return_value="results/report.md"):
                result = await get_report(run_id="report-test")

        assert "markdown" in result
        assert "Flamboyance" in result["markdown"]


class TestStopSimulation:
    """Test the stop_simulation tool."""

    @pytest.mark.asyncio
    async def test_stop_simulation_not_found(self):
        """Unknown run_id returns stopped=False."""
        result = await stop_simulation(run_id="nonexistent")
        assert result["stopped"] is False

    @pytest.mark.asyncio
    async def test_stop_simulation_success(self):
        """Valid run_id cancels task and returns stopped=True."""
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS

        mock_state = RunState(
            run_id="stop-test",
            url="http://localhost:3000",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="running",
        )

        mock_task = MagicMock()
        mock_task.done.return_value = False

        with patch("flamboyance_mcp.server.get_run", return_value=mock_state):
            with patch("flamboyance_mcp.server._tasks", {"stop-test": mock_task}):
                result = await stop_simulation(run_id="stop-test")

        assert result["stopped"] is True
        mock_task.cancel.assert_called_once()


class TestRunMutationTestTool:
    """Test the run_mutation_test_tool."""

    @pytest.mark.asyncio
    async def test_mutation_test_invalid_url(self):
        """Invalid URL returns error."""
        result = await run_mutation_test_tool(
            url="not-valid",
            mutations={"name": "test", "hide": [".button"]},
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mutation_test_unknown_builtin(self):
        """Unknown built-in scenario returns error."""
        result = await run_mutation_test_tool(
            url="http://localhost:3000",
            mutations="unknown_scenario",
        )
        assert "error" in result
        assert "Unknown built-in scenario" in result["error"]


class TestConciseSummary:
    """Test concise summary generation for Cascade readability."""

    def test_concise_summary_under_50_lines(self):
        """Summary should be under 50 lines for Cascade readability."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS
        from agents.report import generate_concise_summary

        # Create state with many events
        events = [
            {"kind": "slow_load", "description": f"Page {i} took 5s", "url": f"http://test.com/page{i}", "severity": "medium"}
            for i in range(20)
        ]
        mock_result = AgentResult(
            persona="frustrated_exec",
            status="done",
            frustration_events=events,
        )
        mock_state = RunState(
            run_id="summary-test",
            url="http://test.com",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="done",
            results=[mock_result],
        )

        summary = generate_concise_summary(mock_state)
        line_count = len(summary.split("\n"))

        assert line_count <= 50, f"Summary has {line_count} lines, should be <= 50"

    def test_concise_summary_grouped_by_url(self):
        """Summary should group issues by URL."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS
        from agents.report import generate_concise_summary

        events = [
            {"kind": "slow_load", "description": "Page took 5s", "url": "http://test.com/page1", "severity": "high"},
            {"kind": "rage_click", "description": "User clicked 5 times", "url": "http://test.com/page1", "severity": "high"},
            {"kind": "dead_end", "description": "No navigation", "url": "http://test.com/page2", "severity": "medium"},
        ]
        mock_result = AgentResult(
            persona="frustrated_exec",
            status="done",
            frustration_events=events,
        )
        mock_state = RunState(
            run_id="grouped-test",
            url="http://test.com",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="done",
            results=[mock_result],
        )

        summary = generate_concise_summary(mock_state)

        # Should have URL headers
        assert "http://test.com/page1" in summary
        assert "http://test.com/page2" in summary
        # Should have "Issues by Location" section
        assert "Issues by Location" in summary

    def test_concise_summary_includes_recommendations(self):
        """Summary should include actionable recommendations."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS
        from agents.report import generate_concise_summary

        events = [
            {"kind": "slow_load", "description": "Page took 5s", "url": "http://test.com", "severity": "high"},
        ]
        mock_result = AgentResult(
            persona="frustrated_exec",
            status="done",
            frustration_events=events,
        )
        mock_state = RunState(
            run_id="rec-test",
            url="http://test.com",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="done",
            results=[mock_result],
        )

        summary = generate_concise_summary(mock_state)

        assert "Recommendations" in summary
        # Should have specific fix recommendation for slow_load
        assert "Optimize" in summary or "performance" in summary.lower()

    def test_concise_summary_no_issues(self):
        """Summary should indicate when no issues found."""
        from agents.agent import AgentResult
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS
        from agents.report import generate_concise_summary

        mock_result = AgentResult(
            persona="frustrated_exec",
            status="done",
            frustration_events=[],
        )
        mock_state = RunState(
            run_id="clean-test",
            url="http://test.com",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="done",
            results=[mock_result],
        )

        summary = generate_concise_summary(mock_state)

        assert "No issues detected" in summary
        assert "✅" in summary


class TestGetStatusErrorState:
    """Test get_status handling of error states."""

    @pytest.mark.asyncio
    async def test_get_status_error_state(self):
        """Error state returns error message and details."""
        from agents.runner_local import RunState
        from agents.persona import DEFAULT_PERSONAS

        mock_state = RunState(
            run_id="error-test",
            url="http://localhost:3000",
            personas=list(DEFAULT_PERSONAS.values())[:1],
            status="error",
        )
        mock_state._error = "Browser disconnected unexpectedly"

        with patch("flamboyance_mcp.server.get_run", return_value=mock_state):
            result = await get_status(run_id="error-test")

        assert result["status"] == "error"
        assert "error" in result
        assert "Browser disconnected" in result["error"]
        assert "details" in result


class TestErrorResponseFormat:
    """Test that error responses have consistent format."""

    @pytest.mark.asyncio
    async def test_validation_errors_return_dict(self):
        """All validation errors return dict with 'error' key."""
        # Test various invalid inputs
        results = [
            await run_flamboyance(url=""),
            await run_flamboyance(url="ftp://invalid.com"),
            await run_simulation(url="file:///etc/passwd"),
        ]

        for result in results:
            assert isinstance(result, dict)
            assert "error" in result
            assert isinstance(result["error"], str)

    @pytest.mark.asyncio
    async def test_not_found_returns_consistent_format(self):
        """Not found responses have consistent structure."""
        status_result = await get_status(run_id="missing")
        feed_result = await get_live_feed(run_id="missing")
        stop_result = await stop_simulation(run_id="missing")

        assert status_result["status"] == "not_found"
        assert feed_result["status"] == "not_found"
        assert stop_result["stopped"] is False
