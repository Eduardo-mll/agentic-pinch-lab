# Agentic Pinch Lab

Hackathon project for **7th Global AI Hackathon — Challenge 03: Agentic Scientific Discovery**.

We are building an **Agentic Process Energy Discovery Lab**:
an Omnigent-orchestrated system that gathers evidence, forms a hypothesis,
runs a deterministic Python Pinch Analysis experiment, learns from the result,
and chooses a better next experiment.

## Core rule

| Layer | Role |
|---|---|
| Claude / LLM agents | Reason and propose ideas |
| Python Pinch engine | Calculate scientific truth |
| Omnigent | Coordinate the discovery loop |
| Humans | Approve consequential science changes |

## Baseline (must reproduce)

| Metric | Value |
|---|---:|
| ΔTmin | 10 °C |
| Hot Pinch | 80 °C |
| Cold Pinch | 70 °C |
| Heat recovery | 490 kW |
| Heating utility | 100 kW |
| Cooling utility | 95 kW |

## Project layout

```text
agentic-pinch-lab/
├── backend/          # FastAPI + Pinch engine
├── scientific/       # Stream data, baseline, constraints
├── omnigent/         # Agents, tools, policies (later)
├── evidence/         # Approved evidence registry
├── results/          # Experiment outputs (JSON)
├── frontend/         # Dashboard (later)
├── tests/            # pytest
└── docs/             # Short architecture notes
```

## Quick start

### 1. Requirements

- Python 3.11+ recommended
- Git

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

### 4. Run tests

```bash
pytest
```

### 5. Run the API (when ready)

```bash
uvicorn backend.main:app --reload
```

## MVP goal

Show one complete discovery loop:

```text
Evidence → Hypothesis → Experiment → Python result → Learning → Changed next experiment
```

First controllable variable: **ΔTmin only** (streams locked).

## Team roles (working split)

| Role | Focus |
|---|---|
| ITC 1 | Python Pinch engine |
| ITC 2 | Omnigent agents |
| ITC 3 | Frontend / integration |
| Chemical Engineering | Scientific validation |

## Secrets

Copy `.env.example` to `.env` and fill keys locally.

**Never commit `.env` or real API keys.**
