"""Evidence Agent: local registry + optional Bright Data SERP."""

from __future__ import annotations

from typing import Any

from pinch_lab.tools.brightdata_client import (
    brightdata_enabled,
    default_search_query,
    search_google_serp,
)
from pinch_lab.tools.evidence_store import (
    find_relevant_evidence,
    register_web_serp_results,
    validate_evidence_ids,
)


def gather_evidence(question: str, limit: int = 3) -> dict[str, Any]:
    """Select approved evidence, enriching with Bright Data when enabled."""
    web_meta: dict[str, Any] = {
        "enabled": brightdata_enabled(),
        "status": "SKIPPED",
        "message": "Bright Data disabled or not configured.",
    }

    if brightdata_enabled():
        query = default_search_query(question)
        serp = search_google_serp(query, limit=max(limit, 3))
        web_meta = {
            "enabled": True,
            "status": serp.get("status"),
            "query": serp.get("query"),
            "message": serp.get("message"),
            "zone": serp.get("zone"),
        }
        if serp.get("status") == "OK":
            register_web_serp_results(
                query=query,
                results=list(serp.get("results") or []),
                limit=limit,
            )

    items = find_relevant_evidence(question=question, limit=limit)
    evidence_ids = [item["evidence_id"] for item in items]

    if not evidence_ids:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "evidence_ids": [],
            "evidence": [],
            "web": web_meta,
            "message": "No approved evidence matched the question.",
        }

    check = validate_evidence_ids(evidence_ids)
    if not check["valid"]:
        return {
            "status": "INVALID_EVIDENCE_REFERENCE",
            "evidence_ids": [],
            "evidence": [],
            "web": web_meta,
            "message": check["message"],
        }

    sources = []
    if any(str(i).startswith("EVID-00") for i in evidence_ids):
        sources.append("local")
    if any(str(i).startswith("EVID-WEB-") for i in evidence_ids):
        sources.append("brightdata")

    return {
        "status": "OK",
        "evidence_ids": evidence_ids,
        "evidence": items,
        "web": web_meta,
        "sources": sources,
        "message": (
            f"Selected {len(items)} approved evidence record(s) "
            f"({'+'.join(sources) or 'unknown'})."
        ),
    }
