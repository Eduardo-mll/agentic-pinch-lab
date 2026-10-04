"""Unified experiment entry point for agents and Omnigent tools."""

from __future__ import annotations

from typing import Any

from .fake_experiment import fake_experiment
from .science_bridge import run_science_experiment, science_available


def run_computational_experiment(delta_t_min: float) -> dict[str, Any]:
    """Prefer the real science engine; fall back to fake sensitivity model."""
    if science_available():
        try:
            return run_science_experiment(delta_t_min=float(delta_t_min))
        except Exception as error:  # noqa: BLE001 - keep agents loop alive
            fallback = fake_experiment(delta_t_min=float(delta_t_min))
            fallback["message"] = (
                f"Science engine failed ({error}); used FAKE_EXPERIMENT fallback."
            )
            fallback["science_error"] = str(error)
            return fallback

    result = fake_experiment(delta_t_min=float(delta_t_min))
    result["message"] = (
        "Science engine unavailable; used FAKE_EXPERIMENT. "
        "Ensure src/ and data/baseline.json are present."
    )
    return result
