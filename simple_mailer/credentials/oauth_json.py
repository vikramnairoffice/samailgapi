"""In-memory OAuth flow used by the UI to avoid writing token files."""

import json
from typing import Callable, Any, Optional, Sequence, Tuple

import requests
from google_auth_oauthlib.flow import InstalledAppFlow

_DEFAULT_SCOPES = (
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/drive",
)

_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


def _default_flow_factory(config: dict, scopes: Sequence[str]):
    return InstalledAppFlow.from_client_config(config, scopes=scopes)


def _default_profile_fetcher(creds) -> str:
    token = getattr(creds, "token", "")
    if not token:
        raise RuntimeError("OAuth credentials did not include an access token.")

    response = requests.get(
        _PROFILE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Gmail profile lookup failed ({response.status_code}): {getattr(response, 'text', '')}"
        )

    data = response.json() or {}
    email = data.get("emailAddress") or data.get("email")
    if not email:
        raise RuntimeError("Gmail profile response did not include an email address.")
    return email


def initialize(
    client_json: str,
    *,
    scopes: Optional[Sequence[str]] = None,
    flow_factory: Optional[Callable[[dict, Sequence[str]], Any]] = None,
    profile_fetcher: Optional[Callable[[Any], str]] = None,
) -> Tuple[str, Any]:
    """Return (email, credentials) after completing the OAuth consent flow."""
    if not client_json or not client_json.strip():
        raise ValueError("OAuth client JSON is required to authorise Gmail access.")

    try:
        config = json.loads(client_json)
    except json.JSONDecodeError as exc:
        raise ValueError("OAuth client JSON could not be parsed.") from exc

    if not isinstance(config, dict):
        raise ValueError("OAuth client JSON must decode to an object.")

    desired_scopes = tuple(scopes or _DEFAULT_SCOPES)
    factory = flow_factory or _default_flow_factory

    try:
        flow = factory(config, desired_scopes)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Failed to initialise the OAuth consent flow: {exc}") from exc

    try:
        creds = flow.run_console()
    except Exception as exc:
        raise RuntimeError(f"OAuth consent failed: {exc}") from exc

    if not getattr(creds, "token", None):
        raise RuntimeError("OAuth consent succeeded but no access token was returned.")

    fetch_profile = profile_fetcher or _default_profile_fetcher
    email = fetch_profile(creds)
    if not email:
        raise RuntimeError("Unable to determine the Gmail account email from OAuth credentials.")

    return email, creds
