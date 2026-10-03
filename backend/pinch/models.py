from pydantic import BaseModel, Field


class PinchResult(BaseModel):
    status: str = Field(description="VALID or REJECTED")
    run_id: str
    delta_t_min: float
    hot_pinch_c: float | None = None
    cold_pinch_c: float | None = None
    heat_recovery_kw: float | None = None
    heating_utility_kw: float | None = None
    cooling_utility_kw: float | None = None
    message: str | None = None
