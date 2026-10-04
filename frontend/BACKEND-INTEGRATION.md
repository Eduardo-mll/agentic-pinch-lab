# Connecting Agentic Pinch Lab to the discovery API

This Lovable project is a TanStack Start app rooted in `src/`, not the separate `frontend/` folder described in the handoff. Do not copy the other repository's backend into this app or rewrite its Git history. Integrate through its HTTP API.

1. Run the backend described in `HANDOFF.md` separately and confirm `GET /health` returns `{ "status": "ok" }`.
2. Set `VITE_API_BASE_URL` to the backend's **browser-reachable** origin (no trailing slash). For local development on the same computer, see `.env.example`; for a Lovable preview, use a deployed HTTPS backend. A visitor's `127.0.0.1` does **not** point to your development machine.
3. Permit this web app's origin in the backend's CORS policy, then restart the frontend when the Vite environment variable changes.
4. Press **Run Scientific Cycle**. The app calls `POST /discovery/run` with `{ "steps": 2 }`. It validates the returned data and renders the two experiment records, evidence, hypothesis, Python results, learning, next decision, and whether experiment #2 changed. Numeric run results only appear when `validation.status === "PASS"`, `result.status === "VALID"`, and `result.generated_by === "SCIENCE_PINCH_ENGINE"`.

`src/lib/discovery-api.ts` contains the handoff contract and endpoint helpers for `/discovery/run`, `/discovery/latest`, `/discovery/history`, `/evidence`, and `/pinch`. The discovery run is the primary integration; optional endpoints are available for later views. API values are kept separate from the initial illustrative sweep. Errors stay visible without presenting sample values as fresh API results.

The baseline (10 °C, 490 kW recovery, 100 kW heating, 95 kW cooling, 80/70 °C pinch) is the reference from the handoff; it is never presented as a result of a newly run experiment. No authentication or secrets are needed for the handoff's local MVP; don't put future credentials in `VITE_` variables.