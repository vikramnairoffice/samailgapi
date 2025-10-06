import random
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
from simple_mailer.core.r1_headers import (
    R1_DELIMITER,
    R1_KEYWORD_CHOICES,
    R1_PREFIX_CHOICES,
    generate_r1_tag_entry,
    generate_subject_with_prefix_pattern,
)
from simple_mailer.core.throttling import DEFAULT_SEND_DELAY_SECONDS as SEND_DELAY_SECONDS



from simple_mailer.core import spintax as spintax_adapter

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


fake = Faker()




PDF_ATTACHMENT_DIR = "./pdfs"
IMAGE_ATTACHMENT_DIR = "./images"

SENDER_NAME_TYPES = ["business", "personal"]
DEFAULT_SENDER_NAME_TYPE = "business"

BUSINESS_SUFFIXES = [
    "Foundation", "Fdn", "Consulting", "Co", "Services", "Ltd", "Instituto", "Institute", "Corp.",
    "Trustees", "Incorporated", "Technologies", "Assoc.", "Trustee", "Company", "Industries", "LLP",
    "Corp", "Assoc", "Associazione", "Trust", "Solutions", "Group", "Associa", "Corporation",
    "Trusts", "Corpo", "Inc", "PC", "LLC", "Institutes", "Associates"
]

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

content_manager = ContentManager()

