"""Discovery API for the frontend and demos."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from pinch_lab.run_discovery_loop import (
    HISTORY_PATH,
    ROOT,
    continuation_from_latest,
    load_saved_records,
    run_loop,
)
from pinch_lab.tools.evidence_store import list_evidence, validate_evidence_ids
from pathlib import Path
import json

router = APIRouter(tags=["discovery"])


class DiscoveryRequest(BaseModel):
    steps: int = Field(default=2, ge=1, le=5)


@router.post("/discovery/run")
def discovery_run(body: DiscoveryRequest | None = None) -> dict:
    """Run the local discovery loop and return the experiment records."""
    requested = 2 if body is None else body.steps
    prior = continuation_from_latest()
    if prior is None:
        fresh = run_loop(steps=requested)
    else:
        fresh = run_loop(steps=1, **prior)
    saved = load_saved_records()
    previous = saved[-2] if len(saved) > 1 else saved[0]
    latest = saved[-1]
    return {
        "status": "ok",
        "steps": len(fresh),
        "experiments": saved,
        "agentic_proof": {
            "first_delta_t_min": previous["experiment"]["proposed_value"],
            "second_delta_t_min": latest["experiment"]["proposed_value"],
            "second_changed": previous["experiment"]["proposed_value"]
            != latest["experiment"]["proposed_value"],
        },
    }


@router.get("/discovery/history")
def discovery_history() -> dict:
    """Return the lightweight experiment history index."""
    if not HISTORY_PATH.exists():
        return {"experiments": [], "notes": "No experiments yet."}
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


@router.get("/discovery/records")
def discovery_records() -> dict:
    """Return every saved run file, oldest first. Missing files are simply absent."""
    runs_dir = ROOT / "results" / "runs"
    if not runs_dir.exists():
        return {"status": "ok", "experiments": []}

    experiments = []
    for path in sorted(runs_dir.glob("RUN-*.json"), key=lambda item: item.stat().st_mtime):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            item.pop("_saved_path", None)
            experiments.append(item)
    return {"status": "ok", "experiments": experiments}


def clear_saved_runs(root: Path, history_path: Path) -> dict:
    """Delete saved discovery runs and reset the history index."""
    runs_dir = root / "results" / "runs"
    removed = 0
    if runs_dir.exists():
        for path in runs_dir.glob("RUN-*.json"):
            path.unlink()
            removed += 1
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps({"experiments": [], "notes": "Cleared."}, indent=2) + "\n",
        encoding="utf-8",
    )
    science_history = root / "results" / "science_history.jsonl"
    if science_history.exists():
        science_history.unlink()
    return {"status": "ok", "removed_runs": removed}


@router.post("/discovery/clear")
def discovery_clear() -> dict:
    """Remove saved experiment runs. Does not delete evidence or the measured-cycle file."""
    return clear_saved_runs(ROOT, HISTORY_PATH)


@router.get("/discovery/latest")
def discovery_latest() -> dict:
    """Return the newest saved experiment record, if any."""
    runs_dir = ROOT / "results" / "runs"
    if not runs_dir.exists():
        return {"status": "empty", "record": None}

    files = sorted(runs_dir.glob("RUN-*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return {"status": "empty", "record": None}

    latest = json.loads(files[-1].read_text(encoding="utf-8"))
    return {"status": "ok", "record": latest}


@router.get("/evidence")
def evidence_list() -> dict:
    """Return approved local evidence records for the frontend."""
    items = list_evidence()
    return {
        "status": "ok",
        "count": len(items),
        "evidence": items,
    }


@router.post("/evidence/validate")
def evidence_validate(body: dict) -> dict:
    """Validate that cited evidence IDs exist in the registry."""
    evidence_ids = body.get("evidence_ids", [])
    if not isinstance(evidence_ids, list):
        return {
            "status": "INVALID_REQUEST",
            "valid": False,
            "message": "evidence_ids must be a list",
        }
    return validate_evidence_ids([str(x) for x in evidence_ids])


@router.get("/lab/status")
def lab_status() -> dict:
    """Expose the human-approval gate and the measured cycle, if one was recorded."""
    from src.human_gate import load_delta_t_limits

    minimum, maximum = load_delta_t_limits()
    metrics_path = ROOT / "results" / "metrics" / "acceleration.json"
    measurement = None
    if metrics_path.exists():
        measurement = json.loads(metrics_path.read_text(encoding="utf-8"))
    return {
        "status": "ok",
        "human_approval": {
            "delta_t_min_min_c": minimum,
            "delta_t_min_max_c": maximum,
            "locked": [
                "stream_identity",
                "supply_temp",
                "target_temp",
                "fcp",
                "h",
            ],
            "message": (
                "ΔTmin inside the approved range can run. "
                "Stream changes and moving that range need a scientist's approval."
            ),
        },
        "measurement": measurement,
    }

