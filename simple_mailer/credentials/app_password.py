"""Utilities for Gmail app password credential files."""

from __future__ import annotations

import imaplib
import os
import re
from typing import Callable, Dict, List, Sequence, Tuple

GMAIL_IMAP_HOST = "imap.gmail.com"
_SENT_MAILBOX_CANDIDATES: Tuple[str, ...] = (
    "[Gmail]/Sent Mail",
    "[Gmail]/Sent",
    "Sent",
    "Sent Mail",
)


CredentialsEntry = Dict[str, str]
Errors = List[str]


def load(path: str) -> Tuple[List[CredentialsEntry], Errors]:
    """Parse the provided credential file into account entries."""
    accounts: List[CredentialsEntry] = []
    errors: Errors = []
    path_str = str(path)
    basename = os.path.basename(path_str)

    try:
        with open(path_str, "r", encoding="utf-8", errors="ignore") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                if line.count(",") != 1:
                    errors.append(f"{basename} line {line_number}: invalid entry")
                    continue
                email, password = (segment.strip() for segment in line.split(",", 1))
                if not email or not password:
                    errors.append(f"{basename} line {line_number}: invalid entry")
                    continue
                accounts.append(
                    {
                        "email": email,
                        "password": password,
                        "path": f"{path_str}:{line_number}",
                        "auth_type": "app_password",
                    }
                )
    except Exception as exc:  # pragma: no cover - surface file IO errors
        return [], [f"{basename}: {exc}"]

    return accounts, errors


def fetch_mailbox_totals(
    email: str,
    password: str,
    *,
    imap_factory: Callable[[str], imaplib.IMAP4_SSL] = imaplib.IMAP4_SSL,
    mailboxes: Sequence[str] = _SENT_MAILBOX_CANDIDATES,
    host: str = GMAIL_IMAP_HOST,
) -> Tuple[int, int]:
    """Return ``(inbox_count, sent_count)`` for the account."""
    imap_conn = imap_factory(host)
    try:
        imap_conn.login(email, password)
        inbox_total = _imap_messages_total(imap_conn, "INBOX")
        sent_total = 0
        for candidate in mailboxes:
            try:
                sent_total = _imap_messages_total(imap_conn, candidate)
                break
            except Exception:
                continue
        return inbox_total, sent_total
    finally:
        try:
            imap_conn.logout()
        except Exception:  # pragma: no cover - defensive cleanup
            pass


def _imap_messages_total(imap_conn, mailbox: str) -> int:
    status, _ = imap_conn.select(mailbox, readonly=True)
    if status != "OK":
        raise RuntimeError(f"IMAP select failed for {mailbox}: {status}")

    status, data = imap_conn.status(mailbox, "(MESSAGES)")
    if status != "OK" or not data:
        raise RuntimeError(f"IMAP status failed for {mailbox}: {status}")

    raw = data[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")
    match = re.search(r"MESSAGES\s+(\d+)", raw or "")
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0
