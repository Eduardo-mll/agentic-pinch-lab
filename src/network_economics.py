"""Wire U / LMTD / area / cost onto an evaluated HEN."""

from __future__ import annotations

import json
from pathlib import Path

from src.economics import (
    calculate_area,
    calculate_exchanger_cost,
    calculate_lmtd,
    calculate_total_network_cost,
    calculate_u,
)
from src.models import Match, Stream
from src.network_engine import (
    calculate_match_duty,
    calculate_outlet_temperature,
    evaluate_network,
)
from src.paths import BASELINE_NETWORK_PATH
from src.validators import validate_temperature_approach


def load_baseline_network(
    path: Path = BASELINE_NETWORK_PATH,
) -> tuple[list[Match], dict]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    matches = [
        Match(
            hot_stream=item["hot_stream"],
            cold_stream=item["cold_stream"],
            heat_duty=float(item["heat_duty"]),
            region=item["region"],
        )
        for item in data["matches"]
    ]
    return matches, data["utilities"]


def _max_feasible_duty(
    hot: Stream,
    cold: Stream,
    hot_in: float,
    cold_in: float,
    hot_limit: float,
    cold_limit: float,
    delta_t_min: float,
) -> float:
    max_q = calculate_match_duty(
        hot,
        cold,
        hot_in,
        cold_in,
        hot_limit,
        cold_limit,
    )
    if max_q <= 1e-12:
        return 0.0

    lo = 0.0
    hi = max_q
    best = 0.0
    for _ in range(48):
        mid = (lo + hi) / 2.0
        if mid <= 1e-12:
            break
        hot_out = calculate_outlet_temperature(hot, hot_in, mid)
        cold_out = calculate_outlet_temperature(cold, cold_in, mid)
        try:
            validate_temperature_approach(
                hot_in=hot_in,
                hot_out=hot_out,
                cold_in=cold_in,
                cold_out=cold_out,
                delta_t_min=delta_t_min,
            )
            best = mid
            lo = mid
        except ValueError:
            hi = mid
    return best


def adapt_matches_to_delta_t_min(
    streams: list[Stream],
    template_matches: list[Match],
    hot_pinch: float,
    cold_pinch: float,
    delta_t_min: float,
) -> list[Match]:
    """Keep stream-pair order; take the largest ΔTmin-feasible duty each step."""
    empty = evaluate_network(
        streams=streams,
        matches=[],
        hot_pinch=hot_pinch,
        cold_pinch=cold_pinch,
        delta_t_min=delta_t_min,
    )
    state = empty["state"]
    by_id = {stream.id: stream for stream in streams}
    adapted: list[Match] = []

    for match in template_matches:
        hot = by_id[match.hot_stream]
        cold = by_id[match.cold_stream]
        hot_state = state[match.region][match.hot_stream]
        cold_state = state[match.region][match.cold_stream]
        hot_in = hot_state["current_temp"]
        cold_in = cold_state["current_temp"]

        duty = _max_feasible_duty(
            hot,
            cold,
            hot_in,
            cold_in,
            hot_state["limit_temp"],
            cold_state["limit_temp"],
            delta_t_min,
        )
        if duty <= 1e-9:
            continue

        hot_out = calculate_outlet_temperature(hot, hot_in, duty)
        cold_out = calculate_outlet_temperature(cold, cold_in, duty)
        hot_state["current_temp"] = hot_out
        cold_state["current_temp"] = cold_out

        adapted.append(
            Match(
                hot_stream=match.hot_stream,
                cold_stream=match.cold_stream,
                heat_duty=duty,
                region=match.region,
            )
        )

    return adapted


def _exchanger_record(
    *,
    name: str,
    equipment_type: str,
    heat_duty_kw: float,
    u_kw_m2_c: float,
    lmtd_c: float,
    area_m2: float,
    cost_per_year: float,
    hot_in_c: float,
    hot_out_c: float,
    cold_in_c: float,
    cold_out_c: float,
) -> dict:
    return {
        "name": name,
        "equipment_type": equipment_type,
        "heat_duty_kw": round(heat_duty_kw, 6),
        "u_kw_m2_c": round(u_kw_m2_c, 6),
        "lmtd_c": round(lmtd_c, 6),
        "area_m2": round(area_m2, 6),
        "cost_per_year": round(cost_per_year, 4),
        "hot_in_c": round(hot_in_c, 6),
        "hot_out_c": round(hot_out_c, 6),
        "cold_in_c": round(cold_in_c, 6),
        "cold_out_c": round(cold_out_c, 6),
    }


