"""SMTP adapter for Gmail app password flows."""

from __future__ import annotations

from typing import Any, Mapping

import mailer


def _normalise_headers(headers: Mapping[str, Any] | None) -> tuple[bool, bool, str]:
    details = headers or {}
    advance = bool(details.get("advance_header"))
    force = bool(details.get("force_header"))
    subtype = str(details.get("body_subtype") or "plain")
    return advance, force, subtype


def _ensure_present(value: str | None, label: str) -> str:
    if not value or not str(value).strip():
        raise ValueError(f"{label} is required for SMTP send.")
    return str(value).strip()


def send(
    *,
    email: str,
    password: str,
    to_email: str,
    subject: str,
    body: str,
    from_header: str | None = None,
    attachments: Mapping[str, str] | None = None,
    headers: Mapping[str, Any] | None = None,
) -> None:
    """Send an email using the legacy SMTP app password helper."""
    login_email = _ensure_present(email, "email")
    app_password = _ensure_present(password, "app password")

    advance_header, force_header, body_subtype = _normalise_headers(headers)
    payload_attachments = dict(attachments or {})
    from_value = from_header or login_email

    try:
        mailer.send_app_password_message(
            login_email=login_email,
            from_header=from_value,
            app_password=app_password,
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=payload_attachments,
            advance_header=advance_header,
            force_header=force_header,
            body_subtype=body_subtype,
        )
    except Exception as exc:
        raise RuntimeError(f"SMTP send failed: {exc}") from exc


def mailbox_totals(email: str, password: str) -> dict[str, int]:
    """Fetch mailbox counts for the given app password credentials."""
    login_email = _ensure_present(email, "email")
    app_password = _ensure_present(password, "app password")

    try:
        inbox_total, sent_total = mailer.fetch_mailbox_totals_app_password(login_email, app_password)
    except Exception as exc:
        raise RuntimeError(f"SMTP mailbox metrics failed: {exc}") from exc

    return {"inbox": int(inbox_total), "sent": int(sent_total)}
