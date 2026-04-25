"""Flamboyance UX-friction agents: persona definitions, Playwright agent, and event detection."""

from .mutations import COMMON_SCENARIOS, MutationScenario, apply_mutations, get_scenario
from .runner_mutation import MutationTestResult, run_mutation_test

__all__ = [
    "MutationScenario",
    "MutationTestResult",
    "COMMON_SCENARIOS",
    "apply_mutations",
    "get_scenario",
    "run_mutation_test",
]
