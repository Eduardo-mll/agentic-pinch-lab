"""Evidence Agent stub (local cache only for MVP)."""

from __future__ import annotations

from typing import Any

from omnigent.tools.evidence_store import (
    find_relevant_evidence,
    validate_evidence_ids,
)


def gather_evidence(question: str, limit: int = 3) -> dict[str, Any]:
    """Select approved local evidence for the scientific question."""
    items = find_relevant_evidence(question=question, limit=limit)
    evidence_ids = [item["evidence_id"] for item in items]

    if not evidence_ids:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "evidence_ids": [],
            "evidence": [],
            "message": "No approved local evidence matched the question.",
        }

    check = validate_evidence_ids(evidence_ids)
    if not check["valid"]:
        return {
            "status": "INVALID_EVIDENCE_REFERENCE",
            "evidence_ids": [],
            "evidence": [],
            "message": check["message"],
        }

    return {
        "status": "OK",
        "evidence_ids": evidence_ids,
        "evidence": items,
        "message": f"Selected {len(items)} approved local evidence record(s).",
    }
