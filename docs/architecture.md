# Architecture (short)

```text
Scientific Question
      ↓
Evidence Agent → Evidence Validator → Evidence Store
      ↓
Hypothesis Agent
      ↓
Experiment Planner
      ↓
Scientific Validator (Python)
      ↓
Pinch Engine (Python)
      ↓
Scientific Analyst
      ↓
Next experiment (must change because of the result)
```

## Trust hierarchy

1. Process data
2. Deterministic Python model
3. Approved evidence
4. Agent hypothesis

## Non-agents

- Evidence validation
- Scientific experiment validation
- Pinch calculation
- Logging / JSON persistence
