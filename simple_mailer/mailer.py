import base64
import datetime
import glob
import os
import random
import smtplib
import mimetypes
import ssl
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.text import MIMEText
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from email.utils import formatdate, make_msgid
from simple_mailer.credentials import app_password as credential_app_password
from simple_mailer.credentials import token_json as credential_token_json
from simple_mailer.credentials import validation as credential_validation

from .content import (
    SEND_DELAY_SECONDS,
    generate_sender_name,
    content_manager,
)
from content_data.content_loader import load_default_gmass_recipients
from simple_mailer.core import attachments as attachments_adapter
from simple_mailer.core.invoice import InvoiceGenerator
from simple_mailer.core.r1_headers import apply_optional_headers
from simple_mailer.core.throttling import coerce_delay, sleep
from manual_mode import ManualConfig
from simple_mailer.core import leads_txt
from simple_mailer.exec.threadpool import ThreadPoolExecutor

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


GMAIL_SMTP_HOST = 'smtp.gmail.com'
GMAIL_SMTP_PORT = 587


_EXTRA_MIME_TYPES = {
    '.heic': 'image/heif',
    '.heif': 'image/heif',
}




def update_file_stats(token_files, leads_file, auth_mode: str = 'oauth'):
    """Return simple status strings for credential and lead uploads."""
    summary = credential_validation.validate_files(token_files, auth_mode)
    token_msg = summary.status

    leads_msg = "Using GMass default seed list."
    if leads_file:
        path = getattr(leads_file, 'name', None) or str(leads_file)
        lead_count = 0
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                lead_count = sum(1 for line in handle if line.strip())
        except Exception:
            leads_msg = f"Leads file ready: {os.path.basename(path)}"
        else:
            if lead_count:
                leads_msg = f"{lead_count} lead(s) loaded from {os.path.basename(path)}"
            else:
                leads_msg = f"No leads found in {os.path.basename(path)}"
    return token_msg, leads_msg


def _create_attachment_part(name: str, path: str) -> MIMEBase:
    extension = os.path.splitext(name)[1].lower()
    ctype = _EXTRA_MIME_TYPES.get(extension)
    if not ctype:
        guessed, encoding = mimetypes.guess_type(name)
        if encoding:
            guessed = None
        ctype = guessed or 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    with open(path, 'rb') as handle:
        payload = handle.read()
    part = MIMEBase(maintype, subtype)
    part.set_payload(payload)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{name}"')
    part.set_param('name', name, header='Content-Type')
    return part


def _attach_files(message: MIMEMultipart, attachments: Optional[Dict[str, str]]) -> None:
    for name, path in (attachments or {}).items():
        part = _create_attachment_part(name, path)
        message.attach(part)





def _build_mime_message(from_header: str, to_email: str, subject: str, body: str, attachments=None,
                        advance_header: bool = False, force_header: bool = False, body_subtype: str = 'plain'):
    message = MIMEMultipart()
    message['To'] = to_email
    from_value = from_header or 'me'
    message['From'] = from_value
    message['Subject'] = subject
    subtype = 'html' if str(body_subtype).lower() == 'html' else 'plain'
    message.attach(MIMEText(body, subtype))

    apply_optional_headers(
        message,
        from_value,
        advance_header=advance_header,
        force_header=force_header,
        date_factory=formatdate,
        msgid_factory=make_msgid,
    )

    _attach_files(message, attachments)

    return message

