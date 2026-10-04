from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Stream:
    id: str
    type: Literal["hot", "cold"]
    supply_temp: float
    target_temp: float
    fcp: float
    h: float


@dataclass(frozen=True)
class ShiftedStream:
    id: str
    type: Literal["hot", "cold"]
    original_supply: float
    original_target: float
    shifted_supply: float
    shifted_target: float
    fcp: float
    h: float


@dataclass
class TemperatureInterval:
    upper_temp: float
    lower_temp: float
    delta_t: float

    hot_fcp: float = 0.0
    cold_fcp: float = 0.0
    delta_h: float = 0.0

    active_hot_streams: tuple[str, ...] = ()
    active_cold_streams: tuple[str, ...] = ()


@dataclass(frozen=True)
class Match:
    hot_stream: str
    cold_stream: str
    heat_duty: float
    region: Literal["above", "below"]