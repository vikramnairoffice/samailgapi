import base64
import datetime
import glob
import os
import random
import smtplib
import mimetypes
import imaplib
import ssl
import re
import time
from queue import Queue
from threading import Thread
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.text import MIMEText
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from email.utils import formatdate, make_msgid
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from content import (
    SEND_DELAY_SECONDS,
    PDF_ATTACHMENT_DIR,
    IMAGE_ATTACHMENT_DIR,
    generate_sender_name,
    content_manager,
)
from content_data.content_loader import load_default_gmass_recipients
from invoice import InvoiceGenerator
from manual_mode import ManualConfig

GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SCOPES = ['https://mail.google.com/']


GMAIL_SMTP_HOST = 'smtp.gmail.com'
GMAIL_SMTP_PORT = 587
GMAIL_IMAP_HOST = 'imap.gmail.com'


_EXTRA_MIME_TYPES = {
    '.heic': 'image/heif',
    '.heif': 'image/heif',
}




def update_file_stats(token_files, leads_file, auth_mode: str = 'oauth'):
    """Return simple status strings for credential and lead uploads."""
    mode = (auth_mode or 'oauth').lower()
    if mode in {'app_password', 'app-password', 'app password'}:
        accounts, errors = load_app_password_files(token_files)
        if accounts:
            token_msg = f"{len(accounts)} app password(s) parsed"
        else:
            token_msg = "No app password entries found"
        if errors:
            token_msg += f"; issues: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                token_msg += '; more issues omitted'
    else:
        token_count = len(token_files or [])
        token_msg = f"{token_count} token file(s) selected" if token_count else "No token files uploaded"

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

