"""Reject locked process changes unless a scientist has approved them.

ΔTmin inside the approved range does not need an extra approval flag.
Stream identity and stream properties stay locked either way: this MVP
does not apply those edits.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.paths import ROOT

VARIABLES_PATH = ROOT / "scientific" / "variables.json"

LOCKED_PARAMETER_KEYS = {
    "streams",
    "stream_identity",
    "stream_id",
    "supply_temp",
    "supply_temp_c",
    "target_temp",
    "target_temp_c",
    "fcp",
    "fcp_kw_per_c",
    "h",
    "h_kw_per_m2c",
}


def load_delta_t_limits(path: Path = VARIABLES_PATH) -> tuple[float, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    controllable = data["controllable"][0]
    return float(controllable["min"]), float(controllable["max"])


def approval_error(parameters: dict | None) -> str | None:
    """Return a block message, or None when the request may run."""
    parameters = parameters or {}
    locked = sorted(key for key in parameters if key in LOCKED_PARAMETER_KEYS)
    if locked and parameters.get("human_approved") is not True:
        names = ", ".join(locked)
        return (
            "NEEDS_HUMAN_APPROVAL: "
            f"{names} are locked. A scientist must approve this change "
            "before it can run."
        )
    if locked:
        names = ", ".join(locked)
        return (
            "NEEDS_HUMAN_APPROVAL: approval was recorded, but this MVP "
            f"still cannot change {names}. Resubmit delta_t_min only."
        )

    if "delta_t_min" not in parameters:
        return None

    minimum, maximum = load_delta_t_limits()
    value = float(parameters["delta_t_min"])
    if value < minimum or value > maximum or value <= 0:
        return (
            "REJECTED: OUT_OF_RANGE "
            f"(allowed {minimum:g}-{maximum:g} C). "
            "Changing that range requires human approval."
        )
    return None
