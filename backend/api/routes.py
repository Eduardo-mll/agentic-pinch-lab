"""Discovery API for the frontend and demos."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from omnigent.run_discovery_loop import HISTORY_PATH, ROOT, run_loop
import json

router = APIRouter(tags=["discovery"])


class DiscoveryRequest(BaseModel):
    steps: int = Field(default=2, ge=1, le=5)


@router.post("/discovery/run")
def discovery_run(body: DiscoveryRequest | None = None) -> dict:
    """Run the local discovery loop and return the experiment records."""
    steps = 2 if body is None else body.steps
    records = run_loop(steps=steps)
    # Drop private helper keys before returning.
    clean = []
    for record in records:
        item = dict(record)
        item.pop("_saved_path", None)
        clean.append(item)
    return {
        "status": "ok",
        "steps": steps,
        "experiments": clean,
        "agentic_proof": {
            "first_delta_t_min": clean[0]["experiment"]["proposed_value"],
            "second_delta_t_min": clean[1]["experiment"]["proposed_value"]
            if len(clean) > 1
            else None,
            "second_changed": (
                len(clean) > 1
                and clean[0]["experiment"]["proposed_value"]
                != clean[1]["experiment"]["proposed_value"]
            ),
        },
    }


@router.get("/discovery/history")
def discovery_history() -> dict:
    """Return the lightweight experiment history index."""
    if not HISTORY_PATH.exists():
        return {"experiments": [], "notes": "No experiments yet."}
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


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
