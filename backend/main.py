from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as discovery_router
from backend.pinch import run_pinch_analysis
from backend.pinch.models import PinchResult

app = FastAPI(
    title="Agentic Pinch Lab API",
    description="Discovery loop + Pinch Analysis backend for the hackathon MVP.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discovery_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/pinch", response_model=PinchResult)
def pinch(delta_t_min: float = 10.0) -> PinchResult:
    """Simple HTTP wrapper around the Python Pinch engine."""
    return run_pinch_analysis(delta_t_min=delta_t_min)
