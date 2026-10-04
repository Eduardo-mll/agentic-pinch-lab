from dataclasses import asdict
from math import isclose

from src.models import (
    Stream,
    ShiftedStream,
    TemperatureInterval
)

from src.stream_calculations import (
    calculate_duty,
    shift_all_streams
)

from src.validators import (
    validate_stream,
    validate_delta_t_min,
    validate_energy_balance
)


def get_temperature_levels(
    shifted_streams: list[ShiftedStream]
) -> list[float]:

    temperatures: set[float] = set()

    for stream in shifted_streams:

        temperatures.add(
            stream.shifted_supply
        )

        temperatures.add(
            stream.shifted_target
        )

    levels = sorted(
        temperatures,
        reverse=True
    )

    if len(levels) < 2:
        raise ValueError(
            "At least two temperature levels "
            "are required."
        )

    return levels


def create_intervals(
    temperature_levels: list[float]
) -> list[TemperatureInterval]:

    intervals: list[
        TemperatureInterval
    ] = []

    for index in range(
        len(temperature_levels) - 1
    ):

        upper_temp = (
            temperature_levels[index]
        )

        lower_temp = (
            temperature_levels[
                index + 1
            ]
        )

        delta_t = (
            upper_temp - lower_temp
        )

        if delta_t <= 0:
            raise ValueError(
                "Temperature levels must be "
                "strictly descending."
            )

        intervals.append(
            TemperatureInterval(
                upper_temp=upper_temp,
                lower_temp=lower_temp,
                delta_t=delta_t
            )
        )

    return intervals


def is_stream_active(
    stream: ShiftedStream,
    upper_temp: float,
    lower_temp: float,
    tolerance: float = 1e-9
) -> bool:

    high_temp = max(
        stream.shifted_supply,
        stream.shifted_target
    )

    low_temp = min(
        stream.shifted_supply,
        stream.shifted_target
    )

    upper_is_inside = (
        upper_temp
        <= high_temp + tolerance
    )

    lower_is_inside = (
        lower_temp
        >= low_temp - tolerance
    )

    return (
        upper_is_inside
        and lower_is_inside
    )


def calculate_interval_balance(
    interval: TemperatureInterval,
    shifted_streams: list[ShiftedStream]
) -> TemperatureInterval:

    hot_fcp = 0.0
    cold_fcp = 0.0

    active_hot: list[str] = []
    active_cold: list[str] = []

    for stream in shifted_streams:

        active = is_stream_active(
            stream,
            interval.upper_temp,
            interval.lower_temp
        )

        if not active:
            continue

        if stream.type == "hot":

            hot_fcp += stream.fcp

            active_hot.append(
                stream.id
            )

        elif stream.type == "cold":

            cold_fcp += stream.fcp

            active_cold.append(
                stream.id
            )

    delta_h = (
        hot_fcp - cold_fcp
    ) * interval.delta_t

    interval.hot_fcp = hot_fcp
    interval.cold_fcp = cold_fcp
    interval.delta_h = delta_h

    interval.active_hot_streams = (
        tuple(active_hot)
    )

    interval.active_cold_streams = (
        tuple(active_cold)
    )

    return interval


def build_problem_table(
    shifted_streams: list[ShiftedStream]
) -> tuple[
    list[float],
    list[TemperatureInterval]
]:

    temperature_levels = (
        get_temperature_levels(
            shifted_streams
        )
    )

    intervals = create_intervals(
        temperature_levels
    )

    completed_intervals = [
        calculate_interval_balance(
            interval,
            shifted_streams
        )
        for interval in intervals
    ]

    return (
        temperature_levels,
        completed_intervals
    )


def run_heat_cascade(
    intervals: list[TemperatureInterval]
) -> dict:

    raw_cascade = [0.0]

    current_value = 0.0

    for interval in intervals:

        current_value += (
            interval.delta_h
        )

        if abs(current_value) < 1e-12:
            current_value = 0.0

        raw_cascade.append(
            current_value
        )

    minimum_raw_value = min(
        raw_cascade
    )

    minimum_heating_kw = max(
        0.0,
        -minimum_raw_value
    )

    adjusted_cascade = [
        minimum_heating_kw
    ]

    current_value = (
        minimum_heating_kw
    )

    for interval in intervals:

        current_value += (
            interval.delta_h
        )

        if abs(current_value) < 1e-12:
            current_value = 0.0

        adjusted_cascade.append(
            current_value
        )

    minimum_cooling_kw = (
        adjusted_cascade[-1]
    )

    if minimum_cooling_kw < -1e-9:
        raise RuntimeError(
            "Corrected heat cascade ended "
            "with negative cooling utility."
        )

    return {
        "raw_cascade":
            raw_cascade,

        "minimum_raw_value":
            minimum_raw_value,

        "minimum_heating_kw":
            minimum_heating_kw,

        "adjusted_cascade":
            adjusted_cascade,

        "minimum_cooling_kw":
            minimum_cooling_kw
    }


