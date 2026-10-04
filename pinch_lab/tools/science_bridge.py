"""Bridge from agents/API contracts to the science-branch Pinch engine.

Friend's code expects:
- package imports as ``src.*``
- baseline file at ``data/baseline.json``
- result keys like ``maximum_heat_recovery_kw`` / ``minimum_heating_kw``

Our agents/API expect:
- ``heat_recovery_kw`` / ``heating_utility_kw`` / ``cooling_utility_kw``
"""

from __future__ import annotations

import uuid
from typing import Any

from src.paths import BASELINE_PATH


def science_available() -> bool:
    try:
        from src.pinch_engine import run_pinch_analysis  # noqa: F401
        from src.experiment_runner import load_baseline  # noqa: F401

        return BASELINE_PATH.exists()
    except Exception:
        return False


def run_science_experiment(delta_t_min: float) -> dict[str, Any]:
    """Run the real Pinch engine and map into the agents result contract."""
    from src.experiment_runner import load_baseline
    from src.pinch_engine import run_pinch_analysis

    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    # MVP scientific policy (agents side). Friend's validator only checks > 0.
    if delta_t_min <= 0 or delta_t_min < 5 or delta_t_min > 30:
        return {
            "status": "REJECTED",
            "generated_by": "SCIENCE_PINCH_ENGINE",
            "run_id": run_id,
            "delta_t_min": float(delta_t_min),
            "message": "REJECTED: OUT_OF_RANGE (allowed 5-30 C)",
            "heat_recovery_kw": None,
            "heating_utility_kw": None,
            "cooling_utility_kw": None,
            "hot_pinch_c": None,
            "cold_pinch_c": None,
        }

    streams, _baseline_dtmin = load_baseline(BASELINE_PATH)
    pinch = run_pinch_analysis(streams=streams, delta_t_min=float(delta_t_min))

    return {
        "status": "VALID",
        "generated_by": "SCIENCE_PINCH_ENGINE",
        "run_id": run_id,
        "delta_t_min": float(delta_t_min),
        "hot_pinch_c": pinch.get("hot_pinch_c"),
        "cold_pinch_c": pinch.get("cold_pinch_c"),
        "heat_recovery_kw": round(float(pinch["maximum_heat_recovery_kw"]), 4),
        "heating_utility_kw": round(float(pinch["minimum_heating_kw"]), 4),
        "cooling_utility_kw": round(float(pinch["minimum_cooling_kw"]), 4),
        "message": "Result from science-branch Pinch engine (src.pinch_engine).",
        "raw_science_keys": {
            "maximum_heat_recovery_kw": pinch.get("maximum_heat_recovery_kw"),
            "minimum_heating_kw": pinch.get("minimum_heating_kw"),
            "minimum_cooling_kw": pinch.get("minimum_cooling_kw"),
            "shifted_pinch_c": pinch.get("shifted_pinch_c"),
        },
    }
