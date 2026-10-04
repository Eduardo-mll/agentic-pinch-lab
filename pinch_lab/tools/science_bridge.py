"""Bridge from agents/API contracts to the science-branch Pinch engine.

Friend's code expects:
- package imports as ``src.*``
- baseline file at ``data/baseline.json``
- result keys like ``maximum_heat_recovery_kw`` / ``minimum_heating_kw``

Our agents/API expect:
- ``heat_recovery_kw`` / ``heating_utility_kw`` / ``cooling_utility_kw``
- nested ``energy`` / ``network`` / ``economics`` when area-cost model runs
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
    """Run Pinch targeting plus baseline HEN area/cost economics."""
    from src.experiment_runner import load_baseline
    from src.network_economics import evaluate_baseline_network_economics
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
            "energy": None,
            "network": None,
            "economics": None,
        }

    streams, _baseline_dtmin = load_baseline(BASELINE_PATH)
    pinch = run_pinch_analysis(streams=streams, delta_t_min=float(delta_t_min))

    heat_recovery = round(float(pinch["maximum_heat_recovery_kw"]), 4)
    heating = round(float(pinch["minimum_heating_kw"]), 4)
    cooling = round(float(pinch["minimum_cooling_kw"]), 4)

    network_payload = None
    economics_payload = None
    warnings: list[str] = []

    try:
        economics_result = evaluate_baseline_network_economics(
            streams=streams,
            hot_pinch=float(pinch["hot_pinch_c"]),
            cold_pinch=float(pinch["cold_pinch_c"]),
            delta_t_min=float(delta_t_min),
        )
        network_payload = {
            "total_area_m2": economics_result["total_area_m2"],
            "number_of_exchangers": economics_result["number_of_exchangers"],
            "process_heat_kw": round(
                float(economics_result["process_heat_kw"]), 4
            ),
            "topology": economics_result.get("topology"),
            "exchangers": economics_result["exchangers"],
        }
        economics_payload = economics_result["economics"]

        achieved = float(economics_result["process_heat_kw"])
        if abs(achieved - float(pinch["maximum_heat_recovery_kw"])) > 1.0:
            warnings.append(
                "Baseline HEN topology does not fully reach Pinch heat-recovery "
                f"target ({achieved:.2f} vs {float(pinch['maximum_heat_recovery_kw']):.2f} kW)."
            )
    except Exception as error:  # noqa: BLE001
        warnings.append(f"Network economics unavailable: {error}")

    message = (
        "Result from science-branch Pinch engine with baseline HEN area/cost model."
        if economics_payload is not None
        else "Result from science-branch Pinch engine (energy targeting only)."
    )
    if warnings:
        message = f"{message} {' '.join(warnings)}"

    return {
        "status": "VALID",
        "generated_by": "SCIENCE_PINCH_ENGINE",
        "run_id": run_id,
        "delta_t_min": float(delta_t_min),
        "hot_pinch_c": pinch.get("hot_pinch_c"),
        "cold_pinch_c": pinch.get("cold_pinch_c"),
        "heat_recovery_kw": heat_recovery,
        "heating_utility_kw": heating,
        "cooling_utility_kw": cooling,
        "energy": {
            "heat_recovery_kw": heat_recovery,
            "heating_kw": heating,
            "cooling_kw": cooling,
        },
        "network": network_payload,
        "economics": economics_payload,
        "warnings": warnings,
        "message": message,
        "raw_science_keys": {
            "maximum_heat_recovery_kw": pinch.get("maximum_heat_recovery_kw"),
            "minimum_heating_kw": pinch.get("minimum_heating_kw"),
            "minimum_cooling_kw": pinch.get("minimum_cooling_kw"),
            "shifted_pinch_c": pinch.get("shifted_pinch_c"),
        },
    }
