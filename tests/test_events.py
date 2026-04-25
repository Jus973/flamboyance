"""Tests for agents.events module — frustration event detection."""

import time
from unittest.mock import patch

from agents.events import EVENT_SEVERITY, EventDetector, EventSeverity


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

    def test_long_dwell_resets_timer_after_firing(self) -> None:
        d = EventDetector()
        evt = d.record_long_dwell("http://example.com", 15.0)
        assert evt is not None
        # After firing, the timer should be reset so the next check
        # does not immediately re-fire (prevents duplicate flooding).
        dwell_since_reset = time.time() - d.last_action_time
        assert dwell_since_reset < 1.0


class TestRageDecoy:
    def test_emits_rage_decoy_with_cursor_pointer(self) -> None:
        d = EventDetector()
        evt = d.record_rage_decoy(
            "http://example.com/page",
            "div.fake-button",
            "cursor:pointer"
        )
        assert evt is not None
        assert evt.kind == "rage_decoy"
        assert "div.fake-button" in evt.description
        assert "cursor:pointer" in evt.description
        assert evt.url == "http://example.com/page"
        assert evt.details["selector"] == "div.fake-button"
        assert evt.details["reason"] == "cursor:pointer"

    def test_emits_rage_decoy_with_clickable_class(self) -> None:
        d = EventDetector()
        evt = d.record_rage_decoy(
            "http://example.com/form",
            "span.clickable-item",
            "clickable class name"
        )
        assert evt is not None
        assert evt.kind == "rage_decoy"
        assert "clickable-item" in evt.description
        assert "clickable class name" in evt.description

    def test_emits_rage_decoy_with_multiple_reasons(self) -> None:
        d = EventDetector()
        evt = d.record_rage_decoy(
            "http://example.com",
            "div.clickable-card",
            "cursor:pointer, clickable class name"
        )
        assert evt is not None
        assert "cursor:pointer" in evt.details["reason"]
        assert "clickable class name" in evt.details["reason"]

    def test_multiple_decoys_accumulate(self) -> None:
        d = EventDetector()
        d.record_rage_decoy("http://a.com", "div.btn", "cursor:pointer")
        d.record_rage_decoy("http://a.com", "span.link", "clickable class name")
        d.record_rage_decoy("http://b.com", "p.action", "cursor:pointer")
        assert len(d.all_events()) == 3
        assert all(e.kind == "rage_decoy" for e in d.all_events())


class TestJsError:
    def test_emits_js_error(self) -> None:
        d = EventDetector()
        evt = d.record_js_error(
            "http://example.com/app",
            "Uncaught TypeError: Cannot read property 'foo' of undefined",
            source="app.js",
            line=42,
        )
        assert evt is not None
        assert evt.kind == "js_error"
        assert "JavaScript error" in evt.description
        assert "TypeError" in evt.description
        assert "app.js:42" in evt.description
        assert evt.url == "http://example.com/app"
        assert evt.details["source"] == "app.js"
        assert evt.details["line"] == 42

    def test_js_error_without_source(self) -> None:
        d = EventDetector()
        evt = d.record_js_error(
            "http://example.com",
            "ReferenceError: x is not defined",
        )
        assert evt is not None
        assert evt.kind == "js_error"
        assert "ReferenceError" in evt.description
        assert "source" not in evt.description

    def test_js_error_truncates_long_message(self) -> None:
        d = EventDetector()
        long_message = "Error: " + "x" * 200
        evt = d.record_js_error("http://example.com", long_message)
        assert evt is not None
        assert len(evt.description) < len(long_message) + 50
        assert evt.details["message"] == long_message

    def test_multiple_js_errors_accumulate(self) -> None:
        d = EventDetector()
        d.record_js_error("http://a.com", "Error 1")
        d.record_js_error("http://a.com", "Error 2")
        d.record_js_error("http://b.com", "Error 3")
        assert len(d.all_events()) == 3
        assert all(e.kind == "js_error" for e in d.all_events())


