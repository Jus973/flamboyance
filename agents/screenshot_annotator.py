"""Screenshot annotation utility for UX friction reports.

Uses Pillow to draw visual markers on screenshots at frustration event locations.
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class AnnotationMarker:
    """A marker to draw on a screenshot."""

    x: int
    y: int
    label: str
    color: str = "red"
    radius: int = 20


def annotate_screenshot(
    image_b64: str,
    markers: list[AnnotationMarker],
) -> str:
    """Draw annotation markers on a screenshot.

    Args:
        image_b64: Base64-encoded PNG screenshot
        markers: List of markers to draw (coordinates, labels, colors)

    Returns:
        Base64-encoded annotated PNG screenshot
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        log.warning("Pillow not installed, returning original screenshot")
        return image_b64

    if not markers:
        return image_b64

    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(image, "RGBA")

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except (OSError, IOError):
                font = ImageFont.load_default()

        for i, marker in enumerate(markers, 1):
            color = _parse_color(marker.color)
            x, y = marker.x, marker.y
            r = marker.radius

            # Draw circle outline
            draw.ellipse(
                [(x - r, y - r), (x + r, y + r)],
                outline=color,
                width=3,
            )

            # Draw semi-transparent fill
            fill_color = (*color[:3], 50)  # Add alpha
            draw.ellipse(
                [(x - r + 2, y - r + 2), (x + r - 2, y + r - 2)],
                fill=fill_color,
            )

            # Draw number label
            label_text = str(i)
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Position label above the circle
            label_x = x - text_width // 2
            label_y = y - r - text_height - 5

            # Draw label background
            padding = 3
            draw.rectangle(
                [
                    (label_x - padding, label_y - padding),
                    (label_x + text_width + padding, label_y + text_height + padding),
                ],
                fill=color,
            )
            draw.text((label_x, label_y), label_text, fill="white", font=font)

        # Save annotated image
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return base64.b64encode(output.getvalue()).decode()

    except Exception as e:
        log.warning("Failed to annotate screenshot: %s", e)
        return image_b64


def _parse_color(color: str) -> tuple[int, int, int, int]:
    """Parse color string to RGBA tuple."""
    colors = {
        "red": (220, 53, 69, 255),
        "orange": (255, 140, 0, 255),
        "yellow": (255, 193, 7, 255),
        "green": (40, 167, 69, 255),
        "blue": (0, 123, 255, 255),
    }
    return colors.get(color.lower(), colors["red"])


def extract_event_coordinates(event: dict) -> tuple[int, int] | None:
    """Extract click coordinates from a frustration event if available.

    Args:
        event: Frustration event dictionary

    Returns:
        (x, y) tuple if coordinates found, None otherwise
    """
    # Check for explicit coordinates
    if "x" in event and "y" in event:
        try:
            return (int(event["x"]), int(event["y"]))
        except (ValueError, TypeError):
            pass

    # Check for coordinates in action history
    if "target" in event:
        target = event["target"]
        if isinstance(target, (list, tuple)) and len(target) == 2:
            try:
                return (int(target[0]), int(target[1]))
            except (ValueError, TypeError):
                pass

    return None


def create_markers_from_events(
    events: list[dict],
    default_positions: list[tuple[int, int]] | None = None,
) -> list[AnnotationMarker]:
    """Create annotation markers from frustration events.

    Args:
        events: List of frustration event dictionaries
        default_positions: Default positions for events without coordinates

    Returns:
        List of AnnotationMarker objects
    """
    markers: list[AnnotationMarker] = []
    severity_colors = {
        "critical": "red",
        "high": "orange",
        "medium": "yellow",
        "low": "green",
    }

    default_idx = 0
    defaults = default_positions or []

    for event in events:
        coords = extract_event_coordinates(event)

        if coords is None and default_idx < len(defaults):
            coords = defaults[default_idx]
            default_idx += 1

        if coords is None:
            continue

        severity = event.get("severity", "medium")
        color = severity_colors.get(severity, "yellow")
        kind = event.get("kind", "unknown")

        markers.append(
            AnnotationMarker(
                x=coords[0],
                y=coords[1],
                label=kind,
                color=color,
            )
        )

    return markers
