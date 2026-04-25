"""Tests for agents.events module — frustration event detection."""

import time
from unittest.mock import patch

from agents.events import EventDetector


class TestCircularNavigation:
    def test_no_event_on_linear_nav(self) -> None:
        d = EventDetector()
        assert d.record_navigation("http://a.com") is None
        assert d.record_navigation("http://b.com") is None
        assert d.record_navigation("http://c.com") is None

    def test_detects_aba_pattern(self) -> None:
        d = EventDetector()
        d.record_navigation("http://a.com")
        d.record_navigation("http://b.com")
        evt = d.record_navigation("http://a.com")
        assert evt is not None
        assert evt.kind == "circular_navigation"
        assert "a.com" in evt.description

    def test_no_event_on_same_page_reload(self) -> None:
        d = EventDetector()
        d.record_navigation("http://a.com")
        d.record_navigation("http://a.com")
        evt = d.record_navigation("http://a.com")
        assert evt is None


class TestRageClick:
    def test_no_event_on_interactive_clicks(self) -> None:
        d = EventDetector()
        for _ in range(5):
            evt = d.record_click("button#submit", is_interactive=True)
            assert evt is None

    def test_detects_rage_click(self) -> None:
        d = EventDetector()
        now = time.time()
        with patch("agents.events.time.time", side_effect=[now, now + 0.3, now + 0.6]):
            d.record_click("div.banner", is_interactive=False)
            d.record_click("div.banner", is_interactive=False)
            evt = d.record_click("div.banner", is_interactive=False)
        assert evt is not None
        assert evt.kind == "rage_click"
        assert "div.banner" in evt.description

    def test_no_rage_click_if_spread_out(self) -> None:
        d = EventDetector()
        now = time.time()
        with patch(
            "agents.events.time.time",
            side_effect=[now, now + 1.0, now + 2.5],
        ):
            d.record_click("div.x", is_interactive=False)
            d.record_click("div.x", is_interactive=False)
            evt = d.record_click("div.x", is_interactive=False)
        assert evt is None


class TestUnmetGoal:
    def test_no_event_if_reached(self) -> None:
        d = EventDetector()
        evt = d.check_unmet_goal("buy item", reached=True, timed_out=False)
        assert evt is None

    def test_event_on_timeout(self) -> None:
        d = EventDetector()
        evt = d.check_unmet_goal("buy item", reached=False, timed_out=True)
        assert evt is not None
        assert evt.kind == "unmet_goal"
        assert "timeout" in evt.description

    def test_event_on_gave_up(self) -> None:
        d = EventDetector()
        evt = d.check_unmet_goal("buy item", reached=False, timed_out=False)
        assert evt is not None
        assert "gave up" in evt.description

    def test_all_events_accumulate(self) -> None:
        d = EventDetector()
        d.record_navigation("http://a.com")
        d.record_navigation("http://b.com")
        d.record_navigation("http://a.com")
        d.check_unmet_goal("test", reached=False, timed_out=True)
        assert len(d.all_events()) == 2


class TestSlowLoad:
    def test_no_event_below_threshold(self) -> None:
        d = EventDetector()
        evt = d.record_slow_load("http://example.com", 2000.0)
        assert evt is None
        assert len(d.all_events()) == 0

    def test_no_event_at_threshold(self) -> None:
        d = EventDetector()
        evt = d.record_slow_load("http://example.com", 3000.0)
        assert evt is None

    def test_detects_slow_load(self) -> None:
        d = EventDetector()
        evt = d.record_slow_load("http://example.com/slow", 5000.0)
        assert evt is not None
        assert evt.kind == "slow_load"
        assert "5000" in evt.description
        assert evt.url == "http://example.com/slow"
        assert evt.details["load_time_ms"] == 5000.0

    def test_very_slow_load(self) -> None:
        d = EventDetector()
        evt = d.record_slow_load("http://example.com/stress", 10000.0)
        assert evt is not None
        assert evt.kind == "slow_load"


class TestDeadEnd:
    def test_emits_dead_end(self) -> None:
        d = EventDetector()
        evt = d.record_dead_end("http://example.com/dead")
        assert evt is not None
        assert evt.kind == "dead_end"
        assert "no clickable" in evt.description
        assert evt.url == "http://example.com/dead"

    def test_multiple_dead_ends_accumulate(self) -> None:
        d = EventDetector()
        d.record_dead_end("http://a.com")
        d.record_dead_end("http://b.com")
        assert len(d.all_events()) == 2


class TestLongDwell:
    def test_no_event_below_threshold(self) -> None:
        d = EventDetector()
        evt = d.record_long_dwell("http://example.com", 5.0)
        assert evt is None
        assert len(d.all_events()) == 0

    def test_no_event_at_threshold(self) -> None:
        d = EventDetector()
        evt = d.record_long_dwell("http://example.com", 10.0)
        assert evt is None

    def test_detects_long_dwell(self) -> None:
        d = EventDetector()
        evt = d.record_long_dwell("http://example.com/form", 15.0)
        assert evt is not None
        assert evt.kind == "long_dwell"
        assert "15.0" in evt.description
        assert evt.url == "http://example.com/form"
        assert evt.details["dwell_seconds"] == 15.0

    def test_touch_resets_timer(self) -> None:
        d = EventDetector()
        old_time = d.last_action_time
        with patch("agents.events.time.time", return_value=old_time + 5):
            d.touch()
        assert d.last_action_time == old_time + 5
