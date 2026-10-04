# Evidence Agent

## Owns

**What evidence is relevant to the current scientific question?**

## Rules

- Retrieve/structure evidence only; never invent numerical Pinch results
- Prefer local approved cache before any web retrieval
- Return structured records with stable `evidence_id` values
- Other agents may cite only IDs that exist in the Evidence Store
- Invented IDs such as `EVID-999` must fail validation

## MVP

Local registry only (`evidence/evidence_registry.json`).  
BrightData/web access can be added later for this agent alone.
