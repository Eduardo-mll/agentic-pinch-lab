# Omnigent (agents branch)

## MVP agents (current slice)

1. **Hypothesis Agent** — forms / refines a falsifiable idea
2. **Experiment Planner** — proposes a `delta_t_min` experiment
3. **Scientific Analyst** — interprets the result and chooses the next experiment

Evidence Agent comes next (local cache first; BrightData later).

## HTTP API (for frontend)

With the API running:

```bash
uvicorn backend.main:app --reload
```

- `POST /discovery/run` — run the loop (`{"steps": 2}`)
- `GET /discovery/history` — experiment index
- `GET /discovery/latest` — newest saved record
- `GET /health`
- `GET /pinch?delta_t_min=10`

## Run the local discovery loop

From the repo root (venv active):

```bash
python -m omnigent.run_discovery_loop
```

This uses a **fake experiment tool** on purpose so agents work can proceed
before the science branch is merged.

Expected proof:

```text
Experiment #1 ΔTmin = 7.5
Experiment #2 ΔTmin = <different value chosen from result #1>
OK: experiment #2 differs because of result #1.
```

Results are written to:

- `results/runs/RUN-XXXX.json`
- `results/experiments.json`

## Important

- Do **not** edit `backend/pinch/` from this branch
- Later swap `omnigent/tools/fake_experiment.py` for the real Pinch engine
- Current Planner/Analyst are rule-based stubs; Omnigent + Claude can replace them later without changing the JSON contracts
