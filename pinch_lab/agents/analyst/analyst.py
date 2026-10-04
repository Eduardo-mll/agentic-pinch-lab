"""Analyst agent: deterministic science gate + optional Claude narration."""

from __future__ import annotations

from typing import Any

from pinch_lab.tools.claude_client import anthropic_enabled, claude_complete


BASELINE_HEATING = 100.0


def analyze_result(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Interpret one experiment and choose a different next ΔTmin.

    Numerical support/reject decisions stay rule-based (Python > LLM).
    Claude may only rewrite the learning sentence when enabled.
    """
    analysis = _analyze_rules(hypothesis, experiment, result)

    if anthropic_enabled() and result.get("status") == "VALID":
        narrated = _narrate_with_claude(hypothesis, experiment, result, analysis)
        if narrated:
            analysis["learning"] = narrated
            analysis["learning_generated_by"] = "CLAUDE"
        else:
            analysis["learning_generated_by"] = "RULES"
    else:
        analysis["learning_generated_by"] = "RULES"

    return analysis


def _analyze_rules(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
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
            "Lowering delta_t_min did not help in this run."
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

    economics = result.get("economics") or {}
    if economics:
        learning += (
            f" Network total cost ≈ ${float(economics.get('total_cost_per_year', 0)):.0f}/yr "
            f"(equipment ${float(economics.get('equipment_cost_per_year', 0)):.0f}, "
            f"utilities ${float(economics.get('utility_cost_per_year', 0)):.0f})."
        )

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


def _narrate_with_claude(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
    analysis: dict[str, Any],
) -> str | None:
    system = (
        "You are the Analyst Agent. Rewrite the learning sentence in 1-2 concise "
        "English sentences. Keep every number exactly as provided. "
        "Do not invent new values. Do not change the support/reject status."
    )
    user = (
        f"status={analysis.get('status')}\n"
        f"hypothesis={hypothesis.get('text')}\n"
        f"delta_t_min={result.get('delta_t_min')}\n"
        f"heating_utility_kw={result.get('heating_utility_kw')}\n"
        f"heat_recovery_kw={result.get('heat_recovery_kw')}\n"
        f"economics={result.get('economics')}\n"
        f"base_learning={analysis.get('learning')}\n"
        f"next_delta_t_min={analysis.get('next_decision', {}).get('experiment', {}).get('delta_t_min')}"
    )
    response = claude_complete(system=system, user=user, max_tokens=180)
    if response.get("status") != "OK":
        return None
    text = str(response.get("text") or "").strip()
    return text or None
