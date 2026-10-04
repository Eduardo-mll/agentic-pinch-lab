# Install Omnigent + Claude (Windows)

Our Python package is named **`pinch_lab`** on purpose.  
The top-level **`omnigent/`** folder holds Omnigent YAML agents only.

## 1. Project venv (already used for FastAPI / pytest)

```powershell
cd C:\Users\troni\Desktop\Hackaton\agentic-pinch-lab
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

## 2. Install Omnigent CLI (separate tool)

Install `uv` first if needed: https://docs.astral.sh/uv/

Then:

```powershell
uv tool install --python 3.12 omnigent
```

Check:

```powershell
omni --help
# or
omnigent --help
```

## 3. Anthropic key

Copy `.env.example` to `.env` and set:

```text
ANTHROPIC_API_KEY=your_key_here
```

Also set it in the current shell before running Omnigent:

```powershell
$env:ANTHROPIC_API_KEY = "your_key_here"
```

Never commit `.env`.

## 4. Run the coordinator

From the repo root, with the project venv active so `pinch_lab` imports resolve:

```powershell
.\.venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
omni run .\omnigent\coordinator\
```

If your install uses `omnigent` instead of `omni`, run:

```powershell
omnigent run .\omnigent\coordinator\
```

Ask the coordinator something like:

```text
Run a 2-step discovery loop for lowering delta_t_min and explain why experiment 2 changed.
```

It should call tools (`gather_evidence`, `run_discovery_loop` / `run_experiment`) instead of inventing numbers.

## 5. Fallback without Omnigent CLI

If Omnigent is not installed yet, the deterministic loop still works:

```powershell
python -m pinch_lab.run_discovery_loop
uvicorn backend.main:app --reload
```

## Notes

- Model in YAML: `claude-sonnet-4-6` (change if your Omnigent version expects another id)
- Exact Omnigent YAML keys can vary by version; adjust `executor` if `omni run` complains
- Do not `pip install omnigent` into this project as a library named `omnigent` — use the CLI tool install
