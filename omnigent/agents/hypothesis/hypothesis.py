"""Simple Hypothesis stub (rule-based for now; later Omnigent/Claude)."""

from __future__ import annotations

from typing import Any


def formulate_hypothesis(
    question: str,
    previous_analysis: dict[str, Any] | None = None,
    evidence_ids: list[str] | None = None,
    evidence_status: str = "OK",
) -> dict[str, Any]:
    """Create or refine a falsifiable hypothesis about delta_t_min."""
    evidence_ids = evidence_ids or []

    if evidence_status == "INSUFFICIENT_EVIDENCE" or not evidence_ids:
        return {
            "id": "HYP-000",
            "text": "No hypothesis formed because approved evidence is missing.",
            "status": "INSUFFICIENT_EVIDENCE",
            "expected_effect": None,
            "evidence_ids": [],
            "variable": "delta_t_min",
            "direction": None,
            "question": question,
        }

    if previous_analysis is None:
        return {
            "id": "HYP-001",
            "text": (
                "Reducing delta_t_min from 10 C toward lower values may increase "
                "heat recovery and reduce external utility demand."
            ),
            "status": "UNTESTED",
            "expected_effect": "reduce_external_utility",
            "evidence_ids": evidence_ids,
            "variable": "delta_t_min",
            "direction": "decrease_delta_t_min",
        }

    status = previous_analysis.get("status", "INCONCLUSIVE")
    next_dt = previous_analysis.get("next_decision", {}).get("experiment", {}).get(
        "delta_t_min"
    )

    if status == "SUPPORTED":
        text = (
            "Further reducing delta_t_min should continue to lower external "
            "heating utility if the previous trend is real."
        )
        direction = "decrease_delta_t_min"
        hyp_id = "HYP-002"
    elif status == "REJECTED":
        text = (
            "Increasing delta_t_min may be a better trade-off if lowering it "
            "did not reduce external utility demand."
        )
        direction = "increase_delta_t_min"
        hyp_id = "HYP-002"
    else:
        text = (
            "The effect of changing delta_t_min on external utility is still "
            "unclear; probe a different value around the baseline."
        )
        direction = "probe_around_baseline"
        hyp_id = "HYP-002"

    return {
        "id": hyp_id,
        "text": text,
        "status": "UNTESTED",
        "expected_effect": "reduce_external_utility",
        "evidence_ids": evidence_ids,
        "variable": "delta_t_min",
        "direction": direction,
        "suggested_delta_t_min": next_dt,
        "based_on_previous_status": status,
        "question": question,
    }
