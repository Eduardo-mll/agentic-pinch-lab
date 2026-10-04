# Install Omnigent + Claude Sonnet + Bright Data (Windows)

Our Python package is named **`pinch_lab`** on purpose.  
The top-level **`omnigent/`** folder holds Omnigent YAML agents only.

## 1. Project venv

```powershell
cd C:\Users\troni\Desktop\Hackaton\agentic-pinch-lab
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

## 2. Install Omnigent CLI

```powershell
uv tool install --python 3.12 omnigent
omni --help
```

## 3. Keys in `.env`

Copy `.env.example` → `.env` and set:

```text
USE_CLAUDE=1
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

USE_BRIGHTDATA=1
BRIGHTDATA_API_KEY=...
BRIGHTDATA_ZONE=pinch_lab_serp
```

Notes:
- **No spaces** around `=`
- The API key cannot create a zone. In Bright Data, add a **SERP API** zone named `pinch_lab_serp`.
- We use **Claude Sonnet 4.6**. It is one step above Haiku. The short id `claude-sonnet-4-5` is not available on this API key.

Also export for Omnigent in the current shell:

```powershell
$env:ANTHROPIC_API_KEY = (Get-Content .env | Where-Object { $_ -match '^ANTHROPIC_API_KEY=' }) -replace '^ANTHROPIC_API_KEY=',''
$env:PYTHONPATH = (Get-Location).Path
```

## 4. Local discovery API (Claude + Bright Data wired)

```powershell
.\.venv\Scripts\activate
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.main:app --reload --port 8000
```

`Run cycle` in the UI will:
1. gather evidence (local + Bright Data SERP)
2. form hypothesis (Claude Sonnet when enabled)
3. run Pinch + area/cost in Python
4. narrate learning with Claude Sonnet (numbers still from Python)

## 5. Omnigent coordinator (optional live agent)

```powershell
omni run .\omnigent\coordinator\ --harness claude-sdk --model claude-sonnet-4-6
```

Ask something like:

```text
Run a 2-step discovery loop for lowering delta_t_min and explain why experiment 2 changed.
```

## 6. Fallback without cloud

```powershell
$env:USE_CLAUDE=0
$env:USE_BRIGHTDATA=0
python -m pinch_lab.run_discovery_loop
```
