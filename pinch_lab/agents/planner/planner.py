"""Simple Planner stub (rule-based for now; later Omnigent/Claude)."""

from __future__ import annotations

from typing import Any


def propose_experiment(
    hypothesis: dict[str, Any],
    previous_result: dict[str, Any] | None = None,
    preferred_delta_t_min: float | None = None,
) -> dict[str, Any]:
    """Select one ΔTmin experiment.

    Priority:
    1. Analyst-provided next value (preferred_delta_t_min)
    2. Default first experiment from the hypothesis (7.5 °C)
    """
    baseline = 10.0

    if preferred_delta_t_min is not None:
        proposed = float(preferred_delta_t_min)
        reason = "Using analyst next-decision value from the previous result."
        experiment_id = "EXP-002"
    else:
        proposed = 7.5
        reason = (
            "First test: lower delta_t_min below baseline to check whether "
            "external utility demand decreases."
        )
        experiment_id = "EXP-001"

    return {
        "experiment_id": experiment_id,
        "hypothesis_id": hypothesis.get("id", "HYP-001"),
        "variable": "delta_t_min",
        "baseline_value": baseline,
        "proposed_value": proposed,
        "expected_effect": "reduce_external_utility",
        "reason": reason,
        "candidates_considered": [7.5, 12.5] if preferred_delta_t_min is None else [proposed],
        "previous_run_id": (previous_result or {}).get("run_id"),
    }
