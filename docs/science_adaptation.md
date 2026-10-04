# Science branch adaptation (agents track)

Your friend uploaded Pinch code that was not drop-in ready for this repo.
We adapted it so agents can call it.

## What was wrong

| Issue | Friend code | Adaptation |
|---|---|---|
| Package name | `from src...` but files lived in `scientific/` | Copied into top-level `src/` |
| Models filename | file was `model.py`, import was `src.models` | Saved as `src/models.py` |
| Baseline data | expected `data/baseline.json` (missing) | Added `data/baseline.json` |
| Result keys | `maximum_heat_recovery_kw`, `minimum_heating_kw`, ... | Mapped in `pinch_lab/tools/science_bridge.py` |
| History path | `experiments/history.jsonl` | Redirected to `results/science_history.jsonl` |

## How agents call science now

```text
run_computational_experiment(delta_t_min)
        ↓
science available? ──yes──► src.pinch_engine.run_pinch_analysis
        │
        no/error
        ↓
FAKE_EXPERIMENT fallback
```

## Keep for ChemE / evidence

`scientific/streams.json`, `baseline.json`, `variables.json` remain as the
human-readable scientific contract. Do not delete them from `agents`/`master`
until evidence and docs are updated.
