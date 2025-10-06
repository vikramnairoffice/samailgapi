"""Adapter for persisted Gmail token JSON credentials."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

DEFAULT_SCOPES: Tuple[str, ...] = (
    "https://mail.google.com/",
)
PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


def load(
    path: str,
    *,
    scopes: Optional[Sequence[str]] = None,
    request_factory: type[Request] = Request,
) -> Tuple[str, Credentials]:
    """Return ``(email, credentials)`` for the given ``token.json`` file."""
    token_path = str(path)
    desired_scopes = tuple(scopes or DEFAULT_SCOPES)
    creds = Credentials.from_authorized_user_file(token_path, desired_scopes)

    if not creds.valid:
        if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            creds.refresh(request_factory())
        else:
            raise RuntimeError("Gmail credentials are invalid and cannot be refreshed.")

    token = getattr(creds, "token", None)
    if not token:
        raise RuntimeError("Gmail credentials did not provide an access token.")

    response = requests.get(
        PROFILE_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to verify Gmail token ({response.status_code}): {getattr(response, 'text', '')}"
        )

    profile = response.json() or {}
    email = profile.get("emailAddress") or profile.get("email")
    if not email:
        raise RuntimeError("Gmail profile response did not include an email address.")

    return email, creds
