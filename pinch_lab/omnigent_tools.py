"""Python callables exposed to the Omnigent Claude coordinator.

These wrappers keep Omnigent configs thin:
Claude reasons -> tools calculate / retrieve deterministic data.
"""

from __future__ import annotations

from typing import Any

from pinch_lab.agents.evidence import gather_evidence
from pinch_lab.run_discovery_loop import run_loop
from pinch_lab.tools.evidence_store import validate_evidence_ids
from pinch_lab.tools import run_computational_experiment


def tool_gather_evidence(question: str, limit: int = 3) -> dict[str, Any]:
    """Select approved local evidence for a scientific question."""
    return gather_evidence(question=question, limit=limit)


def tool_validate_evidence_ids(evidence_ids: list[str]) -> dict[str, Any]:
    """Reject invented evidence IDs that are not in the registry."""
    return validate_evidence_ids(evidence_ids)


def tool_run_experiment(delta_t_min: float) -> dict[str, Any]:
    """Run one computational experiment for a proposed delta_t_min.

    Prefers the science-branch Pinch engine; falls back to fake model.
    """
    return run_computational_experiment(delta_t_min=float(delta_t_min))


def tool_run_discovery_loop(steps: int = 2) -> dict[str, Any]:
    """Run the full local discovery loop and return experiment records."""
    steps = max(1, min(int(steps), 5))
    records = run_loop(steps=steps)
    clean = []
    for record in records:
        item = dict(record)
        item.pop("_saved_path", None)
        clean.append(item)
    first = clean[0]["experiment"]["proposed_value"] if clean else None
    second = clean[1]["experiment"]["proposed_value"] if len(clean) > 1 else None
    return {
        "status": "ok",
        "steps": steps,
        "experiments": clean,
        "agentic_proof": {
            "first_delta_t_min": first,
            "second_delta_t_min": second,
            "second_changed": first is not None and second is not None and first != second,
        },
    }
