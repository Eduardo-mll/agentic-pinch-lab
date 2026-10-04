"""Run a 2-step discovery loop on the agents branch.

Usage (from repo root, venv active):

    python -m pinch_lab.run_discovery_loop

This proves: experiment #2 changes because of result #1.
Numbers come from the science engine. Simulation is not used automatically.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pinch_lab.agents.analyst import analyze_result
from pinch_lab.agents.evidence import gather_evidence
from pinch_lab.agents.hypothesis import formulate_hypothesis
from pinch_lab.agents.planner import propose_experiment
from pinch_lab.tools import run_computational_experiment
from pinch_lab.tools.env_loader import load_repo_env
from pinch_lab.tools.evidence_store import validate_evidence_ids

load_repo_env()

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "runs"
HISTORY_PATH = ROOT / "results" / "experiments.json"

QUESTION = (
    "Can lowering delta_t_min reduce external utility demand while respecting "
    "Pinch Analysis constraints?"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_record(
    *,
    evidence_pack: dict,
    hypothesis: dict,
    experiment: dict,
    result: dict,
    analysis: dict,
) -> dict:
    return {
        "run_id": result.get("run_id"),
        "timestamp": _utc_now(),
        "question": QUESTION,
        "evidence_ids": hypothesis.get("evidence_ids", []),
        "evidence": {
            "status": evidence_pack.get("status"),
            "message": evidence_pack.get("message"),
            "sources": evidence_pack.get("sources"),
            "web": evidence_pack.get("web"),
            "items": [
                {
                    "evidence_id": item.get("evidence_id"),
                    "title": item.get("title"),
                    "source_type": item.get("source_type"),
                    "claim_supported": item.get("claim_supported"),
                    "confidence": item.get("confidence"),
                }
                for item in evidence_pack.get("evidence", [])
            ],
        },
        "hypothesis": {
            "id": hypothesis["id"],
            "text": hypothesis["text"],
            "status": "TESTED",
            "expected_effect": hypothesis.get("expected_effect"),
            "direction": hypothesis.get("direction"),
            "generated_by": hypothesis.get("generated_by"),
        },
        "experiment": {
            "experiment_id": experiment["experiment_id"],
            "variable": experiment["variable"],
            "baseline_value": experiment["baseline_value"],
            "proposed_value": experiment["proposed_value"],
            "expected_effect": experiment["expected_effect"],
            "reason": experiment["reason"],
        },
        "validation": {
            "status": "PASS" if result.get("status") == "VALID" else "REJECTED"
        },
        "result": {
            "generated_by": result.get("generated_by"),
            "status": result.get("status"),
            "delta_t_min": result.get("delta_t_min"),
            "heat_recovery_kw": result.get("heat_recovery_kw"),
            "heating_utility_kw": result.get("heating_utility_kw"),
            "cooling_utility_kw": result.get("cooling_utility_kw"),
            "hot_pinch_c": result.get("hot_pinch_c"),
            "cold_pinch_c": result.get("cold_pinch_c"),
            "energy": result.get("energy"),
            "network": (
                None
                if not result.get("network")
                else {
                    "total_area_m2": result["network"].get("total_area_m2"),
                    "number_of_exchangers": result["network"].get(
                        "number_of_exchangers"
                    ),
                    "process_heat_kw": result["network"].get("process_heat_kw"),
                    "topology": result["network"].get("topology"),
                }
            ),
            "economics": result.get("economics"),
            "message": result.get("message"),
        },
        "analysis": {
            "status": analysis["status"],
            "learning": analysis["learning"],
            "learning_generated_by": analysis.get("learning_generated_by"),
            "decision_basis": analysis.get("decision_basis"),
        },
        "next_decision": analysis["next_decision"],
    }


def _save_record(record: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{record['run_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    if HISTORY_PATH.exists():
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    else:
        history = {"experiments": []}

    try:
        rel_path = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel_path = str(path)

    history.setdefault("experiments", []).append(
        {
            "run_id": record["run_id"],
            "experiment_id": record["experiment"]["experiment_id"],
            "delta_t_min": record["experiment"]["proposed_value"],
            "analysis_status": record["analysis"]["status"],
            "hypothesis_id": record["hypothesis"]["id"],
            "evidence_ids": record.get("evidence_ids", []),
            "path": rel_path,
        }
    )
    history["notes"] = "Updated by pinch_lab/run_discovery_loop.py"
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return path


def load_saved_records() -> list[dict]:
    """Return saved run files, oldest first."""
    if not RESULTS_DIR.exists():
        return []
    records: list[dict] = []
    for path in sorted(RESULTS_DIR.glob("RUN-*.json"), key=lambda item: item.stat().st_mtime):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            item.pop("_saved_path", None)
            records.append(item)
    return records


def continuation_from_latest() -> dict | None:
    """Seed one new step from the last saved next ΔTmin and its result."""
    saved = load_saved_records()
    if not saved:
        return None
    latest = saved[-1]
    next_value = (
        latest.get("next_decision", {}).get("experiment", {}).get("delta_t_min")
    )
    if next_value is None:
        return None
    previous_result = dict(latest.get("result") or {})
    previous_result["run_id"] = latest.get("run_id")
    previous_analysis = dict(latest.get("analysis") or {})
    previous_analysis["next_decision"] = latest.get("next_decision")
    return {
        "previous_result": previous_result,
        "previous_analysis": previous_analysis,
        "preferred_next": float(next_value),
        "completed_count": len(saved),
    }


def run_loop(
    steps: int = 2,
    *,
    previous_result: dict | None = None,
    previous_analysis: dict | None = None,
    preferred_next: float | None = None,
    completed_count: int = 0,
) -> list[dict]:
    records: list[dict] = []

    evidence_pack = gather_evidence(question=QUESTION)
    citation_check = validate_evidence_ids(evidence_pack.get("evidence_ids", []))
    if not citation_check["valid"]:
        raise ValueError(citation_check["message"])

    for _ in range(steps):
        hypothesis = formulate_hypothesis(
            question=QUESTION,
            previous_analysis=previous_analysis,
            evidence_ids=evidence_pack.get("evidence_ids", []),
            evidence_status=evidence_pack.get("status", "OK"),
            evidence_items=evidence_pack.get("evidence", []),
        )
        if hypothesis.get("status") == "INSUFFICIENT_EVIDENCE":
            raise ValueError("INSUFFICIENT_EVIDENCE: cannot plan experiments yet.")

        sequence = completed_count + len(records) + 1
        experiment = propose_experiment(
            hypothesis=hypothesis,
            previous_result=previous_result,
            preferred_delta_t_min=preferred_next,
            sequence=sequence,
        )
        tested = float(experiment["proposed_value"])
        if previous_result is None:
            reference = "the 10 C baseline"
        else:
            reference = f"the previous experiment at {float(previous_result['delta_t_min']):g} C"
        hypothesis["id"] = f"HYP-{sequence:03d}"
        hypothesis["text"] = (
            f"Testing whether delta_t_min = {tested:g} C lowers total network cost "
            f"relative to {reference}."
        )
        hypothesis["generated_by"] = "RULES"
        hypothesis["tested_delta_t_min"] = tested
        result = run_computational_experiment(
            delta_t_min=float(experiment["proposed_value"])
        )
        analysis = analyze_result(
            hypothesis,
            experiment,
            result,
            previous_result=previous_result,
        )
        record = _build_record(
            evidence_pack=evidence_pack,
            hypothesis=hypothesis,
            experiment=experiment,
            result=result,
            analysis=analysis,
        )
        saved = _save_record(record)
        record["_saved_path"] = str(saved)
        records.append(record)

        previous_result = result
        previous_analysis = analysis
        preferred_next = float(analysis["next_decision"]["experiment"]["delta_t_min"])

    return records


def main() -> None:
    records = run_loop(steps=2)
    first = records[0]["experiment"]["proposed_value"]
    second = records[1]["experiment"]["proposed_value"]

    print("Discovery loop complete.")
    print(f"Evidence IDs = {records[0]['evidence_ids']}")
    print(f"Hypothesis #1 = {records[0]['hypothesis']['id']}")
    print(f"Hypothesis #2 = {records[1]['hypothesis']['id']}")
    print(f"Experiment #1 delta_t_min = {first}")
    print(f"Experiment #2 delta_t_min = {second}")
    print(f"Analysis #1 = {records[0]['analysis']['status']}")
    print(f"Learning #1 = {records[0]['analysis']['learning']}")
    print(f"Why #2 changed = {records[0]['next_decision']['reason']}")

    if first == second:
        raise SystemExit(
            "FAIL: experiment #2 did not change. The loop is not agentic yet."
        )

    print("OK: experiment #2 differs because of result #1.")
    print(f"Saved under: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
