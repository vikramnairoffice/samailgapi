"""Simple helpers connecting the Gradio UI to the Gmail REST mailer."""

import traceback
import requests
from typing import Iterable, List, Tuple
from urllib.parse import quote

from mailer import campaign_events, update_file_stats, load_token_files


def analyze_token_files(token_files) -> str:
    """Return a short status string for uploaded Gmail token files."""
    token_msg, _ = update_file_stats(token_files, None)
    return token_msg


def _build_output(log_lines: List[str], status: str, summary: str) -> Tuple[str, str, str]:
    """Helper to prepare consistent UI output."""
    log_text = "\n".join(log_lines[-200:])  # keep output manageable
    return log_text, status, summary


def ui_error_wrapper(func):
    """Wrap a generator function and surface exceptions to the UI."""
    def wrapper(*args, **kwargs):
        try:
            yield from func(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - defensive guard
            details = traceback.format_exc()
            message = f"Error: {exc}\n\n{details}"
            yield _build_output([message], "", "Failed") + ("", "")
    return wrapper


def _format_progress(event) -> str:
    account = event.get('account', 'unknown')
    lead = event.get('lead', 'unknown')
    if event.get('success'):
        return f"OK Sent to {lead} using {account}"
    return f"FAIL for {lead} using {account}: {event.get('message')}"


def build_gmass_preview(mode, token_files) -> Tuple[str, List[List[str]]]:
    """Return status text and table rows for the GMass preview panel."""
    if (mode or '').lower() != 'gmass':
        return "", []

    accounts, _ = load_token_files(token_files)
    emails = [account.get('email') for account in accounts if account.get('email')]

    if not emails:
        return "No Gmail accounts available for GMass preview.", []

    table: List[List[str]] = []
    for email in emails:
        local_part = email.split('@', 1)[0] if '@' in email else email
        encoded = quote(local_part)
        table.append([email, f"https://www.gmass.co/inbox?q={encoded}"])

    status = f"Completed! Check {len(table)} GMass URLs."
    return status, table


def gmass_rows_to_markdown(rows: List[List[str]]) -> str:
    """Convert GMass preview rows into Markdown with clickable links."""
    if not rows:
        return ""

    lines = []
    for account, url in rows:
        safe_account = account or "Unknown account"
        safe_url = url or ""
        if not safe_url:
            lines.append(f"- {safe_account}")
        else:
            lines.append(f"- [{safe_account}]({safe_url})")
    return "\n".join(lines)



GMAIL_LABEL_URL = "https://gmail.googleapis.com/gmail/v1/users/me/labels/{label_id}"

def _fetch_label_total(creds, label_id: str) -> int:
    token = getattr(creds, 'token', '')
    if not token:
        raise RuntimeError("Missing Gmail access token.")

    response = requests.get(
        GMAIL_LABEL_URL.format(label_id=label_id),
        headers={'Authorization': f'Bearer {token}'},
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Gmail label fetch failed ({label_id}): {response.status_code} - {getattr(response, 'text', '')}"
        )

    data = response.json() or {}
    total = data.get('messagesTotal', 0)
    try:
        return int(total)
    except (TypeError, ValueError):
        return 0


def mailbox_rows_to_markdown(rows: List[Tuple[str, int, int]]) -> str:
    if not rows:
        return ""

    lines: List[str] = []
    for email, inbox_total, sent_total in rows:
        name = email or 'Unknown account'
        inbox_value = inbox_total if isinstance(inbox_total, int) else int(inbox_total or 0)
        sent_value = sent_total if isinstance(sent_total, int) else int(sent_total or 0)
        lines.append(f"- {name} - Inbox: {inbox_value} | Sent: {sent_value}")
    return "\\n".join(lines)


def fetch_mailbox_counts(token_files) -> Tuple[str, str]:
    accounts, token_errors = load_token_files(token_files)
    rows: List[Tuple[str, int, int]] = []
    issues: List[str] = list(token_errors)

    for account in accounts:
        email = account.get('email') or account.get('path') or 'Unknown token'
        creds = account.get('creds')
        try:
            inbox_total = _fetch_label_total(creds, 'INBOX')
            sent_total = _fetch_label_total(creds, 'SENT')
        except Exception as exc:
            issues.append(f"{email}: {exc}")
            continue
        rows.append((email, inbox_total, sent_total))

    if rows:
        status = f"Mailbox counts ready for {len(rows)} account(s)."
    elif accounts:
        status = "Failed to collect mailbox counts for uploaded tokens."
    else:
        status = "No Gmail token files available."

    if issues:
        status += f" Issues: {'; '.join(issues)}"

    markdown = mailbox_rows_to_markdown(rows)
    return status, markdown


@ui_error_wrapper
def start_campaign(token_files, leads_file, leads_per_account, send_delay_seconds, mode,
                   email_content_mode, attachment_folder, invoice_format,
                   support_number, advance_header=False, force_header=False, sender_name_type=None, content_template=None):
    """Generator used by the Gradio UI button to stream campaign events."""
    log_lines: List[str] = []
    status = "Waiting"
    summary = ""

    gmass_status, gmass_rows = build_gmass_preview(mode, token_files)
    if gmass_status == "" and gmass_rows:
        # Defensive guard: avoid mismatched state
        gmass_rows = []
    gmass_markdown = gmass_rows_to_markdown(gmass_rows)

    events = campaign_events(
        token_files=token_files,
        leads_file=leads_file,
        leads_per_account=leads_per_account,
        send_delay_seconds=send_delay_seconds,
        mode=mode,
        content_template=content_template,
        email_content_mode=email_content_mode,
        attachment_format='pdf',
        invoice_format=invoice_format,
        support_number=support_number,
        advance_header=advance_header,
        force_header=force_header,
        sender_name_type=sender_name_type,
        attachment_folder=attachment_folder,
    )

    mode_lower = (mode or '').lower()
    if mode_lower != 'gmass':
        gmass_status = ""
        gmass_markdown = ""

    for event in events:
        kind = event.get('kind')
        if kind == 'token_error':
            message = f"Token issue: {event['message']}"
            log_lines.append(message)
            status = message
        elif kind == 'fatal':
            summary = event['message']
            log_lines.append(summary)
            yield _build_output(log_lines, status, summary) + (gmass_status, gmass_markdown)
            return
        elif kind == 'progress':
            status = f"Total {event['successes']}/{event['total']}"
            log_lines.append(_format_progress(event))
        elif kind == 'done':
            summary = event['message']
        else:
            log_lines.append(str(event))

        yield _build_output(log_lines, status, summary) + (gmass_status, gmass_markdown)

    # Final emit to ensure summary is visible
    yield _build_output(log_lines, status, summary or "Completed") + (gmass_status, gmass_markdown)




