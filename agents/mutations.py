"""UI Mutation scenarios for testing degraded UX conditions.

This module provides the MutationScenario schema and Playwright script injection
logic for simulating broken or degraded UI states before persona agents run.

Usage::

    from agents.mutations import MutationScenario, apply_mutations

    scenario = MutationScenario(
        name="broken_checkout",
        hide=["#checkout-btn"],
        disable=[".submit-form"],
    )

    # Apply to a Playwright page
    await apply_mutations(page, scenario)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MutationScenario:
    """Defines UI mutations to apply before running persona agents.

    Attributes:
        name: Identifier for this mutation scenario.
        hide: CSS selectors for elements to hide (visibility: hidden).
        disable: CSS selectors for elements to disable (pointer-events: none).
        remove: CSS selectors for elements to remove from DOM entirely.
        delay_clicks: Mapping of selector -> milliseconds delay before click registers.
    """

    name: str
    hide: list[str] = field(default_factory=list)
    disable: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)
    delay_clicks: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MutationScenario:
        """Create a MutationScenario from a dictionary."""
        return cls(
            name=data.get("name", "unnamed"),
            hide=data.get("hide", []),
            disable=data.get("disable", []),
            remove=data.get("remove", []),
            delay_clicks=data.get("delay_clicks", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "hide": self.hide,
            "disable": self.disable,
            "remove": self.remove,
            "delay_clicks": self.delay_clicks,
        }

    def is_empty(self) -> bool:
        """Return True if no mutations are defined."""
        return not (self.hide or self.disable or self.remove or self.delay_clicks)


def _build_mutation_script(scenario: MutationScenario) -> str:
    """Build JavaScript code to apply mutations to the page."""
    lines = ["(function() {"]

    # Hide elements
    for selector in scenario.hide:
        safe_selector = selector.replace("'", "\\'")
        lines.append(f"""
    document.querySelectorAll('{safe_selector}').forEach(el => {{
        el.style.visibility = 'hidden';
        el.setAttribute('data-flamboyance-mutation', 'hidden');
    }});""")

    # Disable elements (pointer-events: none)
    for selector in scenario.disable:
        safe_selector = selector.replace("'", "\\'")
        lines.append(f"""
    document.querySelectorAll('{safe_selector}').forEach(el => {{
        el.style.pointerEvents = 'none';
        el.style.opacity = '0.5';
        el.setAttribute('data-flamboyance-mutation', 'disabled');
    }});""")

    # Remove elements from DOM
    for selector in scenario.remove:
        safe_selector = selector.replace("'", "\\'")
        lines.append(f"""
    document.querySelectorAll('{safe_selector}').forEach(el => {{
        el.remove();
    }});""")

    # Delay clicks - intercept click events and add delay
    for selector, delay_ms in scenario.delay_clicks.items():
        safe_selector = selector.replace("'", "\\'")
        lines.append(f"""
    document.querySelectorAll('{safe_selector}').forEach(el => {{
        el.setAttribute('data-flamboyance-mutation', 'delayed');
        el.addEventListener('click', function(e) {{
            if (!e._flamboyanceDelayed) {{
                e.preventDefault();
                e.stopPropagation();
                setTimeout(() => {{
                    const newEvent = new MouseEvent('click', {{
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }});
                    newEvent._flamboyanceDelayed = true;
                    el.dispatchEvent(newEvent);
                }}, {delay_ms});
            }}
        }}, true);
    }});""")

    lines.append("})();")
    return "\n".join(lines)


async def apply_mutations(page: object, scenario: MutationScenario) -> None:
    """Apply mutation scenario to a Playwright page.

    This injects JavaScript that modifies the DOM according to the scenario.
    Should be called after page.goto() but before agent interaction begins.

    Args:
        page: Playwright Page object.
        scenario: MutationScenario defining what to mutate.
    """
    if scenario.is_empty():
        return

    from playwright.async_api import Page

    assert isinstance(page, Page)

    script = _build_mutation_script(scenario)
    await page.evaluate(script)


async def add_mutation_init_script(page: object, scenario: MutationScenario) -> None:
    """Add mutation script to run on every page load/navigation.

    Use this instead of apply_mutations() when you want mutations to persist
    across navigations within the same page context.

    Args:
        page: Playwright Page object.
        scenario: MutationScenario defining what to mutate.
    """
    if scenario.is_empty():
        return

    from playwright.async_api import Page

    assert isinstance(page, Page)

    script = _build_mutation_script(scenario)
    await page.add_init_script(script)


# Pre-defined common mutation scenarios
COMMON_SCENARIOS: dict[str, MutationScenario] = {
    "broken_checkout": MutationScenario(
        name="broken_checkout",
        hide=["#checkout-btn", ".checkout-button", "[data-testid='checkout']"],
    ),
    "no_nav": MutationScenario(
        name="no_nav",
        remove=[".main-nav", "nav", "#navigation", ".navbar"],
    ),
    "slow_submit": MutationScenario(
        name="slow_submit",
        delay_clicks={"button[type='submit']": 3000, ".submit-btn": 3000},
    ),
    "disabled_forms": MutationScenario(
        name="disabled_forms",
        disable=["form", "input", "button", "select", "textarea"],
    ),
    "hidden_cta": MutationScenario(
        name="hidden_cta",
        hide=[".cta", ".call-to-action", "[data-cta]", ".primary-button"],
    ),
}


def get_scenario(name: str) -> MutationScenario | None:
    """Get a pre-defined mutation scenario by name."""
    return COMMON_SCENARIOS.get(name)