def evaluate_network_economics(
    streams: list[Stream],
    matches: list[Match],
    hot_pinch: float,
    cold_pinch: float,
    delta_t_min: float,
    *,
    hot_utility_temp_c: float,
    hot_utility_h: float,
    cold_utility_temp_c: float,
    cold_utility_h: float,
) -> dict:
    network = evaluate_network(
        streams=streams,
        matches=matches,
        hot_pinch=hot_pinch,
        cold_pinch=cold_pinch,
        delta_t_min=delta_t_min,
    )
    by_id = {stream.id: stream for stream in streams}
    exchangers: list[dict] = []
    equipment_costs: list[float] = []

    for match in network["matches"]:
        hot = by_id[match["hot_stream"]]
        cold = by_id[match["cold_stream"]]
        u = calculate_u(hot.h, cold.h)
        delta_t_1 = match["hot_in_c"] - match["cold_out_c"]
        delta_t_2 = match["hot_out_c"] - match["cold_in_c"]
        lmtd = calculate_lmtd(delta_t_1, delta_t_2)
        area = calculate_area(
            heat_duty_kw=match["heat_duty_kw"],
            u_kw_m2_c=u,
            lmtd_c=lmtd,
        )
        cost = calculate_exchanger_cost(area_m2=area, equipment_type="process")
        equipment_costs.append(cost)
        exchangers.append(
            _exchanger_record(
                name=f"{match['hot_stream']}-{match['cold_stream']}",
                equipment_type="process",
                heat_duty_kw=match["heat_duty_kw"],
                u_kw_m2_c=u,
                lmtd_c=lmtd,
                area_m2=area,
                cost_per_year=cost,
                hot_in_c=match["hot_in_c"],
                hot_out_c=match["hot_out_c"],
                cold_in_c=match["cold_in_c"],
                cold_out_c=match["cold_out_c"],
            )
        )

    for region in ("above", "below"):
        for stream_id, segment in network["state"][region].items():
            stream = by_id[stream_id]
            current = segment["current_temp"]
            limit = segment["limit_temp"]

            if stream.type == "cold" and current < limit - 1e-9:
                duty = (limit - current) * stream.fcp
                u = calculate_u(hot_utility_h, stream.h)
                lmtd = calculate_lmtd(
                    hot_utility_temp_c - limit,
                    hot_utility_temp_c - current,
                )
                area = calculate_area(duty, u, lmtd)
                cost = calculate_exchanger_cost(area, "heater")
                equipment_costs.append(cost)
                exchangers.append(
                    _exchanger_record(
                        name=f"heater-{stream_id}",
                        equipment_type="heater",
                        heat_duty_kw=duty,
                        u_kw_m2_c=u,
                        lmtd_c=lmtd,
                        area_m2=area,
                        cost_per_year=cost,
                        hot_in_c=hot_utility_temp_c,
                        hot_out_c=hot_utility_temp_c,
                        cold_in_c=current,
                        cold_out_c=limit,
                    )
                )

            if stream.type == "hot" and current > limit + 1e-9:
                duty = (current - limit) * stream.fcp
                u = calculate_u(stream.h, cold_utility_h)
                lmtd = calculate_lmtd(
                    current - cold_utility_temp_c,
                    limit - cold_utility_temp_c,
                )
                area = calculate_area(duty, u, lmtd)
                cost = calculate_exchanger_cost(area, "cooler")
                equipment_costs.append(cost)
                exchangers.append(
                    _exchanger_record(
                        name=f"cooler-{stream_id}",
                        equipment_type="cooler",
                        heat_duty_kw=duty,
                        u_kw_m2_c=u,
                        lmtd_c=lmtd,
                        area_m2=area,
                        cost_per_year=cost,
                        hot_in_c=current,
                        hot_out_c=limit,
                        cold_in_c=cold_utility_temp_c,
                        cold_out_c=cold_utility_temp_c,
                    )
                )

    economics = calculate_total_network_cost(
        equipment_costs=equipment_costs,
        cooling_kw=network["cooling_required_kw"],
        heating_kw=network["heating_required_kw"],
    )
    total_area = sum(item["area_m2"] for item in exchangers)

    return {
        "valid": True,
        "process_heat_kw": network["process_heat_kw"],
        "heating_required_kw": network["heating_required_kw"],
        "cooling_required_kw": network["cooling_required_kw"],
        "number_of_exchangers": len(exchangers),
        "total_area_m2": round(total_area, 6),
        "exchangers": exchangers,
        "economics": {
            "equipment_cost_per_year": round(
                economics["equipment_cost_per_year"], 4
            ),
            "utility_cost_per_year": round(
                economics["utility_cost_per_year"], 4
            ),
            "total_cost_per_year": round(
                economics["total_cost_per_year"], 4
            ),
            "network_heating_kw": round(float(network["heating_required_kw"]), 4),
            "network_cooling_kw": round(float(network["cooling_required_kw"]), 4),
        },
    }


def evaluate_baseline_network_economics(
    streams: list[Stream],
    hot_pinch: float,
    cold_pinch: float,
    delta_t_min: float,
    network_path: Path = BASELINE_NETWORK_PATH,
) -> dict:
    template_matches, utilities = load_baseline_network(network_path)
    adapted = adapt_matches_to_delta_t_min(
        streams=streams,
        template_matches=template_matches,
        hot_pinch=hot_pinch,
        cold_pinch=cold_pinch,
        delta_t_min=delta_t_min,
    )
    result = evaluate_network_economics(
        streams=streams,
        matches=adapted,
        hot_pinch=hot_pinch,
        cold_pinch=cold_pinch,
        delta_t_min=delta_t_min,
        hot_utility_temp_c=float(utilities["hot_utility_temp_c"]),
        hot_utility_h=float(utilities["hot_utility_h"]),
        cold_utility_temp_c=float(utilities["cold_utility_temp_c"]),
        cold_utility_h=float(utilities["cold_utility_h"]),
    )
    result["topology"] = "baseline_greedy"
    result["match_count_process"] = len(adapted)
    return result