def send_gmail_message(creds, sender_email, to_email, subject, body, attachments=None,
                        advance_header=False, force_header=False, body_subtype: str = 'plain'):
    """Send an email via the Gmail REST API using existing credentials."""
    if not creds or not getattr(creds, 'token', None):
        raise RuntimeError("Valid Gmail credentials with an access token are required to send messages.")

    message = _build_mime_message(
        sender_email,
        to_email,
        subject,
        body,
        attachments,
        advance_header,
        force_header,
        body_subtype,
    )
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    response = requests.post(
        GMAIL_SEND_URL,
        headers={
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        },
        json={'raw': raw_message},
        timeout=15,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Gmail send failed ({response.status_code}): {response.text}")

    return response.json()






def fetch_mailbox_totals_app_password(email: str, password: str) -> tuple[int, int]:
    return credential_app_password.fetch_mailbox_totals(email, password)


def send_app_password_message(login_email: str, from_header: str, app_password: str, to_email: str, subject: str, body: str,
                             attachments=None, advance_header: bool = False, force_header: bool = False, body_subtype: str = 'plain') -> None:
    attachments = attachments or {}
    message = _build_mime_message(from_header or login_email, to_email, subject, body, attachments, advance_header, force_header, body_subtype)
    context = ssl.create_default_context()
    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(login_email, app_password)
        smtp.sendmail(login_email, to_email, message.as_string())


def load_token_files(token_files: Optional[List[Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Validate uploaded token files and return (valid_accounts, error_messages)."""
    _, file_inputs, in_memory_errors = credential_validation.partition_token_inputs(token_files)
    accounts, errors = credential_validation.load_oauth_entries(file_inputs, loader=credential_token_json.load)
    if in_memory_errors:
        errors = list(errors) + in_memory_errors
    return accounts, errors



def load_app_password_files(token_files: Optional[List[Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parse uploaded app password files and return (accounts, errors)."""
    _, file_inputs, in_memory_errors = credential_validation.partition_token_inputs(token_files)
    accounts, errors = credential_validation.load_app_password_entries(file_inputs)
    if in_memory_errors:
        errors = list(errors) + in_memory_errors
    return accounts, errors



def load_accounts(token_files: Optional[List[Any]], auth_mode: str = 'oauth') -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return parsed account entries and any validation errors for the given mode."""
    mode = credential_validation.normalize_mode(auth_mode)
    loader = credential_token_json.load if mode != 'app_password' else None
    summary = credential_validation.validate_files(token_files, auth_mode, loader=loader)
    return summary.accounts, summary.errors


def read_leads_file(leads_file) -> List[str]:
    """Read leads from a simple text file."""
    return leads_txt.read(leads_file)


def distribute_leads(leads: List[str], account_count: int) -> List[List[str]]:
    """Evenly split leads across accounts."""
    if account_count <= 0:
        return []

    total = len(leads)
    if total == 0:
        return [[] for _ in range(account_count)]

    base, remainder = divmod(total, account_count)
    distribution: List[List[str]] = []
    start = 0

    for idx in range(account_count):
        take = base + (1 if idx < remainder else 0)
        end = start + take
        distribution.append(leads[start:end])
        start = end

    return distribution


def choose_random_attachments(include_pdfs: bool, include_images: bool) -> Dict[str, str]:
    """Select random attachments from disk based on the requested formats."""
    return attachments_adapter.choose_static(include_pdfs, include_images)


def choose_random_file_from_folder(folder_path: str) -> Dict[str, str]:
    """Select a random file from the provided folder regardless of extension."""
    return attachments_adapter.choose_from_folder(folder_path)


def build_attachments(config: Dict[str, Any], invoice_gen: InvoiceGenerator, lead_email: str) -> Dict[str, str]:
    """Build attachment mapping for the current email."""
    return attachments_adapter.build(
        config,
        lead_email,
        invoice_factory=lambda: invoice_gen,
    )


def compose_email(account_email: str, config: Dict[str, Any]) -> Tuple[str, str, str]:
    """Generate subject, body, and friendly from header."""
    subject_template = config.get('subject_template')
    body_template = config.get('body_template')
    fallback_template = config.get('content_template') or 'own_proven'
    subject_choice = subject_template or fallback_template
    body_choice = body_template or fallback_template
    subject, body = content_manager.get_subject_and_body(subject_choice, body_choice)
    sender_name_type = config.get('sender_name_type') or 'business'
    sender_name = generate_sender_name(sender_name_type)
    from_header = f"{sender_name} <{account_email}>"
    return subject, body, from_header


def send_single_email(account: Dict[str, Any], lead_email: str, config: Dict[str, Any], invoice_gen: InvoiceGenerator) -> Tuple[bool, str]:
    """Send one email and return (success, message)."""
    manual_config = config.get('manual_config')
    body_subtype = 'plain'

    if isinstance(manual_config, ManualConfig) and getattr(manual_config, 'enabled', False):
        context = manual_config.build_context(lead_email)
        subject = manual_config.render_subject(context)
        body, body_subtype = manual_config.render_body(context)
        context['content'] = body
        attachments = manual_config.build_attachments(context)
        sender_name = manual_config.resolve_sender_name(config.get('sender_name_type') or 'business')
        from_header = f"{sender_name} <{account['email']}>"
    else:
        subject, body, from_header = compose_email(account['email'], config)
        attachments = build_attachments(config, invoice_gen, lead_email)

    try:
        advance_flag = bool(config.get('advance_header'))
        force_flag = bool(config.get('force_header'))
        auth_type = (account.get('auth_type') or 'oauth').lower()
        if auth_type in {'app_password', 'app-password', 'app password'}:
            send_app_password_message(
                login_email=account['email'],
                from_header=from_header,
                app_password=account['password'],
                to_email=lead_email,
                subject=subject,
                body=body,
                attachments=attachments,
                advance_header=advance_flag,
                force_header=force_flag,
                body_subtype=body_subtype,
            )
        else:
            send_gmail_message(
                account['creds'],
                from_header,
                lead_email,
                subject,
                body,
                attachments,
                advance_header=advance_flag,
                force_header=force_flag,
                body_subtype=body_subtype,
            )
        return True, f"Sent to {lead_email}"
    except Exception as exc:
        return False, str(exc)





def run_campaign(accounts: List[Dict[str, Any]], mode: str, leads: List[str], config: Dict[str, Any], send_delay_seconds: float) -> Iterable[Dict[str, Any]]:
    """Send emails per account concurrently and yield their progress."""
    account_count = len(accounts)
    if account_count <= 0:
        return

    delay_seconds = coerce_delay(send_delay_seconds, default=0.0)

    if (mode or '').lower() == 'gmass':
        assignments = [list(load_default_gmass_recipients()) for _ in range(account_count)]
    else:
        assignments = distribute_leads(leads, account_count)

    workers = list(zip(accounts, assignments))
    if not workers:
        return

    executor = ThreadPoolExecutor(max_workers=account_count, thread_name_prefix='MailerWorker')
    invoice_factory = InvoiceGenerator

    def _worker(payload: Tuple[Dict[str, Any], List[str]]) -> Iterable[Dict[str, Any]]:
        account, account_leads = payload
        invoice_gen = invoice_factory()
        for lead_email in account_leads:
            try:
                success, message = send_single_email(account, lead_email, config, invoice_gen)
            except Exception as exc:  # pragma: no cover - defensive guard
                success, message = False, str(exc)
            yield {
                'account': account['email'],
                'lead': lead_email,
                'success': success,
                'message': message,
            }
            sleep(delay_seconds)

    yield from executor.stream(workers, _worker)


def campaign_events(token_files: Optional[List[Any]], leads_file, send_delay_seconds: float, mode: str,
                    content_template: Optional[str] = None, subject_template: Optional[str] = None,
                    body_template: Optional[str] = None, email_content_mode: str = "Attachment", attachment_format: str = "pdf",
                    invoice_format: str = "pdf", support_number: str = "", sender_name_type: str = "",
                    attachment_folder: str = "", advance_header: bool = False, force_header: bool = False,
                    auth_mode: str = "oauth", manual_config: Optional[ManualConfig] = None) -> Iterable[Dict[str, Any]]:
    """High-level generator that validates inputs and yields campaign events."""
    accounts, token_errors = load_accounts(token_files, auth_mode=auth_mode)
    for error in token_errors:
        yield {'kind': 'token_error', 'message': error}

    if not accounts:
        yield {'kind': 'fatal', 'message': 'No valid Gmail credentials were found.'}
        return

    mode = (mode or 'gmass').lower()
    leads: List[str]
    if mode == 'gmass':
        leads = list(load_default_gmass_recipients())
    else:
        leads = read_leads_file(leads_file)
        if not leads:
            yield {'kind': 'fatal', 'message': 'Leads mode selected but no leads were found.'}
            return


    fallback_template = content_template or 'own_proven'
    subject_choice = subject_template or fallback_template
    body_choice = body_template or fallback_template

    config = {
        'content_template': fallback_template,
        'subject_template': subject_choice,
        'body_template': body_choice,
        'email_content_mode': email_content_mode,
        'attachment_format': attachment_format,
        'attachment_folder': attachment_folder,
        'invoice_format': invoice_format,
        'support_number': support_number,
        'sender_name_type': sender_name_type,
        'advance_header': advance_header,
        'force_header': force_header,
        'manual_config': manual_config,
    }

    delay_seconds = coerce_delay(send_delay_seconds, default=SEND_DELAY_SECONDS)

    total_attempts = 0
    successes = 0

    for result in run_campaign(accounts, mode, leads, config, delay_seconds):
        total_attempts += 1
        successes += 1 if result['success'] else 0
        yield {
            'kind': 'progress',
            'total': total_attempts,
            'successes': successes,
            **result,
        }

    yield {
        'kind': 'done',
        'message': f"Completed {total_attempts} send attempt(s) with {successes} success(es).",
    }








