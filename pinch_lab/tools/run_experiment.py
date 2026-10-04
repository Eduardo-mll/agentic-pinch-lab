"""Unified experiment entry point for agents and Omnigent tools.

Scientific mode always uses the Pinch engine. A failure is returned as an
error. Simulation runs only when ``mode="simulation"``.
"""

from __future__ import annotations

import uuid
from typing import Any

from .fake_experiment import fake_experiment
from .science_bridge import run_science_experiment, science_available


def run_computational_experiment(
    delta_t_min: float,
    mode: str = "scientific",
) -> dict[str, Any]:
    """Run one experiment.

    ``scientific`` calls ``src.pinch_engine``. ``simulation`` calls
    ``fake_experiment`` only when requested.
    """
    if mode == "simulation":
        result = fake_experiment(delta_t_min=float(delta_t_min))
        result["engine"] = {
            "name": "fake_experiment",
            "mode": "simulation",
            "fallback_used": False,
        }
        return result

    if mode != "scientific":
        return _scientific_failure(
            delta_t_min,
            f"Unknown experiment mode: {mode}",
        )

    if not science_available():
        return _scientific_failure(
            delta_t_min,
            "Science engine unavailable. Ensure src/ and data/baseline.json are present.",
        )

    try:
        result = run_science_experiment(delta_t_min=float(delta_t_min))
    except Exception as error:  # noqa: BLE001 - report the failure, do not simulate
        return _scientific_failure(delta_t_min, f"Science engine failed: {error}")

    result["engine"] = {
        "name": "src.pinch_engine",
        "mode": "scientific",
        "fallback_used": False,
    }
    return result


def _scientific_failure(delta_t_min: float, message: str) -> dict[str, Any]:
    return {
        "status": "FAILED",
        "generated_by": "SCIENCE_PINCH_ENGINE",
        "run_id": f"RUN-{uuid.uuid4().hex[:8].upper()}",
        "delta_t_min": float(delta_t_min),
        "message": message,
        "heat_recovery_kw": None,
        "heating_utility_kw": None,
        "cooling_utility_kw": None,
        "hot_pinch_c": None,
        "cold_pinch_c": None,
        "energy": None,
        "network": None,
        "economics": None,
        "engine": {
            "name": "src.pinch_engine",
            "mode": "scientific",
            "fallback_used": False,
        },
    }
