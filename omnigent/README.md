# Omnigent configs (Challenge 03)

This folder contains **Omnigent YAML agents**.  
The Python runtime lives in **`pinch_lab/`** (renamed to avoid clashing with the Omnigent package).

## Agents

| Agent | Path |
|---|---|
| Coordinator | `omnigent/coordinator/` |
| Evidence | `omnigent/agents/evidence/` |
| Hypothesis | `omnigent/agents/hypothesis/` |
| Planner | `omnigent/agents/planner/` |
| Analyst | `omnigent/agents/analyst/` |

## Fastest demo path

1. Deterministic loop (no Omnigent needed):

```powershell
python -m pinch_lab.run_discovery_loop
```

2. FastAPI for frontend:

```powershell
uvicorn backend.main:app --reload
```

3. Omnigent + Claude coordinator:

See [INSTALL.md](INSTALL.md)

```powershell
omni run .\omnigent\coordinator\
```

## Tool contract

Coordinator tools (Python):

- `pinch_lab.tools.omnigent_tools.tool_gather_evidence`
- `pinch_lab.tools.omnigent_tools.tool_validate_evidence_ids`
- `pinch_lab.tools.omnigent_tools.tool_run_experiment`
- `pinch_lab.tools.omnigent_tools.tool_run_discovery_loop`

Claude reasons. These tools return the numbers.
