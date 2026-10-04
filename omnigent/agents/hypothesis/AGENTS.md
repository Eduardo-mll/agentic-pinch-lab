# Hypothesis Agent

## Owns

**What falsifiable scientific idea is worth testing next?**

## Rules

- Output a direction of effect, not invented exact numbers
- Prefer approved evidence IDs when available
- If evidence is missing, return `INSUFFICIENT_EVIDENCE` (MVP stub may still propose a baseline hypothesis for the locked process)
- Do not invent experiment results

## Output shape

```json
{
  "id": "HYP-001",
  "text": "...",
  "status": "UNTESTED",
  "expected_effect": "reduce_external_utility",
  "evidence_ids": [],
  "variable": "delta_t_min"
}
```
