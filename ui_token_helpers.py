"""Simple helpers connecting the Gradio UI to the Gmail REST mailer."""

import traceback
from typing import Iterable, List, Tuple

from mailer import campaign_events, update_file_stats


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
            yield _build_output([message], "", "Failed")
    return wrapper


def _format_progress(event) -> str:
    account = event.get('account', 'unknown')
    lead = event.get('lead', 'unknown')
    if event.get('success'):
        return f"OK Sent to {lead} using {account}"
    return f"FAIL for {lead} using {account}: {event.get('message')}"


@ui_error_wrapper
def start_campaign(token_files, leads_file, leads_per_account, send_delay_seconds, mode,
                   email_content_mode, attachment_folder, invoice_format,
                   support_number, advance_header=False, force_header=False, sender_name_type=None, content_template=None):
    """Generator used by the Gradio UI button to stream campaign events."""
    log_lines: List[str] = []
    status = "Waiting"
    summary = ""

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

    for event in events:
        kind = event.get('kind')
        if kind == 'token_error':
            message = f"Token issue: {event['message']}"
            log_lines.append(message)
            status = message
        elif kind == 'fatal':
            summary = event['message']
            log_lines.append(summary)
            yield _build_output(log_lines, status, summary)
            return
        elif kind == 'progress':
            status = f"Total {event['successes']}/{event['total']}"
            log_lines.append(_format_progress(event))
        elif kind == 'done':
            summary = event['message']
        else:
            log_lines.append(str(event))

        yield _build_output(log_lines, status, summary)

    # Final emit to ensure summary is visible
    yield _build_output(log_lines, status, summary or "Completed")





