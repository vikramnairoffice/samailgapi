"""Header utilities shared across send and content builders."""

from __future__ import annotations

import random
import string
from datetime import datetime
from email.message import Message
from email.utils import formatdate, make_msgid
from typing import Callable, Dict, Iterable, Optional

from content_data.content_loader import load_default_subjects

from .spintax import TagContext, generate_tag_value

R1_PREFIX_CHOICES = ["Automatic", "Automated", "FWD", "FWD.", "FWD:"]
R1_KEYWORD_CHOICES = [
    "Automatic",
    "Debit",
    "Delievery",
    "Deposit",
    "Details",
    "Project",
    "Proposal",
    "Ticket",
    "Recipet",
    "Refund",
    "Resgiesterd",
    "Re-Print",
    "Receipt",
    "Registrations",
    "Reimbuersement",
    "Reminder",
    "Renewal",
    "Reply",
    "Report",
    "Research",
    "Reservation",
    "Snapshot",
    "Subscription",
    "Updated",
    "Paid",
    "Log",
    "Inovice",
    "Billing",
    "Alert",
    "Slip",
    "Statement",
    "System",
    "Trasnction",
    "Access",
    "Conference",
    "Confirmation",
    "Digital",
    "Generated",
    "Print",
    "Record",
    "Deliver",
    "Upgrade",
    "Service",
    "Upload",
    "Important",
]
R1_NAME_TAGS = ["{{NAME}}", "{{FNAME}}", "{{UNAME}}"]
R1_DATE_TAGS = ["{{DATE}}", "{{DATE1}}", "{{DATETIME}}"]
R1_STRING_TAGS = [
    "{{INV}}",
    "{{UKEY}}",
    "{{TRX}}",
    "{{SMLETT}}",
    "{{LMLETT}}",
    "{{SCLETT}}",
    "{{LCLETT}}",
    "{{SLLETT}}",
    "{{LLLETT}}",
    "{{INUM}}",
    "{{LNUM}}",
]

R1_DELIMITER = " | "

__all__ = [
    "R1_PREFIX_CHOICES",
    "R1_KEYWORD_CHOICES",
    "R1_NAME_TAGS",
    "R1_DATE_TAGS",
    "R1_STRING_TAGS",
    "R1_DELIMITER",
    "generate_r1_tag_entry",
    "generate_subject_with_prefix_pattern",
    "apply_optional_headers",
]

def generate_r1_tag_entry(tag_context: Optional[TagContext] = None) -> str:
    """Assemble the R1 Tag content string using the shared tag system."""
    components: list[str] = []
    if random.random() < 0.5:
        components.append(random.choice(R1_PREFIX_CHOICES))

    core_parts = [
        random.choice(R1_KEYWORD_CHOICES),
        generate_tag_value(random.choice(R1_NAME_TAGS), tag_context),
        generate_tag_value(random.choice(R1_DATE_TAGS), tag_context),
        generate_tag_value(random.choice(R1_STRING_TAGS), tag_context),
    ]
    random.shuffle(core_parts)

    if not components and core_parts and core_parts[0] in R1_PREFIX_CHOICES:
        core_parts.append(core_parts.pop(0))

    components.extend(core_parts)
    return R1_DELIMITER.join(components)

def generate_subject_with_prefix_pattern() -> Dict[str, object]:
    """Generate subject metadata with deterministic structure for R1 headers."""
    base_subject = random.choice(load_default_subjects())
    prefix_array = [
        'invo_', 'invce ', 'invoice-', 'po#', 'po ', 'po_', 'doc_', 'doc ', 'doc-', 'doc#',
        'po-', 'invoxx#', 'inv', 'inv_', 'inv#', 'invv-'
    ]
    selected_prefix = random.choice(prefix_array)
    letter1 = random.choice(string.ascii_uppercase)
    letter2 = random.choice(string.ascii_uppercase)
    letter_pattern = f"{letter1}{letter2}"
    number_pattern = random.randint(9999, 99999)
    prefix_pattern = f"{selected_prefix}{letter_pattern}{number_pattern}"
    return {
        "base_subject": base_subject,
        "selected_prefix": selected_prefix,
        "letter_pattern": letter_pattern,
        "number_pattern": number_pattern,
        "prefix_pattern": prefix_pattern,
        "final_subject": f"{base_subject} {prefix_pattern}",
    }

def apply_optional_headers(
    message: Message,
    from_value: str,
    *,
    advance_header: bool,
    force_header: bool,
    date_factory: Callable[[float], str] = formatdate,
    msgid_factory: Callable[[], str] = make_msgid,
    now_factory: Callable[[], datetime] = datetime.utcnow,
) -> None:
    """Attach optional R1 headers to the outgoing MIME message."""
    if advance_header:
        message.add_header('X-Sender', from_value)
        message.add_header('Date', date_factory(now_factory().timestamp(), localtime=False))
        message.add_header('X-Sender-Identity', from_value)
        message.add_header('Message-ID', msgid_factory())

    if force_header:
        message.add_header(
            'Received-SPF',
            f"Pass (gmail.com: domain of {from_value} designates 192.0.2.1 as permitted sender)",
        )
        message.add_header(
            'Authentication-Results',
            f"mx.google.com; spf=pass smtp.mailfrom={from_value}; dkim=pass; dmarc=pass",
        )
        message.add_header(
            'ARC-Authentication-Results',
            'i=1; mx.google.com; spf=pass; dkim=pass; dmarc=pass',
        )
        message.add_header('X-Sender-Reputation-Score', '90')
