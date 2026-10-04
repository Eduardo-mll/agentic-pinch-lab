"""Bright Data SERP client for the Evidence Agent."""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


BRIGHTDATA_ENDPOINT = "https://api.brightdata.com/request"


def brightdata_enabled() -> bool:
    flag = os.getenv("USE_BRIGHTDATA", "1").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return False
    return bool(os.getenv("BRIGHTDATA_API_KEY", "").strip())


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _resolve_serp_zone(api_key: str, preferred: str) -> dict[str, str]:
    """Use preferred zone, else first active SERP zone on the account."""
    try:
        request = Request(
            "https://api.brightdata.com/zone/get_active_zones",
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )
        with urlopen(request, timeout=20) as response:
            zones = json.loads(response.read().decode("utf-8"))
    except Exception as error:  # noqa: BLE001
        return {"status": "OK", "zone": preferred, "message": str(error)}

    if not isinstance(zones, list):
        zones = []

    names = [
        str(z.get("name", "")).strip()
        for z in zones
        if isinstance(z, dict) and str(z.get("name", "")).strip()
    ]
    serp_names = [
        str(z.get("name", "")).strip()
        for z in zones
        if isinstance(z, dict)
        and str(z.get("type", "")).lower() in {"serp", "serp_api", "serpapi"}
        and str(z.get("name", "")).strip()
    ]

    if preferred and preferred in names:
        return {"status": "OK", "zone": preferred, "message": "preferred zone ok"}
    if serp_names:
        return {
            "status": "OK",
            "zone": serp_names[0],
            "message": f"Using active SERP zone {serp_names[0]}",
        }
    if names:
        return {
            "status": "OK",
            "zone": names[0],
            "message": f"No SERP zone found; falling back to {names[0]}",
        }
    return {
        "status": "ERROR",
        "zone": preferred,
        "message": (
            "Bright Data account has no active zones. "
            "Create a SERP API zone at https://brightdata.com/cp/zones "
            "and set BRIGHTDATA_ZONE in .env."
        ),
    }


def search_google_serp(
    query: str,
    *,
    limit: int = 5,
    timeout_s: float = 45.0,
) -> dict[str, Any]:
    """Query Google via Bright Data SERP API.

    Returns a normalized payload. On configuration/API errors, returns
    ``status="ERROR"`` so the discovery loop can fall back to local evidence.
    """
    api_key = _env("BRIGHTDATA_API_KEY")
    zone = _env("BRIGHTDATA_ZONE", "serp_api1")
    if not api_key:
        return {
            "status": "DISABLED",
            "query": query,
            "results": [],
            "message": "BRIGHTDATA_API_KEY is not set.",
        }
    if not zone:
        return {
            "status": "ERROR",
            "query": query,
            "results": [],
            "message": "BRIGHTDATA_ZONE is empty. Create a SERP zone in Bright Data.",
        }

    # Prefer a usable SERP zone from the account when the configured name is missing.
    resolved_zone = _resolve_serp_zone(api_key, zone)
    if resolved_zone.get("status") == "ERROR":
        return {
            "status": "ERROR",
            "query": query,
            "results": [],
            "message": resolved_zone["message"],
        }
    zone = resolved_zone["zone"]

    # Bright Data rejects Google's `num` parameter and the request then dies
    # on a captcha redirect. Ask for the default result page instead.
    url = (
        "https://www.google.com/search?"
        f"q={quote_plus(query)}&hl=en&gl=us"
    )
    payload = {
        "zone": zone,
        "url": url,
        "format": "json",
        "data_format": "parsed_light",
    }
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        BRIGHTDATA_ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status_code = getattr(response, "status", 200)
    except Exception as error:  # noqa: BLE001 - keep Evidence Agent alive
        message = f"Bright Data request failed: {error}"
        detail = str(error)
        if "zone" in detail.lower() and "not found" in detail.lower():
            message = (
                f'Bright Data zone "{zone}" not found. '
                "Create a SERP API zone at https://brightdata.com/cp/zones "
                "and set BRIGHTDATA_ZONE in .env to that exact name."
            )
        return {
            "status": "ERROR",
            "query": query,
            "results": [],
            "message": message,
        }

    if status_code >= 400:
        message = f"Bright Data HTTP {status_code}: {raw[:300]}"
        if "not found" in raw.lower() and "zone" in raw.lower():
            message = (
                f'Bright Data zone "{zone}" not found. '
                "Create a SERP API zone at https://brightdata.com/cp/zones "
                "and set BRIGHTDATA_ZONE in .env to that exact name."
            )
        return {
            "status": "ERROR",
            "query": query,
            "results": [],
            "message": message,
        }

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "status": "ERROR",
            "query": query,
            "results": [],
            "message": "Bright Data returned non-JSON content.",
            "raw_preview": raw[:300],
        }

    inner_status = parsed.get("status_code") if isinstance(parsed, dict) else None
    headers = parsed.get("headers") if isinstance(parsed, dict) else None
    error_code = ""
    if isinstance(headers, dict):
        error_code = str(headers.get("x-brd-error-code") or headers.get("x-brd-error") or "")
    if (isinstance(inner_status, int) and inner_status >= 400) or error_code:
        return {
            "status": "ERROR",
            "query": query,
            "zone": zone,
            "results": [],
            "message": (
                f"Bright Data SERP failed ({inner_status or 'error'}"
                f"{': ' + error_code if error_code else ''})."
            ),
        }

    organic = _extract_organic(parsed)[:limit]
    return {
        "status": "OK",
        "query": query,
        "zone": zone,
        "results": organic,
        "message": f"Bright Data returned {len(organic)} organic result(s).",
    }


def _extract_organic(payload: Any) -> list[dict[str, str]]:
    """Normalize Bright Data / Google SERP shapes into title/url/snippet."""
    candidates: list[Any] = []

    if isinstance(payload, dict):
        for key in ("organic", "organic_results", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates = value
                break
        if not candidates:
            body = payload.get("body")
            if isinstance(body, str):
                try:
                    nested = json.loads(body)
                    return _extract_organic(nested)
                except json.JSONDecodeError:
                    pass
            elif isinstance(body, dict):
                return _extract_organic(body)
            # Some responses nest under data / serp
            for key in ("data", "serp", "response"):
                nested = payload.get(key)
                if nested is not None:
                    found = _extract_organic(nested)
                    if found:
                        return found
    elif isinstance(payload, list):
        candidates = payload

    normalized: list[dict[str, str]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        title = str(
            item.get("title")
            or item.get("name")
            or item.get("heading")
            or ""
        ).strip()
        link = str(
            item.get("link")
            or item.get("url")
            or item.get("href")
            or ""
        ).strip()
        snippet = str(
            item.get("description")
            or item.get("snippet")
            or item.get("body")
            or item.get("text")
            or ""
        ).strip()
        if not title and not link:
            continue
        normalized.append(
            {
                "title": title or link,
                "url": link,
                "snippet": snippet[:500],
            }
        )
    return normalized


def default_search_query(question: str) -> str:
    cleaned = re.sub(r"\s+", " ", question).strip()
    return (
        f"{cleaned} Pinch Analysis delta Tmin heat recovery "
        "heat exchanger network"
    )
