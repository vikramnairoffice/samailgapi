import base64
import glob
import os
import random
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from content import (
    DEFAULT_GMASS_RECIPIENTS,
    SEND_DELAY_SECONDS,
    PDF_ATTACHMENT_DIR,
    IMAGE_ATTACHMENT_DIR,
    generate_sender_name,
    content_manager,
)
from invoice import InvoiceGenerator

GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_SCOPES = ['https://mail.google.com/']


def update_file_stats(token_files, leads_file):
    """Return simple status strings for token and leads uploads."""
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


def send_gmail_message(creds, sender_email, to_email, subject, body, attachments=None):
    """Send an email via the Gmail REST API using existing credentials."""
    if not creds or not getattr(creds, 'token', None):
        raise RuntimeError("Valid Gmail credentials with an access token are required to send messages.")

    message = MIMEMultipart()
    message['To'] = to_email
    message['From'] = sender_email or 'me'
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    for name, path in (attachments or {}).items():
        with open(path, 'rb') as handle:
            part = MIMEApplication(handle.read(), Name=name)
            part['Content-Disposition'] = f'attachment; filename="{name}"'
            message.attach(part)

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
        valid_accounts.append({'email': email, 'creds': creds, 'path': path})

    return valid_accounts, errors


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


def distribute_leads(leads: List[str], account_count: int, leads_per_account: int) -> List[List[str]]:
    """Simple round-robin distribution of leads across accounts."""
    if account_count <= 0:
        return []
    if leads_per_account <= 0:
        leads_per_account = len(leads)

    distribution: List[List[str]] = [[] for _ in range(account_count)]
    iterator = iter(leads)

    for idx in range(account_count):
        for _ in range(leads_per_account):
            try:
                distribution[idx].append(next(iterator))
            except StopIteration:
                return distribution
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
    template = config.get('content_template') or 'own_proven'
    subject, body = content_manager.get_subject_and_body(template)
    sender_name_type = config.get('sender_name_type') or 'business'
    sender_name = generate_sender_name(sender_name_type)
    from_header = f"{sender_name} <{account_email}>"
    return subject, body, from_header


def send_single_email(account: Dict[str, Any], lead_email: str, config: Dict[str, Any], invoice_gen: InvoiceGenerator) -> Tuple[bool, str]:
    """Send one email and return (success, message)."""
    subject, body, from_header = compose_email(account['email'], config)
    attachments = build_attachments(config, invoice_gen, lead_email)

    try:
        send_gmail_message(account['creds'], from_header, lead_email, subject, body, attachments)
        return True, f"Sent to {lead_email}"
    except Exception as exc:
        return False, str(exc)


def run_campaign(accounts: List[Dict[str, Any]], mode: str, leads: List[str], leads_per_account: int, config: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Sequentially send emails for each account and yield progress dictionaries."""
    invoice_gen = InvoiceGenerator()
    account_count = len(accounts)

    if mode == 'gmass':
        assignments = [list(DEFAULT_GMASS_RECIPIENTS) for _ in range(account_count)]
    else:
        assignments = distribute_leads(leads, account_count, leads_per_account)

    for account, account_leads in zip(accounts, assignments):
        for lead_email in account_leads:
            success, message = send_single_email(account, lead_email, config, invoice_gen)
            yield {
                'account': account['email'],
                'lead': lead_email,
                'success': success,
                'message': message,
            }
            time.sleep(SEND_DELAY_SECONDS)


def campaign_events(token_files: Optional[List[Any]], leads_file, leads_per_account: int, mode: str,
                    content_template: str, email_content_mode: str, attachment_format: str,
                    invoice_format: str, support_number: str, sender_name_type: str,
                    attachment_folder: str = '') -> Iterable[Dict[str, Any]]:
    """High-level generator that validates inputs and yields campaign events."""
    accounts, token_errors = load_token_files(token_files)
    for error in token_errors:
        yield {'kind': 'token_error', 'message': error}

    if not accounts:
        yield {'kind': 'fatal', 'message': 'No valid Gmail tokens were found.'}
        return

    mode = (mode or 'gmass').lower()
    leads: List[str]
    if mode == 'gmass':
        leads = list(DEFAULT_GMASS_RECIPIENTS)
    else:
        leads = read_leads_file(leads_file)
        if not leads:
            yield {'kind': 'fatal', 'message': 'Leads mode selected but no leads were found.'}
            return

    try:
        leads_per_account_int = int(leads_per_account or 0)
    except Exception:
        leads_per_account_int = 0

    config = {
        'content_template': content_template,
        'email_content_mode': email_content_mode,
        'attachment_format': attachment_format,
        'attachment_folder': attachment_folder,
        'invoice_format': invoice_format,
        'support_number': support_number,
        'sender_name_type': sender_name_type,
    }

    total_attempts = 0
    successes = 0

    for result in run_campaign(accounts, mode, leads, leads_per_account_int, config):
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
