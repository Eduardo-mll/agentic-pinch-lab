# Frontend handoff — Agentic Pinch Lab

Technical contract for merge/integration with the backend + discovery loop.

## Git / ownership

| You own | Do not edit |
|---|---|
| `frontend/` | `omnigent/`, `pinch_lab/`, `src/`, `scientific/` (except by agreement) |

- Work on branch **`frontend`**
- Integrate against **`master`** (backend/API already merged there)
- Pull latest `master` before wiring the API

## Product goal (not a chatbot)

Show the scientific loop:

1. Evidence  
2. Hypothesis  
3. Experiment  
4. Result  
5. Learning  
6. Next decision  

Judges must see that **experiment #2 changed because of result #1**.

## Chemistry context (for UI copy)

- Domain: Pinch Analysis / Heat Exchanger Network energy integration  
- Case: sulfuric-acid process benchmark (4 streams: H1, H2, C1, C2)  
- MVP variable: only `delta_t_min`  
- Goal: reduce external heating/cooling utilities by recovering process heat  

### Baseline card (always show)

| Metric | Value |
|---|---:|
| delta_t_min | 10 C |
| Hot Pinch | 80 C |
| Cold Pinch | 70 C |
| Heat recovery | 490 kW |
| Heating utility | 100 kW |
| Cooling utility | 95 kW |

## Run the API locally

From repo root:

```powershell
cd C:\Users\troni\Desktop\Hackaton\agentic-pinch-lab
.\.venv\Scripts\activate
uvicorn backend.main:app --reload
```

- Base URL: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Health: `GET /health` → `{ "status": "ok" }`
- CORS: open (`*`) for local hackathon use

Suggested frontend env:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Endpoints (integration contract)

### 1) Main action — run discovery

`POST /discovery/run`

Body:

```json
{ "steps": 2 }
```

Response (shape):

```json
{
  "status": "ok",
  "steps": 2,
  "experiments": [ /* ExperimentRecord[] */ ],
  "agentic_proof": {
    "first_delta_t_min": 7.5,
    "second_delta_t_min": 6.0,
    "second_changed": true
  }
}
```

Use `agentic_proof.second_changed` as a clear YES/NO badge in the UI.

### 2) Latest saved experiment

`GET /discovery/latest`

```json
{ "status": "ok", "record": { /* ExperimentRecord */ } }
```

### 3) History index

`GET /discovery/history`

```json
{
  "experiments": [
    {
      "run_id": "RUN-...",
      "experiment_id": "EXP-001",
      "delta_t_min": 7.5,
      "analysis_status": "SUPPORTED",
      "hypothesis_id": "HYP-001",
      "evidence_ids": ["EVID-001", "EVID-002", "EVID-003"],
      "path": "results/runs/RUN-....json"
    }
  ]
}
```

### 4) Evidence list

`GET /evidence`

```json
{
  "status": "ok",
  "count": 3,
  "evidence": [
    {
      "evidence_id": "EVID-001",
      "title": "...",
      "source_type": "process_baseline",
      "claim_supported": "...",
      "confidence": "high",
      "approved": true
    }
  ]
}
```

### 5) Optional direct Pinch call

`GET /pinch?delta_t_min=10`

Useful for a baseline calculator widget; main demo should use `/discovery/run`.

## ExperimentRecord fields to render

```json
{
  "run_id": "RUN-...",
  "timestamp": "2026-10-04T01:34:57.388460+00:00",
  "question": "Can lowering delta_t_min reduce external utility demand ...?",
  "evidence_ids": ["EVID-001", "EVID-002", "EVID-003"],
  "evidence": {
    "status": "OK",
    "message": "Selected 3 approved local evidence record(s).",
    "items": [
      {
        "evidence_id": "EVID-001",
        "title": "...",
        "source_type": "process_baseline",
        "claim_supported": "...",
        "confidence": "high"
      }
    ]
  },
  "hypothesis": {
    "id": "HYP-001",
    "text": "...",
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
    "reason": "..."
  },
  "validation": { "status": "PASS" },
  "result": {
    "generated_by": "SCIENCE_PINCH_ENGINE",
    "status": "VALID",
    "delta_t_min": 7.5,
    "heat_recovery_kw": 502.5,
    "heating_utility_kw": 87.5,
    "cooling_utility_kw": 82.5,
    "hot_pinch_c": 77.5,
    "cold_pinch_c": 70.0,
    "message": "Result from science-branch Pinch engine..."
  },
  "analysis": {
    "status": "SUPPORTED",
    "learning": "..."
  },
  "next_decision": {
    "reason": "...",
    "experiment": { "delta_t_min": 6.0 }
  }
}
```

### Enums / important values

- `analysis.status`: `SUPPORTED` | `REJECTED` | `INCONCLUSIVE`
- `result.status`: `VALID` | `REJECTED`
- `result.generated_by`: expect `SCIENCE_PINCH_ENGINE` (real Pinch). Fallback may be `FAKE_EXPERIMENT`.
- `validation.status`: `PASS` | `REJECTED`

## Suggested UI layout

1. **Header / goal** — scientific question + baseline card  
2. **Evidence** — from `GET /evidence` or `experiments[i].evidence.items`  
3. **Run discovery** button → `POST /discovery/run`  
4. **Experiment timeline** — one card per item in `experiments[]`  
5. **Agentic proof banner** — `second_changed === true`  
6. **Compare vs baseline** — show recovery/heating/cooling deltas  

## Merge checklist for frontend

1. Pull latest `master`
2. Scaffold React+Vite+TS inside `frontend/` (or keep app there)
3. Set `VITE_API_BASE_URL=http://127.0.0.1:8000`
4. Implement:
   - baseline card (hardcoded values above are fine)
   - Run discovery button
   - render `experiments[]`
   - show evidence + learning + next decision
5. Do **not** invent numbers in the UI — only display API values
6. English UI labels for submission

## Stack recommendation

- Vite + React + TypeScript
- Fetch or axios against `VITE_API_BASE_URL`
- No auth required for local MVP

## Out of scope for frontend (for now)

- Omnigent CLI / Claude chat UI
- BrightData
- Editing Pinch equations
- Changing stream data

## Contract freeze

If a field must be renamed, ask backend/agents first.  
Canonical doc in repo: `frontend/HANDOFF.md`  
Live schema explorer: `http://127.0.0.1:8000/docs`
