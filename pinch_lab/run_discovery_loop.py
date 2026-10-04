"""Run a 2-step discovery loop on the agents branch.

Usage (from repo root, venv active):

    python -m pinch_lab.run_discovery_loop

This proves: experiment #2 changes because of result #1.
Later: replace fake_experiment with the real Pinch engine.
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
from pinch_lab.tools.evidence_store import validate_evidence_ids

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
            "message": result.get("message"),
        },
        "analysis": {
            "status": analysis["status"],
            "learning": analysis["learning"],
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


def run_loop(steps: int = 2) -> list[dict]:
    records: list[dict] = []
    previous_result: dict | None = None
    previous_analysis: dict | None = None
    preferred_next: float | None = None

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
        )
        if hypothesis.get("status") == "INSUFFICIENT_EVIDENCE":
            raise ValueError("INSUFFICIENT_EVIDENCE: cannot plan experiments yet.")

        experiment = propose_experiment(
            hypothesis=hypothesis,
            previous_result=previous_result,
            preferred_delta_t_min=preferred_next,
        )
        result = run_computational_experiment(
            delta_t_min=float(experiment["proposed_value"])
        )
        analysis = analyze_result(hypothesis, experiment, result)
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
