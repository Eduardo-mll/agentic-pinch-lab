"""Local + Bright Data evidence store.

Only IDs present in evidence/evidence_registry.json may be cited.
BrightData SERP hits are registered as provisional web evidence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "evidence" / "evidence_registry.json"


class EvidenceStoreError(ValueError):
    """Invalid evidence reference or store state."""


def load_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or REGISTRY_PATH
    if not registry_path.exists():
        return {"evidence": [], "notes": "Empty evidence registry."}
    return json.loads(registry_path.read_text(encoding="utf-8"))


def save_registry(data: dict[str, Any], path: Path | None = None) -> None:
    registry_path = path or REGISTRY_PATH
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def list_evidence(path: Path | None = None) -> list[dict[str, Any]]:
    data = load_registry(path)
    return list(data.get("evidence", []))


def get_evidence(evidence_id: str, path: Path | None = None) -> dict[str, Any] | None:
    for item in list_evidence(path):
        if item.get("evidence_id") == evidence_id:
            return item
    return None


def validate_evidence_ids(
    evidence_ids: list[str],
    path: Path | None = None,
) -> dict[str, Any]:
    """Validate citations against the registry.

    Invented IDs must fail.
    """
    known = {item.get("evidence_id") for item in list_evidence(path)}
    missing = [eid for eid in evidence_ids if eid not in known]
    if missing:
        return {
            "status": "INVALID_EVIDENCE_REFERENCE",
            "valid": False,
            "missing_ids": missing,
            "message": f"Unknown evidence IDs: {', '.join(missing)}",
        }
    return {
        "status": "OK",
        "valid": True,
        "missing_ids": [],
        "message": "All evidence IDs exist in the registry.",
    }


def find_relevant_evidence(
    question: str,
    tags: list[str] | None = None,
    path: Path | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Select approved local evidence relevant to the scientific question."""
    tags = tags or ["delta_t_min", "pinch", "baseline", "utilities"]
    question_l = question.lower()
    scored: list[tuple[int, dict[str, Any]]] = []

    for item in list_evidence(path):
        if not item.get("approved", False):
            continue
        score = 0
        item_tags = [str(t).lower() for t in item.get("tags", [])]
        for tag in tags:
            if tag.lower() in item_tags:
                score += 2
            if tag.lower() in question_l:
                score += 1
        blob = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("claim_supported", "")),
                str(item.get("relevant_excerpt", "")),
            ]
        ).lower()
        if "delta_t_min" in blob or "pinch" in blob:
            score += 1
        if item.get("source_type") == "web_serp":
            score += 1
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def register_web_serp_results(
    query: str,
    results: list[dict[str, str]],
    path: Path | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Persist Bright Data SERP hits into the registry and return new/updated items."""
    if not results:
        return []

    registry = load_registry(path)
    evidence = list(registry.get("evidence", []))
    by_id = {item.get("evidence_id"): item for item in evidence}
    now = datetime.now(timezone.utc).isoformat()
    registered: list[dict[str, Any]] = []

    for result in results[:limit]:
        url = str(result.get("url", "")).strip()
        title = str(result.get("title", "")).strip() or "Web SERP result"
        snippet = str(result.get("snippet", "")).strip()
        digest = hashlib.sha1(f"{url}|{title}".encode("utf-8")).hexdigest()[:10].upper()
        evidence_id = f"EVID-WEB-{digest}"

        item = {
            "evidence_id": evidence_id,
            "title": title[:180],
            "source_url": url or "serp://unknown",
            "source_type": "web_serp",
            "retrieved_at": now,
            "relevant_excerpt": snippet[:500]
            or f"SERP hit for query: {query}",
            "claim_supported": (
                "External literature/web context related to Pinch Analysis / "
                f"delta_t_min (query: {query}). Qualitative only — do not invent "
                "numerical Pinch targets from this source."
            ),
            "confidence": "low",
            "approved": True,
            "tags": ["web", "pinch", "delta_t_min", "brightdata"],
            "query": query,
        }
        by_id[evidence_id] = item
        registered.append(item)

    # Keep seed local evidence first, then web/other.
    seed = [
        item
        for item in evidence
        if str(item.get("evidence_id", "")).startswith("EVID-00")
    ]
    others = [
        item
        for eid, item in by_id.items()
        if not str(eid).startswith("EVID-00")
    ]
    registry["evidence"] = seed + others
    registry["notes"] = (
        "Local approved evidence plus Bright Data SERP web hits. "
        "Web hits are qualitative context only; Pinch numbers must come from Python."
    )
    save_registry(registry, path)
    return registered
