from src.models import (
    Stream,
    Match
)

from src.stream_calculations import (
    calculate_duty
)

from src.validators import (
    validate_match,
    validate_temperature_approach
)


def calculate_outlet_temperature(
    stream: Stream,
    inlet_temperature: float,
    heat_duty: float
) -> float:

    if heat_duty < 0:
        raise ValueError(
            "Heat duty cannot be negative."
        )

    delta_t = (
        heat_duty / stream.fcp
    )

    if stream.type == "hot":

        return (
            inlet_temperature
            - delta_t
        )

    if stream.type == "cold":

        return (
            inlet_temperature
            + delta_t
        )

    raise ValueError(
        "Unknown stream type."
    )


def calculate_match_duty(
    hot_stream: Stream,
    cold_stream: Stream,
    hot_in_temp: float,
    cold_in_temp: float,
    hot_limit_temp: float,
    cold_limit_temp: float
) -> float:
    """
    Calcula el máximo Q posible según
    la energía aún disponible de ambos lados.
    """

    hot_available = max(
        0.0,
        (
            hot_in_temp
            - hot_limit_temp
        )
        * hot_stream.fcp
    )

    cold_required = max(
        0.0,
        (
            cold_limit_temp
            - cold_in_temp
        )
        * cold_stream.fcp
    )

    return min(
        hot_available,
        cold_required
    )


def evaluate_network(
    streams: list[Stream],
    matches: list[Match],
    hot_pinch: float,
    cold_pinch: float,
    delta_t_min: float
) -> dict:

    streams_by_id = {
        stream.id: stream
        for stream in streams
    }

    for match in matches:
        validate_match(
            match,
            streams_by_id
        )

    state: dict = {
        "above": {},
        "below": {}
    }

    for stream in streams:

        if stream.type == "hot":

            if (
                stream.supply_temp
                > hot_pinch
            ):
                state["above"][
                    stream.id
                ] = {
                    "current_temp":
                        stream.supply_temp,

                    "limit_temp":
                        hot_pinch
                }

            if (
                stream.target_temp
                < hot_pinch
            ):
                state["below"][
                    stream.id
                ] = {
                    "current_temp":
                        hot_pinch,

                    "limit_temp":
                        stream.target_temp
                }

        elif stream.type == "cold":

            if (
                stream.target_temp
                > cold_pinch
            ):
                state["above"][
                    stream.id
                ] = {
                    "current_temp":
                        cold_pinch,

                    "limit_temp":
                        stream.target_temp
                }

            if (
                stream.supply_temp
                < cold_pinch
            ):
                state["below"][
                    stream.id
                ] = {
                    "current_temp":
                        stream.supply_temp,

                    "limit_temp":
                        cold_pinch
                }

    match_results = []

    total_process_heat = 0.0

    for match in matches:

        region = match.region

        hot_stream = streams_by_id[
            match.hot_stream
        ]

        cold_stream = streams_by_id[
            match.cold_stream
        ]

        if (
            hot_stream.id
            not in state[region]
        ):
            raise ValueError(
                f"{hot_stream.id} has no "
                f"{region}-pinch segment."
            )

        if (
            cold_stream.id
            not in state[region]
        ):
            raise ValueError(
                f"{cold_stream.id} has no "
                f"{region}-pinch segment."
            )

        hot_state = state[region][
            hot_stream.id
        ]

        cold_state = state[region][
            cold_stream.id
        ]

        hot_in = hot_state[
            "current_temp"
        ]

        cold_in = cold_state[
            "current_temp"
        ]

        maximum_q = (
            calculate_match_duty(
                hot_stream,
                cold_stream,
                hot_in,
                cold_in,
                hot_state[
                    "limit_temp"
                ],
                cold_state[
                    "limit_temp"
                ]
            )
        )

        if (
            match.heat_duty
            > maximum_q + 1e-9
        ):
            raise ValueError(
                f"Match "
                f"{match.hot_stream}-"
                f"{match.cold_stream} "
                f"requests "
                f"{match.heat_duty} kW, "
                f"but maximum feasible duty "
                f"is {maximum_q} kW."
            )

        hot_out = (
            calculate_outlet_temperature(
                hot_stream,
                hot_in,
                match.heat_duty
            )
        )

        cold_out = (
            calculate_outlet_temperature(
                cold_stream,
                cold_in,
                match.heat_duty
            )
        )

        validate_temperature_approach(
            hot_in=hot_in,
            hot_out=hot_out,
            cold_in=cold_in,
            cold_out=cold_out,
            delta_t_min=delta_t_min
        )

        hot_state[
            "current_temp"
        ] = hot_out

        cold_state[
            "current_temp"
        ] = cold_out

        total_process_heat += (
            match.heat_duty
        )

        match_results.append(
            {
                "hot_stream":
                    match.hot_stream,

                "cold_stream":
                    match.cold_stream,

                "region":
                    match.region,

                "heat_duty_kw":
                    match.heat_duty,

                "hot_in_c":
                    hot_in,

                "hot_out_c":
                    hot_out,

                "cold_in_c":
                    cold_in,

                "cold_out_c":
                    cold_out
            }
        )

    total_hot_duty = sum(
        calculate_duty(stream)
        for stream in streams
        if stream.type == "hot"
    )

    total_cold_duty = sum(
        calculate_duty(stream)
        for stream in streams
        if stream.type == "cold"
    )

    cooling_required = (
        total_hot_duty
        - total_process_heat
    )

    heating_required = (
        total_cold_duty
        - total_process_heat
    )

    return {
        "valid": True,

        "process_heat_kw":
            total_process_heat,

        "heating_required_kw":
            heating_required,

        "cooling_required_kw":
            cooling_required,

        "matches":
            match_results,

        "state":
            state
    }