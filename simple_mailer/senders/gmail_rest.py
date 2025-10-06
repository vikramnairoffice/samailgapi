"""Gmail REST adapter that forwards to the legacy mailer implementation."""

from __future__ import annotations

from typing import Any, Mapping

import mailer


# Keep interface minimal so orchestration layers can pass configuration dicts.
def send(
    creds: Any,
    sender_email: str,
    to_email: str,
    subject: str,
    body: str,
    *,
    attachments: Mapping[str, str] | None = None,
    headers: Mapping[str, Any] | None = None,
) -> Any:
    """Send an email using the Gmail REST path via the legacy mailer."""
    header_config = headers or {}
    payload_attachments = dict(attachments or {})

    advance_header = bool(header_config.get("advance_header"))
    force_header = bool(header_config.get("force_header"))
    body_subtype = str(header_config.get("body_subtype") or "plain")

    return mailer.send_gmail_message(
        creds,
        sender_email,
        to_email,
        subject,
        body,
        payload_attachments,
        advance_header=advance_header,
        force_header=force_header,
        body_subtype=body_subtype,
    )
