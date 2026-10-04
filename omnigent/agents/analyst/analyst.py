"""Simple Analyst stub (rule-based for now; later Omnigent/Claude)."""

from __future__ import annotations

from typing import Any


BASELINE_HEATING = 100.0


def analyze_result(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Interpret one experiment and choose a different next ΔTmin."""
    if result.get("status") != "VALID":
        current = float(experiment["proposed_value"])
        next_value = min(30.0, current + 2.5)
        return {
            "status": "INCONCLUSIVE",
            "learning": f"Experiment rejected or invalid: {result.get('message')}",
            "next_decision": {
                "reason": "Previous value was invalid; try a safer delta_t_min inside range.",
                "experiment": {"delta_t_min": next_value},
            },
        }

    heating = float(result["heating_utility_kw"])
    recovery = float(result["heat_recovery_kw"])
    current = float(result["delta_t_min"])
    expected = experiment.get("expected_effect", "reduce_external_utility")

    heating_improved = heating < BASELINE_HEATING

    if expected == "reduce_external_utility" and heating_improved:
        status = "SUPPORTED"
        # Push a bit lower to see if utilities keep falling.
        next_value = max(5.0, round(current - 1.5, 1))
        learning = (
            f"Heating utility fell to {heating} kW (baseline {BASELINE_HEATING} kW) "
            f"and recovery rose to {recovery} kW. Hypothesis direction is supported."
        )
        reason = (
            f"Because heating improved at delta_t_min={current} C, test an even lower "
            f"value ({next_value} C) to check if the trend continues."
        )
    elif expected == "reduce_external_utility" and not heating_improved:
        status = "REJECTED"
        next_value = min(30.0, round(current + 2.5, 1))
        learning = (
            f"Heating utility was {heating} kW, not below baseline {BASELINE_HEATING} kW. "
            "Lowering delta_t_min did not help in this fake run."
        )
        reason = (
            f"Because lowering delta_t_min did not reduce heating, try a higher value "
            f"({next_value} C) next."
        )
    else:
        status = "INCONCLUSIVE"
        next_value = 12.5 if current <= 10 else 7.5
        learning = "Result did not clearly support or reject the hypothesis direction."
        reason = (
            f"Probe the opposite side of the baseline with delta_t_min={next_value} C."
        )

    if next_value == current:
        next_value = 5.0 if current > 5 else 8.0

    return {
        "status": status,
        "learning": learning,
        "compared_to_baseline_heating_kw": BASELINE_HEATING,
        "observed_heating_utility_kw": heating,
        "observed_heat_recovery_kw": recovery,
        "next_decision": {
            "reason": reason,
            "experiment": {"delta_t_min": next_value},
        },
    }
