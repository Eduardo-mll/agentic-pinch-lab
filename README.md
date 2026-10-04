# Agentic Pinch Lab

Hackathon project for **7th Global AI Hackathon — Challenge 03: Agentic Scientific Discovery**.

Omnigent orchestrates the discovery workflow; the Python Pinch Engine performs deterministic scientific calculations.

The lab studies one locked four-stream heat-exchanger network. Each cycle gathers evidence, forms a hypothesis, runs one ΔTmin experiment, learns from the engine result, and chooses a different next ΔTmin.

```text
Evidence → Hypothesis → Experiment → Python result → Learning → Changed next experiment
```

## Core rule

| Layer | Role |
|---|---|
| Omnigent | Orchestrate the specialist handoff: evidence, hypothesis, planner, analyst |
| Claude | Reason when `USE_CLAUDE=1` and `ANTHROPIC_API_KEY` are set. Model: `claude-sonnet-4-6` |
| Python Pinch engine | Calculate recovery, utilities, pinch temperatures, area, and total annual cost |
| Humans | Approve stream changes and any move of the 5–30 °C ΔTmin range |

Pinch numbers are never invented by the model. A Claude Max subscription is not required. The API key in `.env` is enough.

## What one Run does

The dashboard **Run cycle** button calls `POST /discovery/run`.

- With no saved runs, the loop tests 7.5 °C and then the ΔTmin chosen from that result.
- With saved runs, the next click runs only the untested ΔTmin from the last analysis, compared with that previous result.
- Clearing saved runs returns the next cycle to the 7.5 °C start.
- The only controllable variable is `delta_t_min`, inside 5–30 °C. Stream identity, temperatures, FCp, and film coefficients stay locked.

## Baseline

Reference point at ΔTmin = 10 °C:

| Metric | Value |
|---|---:|
| Hot pinch | 80 °C |
| Cold pinch | 70 °C |
| Heat recovery | 490 kW |
| Heating utility | 100 kW |
| Cooling utility | 95 kW |

The engine also reports exchanger area, equipment cost, utility cost, and total annual cost for every tested ΔTmin. The 10 °C case is the only baseline. Other tested values are previous experiments.

## Project layout

```text
agentic-pinch-lab/
├── backend/          # FastAPI. /pinch and /discovery/* 
├── pinch_lab/        # Discovery runtime (Python agents + tools/)
├── src/              # Pinch, network, and cost engine
├── data/             # Engine inputs (baseline streams and HEN)
├── scientific/       # Human-readable scientific contract
├── omnigent/         # Omnigent YAML agents and policies
├── evidence/         # Approved evidence registry
├── results/          # Experiment outputs (JSON)
├── frontend/         # Dashboard
├── tests/            # pytest
└── docs/             # Short architecture notes
```

## Quick start

### 1. Requirements

- Python 3.11+
- Node.js and npm, for the dashboard
- Git

### 2. Python environment

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\activate
pip install -e ".[dev]"
$env:PYTHONPATH = (Get-Location).Path
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
export PYTHONPATH="$(pwd)"
```

### 3. Environment

Create a repo-root `.env`. The variable list is in [omnigent/INSTALL.md](omnigent/INSTALL.md).

```text
USE_CLAUDE=1
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

USE_BRIGHTDATA=1
BRIGHTDATA_API_KEY=...
BRIGHTDATA_ZONE=pinch_lab_serp
```

Bright Data is optional. If the SERP call fails, evidence falls back to the local registry. Do not put spaces around `=`.

**Never commit `.env` or real API keys.**

### 4. Tests

```bash
pytest
```

### 5. API and dashboard

API:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Dashboard, from `frontend/`:

```bash
npm install
npm run dev
```

Open http://127.0.0.1:8080/. In development the page calls http://127.0.0.1:8000/ when `frontend/.env` does not set another `VITE_API_BASE_URL`.

### 6. Command-line loop

A fresh two-step loop, without reading saved runs:

```bash
python -m pinch_lab.run_discovery_loop
```

### 7. Omnigent coordinator

See [omnigent/INSTALL.md](omnigent/INSTALL.md).

```powershell
omni run .\omnigent\coordinator\ --harness claude-sdk --model claude-sonnet-4-6
```

The coordinator calls the same Python tools as the discovery API. It does not replace the Pinch engine.

## Team workflow

Ownership, branch names, and shared contracts: [docs/team_workflow.md](docs/team_workflow.md).

| Role | Focus |
|---|---|
| ITC 1 | Python Pinch engine |
| ITC 2 | Omnigent agents |
| ITC 3 | Frontend / integration |
| Chemical Engineering | Scientific validation |
