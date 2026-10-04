"""Repo-root aware paths for the science package."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BASELINE_PATH = DATA_DIR / "baseline.json"
HISTORY_PATH = ROOT / "results" / "science_history.jsonl"
