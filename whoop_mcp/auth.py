"""WHOOP OAuth2 (authorization code + refresh) and API client.

Auth state machine:
- No tokens          -> raises AuthNeededError with `authorize_url` guidance.
- Access expired     -> transparent auto-refresh (single-flight via file lock).
- Refresh fails/revoked -> clears tokens, raises AuthNeededError.
"""
import base64
import hashlib
import json
import os
import secrets
import time
import webbrowser
from urllib.parse import urlencode, urlsplit, parse_qs

import requests

from . import config

LOCK_FILE = os.path.join(config.APP_DIR, ".token_refresh.lock")


class AuthNeededError(Exception):
    """Raised when the user must run `python -m whoop_mcp.auth` to (re)authorize."""

    def __init__(self, msg):
        super().__init__(
            msg + " Run: python -m whoop_mcp.auth  (from the whoop-app project dir)"
        )


def get_client_id() -> str:
    cid = config.get_credential("client_id")
    if not cid:
        raise AuthNeededError(
            "WHOOP client_id not found in keychain (service whoop-dev-app). "
            "Store it with: python -m whoop_mcp.auth --store"
        )
    return cid


def get_redirect_uri() -> str:
    uri = config.get_credential("redirect_uri")
    return uri or config.DEFAULT_REDIRECT


def _refresh_lock():
    """Cross-process simple spinner lock using a lock file."""
    deadline = time.time() + 10
    while os.path.exists(LOCK_FILE) and time.time() < deadline:
        time.sleep(0.2)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def _refresh_unlock():
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


def _compute_expiry(tokens: dict) -> None:
    tokens.setdefault("fetched_at", time.time())
    tokens["expires_at"] = tokens["fetched_at"] + int(tokens.get("expires_in", 0))


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for tokens; saves them."""
    resp = requests.post(
        config.TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": get_client_id(),
            "client_secret": _get_secret(),
            "redirect_uri": get_redirect_uri(),
        },
        timeout=30,
    )
    resp.raise_for_status()
    tokens = resp.json()
    _compute_expiry(tokens)
    config.save_tokens(tokens)
    return tokens


def _get_secret() -> str:
    secret = config.get_credential("client_secret")
    if not secret:
        raise AuthNeededError(
            "WHOOP client_secret not found in keychain (service whoop-dev-app)."
        )
    return secret


def _do_refresh(tokens: dict) -> dict:
    cid = get_client_id()
    resp = requests.post(
        config.TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": cid,
            "client_secret": _get_secret(),
        },
        timeout=30,
    )
    if resp.status_code in (400, 401, 403):
        # refresh token revoked or invalid -> user must re-authorize
        config.clear_tokens()
        raise AuthNeededError("Token refresh rejected by WHOOP (re-authorization needed).")
    resp.raise_for_status()
    new = resp.json()
    _compute_expiry(new)
    # WHOOP refresh may or may not rotate the refresh token
    if not new.get("refresh_token"):
        new["refresh_token"] = tokens["refresh_token"]
    config.save_tokens(new)
    return new


def get_access_token() -> str:
    tokens = config.load_tokens()
    if not tokens:
        raise AuthNeededError("No WHOOP tokens stored yet.")
    if time.time() >= tokens.get("expires_at", 0) - 60:
        _refresh_lock()
        try:
            # re-load in case another process refreshed meanwhile
            latest = config.load_tokens()
            if time.time() >= latest.get("expires_at", 0) - 60:
                tokens = _do_refresh(latest)
            else:
                tokens = latest
        finally:
            _refresh_unlock()
    return tokens["access_token"]


def token_status() -> dict:
    tokens = config.load_tokens()
    if not tokens:
        return {"authorized": False}
    return {
        "authorized": True,
        "expires_at": tokens.get("expires_at"),
        "expires_in_secs_remaining": int(tokens.get("expires_at", 0) - time.time()),
        "has_refresh_token": bool(tokens.get("refresh_token")),
    }


# ---------------------------------------------------------------- OAuth flow

def build_authorize_url(state: str | None = None) -> tuple[str, str]:
    """PKCE + state. Returns (url, state)."""
    client_id = get_client_id()
    state = state or secrets.token_urlsafe(16)
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    # stash verifier so the callback handler can complete the exchange
    config.set_credential("pkce_verifier", verifier)
    params = {
        "client_id": client_id,
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": config.SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return config.AUTH_URL + "?" + urlencode(params), state


def open_browser_authorize() -> str:
    url, state = build_authorize_url()
    _start = time.time()
    webbrowser.open(url)
    return url


def handle_callback(redirected_url: str) -> dict:
    """Complete flow from a pasted redirect URL. Verifies state + PKCE."""
    q = parse_qs(urlsplit(redirected_url).query)
    if "error" in q:
        raise RuntimeError(f"WHOOP auth error: {q['error'][0]}: {q.get('error_description', [''])[0]}")
    code = q["code"][0]
    verifier = config.get_credential("pkce_verifier")
    client_id = get_client_id()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": _get_secret(),
        "redirect_uri": get_redirect_uri(),
    }
    if verifier:
        data["code_verifier"] = verifier
    resp = requests.post(config.TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    tokens = resp.json()
    _compute_expiry(tokens)
    config.save_tokens(tokens)
    return {"user_id": tokens.get("user_id"), "scope": tokens.get("scope")}
