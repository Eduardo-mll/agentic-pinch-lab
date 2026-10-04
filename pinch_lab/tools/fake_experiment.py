"""Temporary deterministic experiment tool for the agents branch.

Replace this with the real Pinch engine once science is merged:
    from backend.pinch import run_pinch_analysis
    # or friend's run_experiment(...)
"""

from __future__ import annotations

import uuid
from typing import Any


BASELINE = {
    "delta_t_min": 10.0,
    "heat_recovery_kw": 490.0,
    "heating_utility_kw": 100.0,
    "cooling_utility_kw": 95.0,
    "hot_pinch_c": 80.0,
    "cold_pinch_c": 70.0,
}


def fake_experiment(delta_t_min: float) -> dict[str, Any]:
    """Return a structured numeric result for a proposed ΔTmin.

    Simple stand-in model so agents can learn without the real Pinch engine:
    - lower ΔTmin → more recovery, less external utility
    - higher ΔTmin → less recovery, more external utility
    """
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    if delta_t_min <= 0 or delta_t_min < 5 or delta_t_min > 30:
        return {
            "status": "REJECTED",
            "generated_by": "FAKE_EXPERIMENT",
            "run_id": run_id,
            "delta_t_min": delta_t_min,
            "message": "REJECTED: OUT_OF_RANGE (allowed 5-30 C)",
            "heat_recovery_kw": None,
            "heating_utility_kw": None,
            "cooling_utility_kw": None,
            "hot_pinch_c": None,
            "cold_pinch_c": None,
        }

    # Linear sensitivity around the known baseline (NOT real Pinch physics).
    shift = BASELINE["delta_t_min"] - float(delta_t_min)
    heat_recovery = BASELINE["heat_recovery_kw"] + 2.0 * shift
    heating = max(0.0, BASELINE["heating_utility_kw"] - 1.5 * shift)
    cooling = max(0.0, BASELINE["cooling_utility_kw"] - 1.4 * shift)

    return {
        "status": "VALID",
        "generated_by": "FAKE_EXPERIMENT",
        "run_id": run_id,
        "delta_t_min": float(delta_t_min),
        "hot_pinch_c": BASELINE["hot_pinch_c"] + 0.5 * shift,
        "cold_pinch_c": BASELINE["cold_pinch_c"] + 0.5 * shift,
        "heat_recovery_kw": round(heat_recovery, 2),
        "heating_utility_kw": round(heating, 2),
        "cooling_utility_kw": round(cooling, 2),
        "message": (
            "Fake sensitivity result for agent-loop testing. "
            "Swap to real Pinch engine later."
        ),
    }