def update_attachment_stats(include_pdfs: bool, include_images: bool) -> str:
    """Return a short summary of available attachments on disk."""
    pdf_count = len(glob.glob(os.path.join(PDF_ATTACHMENT_DIR, "*.pdf"))) if include_pdfs and os.path.exists(PDF_ATTACHMENT_DIR) else 0
    img_count = 0
    if include_images and os.path.exists(IMAGE_ATTACHMENT_DIR):
        img_count = len(glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.jpg")))
        img_count += len(glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.png")))
    stats = []
    if include_pdfs:
        stats.append(f"PDFs: {pdf_count}")
    if include_images:
        stats.append(f"Images: {img_count}")
    return " | ".join(stats) if stats else "No attachments selected"


def load_gmail_token(token_path):
    """Load a Gmail token JSON file, refresh if needed, and return (email, credentials)."""
    token_path = str(token_path)
    creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("Gmail credentials are invalid and cannot be refreshed.")

    if not creds.token:
        raise RuntimeError("Gmail credentials did not provide an access token.")

    response = requests.get(
        GMAIL_PROFILE_URL,
        headers={'Authorization': f'Bearer {creds.token}'},
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Failed to verify Gmail token ({response.status_code}): {response.text}")

    profile = response.json()
    email = profile.get('emailAddress')
    if not email:
        raise RuntimeError("Gmail profile response did not include an email address.")

    return email, creds


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
    message['From'] = from_header or 'me'
    message['Subject'] = subject
    subtype = 'html' if str(body_subtype).lower() == 'html' else 'plain'
    message.attach(MIMEText(body, subtype))

    if advance_header:
        message.add_header('X-Sender', from_header)
        message.add_header('Date', formatdate(datetime.datetime.utcnow().timestamp(), localtime=False))
        message.add_header('X-Sender-Identity', from_header)
        message.add_header('Message-ID', make_msgid())

    if force_header:
        message.add_header('Received-SPF', f"Pass (gmail.com: domain of {from_header} designates 192.0.2.1 as permitted sender)")
        message.add_header('Authentication-Results', f"mx.google.com; spf=pass smtp.mailfrom={from_header}; dkim=pass; dmarc=pass")
        message.add_header('ARC-Authentication-Results', 'i=1; mx.google.com; spf=pass; dkim=pass; dmarc=pass')
        message.add_header('X-Sender-Reputation-Score', '90')

    _attach_files(message, attachments)

    return message


def send_gmail_message(creds, sender_email, to_email, subject, body, attachments=None,
                        advance_header=False, force_header=False, body_subtype: str = 'plain'):
    """Send an email via the Gmail REST API using existing credentials."""
    if not creds or not getattr(creds, 'token', None):
        raise RuntimeError("Valid Gmail credentials with an access token are required to send messages.")

    message = MIMEMultipart()
    message['To'] = to_email
    message['From'] = sender_email or 'me'
    message['Subject'] = subject
    subtype = 'html' if str(body_subtype).lower() == 'html' else 'plain'
    message.attach(MIMEText(body, subtype))

    if advance_header:
        message.add_header('X-Sender', sender_email)
        message.add_header('Date', formatdate(datetime.datetime.utcnow().timestamp(), localtime=False))
        message.add_header('X-Sender-Identity', sender_email)
        message.add_header('Message-ID', make_msgid())

    if force_header:
        message.add_header('Received-SPF', f"Pass (gmail.com: domain of {sender_email} designates 192.0.2.1 as permitted sender)")
        message.add_header('Authentication-Results', f"mx.google.com; spf=pass smtp.mailfrom={sender_email}; dkim=pass; dmarc=pass")
        message.add_header('ARC-Authentication-Results', 'i=1; mx.google.com; spf=pass; dkim=pass; dmarc=pass')
        message.add_header('X-Sender-Reputation-Score', '90')

    _attach_files(message, attachments)

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




def _imap_messages_total(imap_conn, mailbox: str) -> int:
    status, _ = imap_conn.select(mailbox, readonly=True)
    if status != 'OK':
        raise RuntimeError(f'IMAP select failed for {mailbox}: {status}')

    status, data = imap_conn.status(mailbox, '(MESSAGES)')
    if status != 'OK' or not data:
        raise RuntimeError(f'IMAP status failed for {mailbox}: {status}')

    raw = data[0]
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', 'ignore')
    match = re.search(r'MESSAGES\s+(\d+)', raw or '')
    if not match:
        return 0
    try:
        return int(match.group(1))
    except ValueError:
        return 0



def fetch_mailbox_totals_app_password(email: str, password: str) -> tuple[int, int]:
    imap_conn = imaplib.IMAP4_SSL(GMAIL_IMAP_HOST)
    try:
        imap_conn.login(email, password)
        inbox_total = _imap_messages_total(imap_conn, 'INBOX')
        sent_total = 0
        for candidate in ('[Gmail]/Sent Mail', '[Gmail]/Sent', 'Sent', 'Sent Mail'):
            try:
                sent_total = _imap_messages_total(imap_conn, candidate)
                break
            except Exception:
                continue
        return inbox_total, sent_total
    finally:
        try:
            imap_conn.logout()
        except Exception:
            pass


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
    valid_accounts: List[Dict[str, Any]] = []
    errors: List[str] = []

    for file_obj in token_files or []:
        path = getattr(file_obj, 'name', None) or str(file_obj)
        try:
            email, creds = load_gmail_token(path)
        except Exception as exc:
            errors.append(f"{os.path.basename(path)}: {exc}")
            continue
        valid_accounts.append({'email': email, 'creds': creds, 'path': path, 'auth_type': 'oauth'})

    return valid_accounts, errors



def load_app_password_files(token_files: Optional[List[Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    accounts: List[Dict[str, Any]] = []
    errors: List[str] = []

    for file_obj in token_files or []:
        path = getattr(file_obj, 'name', None) or str(file_obj)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    if line.count(',') != 1:
                        errors.append(f"{os.path.basename(path)} line {line_number}: invalid entry")
                        continue
                    parts = [segment.strip() for segment in line.split(',', 1)]
                    if len(parts) != 2 or not parts[0] or not parts[1]:
                        errors.append(f"{os.path.basename(path)} line {line_number}: invalid entry")
                        continue
                    email, password = parts
                    accounts.append({
                        'email': email,
                        'password': password,
                        'path': f"{path}:{line_number}",
                        'auth_type': 'app_password',
                    })
        except Exception as exc:
            errors.append(f"{os.path.basename(path)}: {exc}")

    return accounts, errors


def load_accounts(token_files: Optional[List[Any]], auth_mode: str = 'oauth') -> Tuple[List[Dict[str, Any]], List[str]]:
    mode = (auth_mode or 'oauth').lower()
    if mode in {'app_password', 'app-password', 'app password'}:
        return load_app_password_files(token_files)
    return load_token_files(token_files)


def read_leads_file(leads_file) -> List[str]:
    """Read leads from a simple text file."""
    if not leads_file:
        return []
    path = getattr(leads_file, 'name', None) or str(leads_file)
    leads: List[str] = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
        for line in handle:
            email = line.strip()
            if email:
                leads.append(email)
    return leads


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
    attachments: Dict[str, str] = {}

    if include_pdfs and os.path.exists(PDF_ATTACHMENT_DIR):
        pdf_files = glob.glob(os.path.join(PDF_ATTACHMENT_DIR, "*.pdf"))
        if pdf_files:
            pdf_path = random.choice(pdf_files)
            attachments[os.path.basename(pdf_path)] = pdf_path

    if include_images and os.path.exists(IMAGE_ATTACHMENT_DIR):
        image_files = glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.jpg"))
        image_files += glob.glob(os.path.join(IMAGE_ATTACHMENT_DIR, "*.png"))
        if image_files:
            image_path = random.choice(image_files)
            attachments[os.path.basename(image_path)] = image_path

    return attachments


def choose_random_file_from_folder(folder_path: str) -> Dict[str, str]:
    """Select a random file from the provided folder regardless of extension."""
    folder = os.path.abspath(os.path.expanduser(folder_path))
    if not os.path.exists(folder):
        raise RuntimeError(f"Attachment folder not found: {folder}")
    if not os.path.isdir(folder):
        raise RuntimeError(f"Attachment folder is not a directory: {folder}")

    try:
        files = [entry.path for entry in os.scandir(folder) if entry.is_file()]
    except Exception as exc:
        raise RuntimeError(f"Failed to read attachment folder: {exc}") from exc

    if not files:
        raise RuntimeError(f"No files available in attachment folder: {folder}")

    chosen_path = random.choice(files)
    return {os.path.basename(chosen_path): chosen_path}


def build_attachments(config: Dict[str, Any], invoice_gen: InvoiceGenerator, lead_email: str) -> Dict[str, str]:
    """Build attachment mapping for the current email."""
    mode = (config.get('email_content_mode') or 'Attachment').lower()
    if mode == 'attachment':
        folder_override = (config.get('attachment_folder') or '').strip()
        if folder_override:
            return choose_random_file_from_folder(folder_override)
        fmt = (config.get('attachment_format') or 'pdf').lower()
        include_pdfs = fmt == 'pdf'
        include_images = fmt == 'image'
        return choose_random_attachments(include_pdfs, include_images)

    invoice_format = (config.get('invoice_format') or 'pdf').lower()
    support_number = config.get('support_number') or ''
    invoice_path = invoice_gen.generate_for_recipient(lead_email, support_number, invoice_format)
    return {os.path.basename(invoice_path): invoice_path}


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

    delay_seconds = float(send_delay_seconds or 0.0)
    if delay_seconds < 0:
        delay_seconds = 0.0

    if (mode or '').lower() == 'gmass':
        assignments = [list(load_default_gmass_recipients()) for _ in range(account_count)]
    else:
        assignments = distribute_leads(leads, account_count)

    result_queue: Queue = Queue()
    sentinel = object()
    threads: List[Thread] = []
    invoice_factory = InvoiceGenerator

    def worker(account: Dict[str, Any], account_leads: List[str]) -> None:
        try:
            invoice_gen = invoice_factory()
            for lead_email in account_leads:
                try:
                    success, message = send_single_email(account, lead_email, config, invoice_gen)
                except Exception as exc:  # pragma: no cover - defensive guard
                    success, message = False, str(exc)
                result_queue.put({
                    'account': account['email'],
                    'lead': lead_email,
                    'success': success,
                    'message': message,
                })
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
        finally:
            result_queue.put(sentinel)

    for account, account_leads in zip(accounts, assignments):
        thread = Thread(target=worker, args=(account, account_leads), daemon=True)
        thread.start()
        threads.append(thread)

    if not threads:
        return

    active_workers = len(threads)
    try:
        while active_workers:
            item = result_queue.get()
            if item is sentinel:
                active_workers -= 1
                continue
            yield item
    finally:
        for thread in threads:
            thread.join()

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

    try:
        delay_seconds = float(send_delay_seconds)
    except (TypeError, ValueError):
        delay_seconds = SEND_DELAY_SECONDS
    else:
        if delay_seconds < 0:
            delay_seconds = 0.0

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







