"""Live token smoke harness for Gmail send + inbox poll + Drive share."""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Mapping, Optional

import requests

from simple_mailer.core.invoice import InvoiceGenerator
from simple_mailer.senders import gmail_rest

_ENV_FLAG = "LIVE_TOKEN_SMOKE"
_GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"

LogFunc = Optional[Callable[[str], None]]


def is_enabled(env: Optional[Mapping[str, Any]] = None) -> bool:
    """Return True when the live smoke harness should run."""
    source = env or os.environ
    return str(source.get(_ENV_FLAG, "")).strip() == "1"


def build_reference() -> str:
    """Generate a unique reference token embedded in the email headers."""
    return f"live-smoke-{uuid.uuid4().hex}"


def _apply_log(logger: LogFunc, message: str) -> None:
    if logger:
        logger(message)


def send_test_email(
    *,
    creds: Any,
    sender_email: str,
    recipient_email: str,
    reference: str,
    subject: str,
    body: str,
    attachments: Optional[Mapping[str, str]] = None,
    send_adapter: Callable[..., Any] = gmail_rest.send,
    log: LogFunc = None,
) -> Any:
    """Send a single email via the Gmail REST adapter with a tracking header."""
    headers = {"X-Ref": reference}

    try:
        result = send_adapter(
            creds,
            sender_email,
            recipient_email,
            subject,
            body,
            attachments=attachments or {},
            headers=headers,
        )
    except Exception as exc:
        raise RuntimeError(f"Gmail send failed for {recipient_email}: {exc}") from exc

    message_id = getattr(result, "get", lambda key, default=None: None)("id", None)
    display_id = message_id or "<unknown>"
    _apply_log(log, f"Sent message {display_id} to {recipient_email} with reference {reference}")
    return result


def _build_auth_headers(creds: Any) -> Dict[str, str]:
    token = getattr(creds, "token", None)
    if not token:
        raise RuntimeError("Gmail credentials must include an access token for live polling.")
    return {"Authorization": f"Bearer {token}"}


def poll_inbox_for_reference(
    *,
    creds: Any,
    reference: str,
    http_get: Callable[..., Any] = requests.get,
    sleep: Callable[[float], None] = time.sleep,
    interval_seconds: float = 5.0,
    max_wait_seconds: float = 60.0,
    log: LogFunc = None,
) -> Dict[str, Any]:
    """Poll the Gmail inbox until a message containing the reference header appears."""
    headers = _build_auth_headers(creds)
    deadline = time.monotonic() + max_wait_seconds
    query = f'header:X-Ref "{reference}"'
    attempt = 0

    while True:
        attempt += 1
        response = http_get(
            _GMAIL_MESSAGES_URL,
            headers=headers,
            params={"q": query, "maxResults": 5},
            timeout=20,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Gmail lookup failed ({response.status_code}) while waiting for {reference}: {getattr(response, 'text', '')}"
            )

        data = response.json() or {}
        messages = data.get("messages") or []
        if messages:
            message = messages[0]
            message_id = message.get("id")
            if not message_id:
                raise RuntimeError("Gmail returned a message without an id during live polling.")
            _apply_log(
                log,
                f"Found message {message_id} for reference {reference} after {attempt} attempt(s)",
            )
            return {"id": message_id}

        if time.monotonic() >= deadline:
            raise RuntimeError(f"Timed out waiting for live email with reference {reference}.")

        _apply_log(log, f"No message for {reference} yet; retrying (attempt {attempt}).")
        sleep(max(interval_seconds, 0.0))


def _default_drive_factory(creds: Any):
    from googleapiclient.discovery import build  # type: ignore

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _build_media_body(path: str) -> Any:
    try:
        from googleapiclient.http import MediaFileUpload  # type: ignore
    except ModuleNotFoundError:
        return SimpleNamespace(path=path)

    return MediaFileUpload(path, resumable=False)


def share_invoice_via_drive(
    *,
    creds: Any,
    invoice_path: str,
    recipient_email: str,
    drive_factory: Callable[[Any], Any] = _default_drive_factory,
    log: LogFunc = None,
) -> Dict[str, str]:
    """Upload the invoice to Drive and grant reader access to the recipient."""
    path = Path(invoice_path)
    if not path.is_file():
        raise FileNotFoundError(f"Invoice path does not exist for Drive share: {invoice_path}")

    drive = drive_factory(creds)
    media = _build_media_body(str(path))
    file_metadata = {"name": path.name}
    upload = drive.files().create(body=file_metadata, media_body=media, fields="id")
    file_info = upload.execute()
    file_id = (file_info or {}).get("id")
    if not file_id:
        raise RuntimeError("Drive upload did not return a file id.")

    permissions = drive.permissions().create(
        fileId=file_id,
        body={"type": "user", "role": "reader", "emailAddress": recipient_email},
        fields="id,role",
    )
    perm_info = permissions.execute()
    if (perm_info or {}).get("role") != "reader":
        raise RuntimeError("Drive permission grant did not confirm reader access.")

    _apply_log(log, f"Shared Drive file {file_id} with {recipient_email} as reader.")
    return {"file_id": file_id, "permission_id": perm_info.get("id", "")}


def _default_logger(message: str) -> None:
    print(f"[live-smoke] {message}")


def run_live_smoke(
    *,
    creds: Any,
    sender_email: str,
    recipient_email: str,
    env: Optional[Mapping[str, Any]] = None,
    log: LogFunc = _default_logger,
    send_helper: Optional[Callable[..., Any]] = None,
    poll_helper: Optional[Callable[..., Dict[str, Any]]] = None,
    drive_helper: Optional[Callable[..., Dict[str, str]]] = None,
    support_number: str = "",
    cleanup: bool = False,
) -> Dict[str, Any]:
    """Execute the live smoke workflow end-to-end."""
    if not is_enabled(env):
        raise RuntimeError("LIVE_TOKEN_SMOKE=1 must be set to run the live smoke harness.")

    reference = build_reference()
    subject = f"Live smoke invoice {reference}"
    body = (
        "This is an automated live smoke check using your Mailer adapter stack. "
        "Please disregard this email."
    )

    generator = InvoiceGenerator()
    invoice_path = generator.generate_for_recipient(recipient_email, support_number or "000-000-0000", "pdf")
    attachments = {Path(invoice_path).name: invoice_path}

    log_send = send_helper or (
        lambda **kwargs: send_test_email(
            creds=creds,
            sender_email=sender_email,
            recipient_email=recipient_email,
            reference=reference,
            subject=subject,
            body=body,
            attachments=attachments,
            log=log,
        )
    )

    send_result = log_send()

    poll = poll_helper or (
        lambda **kwargs: poll_inbox_for_reference(
            creds=creds,
            reference=reference,
            log=log,
        )
    )
    poll_result = poll()

    drive = drive_helper or (
        lambda **kwargs: share_invoice_via_drive(
            creds=creds,
            invoice_path=invoice_path,
            recipient_email=recipient_email,
            log=log,
        )
    )
    drive_result = drive()

    if cleanup:
        try:
            Path(invoice_path).unlink()
        except OSError:
            _apply_log(log, f"Failed to remove temporary invoice {invoice_path}; please clean up manually.")

    return {
        "reference": reference,
        "send": send_result,
        "poll": poll_result,
        "drive": drive_result,
        "invoice_path": invoice_path,
    }


__all__ = [
    "is_enabled",
    "build_reference",
    "send_test_email",
    "poll_inbox_for_reference",
    "share_invoice_via_drive",
    "run_live_smoke",
]