class TestBrokenImage:
    def test_emits_broken_image(self) -> None:
        d = EventDetector()
        evt = d.record_broken_image(
            "http://example.com/page",
            "http://example.com/images/missing.png",
            selector="img.hero",
        )
        assert evt is not None
        assert evt.kind == "broken_image"
        assert "Broken image" in evt.description
        assert "missing.png" in evt.description
        assert evt.url == "http://example.com/page"
        assert evt.details["image_src"] == "http://example.com/images/missing.png"
        assert evt.details["selector"] == "img.hero"

    def test_broken_image_truncates_long_src(self) -> None:
        d = EventDetector()
        long_src = "http://example.com/images/" + "x" * 200 + ".png"
        evt = d.record_broken_image("http://example.com", long_src)
        assert evt is not None
        assert len(evt.description) < len(long_src) + 50
        assert evt.details["image_src"] == long_src

    def test_multiple_broken_images_accumulate(self) -> None:
        d = EventDetector()
        d.record_broken_image("http://a.com", "http://a.com/img1.png")
        d.record_broken_image("http://a.com", "http://a.com/img2.png")
        assert len(d.all_events()) == 2
        assert all(e.kind == "broken_image" for e in d.all_events())


class TestNetworkError:
    def test_emits_network_error_with_status(self) -> None:
        d = EventDetector()
        evt = d.record_network_error(
            "http://example.com/app",
            "http://api.example.com/users",
            status_code=500,
            error_text="Internal Server Error",
            method="POST",
        )
        assert evt is not None
        assert evt.kind == "network_error"
        assert "Network error" in evt.description
        assert "500" in evt.description
        assert "POST" in evt.description
        assert evt.url == "http://example.com/app"
        assert evt.details["request_url"] == "http://api.example.com/users"
        assert evt.details["status_code"] == 500
        assert evt.details["method"] == "POST"

    def test_emits_network_error_404(self) -> None:
        d = EventDetector()
        evt = d.record_network_error(
            "http://example.com",
            "http://example.com/api/missing",
            status_code=404,
            error_text="Not Found",
        )
        assert evt is not None
        assert "404" in evt.description

    def test_emits_network_error_connection_failure(self) -> None:
        d = EventDetector()
        evt = d.record_network_error(
            "http://example.com",
            "http://api.example.com/data",
            status_code=0,
            error_text="net::ERR_CONNECTION_REFUSED",
        )
        assert evt is not None
        assert evt.kind == "network_error"
        assert "failed" in evt.description.lower()
        assert evt.details["status_code"] == 0

    def test_multiple_network_errors_accumulate(self) -> None:
        d = EventDetector()
        d.record_network_error("http://a.com", "http://api.a.com/1", status_code=500)
        d.record_network_error("http://a.com", "http://api.a.com/2", status_code=404)
        d.record_network_error("http://b.com", "http://api.b.com/3", status_code=0)
        assert len(d.all_events()) == 3
        assert all(e.kind == "network_error" for e in d.all_events())


class TestEventSeverity:
    def test_severity_levels_defined(self) -> None:
        assert EventSeverity.LOW.value == "low"
        assert EventSeverity.MEDIUM.value == "medium"
        assert EventSeverity.HIGH.value == "high"
        assert EventSeverity.CRITICAL.value == "critical"

    def test_all_event_types_have_severity(self) -> None:
        event_types = [
            "slow_load", "dead_end", "long_dwell", "rage_decoy",
            "js_error", "broken_image", "network_error",
            "circular_navigation", "rage_click", "unmet_goal"
        ]
        for event_type in event_types:
            assert event_type in EVENT_SEVERITY

    def test_event_severity_property(self) -> None:
        d = EventDetector()

        # Test high severity events
        evt = d.record_js_error("http://example.com", "Error")
        assert evt.severity == EventSeverity.HIGH

        evt = d.record_dead_end("http://example.com")
        assert evt.severity == EventSeverity.HIGH

        # Test critical severity
        evt = d.check_unmet_goal("goal", reached=False, timed_out=True)
        assert evt.severity == EventSeverity.CRITICAL

        # Test medium severity
        evt = d.record_slow_load("http://example.com", 5000.0)
        assert evt.severity == EventSeverity.MEDIUM

        # Test low severity
        evt = d.record_long_dwell("http://example.com", 15.0)
        assert evt.severity == EventSeverity.LOW
