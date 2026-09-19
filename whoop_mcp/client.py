"""Thin WHOOP REST client used by the MCP tools."""
import requests

from . import config
from .auth import get_access_token, AuthNeededError


def _get(path: str, params: dict | None = None) -> dict:
    return requests.get(
        config.BASE_URL + path,
        headers={"Authorization": f"Bearer {get_access_token()}"},
        params=params,
        timeout=30,
    ).json()


def paginate(path: str, params: dict | None = None, max_pages: int = 20) -> dict:
    """Fetch all pages of a collection endpoint (limit 25/page)."""
    out = []
    params = dict(params or {})
    nxt = None
    for _ in range(max_pages):
        if nxt:
            params["nextToken"] = nxt
        data = _get(path, params)
        out.extend(data.get("records", []))
        nxt = data.get("next_token")
        if not nxt:
            break
    return {"records": out, "count": len(out), "pages_fetched": min(_ + 1 for _ in (range(max_pages)))}


def revoke() -> None:
    try:
        requests.request(
            "DELETE",  # endpoint is implemented over DELETE on some versions; try DELETE then POST fallback
            config.BASE_URL + "/oauth/revoke",
            headers={"Authorization": f"Bearer {get_access_token()}"},
            timeout=30,
        )
    finally:
        config.clear_tokens()
