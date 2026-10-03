from fastapi import FastAPI

from backend.pinch import run_pinch_analysis
from backend.pinch.models import PinchResult

app = FastAPI(
    title="Agentic Pinch Lab API",
    description="Deterministic Pinch Analysis backend for the hackathon MVP.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/pinch", response_model=PinchResult)
def pinch(delta_t_min: float = 10.0) -> PinchResult:
    """Simple HTTP wrapper around the Python Pinch engine."""
    return run_pinch_analysis(delta_t_min=delta_t_min)
