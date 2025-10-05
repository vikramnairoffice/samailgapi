import random
import string
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Mapping, Optional

from faker import Faker
from content_data.content_loader import (
    load_default_subjects, load_default_gmass_recipients,
    load_body_parts, load_bodyB
)


fake = Faker()




PDF_ATTACHMENT_DIR = "./pdfs"
IMAGE_ATTACHMENT_DIR = "./images"
SEND_DELAY_SECONDS = 4.5

SENDER_NAME_TYPES = ["business", "personal"]
DEFAULT_SENDER_NAME_TYPE = "business"

BUSINESS_SUFFIXES = [
    "Foundation", "Fdn", "Consulting", "Co", "Services", "Ltd", "Instituto", "Institute", "Corp.",
    "Trustees", "Incorporated", "Technologies", "Assoc.", "Trustee", "Company", "Industries", "LLP",
    "Corp", "Assoc", "Associazione", "Trust", "Solutions", "Group", "Associa", "Corporation",
    "Trusts", "Corpo", "Inc", "PC", "LLC", "Institutes", "Associates"
]

R1_ALPHA_POOL = string.ascii_uppercase + string.digits
R1_DELIMITER = " | "



from core import spintax as spintax_adapter

TagContext = spintax_adapter.TagContext
TagDefinition = spintax_adapter.TagDefinition
TAG_DEFINITIONS = spintax_adapter.TAG_DEFINITIONS
LEGACY_TAG_ALIASES = spintax_adapter.LEGACY_TAG_ALIASES


def render_tagged_content(text: str, context: TagContext = None) -> str:
    """Replace tag tokens in text using the provided context."""
    return spintax_adapter.render_tags(text, context)


def expand_spintax(text: str, rng: Optional[random.Random] = None) -> str:
    """Resolve {a|b|c} style spintax expressions within text."""
    return spintax_adapter.expand_spintax(text, rng)


def get_tag_definitions() -> List[TagDefinition]:
    """Return tag definitions preserving declaration order."""
    return spintax_adapter.get_tag_definitions()


def generate_tag_value(tag_name: str, context: TagContext = None) -> str:
    """Return a realized tag value for the provided tag name."""
    return spintax_adapter.generate_tag_value(tag_name, context)


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


def generate_r1_tag_entry(tag_context: TagContext = None) -> str:
    """Assemble the R1 Tag content string using the shared tag system."""
    components: List[str] = []
    if random.random() < 0.5:
        components.append(random.choice(R1_PREFIX_CHOICES))

    core_parts = [
        random.choice(R1_KEYWORD_CHOICES),
        generate_tag_value(random.choice(R1_NAME_TAGS), tag_context),
        generate_tag_value(random.choice(R1_DATE_TAGS), tag_context),
        generate_tag_value(random.choice(R1_STRING_TAGS), tag_context),
    ]
    random.shuffle(core_parts)

    if not components and core_parts[0] in R1_PREFIX_CHOICES:
        core_parts.append(core_parts.pop(0))

    components.extend(core_parts)
    return R1_DELIMITER.join(components)


def generate_business_name():
    """Generate business name: FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix"""
    first_name = fake.first_name()
    random_letters_1 = fake.lexify("??").upper()
    business_word = fake.word().capitalize()
    random_letters_2 = fake.lexify("??").upper()
    suffix = random.choice(BUSINESS_SUFFIXES)
    
    return f"{first_name} {random_letters_1} {business_word} {random_letters_2} {suffix}"

def generate_personal_name():
    """Generate personal name: FirstName + RandomTwoLetters"""
    first_name = fake.first_name()
    random_letters = fake.lexify("? ?").upper()
    
    return f"{first_name} {random_letters[0]}. {random_letters[2]}."

def generate_sender_name(name_type="business"):
    """
    Generate sender name based on type
    Args:
        name_type: "business" or "personal"
    Returns:
        Generated sender name string
    """
    if name_type == "business":
        return generate_business_name()
    elif name_type == "personal":
        return generate_personal_name()
    else:
        return generate_business_name()


