# Scientific specification (MVP)

## Question

Can an agentic AI laboratory autonomously generate, test and refine
heat-exchanger-network hypotheses to reduce external utility requirements
while respecting Pinch Analysis and thermodynamic constraints?

## Process data

Four streams: H1, H2, C1, C2. See `streams.json`.

## Controllable variable (MVP)

- `delta_t_min` only
- Provisional range: 5–30 °C (needs Chemical Engineering approval)

## Locked variables

- Stream identities
- Supply / target temperatures
- FCp
- Film coefficients `h`

## Trust hierarchy

1. Process / experimental data
2. Deterministic Python Pinch model
3. Approved scientific literature
4. Agent-generated hypothesis

If an LLM statement conflicts with Python or validated process data, **Python/data wins**.

## Baseline regression target

At `delta_t_min = 10 °C`:

- Hot Pinch = 80 °C
- Cold Pinch = 70 °C
- Heat recovery = 490 kW
- Heating utility = 100 kW
- Cooling utility = 95 kW
