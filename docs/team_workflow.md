# Team workflow (easy, no GitFlow)

Goal: let people work on **agents + API glue**, **Pinch Python**, and **frontend** in parallel without overwriting each other.

## Ownership map

| Person / pair | Owns (write freely) | Do not edit without asking |
|---|---|---|
| Agents + backend glue | `omnigent/`, `backend/main.py`, future `backend/api/`, `backend/experiments/`, `evidence/`, agent-related tests | `backend/pinch/`, `frontend/` |
| Pinch Python + UI | `backend/pinch/`, `scientific/`, `frontend/`, pinch math tests | `omnigent/` |
| Shared carefully | `README.md`, `docs/`, `pyproject.toml`, root config | — |

**Rule:** edit only your folders. Cross-folder changes need a short chat message first.

Chemical Engineering owns approval of `scientific/variables.json` and scientific constraints — not random code edits.

## Stable contracts (the anti-break layer)

Do not share implementation details across teams. Share only these interfaces.

### 1. Pinch function contract

Python owner implements; agents call it:

```python
result = run_pinch_analysis(delta_t_min=7.5)
```

Response shape lives in `backend/pinch/models.py`.

### 2. HTTP contract

Agents/backend glue owns the route; Pinch stays importable:

```text
GET /health
GET /pinch?delta_t_min=10
```

### 3. Experiment JSON contract

Frontend consumes; agents/backend produce.

Use the fields in `frontend/dummy_experiment.json` as the shared shape until the real API exists.

If a contract must change: update the JSON/schema **first**, tell the team, then implement.

```text
omnigent agents → backend API routes → Pinch engine
                      ↓
                 results JSON → frontend
scientific data → Pinch engine
```

## Git branches

This repo’s integration branch is currently **`master`** (same role as `main` in the team plan).

| Branch | Who | Purpose |
|---|---|---|
| `master` | everyone | Always runnable; merge only tested work |
| `agents` | agents + backend glue | Omnigent, policies, tools, API glue |
| `science` | Pinch Python owner | Pinch engine + scientific data + math tests |
| `frontend` | UI owner | Dashboard / visualizations |

### Daily loop

1. Start from updated `master`
2. Work only on your branch / folders
3. Commit often with short messages
4. Open a PR (or ask for review) into `master`
5. Merge `master` back into your branch after each accepted merge

### Conflict-avoidance rules

- Never force-push `master`
- Never edit someone else’s owned folder “just to fix something” without pinging them
- Prefer dummy/fake adapters over editing the Pinch engine from the agents branch:
  - Agents may use `fake_experiment()` until Pinch sensitivity exists
  - Frontend may keep using `dummy_experiment.json` until API is ready
- Shared root files (`pyproject.toml`, README): one person changes them, or do it together in a short sync

## Integration order (keep `master` green)

1. **Science:** `run_pinch_analysis(10)` keeps reproducing 490 / 100 / 95
2. **Agents:** prove `agent → tool → result → next decision` (fake tool OK)
3. **API glue:** agents call real `/pinch` or `run_pinch_analysis`
4. **Frontend:** swap dummy JSON for real experiment records
5. Only then expand features (BrightData, economics, matching)

## Success definition

Parallel work is safe when:

- Agents PRs do not touch `backend/pinch/`
- Science PRs do not touch `omnigent/` or `frontend/`
- Frontend PRs only read the experiment JSON / API response shape
- `master` always passes `pytest` after merge
