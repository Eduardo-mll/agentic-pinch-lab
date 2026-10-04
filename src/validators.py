from math import isclose

from src.models import Stream, Match


def validate_stream(
    stream: Stream
) -> None:

    if stream.fcp <= 0:
        raise ValueError(
            f"{stream.id}: FCp must be positive."
        )

    if stream.h <= 0:
        raise ValueError(
            f"{stream.id}: h must be positive."
        )

    if stream.type == "hot":

        if (
            stream.supply_temp
            <= stream.target_temp
        ):
            raise ValueError(
                f"{stream.id}: hot stream must "
                "cool down."
            )

    elif stream.type == "cold":

        if (
            stream.supply_temp
            >= stream.target_temp
        ):
            raise ValueError(
                f"{stream.id}: cold stream must "
                "heat up."
            )

    else:
        raise ValueError(
            f"{stream.id}: unknown stream type."
        )


def validate_delta_t_min(
    delta_t_min: float
) -> None:

    if delta_t_min <= 0:
        raise ValueError(
            "Delta Tmin must be greater than zero."
        )


def validate_energy_balance(
    total_hot_kw: float,
    total_cold_kw: float,
    heating_kw: float,
    cooling_kw: float,
    tolerance: float = 1e-6
) -> None:

    left_side = (
        total_hot_kw + heating_kw
    )

    right_side = (
        total_cold_kw + cooling_kw
    )

    if not isclose(
        left_side,
        right_side,
        abs_tol=tolerance
    ):
        raise ValueError(
            "Global energy balance does not close. "
            f"Hot + heating = {left_side}; "
            f"cold + cooling = {right_side}."
        )


def validate_pinch_rule(
    hot_stream: Stream,
    cold_stream: Stream,
    region: str
) -> None:


    if region == "above":

        if (
            cold_stream.fcp
            < hot_stream.fcp
        ):
            raise ValueError(
                "Above pinch rule violated: "
                "FCp_cold must be >= FCp_hot."
            )

    elif region == "below":

        if (
            hot_stream.fcp
            < cold_stream.fcp
        ):
            raise ValueError(
                "Below pinch rule violated: "
                "FCp_hot must be >= FCp_cold."
            )

    else:
        raise ValueError(
            "Region must be 'above' or 'below'."
        )


def validate_temperature_approach(
    hot_in: float,
    hot_out: float,
    cold_in: float,
    cold_out: float,
    delta_t_min: float
) -> None:

    delta_t_1 = (
        hot_in - cold_out
    )

    delta_t_2 = (
        hot_out - cold_in
    )

    if delta_t_1 < delta_t_min - 1e-9:
        raise ValueError(
            "Minimum temperature approach violated "
            f"at end 1: {delta_t_1:.4f} °C."
        )

    if delta_t_2 < delta_t_min - 1e-9:
        raise ValueError(
            "Minimum temperature approach violated "
            f"at end 2: {delta_t_2:.4f} °C."
        )


def validate_match(
    match: Match,
    streams_by_id: dict[str, Stream]
) -> None:

    if match.heat_duty <= 0:
        raise ValueError(
            "Heat duty must be greater than zero."
        )

    if (
        match.hot_stream
        not in streams_by_id
    ):
        raise ValueError(
            f"Unknown hot stream: "
            f"{match.hot_stream}"
        )

    if (
        match.cold_stream
        not in streams_by_id
    ):
        raise ValueError(
            f"Unknown cold stream: "
            f"{match.cold_stream}"
        )

    hot = streams_by_id[
        match.hot_stream
    ]

    cold = streams_by_id[
        match.cold_stream
    ]

    if hot.type != "hot":
        raise ValueError(
            f"{hot.id} is not a hot stream."
        )

    if cold.type != "cold":
        raise ValueError(
            f"{cold.id} is not a cold stream."
        )

    validate_pinch_rule(
        hot,
        cold,
        match.region
    )