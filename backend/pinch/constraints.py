from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
VARIABLES_PATH = ROOT / "scientific" / "variables.json"


def load_delta_t_limits() -> tuple[float, float]:
    data = json.loads(VARIABLES_PATH.read_text(encoding="utf-8"))
    controllable = data["controllable"][0]
    return float(controllable["min"]), float(controllable["max"])


def validate_delta_t_min(delta_t_min: float) -> str | None:
    """Return an error message if invalid, otherwise None."""
    if delta_t_min <= 0:
        return "REJECTED: OUT_OF_RANGE (delta_t_min must be > 0)"

    min_v, max_v = load_delta_t_limits()
    if delta_t_min < min_v or delta_t_min > max_v:
        return f"REJECTED: OUT_OF_RANGE (allowed {min_v}–{max_v} °C)"

    return None