class ContentManager:
    """Backend-only content generation - NO UI exposure"""
    
    def __init__(self):
        # Template 1: Own Proven Bodies (Spintax)
        self.body_parts = load_body_parts()
        
        # Template 2: Own content last update (reuses Template 1 part1 + bodyB)
        self.bodyB = load_bodyB()
        
        # Keep default subjects for proven mode
        self.default_subjects = load_default_subjects()
    
    def get_subject_and_body(self, subject_template="own_proven", body_template=None, tag_context: TagContext = None):
        """Return subject/body using independently selected templates."""
        subject_mode = self._normalize_template_choice(subject_template)
        if body_template is None:
            body_template = subject_template
        body_mode = self._normalize_template_choice(body_template)

        if subject_mode == "r1_tag" and body_mode == "r1_tag":
            tag_content = generate_r1_tag_entry(tag_context)
            return tag_content, tag_content

        subject = self._generate_subject(subject_mode, tag_context)
        body = self._generate_body(body_mode, tag_context)
        body = expand_spintax(body)
        return subject, body

    def _normalize_template_choice(self, template: str) -> str:
        value = (template or "own_proven").lower()
        if value in {"gmass_inboxed", "own_last", "own-last"}:
            return "own_last"
        if value == "r1_tag":
            return "r1_tag"
        return "own_proven"

    def _generate_subject(self, mode: str, tag_context: TagContext) -> str:
        if mode == "own_proven":
            return random.choice(load_default_subjects())
        if mode == "own_last":
            return generate_subject_with_prefix_pattern()["final_subject"]
        if mode == "r1_tag":
            return generate_r1_tag_entry(tag_context)
        return random.choice(DEFAULT_SUBJECTS)

    def _generate_body(self, mode: str, tag_context: TagContext) -> str:
        if mode == "own_proven":
            return self._generate_spintax_body()
        if mode == "own_last":
            return self._generate_own_content_last_update()
        if mode == "r1_tag":
            return generate_r1_tag_entry(tag_context)
        return self._generate_spintax_body()

    def _generate_spintax_body(self):
        """Private: Sequential random from each part"""
        return " ".join([
            random.choice(self.body_parts["part1"]),
            random.choice(self.body_parts["part2"]),
            random.choice(self.body_parts["part3"]),
            random.choice(self.body_parts["part4"]),
            random.choice(self.body_parts["part5"])
        ])
    
    def _generate_own_content_last_update(self):
        """Private: Compose body using Template 1 part1 + delimiter + bodyB"""
        first = random.choice(self.body_parts["part1"])  # reuse Template 1 part1
        delim = random.choice([' ', '\n'])
        tail = random.choice(self.bodyB)
        return f"{first}{delim}{tail}"

def generate_subject_with_prefix_pattern():
    """Generate subject with prefix pattern: base_subject + prefix + letters + numbers"""
    base_subject = random.choice(load_default_subjects())
    prefix_array = ['invo_', 'invce ', 'invoice-', 'po#', 'po ', 'po_', 'doc_', 'doc ', 'doc-', 'doc#', 'po-', 'invoxx#', 'inv', 'inv_', 'inv#', 'invv-']
    selected_prefix = random.choice(prefix_array)
    letter1 = random.choice(string.ascii_uppercase)
    letter2 = random.choice(string.ascii_uppercase)
    letter_pattern = f"{letter1}{letter2}"
    number_pattern = random.randint(9999, 99999)
    prefix_pattern = f"{selected_prefix}{letter_pattern}{number_pattern}"
    final_subject = f"{base_subject} {prefix_pattern}"
    
    return {
        "base_subject": base_subject,
        "selected_prefix": selected_prefix,
        "letter_pattern": letter_pattern,
        "number_pattern": number_pattern,
        "prefix_pattern": prefix_pattern,
        "final_subject": final_subject
    }


# Global instance for easy import
content_manager = ContentManager()

