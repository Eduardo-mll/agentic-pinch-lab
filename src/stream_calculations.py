from typing import Iterable

from src.models import Stream, ShiftedStream


def calculate_duty(stream: Stream) -> float:

    delta_t = abs(
        stream.supply_temp
        - stream.target_temp
    )

    return stream.fcp * delta_t


def shift_stream_temperature(
    stream: Stream,
    delta_t_min: float
) -> ShiftedStream:

    shift = delta_t_min / 2.0

    if stream.type == "hot":

        shifted_supply = (
            stream.supply_temp - shift
        )

        shifted_target = (
            stream.target_temp - shift
        )

    elif stream.type == "cold":

        shifted_supply = (
            stream.supply_temp + shift
        )

        shifted_target = (
            stream.target_temp + shift
        )

    else:
        raise ValueError(
            f"Unknown stream type: {stream.type}"
        )

    return ShiftedStream(
        id=stream.id,
        type=stream.type,
        original_supply=stream.supply_temp,
        original_target=stream.target_temp,
        shifted_supply=shifted_supply,
        shifted_target=shifted_target,
        fcp=stream.fcp,
        h=stream.h
    )


def shift_all_streams(
    streams: Iterable[Stream],
    delta_t_min: float
) -> list[ShiftedStream]:

    return [
        shift_stream_temperature(
            stream,
            delta_t_min
        )
        for stream in streams
    ]