def find_pinch(
    temperature_levels: list[float],
    adjusted_cascade: list[float],
    delta_t_min: float,
    tolerance: float = 1e-7
) -> dict:

    if (
        len(temperature_levels)
        != len(adjusted_cascade)
    ):
        raise ValueError(
            "Temperature levels and cascade "
            "must have same length."
        )

    pinch_candidates: list[
        float
    ] = []

    for index, value in enumerate(
        adjusted_cascade
    ):

        if abs(value) <= tolerance:

            pinch_candidates.append(
                temperature_levels[index]
            )

    if len(pinch_candidates) == 0:
        raise RuntimeError(
            "No pinch point was found."
        )

    shifted_pinch = (
        pinch_candidates[0]
    )

    shift = delta_t_min / 2.0

    hot_pinch = (
        shifted_pinch + shift
    )

    cold_pinch = (
        shifted_pinch - shift
    )

    return {
        "shifted_pinch_c":
            shifted_pinch,

        "hot_pinch_c":
            hot_pinch,

        "cold_pinch_c":
            cold_pinch,

        "all_shifted_candidates_c":
            pinch_candidates
    }


def calculate_heat_recovery(
    streams: list[Stream],
    minimum_heating_kw: float,
    minimum_cooling_kw: float
) -> dict:

    total_hot_kw = sum(
        calculate_duty(stream)
        for stream in streams
        if stream.type == "hot"
    )

    total_cold_kw = sum(
        calculate_duty(stream)
        for stream in streams
        if stream.type == "cold"
    )

    recovery_from_hot = (
        total_hot_kw
        - minimum_cooling_kw
    )

    recovery_from_cold = (
        total_cold_kw
        - minimum_heating_kw
    )

    if not isclose(
        recovery_from_hot,
        recovery_from_cold,
        abs_tol=1e-6
    ):
        raise RuntimeError(
            "Heat recovery does not match "
            "from hot and cold sides."
        )

    maximum_recovery = (
        recovery_from_hot
        + recovery_from_cold
    ) / 2.0

    return {
        "total_hot_duty_kw":
            total_hot_kw,

        "total_cold_duty_kw":
            total_cold_kw,

        "maximum_heat_recovery_kw":
            maximum_recovery
    }


def run_pinch_analysis(
    streams: list[Stream],
    delta_t_min: float
) -> dict:

    validate_delta_t_min(
        delta_t_min
    )

    for stream in streams:
        validate_stream(stream)

    shifted_streams = (
        shift_all_streams(
            streams,
            delta_t_min
        )
    )

    (
        temperature_levels,
        intervals
    ) = build_problem_table(
        shifted_streams
    )

    cascade = run_heat_cascade(
        intervals
    )

    pinch = find_pinch(
        temperature_levels,
        cascade["adjusted_cascade"],
        delta_t_min
    )

    recovery = (
        calculate_heat_recovery(
            streams,
            cascade[
                "minimum_heating_kw"
            ],
            cascade[
                "minimum_cooling_kw"
            ]
        )
    )

    validate_energy_balance(
        total_hot_kw=recovery[
            "total_hot_duty_kw"
        ],
        total_cold_kw=recovery[
            "total_cold_duty_kw"
        ],
        heating_kw=cascade[
            "minimum_heating_kw"
        ],
        cooling_kw=cascade[
            "minimum_cooling_kw"
        ]
    )

    return {
        "delta_t_min_c":
            delta_t_min,

        "hot_pinch_c":
            pinch["hot_pinch_c"],

        "cold_pinch_c":
            pinch["cold_pinch_c"],

        "shifted_pinch_c":
            pinch["shifted_pinch_c"],

        "minimum_heating_kw":
            cascade[
                "minimum_heating_kw"
            ],

        "minimum_cooling_kw":
            cascade[
                "minimum_cooling_kw"
            ],

        "maximum_heat_recovery_kw":
            recovery[
                "maximum_heat_recovery_kw"
            ],

        "total_hot_duty_kw":
            recovery[
                "total_hot_duty_kw"
            ],

        "total_cold_duty_kw":
            recovery[
                "total_cold_duty_kw"
            ],

        "temperature_levels_c":
            temperature_levels,

        "problem_table": [
            asdict(interval)
            for interval in intervals
        ],

        "raw_cascade":
            cascade["raw_cascade"],

        "adjusted_cascade":
            cascade[
                "adjusted_cascade"
            ]
    }