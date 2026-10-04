"""Load repo-root .env into process environment (no extra dependency)."""

from __future__ import annotations

import os
from pathlib import Path


def load_repo_env(path: Path | None = None) -> Path:
    root = Path(__file__).resolve().parents[2]
    env_path = path or (root / ".env")
    if not env_path.exists():
        return env_path

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Do not override an explicitly exported shell variable.
        if key and key not in os.environ:
            os.environ[key] = value
    return env_path
