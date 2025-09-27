"""Simple helpers connecting the Gradio UI to the Gmail REST mailer."""

import html as _html_module
import traceback
import requests
from functools import wraps
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote

from mailer import campaign_events, update_file_stats, load_accounts, fetch_mailbox_totals_app_password
from content import generate_sender_name
from manual_mode import ManualConfig, parse_extra_tags, to_attachment_specs, preview_attachment


def analyze_token_files(token_files, auth_mode: str = 'oauth') -> str:
    """Return a short status string for uploaded credential files."""
    token_msg, _ = update_file_stats(token_files, None, auth_mode=auth_mode)
    return token_msg


def _build_output(log_lines: List[str], status: str, summary: str) -> str:
    """Helper to prepare consistent UI output for the consolidated run panel."""
    clipped_logs = log_lines[-200:]
    log_text = "\n".join(clipped_logs).strip()
    status_text = (status or 'Idle').strip() or 'Idle'
    sections = [f"Status: {status_text}"]
    if summary:
        sections.append(f"Summary: {summary}")
    if log_text:
        sections.extend(['', 'Log:', log_text])
    return "\n".join(sections)


def ui_error_wrapper(*, extra_outputs: Tuple[str, ...] = ()):
    """Wrap a generator function and surface exceptions to the UI."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                yield from func(*args, **kwargs)
            except Exception as exc:  # pragma: no cover - defensive guard
                details = traceback.format_exc()
                message = f"Error: {exc}\n\n{details}"
                combined = _build_output([message], "", "Failed")
                yield (combined, *extra_outputs)
        return wrapper
    return decorator


def _format_progress(event) -> str:
    account = event.get('account', 'unknown')
    lead = event.get('lead', 'unknown')
    if event.get('success'):
        return f"OK Sent to {lead} using {account}"
    return f"FAIL for {lead} using {account}: {event.get('message')}"


def build_gmass_preview(mode, token_files, auth_mode: str = 'oauth') -> Tuple[str, List[List[str]]]:
    """Return status text and table rows for the GMass preview panel."""
    if (mode or '').lower() != 'gmass':
        return '', []

    accounts, _ = load_accounts(token_files, auth_mode=auth_mode)
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
    return "\n".join(lines)


def fetch_mailbox_counts(token_files, auth_mode: str = 'oauth') -> Tuple[str, str]:
    accounts, token_errors = load_accounts(token_files, auth_mode=auth_mode)
    rows: List[Tuple[str, int, int]] = []
    issues: List[str] = list(token_errors)

    for account in accounts:
        email = account.get('email') or account.get('path') or 'Unknown credential'
        auth_type = (account.get('auth_type') or 'oauth').lower()
        try:
            if auth_type in {'app_password', 'app-password', 'app password'}:
                inbox_total, sent_total = fetch_mailbox_totals_app_password(account['email'], account['password'])
            else:
                creds = account.get('creds')
                inbox_total = _fetch_label_total(creds, 'INBOX')
                sent_total = _fetch_label_total(creds, 'SENT')
        except Exception as exc:
            issues.append(f"{email}: {exc}")
            continue
        rows.append((email, inbox_total, sent_total))

    if rows:
        status = f"Mailbox counts ready for {len(rows)} account(s)."
    elif accounts:
        status = "Failed to collect mailbox counts for uploaded credentials."
    else:
        status = "No Gmail credential files available."

    if issues:
        status += f" Issues: {'; '.join(issues)}"

    markdown = mailbox_rows_to_markdown(rows)
    return status, markdown

@ui_error_wrapper()
def start_manual_campaign(
    token_files,
    leads_file,
    send_delay_seconds,
    mode,
    manual_subject,
    manual_body,
    manual_body_is_html,
    manual_body_image_enabled,
    manual_randomize_html,
    manual_tfn,
    manual_extra_tags,
    manual_attachment_enabled,
    manual_attachment_mode,
    manual_attachment_files,
    manual_inline_html,
    manual_inline_name,
    manual_sender_name,
    manual_change_name,
    manual_sender_type,
    advance_header=False,
    force_header=False,
    auth_mode: str = 'oauth',
):
    """Manual mode sender wired to the shared campaign generator."""
    log_lines: List[str] = []
    status = "Waiting"
    summary = ""

    manual_config = build_manual_config_from_inputs(
        manual_subject=manual_subject,
        manual_body=manual_body,
        manual_body_is_html=manual_body_is_html,
        manual_body_image_enabled=manual_body_image_enabled,
        manual_randomize_html=manual_randomize_html,
        manual_tfn=manual_tfn,
        manual_extra_tags=manual_extra_tags,
        manual_attachment_enabled=manual_attachment_enabled,
        manual_attachment_mode=manual_attachment_mode,
        manual_attachment_files=manual_attachment_files,
        manual_inline_html=manual_inline_html,
        manual_inline_name=manual_inline_name,
        manual_sender_name=manual_sender_name,
        manual_change_name=manual_change_name,
        manual_sender_type=manual_sender_type,
    )

    events = campaign_events(
        token_files=token_files,
        leads_file=leads_file,
        send_delay_seconds=send_delay_seconds,
        mode=mode,
        content_template='own_proven',
        subject_template='own_proven',
        body_template='own_proven',
        email_content_mode='Attachment',
        attachment_format='pdf',
        invoice_format='pdf',
        support_number='',
        advance_header=advance_header,
        force_header=force_header,
        sender_name_type=manual_sender_type or 'business',
        attachment_folder='',
        auth_mode=auth_mode,
        manual_config=manual_config,
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

    yield _build_output(log_lines, status, summary or "Completed")




_PREVIEW_EMAIL = "preview@example.com"


def build_manual_config_from_inputs(
    manual_subject,
    manual_body,
    manual_body_is_html,
    manual_body_image_enabled,
    manual_randomize_html,
    manual_tfn,
    manual_extra_tags,
    manual_attachment_enabled,
    manual_attachment_mode,
    manual_attachment_files,
    manual_inline_html,
    manual_inline_name,
    manual_sender_name,
    manual_change_name,
    manual_sender_type,
):
    extra_tags = parse_extra_tags(manual_extra_tags)
    inline_html = manual_inline_html if manual_attachment_enabled else ''
    inline_name = manual_inline_name if manual_attachment_enabled else ''
    specs = to_attachment_specs(
        manual_attachment_files if manual_attachment_enabled else [],
        inline_html,
        inline_name,
    )
    normalized_mode = (manual_attachment_mode or 'original').strip().lower().replace(' ', '_')
    return ManualConfig(
        enabled=True,
        subject=manual_subject or '',
        body=manual_body or '',
        body_is_html=bool(manual_body_is_html),
        body_image_enabled=bool(manual_body_image_enabled),
        randomize_html=bool(manual_randomize_html),
        tfn=manual_tfn or '',
        extra_tags=extra_tags,
        attachments=specs,
        attachment_mode=normalized_mode,
        attachments_enabled=bool(manual_attachment_enabled),
        sender_name=manual_sender_name or '',
        change_name_every_time=bool(manual_change_name),
        sender_name_type=manual_sender_type or 'business',
    )



def _wrap_text_as_html(text: str) -> str:
    return f"<pre style='white-space:pre-wrap; margin:0;'>{_html_module.escape(text or '')}</pre>"


def _wrap_preview_container(title: str, inner_html: str) -> str:
    header = f"<div style='font-weight:600; margin-bottom:8px;'>{_html_module.escape(title)}</div>" if title else ''
    body = inner_html or ''
    return (
        '<div style="max-height:600px; overflow:auto; padding:12px; '
        'border:1px solid rgba(255,255,255,0.15); border-radius:8px; ' 
        'background:rgba(0,0,0,0.25);">'
        f'{header}{body}</div>'
    )


def manual_preview_snapshot(
    *,
    manual_body,
    manual_body_is_html,
    manual_body_image_enabled,
    manual_randomize_html,
    manual_tfn,
    manual_extra_tags,
    manual_attachment_enabled,
    manual_attachment_mode,
    manual_attachment_files,
    manual_inline_html,
    manual_inline_name,
    selected_attachment_name,
):
    config = build_manual_config_from_inputs(
        manual_subject='',
        manual_body=manual_body,
        manual_body_is_html=manual_body_is_html,
        manual_body_image_enabled=manual_body_image_enabled,
        manual_randomize_html=manual_randomize_html,
        manual_tfn=manual_tfn,
        manual_extra_tags=manual_extra_tags,
        manual_attachment_enabled=manual_attachment_enabled,
        manual_attachment_mode=manual_attachment_mode,
        manual_attachment_files=manual_attachment_files,
        manual_inline_html=manual_inline_html,
        manual_inline_name=manual_inline_name,
        manual_sender_name='',
        manual_change_name=False,
        manual_sender_type='business',
    )

    context = config.build_context(_PREVIEW_EMAIL)
    html_map = {}
    choices = []

    body_rendered, body_kind = config.render_body(context)
    if body_rendered:
        if body_kind == 'html':
            fragment = body_rendered
        else:
            fragment = _wrap_text_as_html(body_rendered)
        html_map['Body'] = _wrap_preview_container('Body Preview', fragment)
        choices.append('Body')

    if config.attachments_enabled and config.attachments:
        specs = config.attachments
        target = None
        if selected_attachment_name:
            for spec in specs:
                if spec.display_name == selected_attachment_name:
                    target = spec
                    break
        if target is None:
            target = specs[0]
        kind, payload = preview_attachment(target)
        if kind == 'html':
            attachment_fragment = payload
        else:
            attachment_fragment = _wrap_text_as_html(payload)
        title = f"Attachment Preview ({target.display_name})"
        html_map['Attachment'] = _wrap_preview_container(title, attachment_fragment)
        choices.append('Attachment')

    default = choices[0] if choices else ''
    return choices, default, html_map


def manual_random_sender_name(sender_type: str = 'business') -> str:
    return generate_sender_name(sender_type or 'business')


def manual_attachment_listing(files, inline_html='', inline_name=''):
    """Return dropdown choices and initial preview for manual attachments."""
    specs = to_attachment_specs(files, inline_html, inline_name)
    names = [spec.display_name for spec in specs]
    if specs:
        kind, payload = preview_attachment(specs[0])
        if kind == 'html':
            html_payload, text_payload = payload, ''
        else:
            html_payload, text_payload = '', payload
        default = names[0]
    else:
        html_payload = ''
        text_payload = ''
        default = None
    return names, default, html_payload, text_payload


def manual_attachment_preview_content(selected_name: str, files, inline_html='', inline_name=''):
    """Return HTML/text preview content for the selected manual attachment."""
    specs = to_attachment_specs(files, inline_html, inline_name)
    target = None
    for spec in specs:
        if spec.display_name == selected_name:
            target = spec
            break
    if target is None:
        return '', ''
    kind, payload = preview_attachment(target)
    if kind == 'html':
        return payload, ''
    return '', payload


@ui_error_wrapper(extra_outputs=("", ""))
def start_campaign(token_files, leads_file, send_delay_seconds, mode,
                   email_content_mode, attachment_folder, invoice_format,
                   support_number, advance_header=False, force_header=False, sender_name_type=None, content_template=None,
                   subject_template=None, body_template=None, auth_mode: str = 'oauth'):
    """Generator used by the Gradio UI button to stream campaign events."""
    log_lines: List[str] = []
    status = "Waiting"
    summary = ""

    gmass_status, gmass_rows = build_gmass_preview(mode, token_files, auth_mode=auth_mode)
    if gmass_status == "" and gmass_rows:
        # Defensive guard: avoid mismatched state
        gmass_rows = []
    gmass_markdown = gmass_rows_to_markdown(gmass_rows)

    events = campaign_events(
        token_files=token_files,
        leads_file=leads_file,
        send_delay_seconds=send_delay_seconds,
        mode=mode,
        content_template=content_template,
        subject_template=subject_template,
        body_template=body_template,
        email_content_mode=email_content_mode,
        attachment_format='pdf',
        invoice_format=invoice_format,
        support_number=support_number,
        advance_header=advance_header,
        force_header=force_header,
        sender_name_type=sender_name_type,
        attachment_folder=attachment_folder,
        auth_mode=auth_mode,
        manual_config=None,
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
            yield (_build_output(log_lines, status, summary), gmass_status, gmass_markdown)
            return
        elif kind == 'progress':
            status = f"Total {event['successes']}/{event['total']}"
            log_lines.append(_format_progress(event))
        elif kind == 'done':
            summary = event['message']
        else:
            log_lines.append(str(event))

        yield (_build_output(log_lines, status, summary), gmass_status, gmass_markdown)

    # Final emit to ensure summary is visible
    yield (_build_output(log_lines, status, summary or "Completed"), gmass_status, gmass_markdown)


@ui_error_wrapper(extra_outputs=("", ""))
def run_unified_campaign(
    active_ui_mode,
    token_files,
    leads_file,
    send_delay_seconds,
    mode,
    email_content_mode,
    attachment_folder,
    invoice_format,
    support_number,
    manual_subject,
    manual_body,
    manual_body_is_html,
    manual_body_image_enabled,
    manual_randomize_html,
    manual_tfn,
    manual_extra_tags,
    manual_attachment_enabled,
    manual_attachment_mode,
    manual_attachment_files,
    manual_inline_html,
    manual_inline_name,
    manual_sender_name,
    manual_change_name,
    manual_sender_type,
    advance_header=False,
    force_header=False,
    auth_mode: str = 'oauth',
    sender_name_type=None,
    content_template=None,
    subject_template=None,
    body_template=None,
):
    selected_mode = (active_ui_mode or 'automated').strip().lower()
    if selected_mode == 'manual':
        generator = start_manual_campaign(
            token_files,
            leads_file,
            send_delay_seconds,
            mode,
            manual_subject,
            manual_body,
            manual_body_is_html,
            manual_body_image_enabled,
            manual_randomize_html,
            manual_tfn,
            manual_extra_tags,
            manual_attachment_enabled,
            manual_attachment_mode,
            manual_attachment_files,
            manual_inline_html,
            manual_inline_name,
            manual_sender_name,
            manual_change_name,
            manual_sender_type,
            advance_header,
            force_header,
            auth_mode,
        )
        for output in generator:
            yield (output, "", "")
        return

    generator = start_campaign(
        token_files,
        leads_file,
        send_delay_seconds,
        mode,
        email_content_mode,
        attachment_folder,
        invoice_format,
        support_number,
        advance_header,
        force_header,
        sender_name_type,
        content_template,
        subject_template,
        body_template,
        auth_mode,
    )
    for output in generator:
        yield output

