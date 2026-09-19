"""Credentials & constants. Client Secret lives in the Windows keychain under
service `whoop-dev-app`. Tokens live in keyring (service `whoop-dev-app`,
username `tokens`)."""
import json
import os

KEYRING_SERVICE = "whoop-dev-app"
TOKEN_ENTRY = "tokens"

BASE_URL = "https://api.prod.whoop.com/developer/v2"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

DEFAULT_REDIRECT = "http://localhost:49152/callback"
SCOPES = "offline read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout"

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_credential(entry: str) -> str | None:
    import keyring
    return keyring.get_password(KEYRING_SERVICE, entry)


def set_credential(entry: str, value: str) -> None:
    import keyring
    keyring.set_password(KEYRING_SERVICE, entry, value)


def load_tokens() -> dict | None:
    raw = get_credential(TOKEN_ENTRY)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None


def save_tokens(tokens: dict) -> None:
    set_credential(TOKEN_ENTRY, json.dumps(tokens))


def clear_tokens() -> None:
    try:
        import keyring
        keyring.delete_password(KEYRING_SERVICE, TOKEN_ENTRY)
    except Exception:
        pass
