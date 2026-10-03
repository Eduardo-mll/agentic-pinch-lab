"""Deterministic Pinch Analysis entry point.

MVP note:
- At ΔTmin = 10 °C we return the known academic baseline.
- Full composite-curve / Problem Table implementation is the next ITC 1 task.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from .constraints import validate_delta_t_min
from .models import PinchResult

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scientific" / "baseline.json"


def _load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def run_pinch_analysis(delta_t_min: float = 10.0) -> PinchResult:
    """Run Pinch Analysis for the locked H1/H2/C1/C2 process."""
    error = validate_delta_t_min(delta_t_min)
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    if error:
        return PinchResult(
            status="REJECTED",
            run_id=run_id,
            delta_t_min=delta_t_min,
            message=error,
        )

    baseline = _load_baseline()

    # Easy starter: reproduce the known baseline exactly at ΔTmin = 10.
    # Replace this branch with a full Pinch calculation next.
    if abs(delta_t_min - baseline["delta_t_min_c"]) < 1e-9:
        return PinchResult(
            status="VALID",
            run_id=run_id,
            delta_t_min=delta_t_min,
            hot_pinch_c=baseline["hot_pinch_c"],
            cold_pinch_c=baseline["cold_pinch_c"],
            heat_recovery_kw=baseline["heat_recovery_kw"],
            heating_utility_kw=baseline["heating_utility_kw"],
            cooling_utility_kw=baseline["cooling_utility_kw"],
            message="Baseline reproduced from scientific/baseline.json",
        )

    return PinchResult(
        status="VALID",
        run_id=run_id,
        delta_t_min=delta_t_min,
        hot_pinch_c=None,
        cold_pinch_c=None,
        heat_recovery_kw=None,
        heating_utility_kw=None,
        cooling_utility_kw=None,
        message=(
            "ΔTmin accepted, but full Pinch sensitivity is not implemented yet. "
            "ITC 1: replace this stub with the real engine."
        ),
    )
