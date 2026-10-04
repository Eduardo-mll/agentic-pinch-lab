"""Hypothesis agent: Claude Haiku when enabled, else deterministic rules."""

from __future__ import annotations

import json
import re
from typing import Any

from pinch_lab.tools.claude_client import anthropic_enabled, claude_complete


def formulate_hypothesis(
    question: str,
    previous_analysis: dict[str, Any] | None = None,
    evidence_ids: list[str] | None = None,
    evidence_status: str = "OK",
    evidence_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create or refine a falsifiable hypothesis about delta_t_min."""
    evidence_ids = evidence_ids or []
    evidence_items = evidence_items or []

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

    if anthropic_enabled():
        claude_hyp = _hypothesis_with_claude(
            question=question,
            evidence_ids=evidence_ids,
            evidence_items=evidence_items,
            previous_analysis=previous_analysis,
        )
        if claude_hyp is not None:
            return claude_hyp

    return _hypothesis_rules(
        question=question,
        evidence_ids=evidence_ids,
        previous_analysis=previous_analysis,
    )


def _hypothesis_rules(
    *,
    question: str,
    evidence_ids: list[str],
    previous_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
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
            "generated_by": "RULES",
            "question": question,
        }

    status = previous_analysis.get("status", "INCONCLUSIVE")
    next_dt = previous_analysis.get("next_decision", {}).get("experiment", {}).get(
        "delta_t_min"
    )
    basis = previous_analysis.get("decision_basis")

    if basis == "total_cost":
        text = (
            "The next delta_t_min should follow the cheaper total network cost, "
            "counting both equipment and utilities, not heating utility alone."
            if status == "SUPPORTED"
            else "The previous delta_t_min raised total network cost. The other direction may be cheaper even if heat recovery changes."
            if status == "REJECTED"
            else "Total network cost did not change enough to choose a direction; probe another delta_t_min."
        )
        direction = previous_analysis.get("direction") or "probe_around_baseline"
        hyp_id = "HYP-002"
    elif status == "SUPPORTED":
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
        "generated_by": "RULES",
        "question": question,
    }


def _hypothesis_with_claude(
    *,
    question: str,
    evidence_ids: list[str],
    evidence_items: list[dict[str, Any]],
    previous_analysis: dict[str, Any] | None,
) -> dict[str, Any] | None:
    excerpts = []
    for item in evidence_items[:4]:
        excerpts.append(
            {
                "evidence_id": item.get("evidence_id"),
                "title": item.get("title"),
                "claim_supported": item.get("claim_supported"),
                "source_type": item.get("source_type"),
            }
        )

    system = (
        "You are the Hypothesis Agent for a Pinch Analysis lab. "
        "Propose ONE falsifiable hypothesis about changing delta_t_min only. "
        "If previous_analysis.decision_basis is total_cost, the hypothesis must "
        "be about total network cost, not only utility demand. "
        "Never invent numerical Pinch results. "
        "Reply with compact JSON only: "
        '{"id":"HYP-001","text":"...","expected_effect":"reduce_external_utility",'
        '"direction":"decrease_delta_t_min"|"increase_delta_t_min"|"probe_around_baseline"}'
    )
    user = json.dumps(
        {
            "question": question,
            "evidence_ids": evidence_ids,
            "evidence": excerpts,
            "previous_analysis": previous_analysis,
        },
        ensure_ascii=False,
    )
    response = claude_complete(system=system, user=user, max_tokens=350)
    if response.get("status") != "OK" or not response.get("text"):
        return None

    parsed = _extract_json(response["text"])
    if not isinstance(parsed, dict) or not parsed.get("text"):
        return None

    return {
        "id": str(parsed.get("id") or ("HYP-001" if previous_analysis is None else "HYP-002")),
        "text": str(parsed.get("text")).strip(),
        "status": "UNTESTED",
        "expected_effect": str(
            parsed.get("expected_effect") or "reduce_external_utility"
        ),
        "evidence_ids": evidence_ids,
        "variable": "delta_t_min",
        "direction": str(parsed.get("direction") or "decrease_delta_t_min"),
        "generated_by": "CLAUDE",
        "model": response.get("model"),
        "question": question,
    }


def _extract_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
