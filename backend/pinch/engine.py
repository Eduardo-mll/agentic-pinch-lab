"""HTTP Pinch endpoint backed by the science engine in src/."""

from __future__ import annotations

import uuid

from src.experiment_runner import load_baseline
from src.paths import BASELINE_PATH
from src.pinch_engine import run_pinch_analysis as run_science_pinch

from .constraints import validate_delta_t_min
from .models import PinchResult


def run_pinch_analysis(delta_t_min: float = 10.0) -> PinchResult:
    """Validate the MVP range, then calculate with src.pinch_engine."""
    error = validate_delta_t_min(delta_t_min)
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    if error:
        return PinchResult(
            status="REJECTED",
            run_id=run_id,
            delta_t_min=delta_t_min,
            message=error,
        )

    streams, _baseline_dtmin = load_baseline(BASELINE_PATH)
    pinch = run_science_pinch(streams=streams, delta_t_min=float(delta_t_min))

    return PinchResult(
        status="VALID",
        run_id=run_id,
        delta_t_min=float(delta_t_min),
        hot_pinch_c=pinch.get("hot_pinch_c"),
        cold_pinch_c=pinch.get("cold_pinch_c"),
        heat_recovery_kw=float(pinch["maximum_heat_recovery_kw"]),
        heating_utility_kw=float(pinch["minimum_heating_kw"]),
        cooling_utility_kw=float(pinch["minimum_cooling_kw"]),
        message="Result from src.pinch_engine.",
    )
