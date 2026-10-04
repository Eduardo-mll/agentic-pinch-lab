"""Analyst agent: deterministic science gate + optional Claude narration."""

from __future__ import annotations

import re
from typing import Any

from pinch_lab.tools.claude_client import anthropic_enabled, claude_complete


BASELINE_HEATING = 100.0
BASELINE_DELTA_T_MIN = 10.0
# Engine total at ΔTmin = 10 °C. Same figure the cost model returns, not a second rounded copy.
BASELINE_TOTAL_COST_PER_YEAR = 104828.3995


def analyze_result(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
    previous_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Interpret one experiment and choose a different next ΔTmin.

    When two total costs exist, the next ΔTmin follows the cheaper one.
    Numerical support/reject decisions stay rule-based (Python > LLM).
    Claude may only rewrite the learning sentence when enabled.
    """
    analysis = _analyze_rules(hypothesis, experiment, result, previous_result)

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


def _total_cost(payload: dict[str, Any] | None) -> float | None:
    if not payload:
        return None
    economics = payload.get("economics") or {}
    value = economics.get("total_cost_per_year")
    if value is None:
        return None
    return float(value)


def _neighbor(current: float, toward_lower: bool) -> float:
    if toward_lower:
        nxt = max(5.0, round(current - 1.5, 1))
    else:
        nxt = min(30.0, round(current + 2.5, 1))
    if nxt == current:
        nxt = 5.0 if current > 5 else 8.0
    return nxt


def _analyze_rules(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
    previous_result: dict[str, Any] | None = None,
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
    current_cost = _total_cost(result)

    if current_cost is not None:
        previous_cost = _total_cost(previous_result)
        if previous_cost is None:
            reference_cost = BASELINE_TOTAL_COST_PER_YEAR
            reference_dt = BASELINE_DELTA_T_MIN
            reference_label = "baseline"
        else:
            reference_cost = previous_cost
            reference_dt = float(previous_result["delta_t_min"])
            reference_label = "previous experiment"
        return _decide_from_cost(
            current=current,
            heating=heating,
            cooling=float(result.get("cooling_utility_kw") or 0),
            recovery=recovery,
            current_cost=current_cost,
            reference_cost=reference_cost,
            reference_dt=reference_dt,
            reference_label=reference_label,
            economics=result.get("economics") or {},
        )

    expected = experiment.get("expected_effect", "reduce_external_utility")
    heating_improved = heating < BASELINE_HEATING

    if expected == "reduce_external_utility" and heating_improved:
        status = "SUPPORTED"
        next_value = _neighbor(current, toward_lower=True)
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
        next_value = _neighbor(current, toward_lower=False)
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

    return _decision(
        status=status,
        learning=learning,
        reason=reason,
        next_value=next_value,
        heating=heating,
        recovery=recovery,
        decision_basis="heating_utility",
    )


def _decide_from_cost(
    *,
    current: float,
    heating: float,
    cooling: float,
    recovery: float,
    current_cost: float,
    reference_cost: float,
    reference_dt: float,
    reference_label: str,
    economics: dict[str, Any],
) -> dict[str, Any]:
    moved_down = current < reference_dt - 1e-9
    cost_delta = current_cost - reference_cost
    equipment = float(economics.get("equipment_cost_per_year", 0))
    utilities = float(economics.get("utility_cost_per_year", 0))
    network_heating = economics.get("network_heating_kw")
    network_cooling = economics.get("network_cooling_kw")
    network_note = ""
    if network_heating is not None and network_cooling is not None:
        if abs(float(network_heating) - heating) > 0.05 or abs(float(network_cooling) - cooling) > 0.05:
            network_note = (
                f" Pinch targets are heating {heating:g} kW and cooling {cooling:g} kW. "
                f"This network actually requires heating {float(network_heating):.2f} kW "
                f"and cooling {float(network_cooling):.2f} kW, and those loads set the utility cost "
                f"(${utilities:.2f}/yr), so equipment plus utilities is ${current_cost:.2f}/yr."
            )

    if cost_delta < -1.0:
        status = "SUPPORTED"
        next_value = _neighbor(current, toward_lower=moved_down)
        learning = (
            f"Total network cost fell to ${current_cost:.2f}/yr from "
            f"${reference_cost:.2f}/yr at ΔTmin {reference_dt} C ({reference_label}). "
            f"Heating is {heating} kW and recovery is {recovery} kW. "
            f"Equipment ${equipment:.2f}/yr, utilities ${utilities:.2f}/yr."
            f"{network_note}"
        )
        reason = (
            f"Because total cost was lower at delta_t_min={current} C than at "
            f"{reference_dt} C, continue that direction with {next_value} C."
        )
    elif cost_delta > 1.0:
        status = "REJECTED"
        next_value = _neighbor(current, toward_lower=not moved_down)
        learning = (
            f"Total network cost rose to ${current_cost:.2f}/yr from "
            f"${reference_cost:.2f}/yr at ΔTmin {reference_dt} C ({reference_label}), "
            f"even with heating {heating} kW and recovery {recovery} kW. "
            f"Equipment ${equipment:.2f}/yr, utilities ${utilities:.2f}/yr. "
            "Lower utility demand did not minimize total cost."
            f"{network_note}"
        )
        reason = (
            f"Because total cost was higher at delta_t_min={current} C than at "
            f"{reference_dt} C, try the other direction at {next_value} C."
        )
    else:
        status = "INCONCLUSIVE"
        next_value = _neighbor(current, toward_lower=not moved_down)
        learning = (
            f"Total cost ${current_cost:.2f}/yr is effectively the same as "
            f"${reference_cost:.2f}/yr at ΔTmin {reference_dt} C."
        )
        reason = (
            f"Costs match within $1/yr, so probe the other side at {next_value} C."
        )

    return _decision(
        status=status,
        learning=learning,
        reason=reason,
        next_value=next_value,
        heating=heating,
        recovery=recovery,
        decision_basis="total_cost",
        direction=(
            "decrease_delta_t_min" if next_value < current else "increase_delta_t_min"
        ),
        compared_cost=reference_cost,
        observed_cost=current_cost,
    )


def _decision(
    *,
    status: str,
    learning: str,
    reason: str,
    next_value: float,
    heating: float,
    recovery: float,
    decision_basis: str,
    direction: str | None = None,
    compared_cost: float | None = None,
    observed_cost: float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "learning": learning,
        "decision_basis": decision_basis,
        "compared_to_baseline_heating_kw": BASELINE_HEATING,
        "observed_heating_utility_kw": heating,
        "observed_heat_recovery_kw": recovery,
        "next_decision": {
            "reason": reason,
            "experiment": {"delta_t_min": next_value},
        },
    }
    if direction is not None:
        payload["direction"] = direction
    if compared_cost is not None:
        payload["compared_total_cost_per_year"] = compared_cost
        payload["observed_total_cost_per_year"] = observed_cost
    return payload


def _narrate_with_claude(
    hypothesis: dict[str, Any],
    experiment: dict[str, Any],
    result: dict[str, Any],
    analysis: dict[str, Any],
) -> str | None:
    system = (
        "You are the Analyst Agent. Rewrite the learning sentence in 1-2 concise "
        "English sentences. Keep every number exactly as provided. "
        "The only baseline is delta_t_min = 10 C. "
        "Call every other value a previous experiment, never baseline. "
        "Do not describe an untested next delta_t_min as if it already ran. "
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
    tested = float(result.get("delta_t_min") or 0)
    if "baseline" in text.lower() and abs(tested - BASELINE_DELTA_T_MIN) > 0.05:
        if not re.search(r"\b10(?:\.0+)?\b", text):
            return None
    return text or None
