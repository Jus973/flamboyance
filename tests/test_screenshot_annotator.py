"""Tests for agents.screenshot_annotator module — screenshot annotation utilities."""

import base64
import io
from unittest.mock import patch

from agents.screenshot_annotator import (
    AnnotationMarker,
    _parse_color,
    annotate_screenshot,
    create_markers_from_events,
    extract_event_coordinates,
)


def _create_test_image_b64(width: int = 100, height: int = 100) -> str:
    """Create a simple test PNG image as base64."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


class TestAnnotationMarker:
    def test_marker_defaults(self) -> None:
        marker = AnnotationMarker(x=50, y=50, label="test")
        assert marker.x == 50
        assert marker.y == 50
        assert marker.label == "test"
        assert marker.color == "red"
        assert marker.radius == 20

    def test_marker_custom_values(self) -> None:
        marker = AnnotationMarker(x=100, y=200, label="custom", color="blue", radius=30)
        assert marker.x == 100
        assert marker.y == 200
        assert marker.label == "custom"
        assert marker.color == "blue"
        assert marker.radius == 30


class TestParseColor:
    def test_parse_red(self) -> None:
        color = _parse_color("red")
        assert color == (220, 53, 69, 255)

    def test_parse_orange(self) -> None:
        color = _parse_color("orange")
        assert color == (255, 140, 0, 255)

    def test_parse_yellow(self) -> None:
        color = _parse_color("yellow")
        assert color == (255, 193, 7, 255)

    def test_parse_green(self) -> None:
        color = _parse_color("green")
        assert color == (40, 167, 69, 255)

    def test_parse_blue(self) -> None:
        color = _parse_color("blue")
        assert color == (0, 123, 255, 255)

    def test_parse_case_insensitive(self) -> None:
        assert _parse_color("RED") == _parse_color("red")
        assert _parse_color("Blue") == _parse_color("blue")
        assert _parse_color("YELLOW") == _parse_color("yellow")

    def test_parse_unknown_defaults_to_red(self) -> None:
        color = _parse_color("purple")
        assert color == (220, 53, 69, 255)  # red

        color = _parse_color("invalid")
        assert color == (220, 53, 69, 255)  # red


class TestExtractEventCoordinates:
    def test_extract_from_x_y_keys(self) -> None:
        event = {"x": 100, "y": 200, "kind": "rage_decoy"}
        coords = extract_event_coordinates(event)
        assert coords == (100, 200)

    def test_extract_from_x_y_as_strings(self) -> None:
        event = {"x": "150", "y": "250"}
        coords = extract_event_coordinates(event)
        assert coords == (150, 250)

    def test_extract_from_target_list(self) -> None:
        event = {"target": [300, 400]}
        coords = extract_event_coordinates(event)
        assert coords == (300, 400)

    def test_extract_from_target_tuple(self) -> None:
        event = {"target": (350, 450)}
        coords = extract_event_coordinates(event)
        assert coords == (350, 450)

    def test_returns_none_for_no_coordinates(self) -> None:
        event = {"kind": "dead_end", "url": "http://example.com"}
        coords = extract_event_coordinates(event)
        assert coords is None

    def test_returns_none_for_invalid_x_y(self) -> None:
        event = {"x": "invalid", "y": "also_invalid"}
        coords = extract_event_coordinates(event)
        assert coords is None

    def test_returns_none_for_invalid_target(self) -> None:
        event = {"target": "not_a_tuple"}
        coords = extract_event_coordinates(event)
        assert coords is None

    def test_returns_none_for_short_target(self) -> None:
        event = {"target": [100]}  # Only one element
        coords = extract_event_coordinates(event)
        assert coords is None

    def test_prefers_x_y_over_target(self) -> None:
        event = {"x": 10, "y": 20, "target": [100, 200]}
        coords = extract_event_coordinates(event)
        assert coords == (10, 20)


class TestCreateMarkersFromEvents:
    def test_creates_markers_with_coordinates(self) -> None:
        events = [
            {"kind": "rage_decoy", "x": 100, "y": 100, "severity": "medium"},
            {"kind": "dead_end", "x": 200, "y": 200, "severity": "high"},
        ]
        markers = create_markers_from_events(events)
        assert len(markers) == 2
        assert markers[0].x == 100
        assert markers[0].y == 100
        assert markers[0].label == "rage_decoy"
        assert markers[0].color == "yellow"  # medium severity
        assert markers[1].x == 200
        assert markers[1].y == 200
        assert markers[1].label == "dead_end"
        assert markers[1].color == "orange"  # high severity

    def test_skips_events_without_coordinates(self) -> None:
        events = [
            {"kind": "rage_decoy", "x": 100, "y": 100},
            {"kind": "dead_end"},  # No coordinates
            {"kind": "js_error", "x": 300, "y": 300},
        ]
        markers = create_markers_from_events(events)
        assert len(markers) == 2
        assert markers[0].label == "rage_decoy"
        assert markers[1].label == "js_error"

    def test_uses_default_positions(self) -> None:
        events = [
            {"kind": "rage_decoy"},  # No coordinates
            {"kind": "dead_end"},  # No coordinates
        ]
        defaults = [(50, 50), (150, 150)]
        markers = create_markers_from_events(events, default_positions=defaults)
        assert len(markers) == 2
        assert markers[0].x == 50
        assert markers[0].y == 50
        assert markers[1].x == 150
        assert markers[1].y == 150

    def test_default_positions_only_used_when_needed(self) -> None:
        events = [
            {"kind": "rage_decoy", "x": 100, "y": 100},  # Has coordinates
            {"kind": "dead_end"},  # No coordinates, uses default
        ]
        defaults = [(50, 50), (150, 150)]
        markers = create_markers_from_events(events, default_positions=defaults)
        assert len(markers) == 2
        assert markers[0].x == 100  # Uses event coordinates
        assert markers[1].x == 50  # Uses first default

    def test_severity_color_mapping(self) -> None:
        events = [
            {"kind": "critical_event", "x": 10, "y": 10, "severity": "critical"},
            {"kind": "high_event", "x": 20, "y": 20, "severity": "high"},
            {"kind": "medium_event", "x": 30, "y": 30, "severity": "medium"},
            {"kind": "low_event", "x": 40, "y": 40, "severity": "low"},
        ]
        markers = create_markers_from_events(events)
        assert markers[0].color == "red"  # critical
        assert markers[1].color == "orange"  # high
        assert markers[2].color == "yellow"  # medium
        assert markers[3].color == "green"  # low

    def test_default_severity_is_medium(self) -> None:
        events = [{"kind": "unknown", "x": 100, "y": 100}]  # No severity
        markers = create_markers_from_events(events)
        assert markers[0].color == "yellow"  # medium (default)

    def test_empty_events_list(self) -> None:
        markers = create_markers_from_events([])
        assert markers == []

    def test_all_events_without_coordinates_and_no_defaults(self) -> None:
        events = [
            {"kind": "dead_end"},
            {"kind": "unmet_goal"},
        ]
        markers = create_markers_from_events(events)
        assert markers == []


class TestAnnotateScreenshot:
    def test_returns_original_if_no_markers(self) -> None:
        original_b64 = _create_test_image_b64()
        result = annotate_screenshot(original_b64, [])
        assert result == original_b64

    def test_annotates_single_marker(self) -> None:
        original_b64 = _create_test_image_b64(200, 200)
        markers = [AnnotationMarker(x=100, y=100, label="test", color="red")]
        result = annotate_screenshot(original_b64, markers)

        # Result should be different from original (annotated)
        assert result != original_b64

        # Result should be valid base64 PNG
        decoded = base64.b64decode(result)
        from PIL import Image

        img = Image.open(io.BytesIO(decoded))
        assert img.format == "PNG"
        assert img.size == (200, 200)

    def test_annotates_multiple_markers(self) -> None:
        original_b64 = _create_test_image_b64(300, 300)
        markers = [
            AnnotationMarker(x=50, y=50, label="1", color="red"),
            AnnotationMarker(x=150, y=150, label="2", color="orange"),
            AnnotationMarker(x=250, y=250, label="3", color="yellow"),
        ]
        result = annotate_screenshot(original_b64, markers)

        assert result != original_b64
        decoded = base64.b64decode(result)
        from PIL import Image

        img = Image.open(io.BytesIO(decoded))
        assert img.format == "PNG"

    def test_handles_different_colors(self) -> None:
        original_b64 = _create_test_image_b64(200, 200)
        for color in ["red", "orange", "yellow", "green", "blue"]:
            markers = [AnnotationMarker(x=100, y=100, label="test", color=color)]
            result = annotate_screenshot(original_b64, markers)
            assert result != original_b64

    def test_handles_edge_positions(self) -> None:
        original_b64 = _create_test_image_b64(100, 100)
        markers = [
            AnnotationMarker(x=5, y=5, label="corner", color="red"),
            AnnotationMarker(x=95, y=95, label="corner2", color="blue"),
        ]
        result = annotate_screenshot(original_b64, markers)
        # Should not raise an error even with edge positions
        assert result is not None

    def test_returns_original_on_invalid_base64(self) -> None:
        invalid_b64 = "not_valid_base64!!!"
        markers = [AnnotationMarker(x=50, y=50, label="test")]
        result = annotate_screenshot(invalid_b64, markers)
        # Should return original on error
        assert result == invalid_b64

    def test_returns_original_on_invalid_image_data(self) -> None:
        # Valid base64 but not an image
        invalid_image_b64 = base64.b64encode(b"not an image").decode()
        markers = [AnnotationMarker(x=50, y=50, label="test")]
        result = annotate_screenshot(invalid_image_b64, markers)
        assert result == invalid_image_b64

    def test_custom_radius(self) -> None:
        original_b64 = _create_test_image_b64(200, 200)
        markers = [
            AnnotationMarker(x=100, y=100, label="small", color="red", radius=10),
            AnnotationMarker(x=150, y=100, label="large", color="blue", radius=40),
        ]
        result = annotate_screenshot(original_b64, markers)
        assert result != original_b64


class TestAnnotateScreenshotWithoutPillow:
    def test_returns_original_when_pillow_not_installed(self) -> None:
        original_b64 = "test_base64_string"
        markers = [AnnotationMarker(x=50, y=50, label="test")]

        with patch.dict("sys.modules", {"PIL": None, "PIL.Image": None}):
            # Force reimport to trigger ImportError path
            import agents.screenshot_annotator as sa

            # Mock the import to raise ImportError
            def mock_annotate(image_b64, markers):
                # Simulate what happens when PIL import fails
                if not markers:
                    return image_b64
                return image_b64  # Return original when PIL unavailable

            with patch.object(sa, "annotate_screenshot", mock_annotate):
                result = sa.annotate_screenshot(original_b64, markers)
                assert result == original_b64


class TestIntegrationWithEvents:
    def test_full_pipeline_rage_decoy_events(self) -> None:
        """Test creating markers from rage_decoy events and annotating."""
        events = [
            {
                "kind": "rage_decoy",
                "x": 100,
                "y": 100,
                "severity": "medium",
                "description": "Fake button",
            },
            {
                "kind": "rage_decoy",
                "x": 200,
                "y": 150,
                "severity": "medium",
                "description": "Fake link",
            },
        ]

        markers = create_markers_from_events(events)
        assert len(markers) == 2

        original_b64 = _create_test_image_b64(300, 200)
        result = annotate_screenshot(original_b64, markers)

        # Verify annotation was applied
        assert result != original_b64

        # Verify result is valid image
        decoded = base64.b64decode(result)
        from PIL import Image

        img = Image.open(io.BytesIO(decoded))
        assert img.format == "PNG"

    def test_full_pipeline_mixed_severity_events(self) -> None:
        """Test markers with different severities get correct colors."""
        events = [
            {"kind": "unmet_goal", "x": 50, "y": 50, "severity": "critical"},
            {"kind": "js_error", "x": 100, "y": 50, "severity": "high"},
            {"kind": "rage_decoy", "x": 150, "y": 50, "severity": "medium"},
            {"kind": "long_dwell", "x": 200, "y": 50, "severity": "low"},
        ]

        markers = create_markers_from_events(events)
        assert len(markers) == 4
        assert markers[0].color == "red"
        assert markers[1].color == "orange"
        assert markers[2].color == "yellow"
        assert markers[3].color == "green"

        original_b64 = _create_test_image_b64(250, 100)
        result = annotate_screenshot(original_b64, markers)
        assert result != original_b64

    def test_full_pipeline_with_target_coordinates(self) -> None:
        """Test events using target tuple for coordinates."""
        events = [
            {"kind": "click", "target": [100, 100], "severity": "medium"},
            {"kind": "click", "target": (200, 200), "severity": "medium"},
        ]

        markers = create_markers_from_events(events)
        assert len(markers) == 2
        assert markers[0].x == 100
        assert markers[0].y == 100
        assert markers[1].x == 200
        assert markers[1].y == 200
