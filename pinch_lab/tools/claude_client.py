"""Optional Anthropic Claude helper (Sonnet by default)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_MODEL = "claude-sonnet-4-6"


def anthropic_enabled() -> bool:
    flag = os.getenv("USE_CLAUDE", "1").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return False
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


def claude_model() -> str:
    return os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def claude_complete(
    *,
    system: str,
    user: str,
    max_tokens: int = 400,
) -> dict[str, Any]:
    """Call Anthropic Messages API. Returns text or an error payload."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return {"status": "DISABLED", "text": "", "message": "ANTHROPIC_API_KEY missing."}

    model = claude_model()
    body = json.dumps(
        {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:400]
        return {
            "status": "ERROR",
            "text": "",
            "model": model,
            "message": f"Anthropic HTTP {error.code}: {detail}",
        }
    except Exception as error:  # noqa: BLE001
        return {
            "status": "ERROR",
            "text": "",
            "model": model,
            "message": f"Anthropic request failed: {error}",
        }

    chunks = []
    for block in payload.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            chunks.append(str(block.get("text", "")))
    text = "\n".join(chunks).strip()
    return {
        "status": "OK",
        "text": text,
        "model": payload.get("model", model),
        "usage": payload.get("usage", {}),
        "message": "Claude response received.",
    }
