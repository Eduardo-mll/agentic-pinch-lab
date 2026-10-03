"""Small deterministic helpers. Keep physics here — not in the LLM."""


def heat_load_kw(fcp_kw_per_c: float, supply_temp_c: float, target_temp_c: float) -> float:
    """Q = FCp * |ΔT| for a single stream duty."""
    return abs(fcp_kw_per_c * (supply_temp_c - target_temp_c))
