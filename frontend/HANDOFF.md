# Frontend handoff — Agentic Pinch Lab

This is what the frontend should use from the agents/API track.

## Branch / ownership

| You own | Do not edit |
|---|---|
| `frontend/` | `omnigent/`, `backend/pinch/`, `scientific/` |

Work on branch **`frontend`**.  
API glue lives on **`agents`**. Integration branch is **`master`**.

## Product goal (not a chatbot)

Show the scientific loop clearly:

1. Evidence  
2. Hypothesis  
3. Experiment  
4. Result  
5. Learning  
6. Next decision  

Judges must see that **experiment #2 changed because of result #1**.

## Baseline to display

| Metric | Value |
|---|---:|
| delta_t_min | 10 C |
| Hot Pinch | 80 C |
| Cold Pinch | 70 C |
| Heat recovery | 490 kW |
| Heating utility | 100 kW |
| Cooling utility | 95 kW |

## How to run the API (local)

Ask the agents teammate to run, or run yourself from repo root:

```powershell
cd C:\Users\troni\Desktop\Hackaton\agentic-pinch-lab
.\.venv\Scripts\activate
uvicorn backend.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

CORS is open (`*`) for local hackathon use.

## Endpoints you should use

### 1) Run the discovery loop (main button)

`POST http://127.0.0.1:8000/discovery/run`

Body:

```json
{ "steps": 2 }
```

Returns:

- `experiments`: array of full experiment records
- `agentic_proof.second_changed`: should be `true`

### 2) Latest saved experiment

`GET http://127.0.0.1:8000/discovery/latest`

### 3) History index

`GET http://127.0.0.1:8000/discovery/history`

### 4) Evidence list

`GET http://127.0.0.1:8000/evidence`

Use this to render the Evidence section (`evidence_id`, title, claim, confidence).

### 5) Optional Pinch endpoint

`GET http://127.0.0.1:8000/pinch?delta_t_min=10`

## Experiment record shape (render this)

Each item in `experiments[]` looks like:

```json
{
  "run_id": "RUN-19A79FA8",
  "timestamp": "2026-10-04T01:34:57.388460+00:00",
  "question": "Can lowering delta_t_min reduce external utility demand while respecting Pinch Analysis constraints?",
  "evidence_ids": [],
  "hypothesis": {
    "id": "HYP-001",
    "text": "Reducing delta_t_min from 10 C toward lower values may increase heat recovery and reduce external utility demand.",
    "status": "TESTED",
    "expected_effect": "reduce_external_utility",
    "direction": "decrease_delta_t_min"
  },
  "experiment": {
    "experiment_id": "EXP-001",
    "variable": "delta_t_min",
    "baseline_value": 10.0,
    "proposed_value": 7.5,
    "expected_effect": "reduce_external_utility",
    "reason": "First test: lower delta_t_min below baseline..."
  },
  "validation": { "status": "PASS" },
  "result": {
    "generated_by": "FAKE_EXPERIMENT",
    "status": "VALID",
    "delta_t_min": 7.5,
    "heat_recovery_kw": 495.0,
    "heating_utility_kw": 96.25,
    "cooling_utility_kw": 91.5,
    "hot_pinch_c": 81.25,
    "cold_pinch_c": 71.25,
    "message": "Fake sensitivity result for agent-loop testing..."
  },
  "analysis": {
    "status": "SUPPORTED",
    "learning": "Heating utility fell to 96.25 kW..."
  },
  "next_decision": {
    "reason": "Because heating improved at delta_t_min=7.5 C, test an even lower value (6.0 C)...",
    "experiment": { "delta_t_min": 6.0 }
  }
}
```

## Suggested UI sections

For each experiment card / step:

- Hypothesis text + id  
- Experiment: variable + proposed `delta_t_min`  
- Result numbers: recovery / heating / cooling  
- Analysis status badge: `SUPPORTED` | `REJECTED` | `INCONCLUSIVE`  
- Learning text  
- Next decision reason + next `delta_t_min`  

Also show a clear comparison:

```text
Experiment #1 delta_t_min = 7.5
Experiment #2 delta_t_min = 6.0
Changed because of result #1: YES
```

## Easy start path

1. Keep using `frontend/dummy_experiment.json` until API is running  
2. Add a "Run discovery" button that calls `POST /discovery/run`  
3. Replace dummy cards with `response.experiments`  
4. Highlight `agentic_proof.second_changed`

## Important notes

- Results may currently say `generated_by: "FAKE_EXPERIMENT"`. That is OK for now. Later this becomes the real Pinch engine.  
- Do not invent numbers in the UI. Only display API values.  
- `evidence_ids` may be empty until Evidence Agent is added.  
- Prefer English labels in the UI for the hackathon submission.
- Evidence may include `EVID-001`, `EVID-002`, `EVID-003` from the local registry.
- Invented IDs like `EVID-999` are invalid and must not be shown as real citations.

## Contact / contract freeze

If you need a field renamed, tell the agents teammate **before** changing the UI assumptions.  
Shared contract = this JSON shape + the endpoints above.
