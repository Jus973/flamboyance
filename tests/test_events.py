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
