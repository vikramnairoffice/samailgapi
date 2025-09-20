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



TagContext = Optional[Mapping[str, str]]
TagGenerator = Callable[[TagContext], str]


@dataclass(frozen=True)
class TagDefinition:
    name: str
    description: str
    example: str
    generator: TagGenerator


def _context_lookup(context: TagContext, key: str) -> Optional[str]:
    if context:
        value = context.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _random_numeric_string(min_digits: int, max_digits: int) -> str:
    length = random.randint(min_digits, max_digits)
    return ''.join(random.choices(string.digits, k=length))


def _random_letter_string(min_length: int, max_length: int, alphabet: str) -> str:
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(alphabet, k=length))


def _random_upper_alphanumeric(min_length: int, max_length: int) -> str:
    length = random.randint(min_length, max_length)
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choices(alphabet, k=length))


def _tag_date_multi(_: TagContext = None) -> str:
    today = datetime.now()
    formats = ["%d %B, %Y", "%B %d, %Y", "%d %b %Y"]
    return today.strftime(random.choice(formats))


def _tag_date_numeric(_: TagContext = None) -> str:
    today = datetime.now()
    formats = ["%m/%d/%Y", "%d/%m/%Y"]
    return today.strftime(random.choice(formats))


def _tag_datetime(_: TagContext = None) -> str:
    today = datetime.now()
    formats = ["%d %B, %Y %H:%M:%S", "%d %b %Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]
    return today.strftime(random.choice(formats))


def _tag_single_name(_: TagContext = None) -> str:
    return fake.first_name()


def _tag_full_name(_: TagContext = None) -> str:
    return f"{fake.first_name()} {fake.last_name()}"


def _tag_unique_name(_: TagContext = None) -> str:
    initial = fake.first_name()[0]
    primary = fake.first_name()
    last = fake.last_name()
    return f"{initial}. {primary} {last}"


def _tag_email(context: TagContext = None) -> str:
    value = _context_lookup(context, 'email')
    if value:
        return value
    return fake.email()


def _tag_content(context: TagContext = None) -> str:
    value = _context_lookup(context, 'content')
    if value:
        return value
    return "Content"


def _tag_invoice(_: TagContext = None) -> str:
    prefix = ''.join(random.choices(string.ascii_uppercase, k=10))
    mid = _random_numeric_string(7, 8)
    suffix = ''.join(random.choices(string.ascii_uppercase, k=5))
    return f"INV-{prefix}-{mid}-{suffix}"


def _tag_short_numeric(_: TagContext = None) -> str:
    return _random_numeric_string(5, 10)


def _tag_long_numeric(_: TagContext = None) -> str:
    return _random_numeric_string(10, 15)


def _tag_short_mixed_letters(_: TagContext = None) -> str:
    return _random_letter_string(10, 15, string.ascii_letters)


def _tag_long_mixed_letters(_: TagContext = None) -> str:
    return _random_letter_string(20, 30, string.ascii_letters)


def _tag_short_upper_letters(_: TagContext = None) -> str:
    return _random_letter_string(10, 15, string.ascii_uppercase)


def _tag_long_upper_letters(_: TagContext = None) -> str:
    return _random_letter_string(20, 30, string.ascii_uppercase)


def _tag_short_lower_letters(_: TagContext = None) -> str:
    return _random_letter_string(10, 15, string.ascii_lowercase)


def _tag_long_lower_letters(_: TagContext = None) -> str:
    return _random_letter_string(20, 30, string.ascii_lowercase)


def _tag_uuid(_: TagContext = None) -> str:
    return str(uuid.uuid4())


def _tag_trx(_: TagContext = None) -> str:
    return _random_upper_alphanumeric(35, 40)


def _tag_address(_: TagContext = None) -> str:
    return fake.street_address()


def _tag_full_address(_: TagContext = None) -> str:
    raw = fake.address()
    clean = raw.replace('\r\n', '\n').replace('\n', ', ')
    return clean.strip()


def _tag_tfn(context: TagContext = None) -> str:
    value = _context_lookup(context, 'tfn')
    if value:
        return value
    return fake.phone_number()






TAG_DEFINITIONS: Dict[str, TagDefinition] = {
    "#DATE#": TagDefinition(
        name="#DATE#",
        description="Generates the current date in multiple formats.",
        example="18 June, 2024",
        generator=_tag_date_multi,
    ),
    "#DATE1#": TagDefinition(
        name="#DATE1#",
        description="Generates the current date in various numeric formats.",
        example="07/05/2025",
        generator=_tag_date_numeric,
    ),
    "#DATETIME#": TagDefinition(
        name="#DATETIME#",
        description="Generates the current date and time in different formats.",
        example="20 May, 2025 00:00:00",
        generator=_tag_datetime,
    ),
    "#NAME#": TagDefinition(
        name="#NAME#",
        description="Generates a random single name.",
        example="Crystle",
        generator=_tag_single_name,
    ),
    "#FNAME#": TagDefinition(
        name="#FNAME#",
        description="Generates a random full name.",
        example="Robert Schmidt",
        generator=_tag_full_name,
    ),
    "#UNAME#": TagDefinition(
        name="#UNAME#",
        description="Generates a random unique name.",
        example="R. Nathan Hahn",
        generator=_tag_unique_name,
    ),
    "#EMAIL#": TagDefinition(
        name="#EMAIL#",
        description="Retrieves the client's email address.",
        example="alex2024@gmail.com",
        generator=_tag_email,
    ),
    "#CONTENT#": TagDefinition(
        name="#CONTENT#",
        description="Gets the main body content entered in the body box using this tag.",
        example="Content",
        generator=_tag_content,
    ),
    "#INV#": TagDefinition(
        name="#INV#",
        description="Generates a unique sequence number.",
        example="INV-FIGGRWNNFIT-04446407-SJXNE",
        generator=_tag_invoice,
    ),
    "#INUM#": TagDefinition(
        name="#INUM#",
        description="Generates a short numeric value (5 to 10 digits).",
        example="494500",
        generator=_tag_short_numeric,
    ),
    "#LNUM#": TagDefinition(
        name="#LNUM#",
        description="Generates a long numeric value (10 to 15 digits).",
        example="0770431750123",
        generator=_tag_long_numeric,
    ),
    "#SMLETT#": TagDefinition(
        name="#SMLETT#",
        description="Generates a short mixed-case letter string (10 to 15 characters).",
        example="FzsAcgjWqN",
        generator=_tag_short_mixed_letters,
    ),
    "#LMLETT#": TagDefinition(
        name="#LMLETT#",
        description="Generates a long mixed-case letter string (20 to 30 characters).",
        example="JVyDJmYahbZGHJQUtdBF",
        generator=_tag_long_mixed_letters,
    ),
    "#SCLETT#": TagDefinition(
        name="#SCLETT#",
        description="Generates a short uppercase letter string (10 to 15 characters).",
        example="EVOUAHLEM",
        generator=_tag_short_upper_letters,
    ),
    "#LCLETT#": TagDefinition(
        name="#LCLETT#",
        description="Generates a long uppercase letter string (20 to 30 characters).",
        example="PEQLXACTDWRDPHZTT",
        generator=_tag_long_upper_letters,
    ),
    "#SLLETT#": TagDefinition(
        name="#SLLETT#",
        description="Generates a short lowercase letter string (10 to 15 characters).",
        example="mxsebrvl",
        generator=_tag_short_lower_letters,
    ),
    "#LLLETT#": TagDefinition(
        name="#LLLETT#",
        description="Generates a long lowercase letter string (20 to 30 characters).",
        example="igxnibvmtqksywep",
        generator=_tag_long_lower_letters,
    ),
    "#UKEY#": TagDefinition(
        name="#UKEY#",
        description="Generates a unique UUID key.",
        example="1038df95-d2db-4fff-a668-c4cde9f7ec30",
        generator=_tag_uuid,
    ),
    "#TRX#": TagDefinition(
        name="#TRX#",
        description="Generates a random alphanumeric string (35 to 40 characters).",
        example="2CHCICPY1U0EVU6SMZZ1A3M0GGG05JPNETYYSI",
        generator=_tag_trx,
    ),
    "#ADDRESS#": TagDefinition(
        name="#ADDRESS#",
        description="Generates a random postal address.",
        example="108 Hemway Center",
        generator=_tag_address,
    ),
    "#ADDRESS1#": TagDefinition(
        name="#ADDRESS1#",
        description="Generates a random full address.",
        example="3356 Leon Keys Suite 431 Shawton, VY 88912",
        generator=_tag_full_address,
    ),
    "#TFN#": TagDefinition(
        name="#TFN#",
        description="Retrieves the number entered in the TFN input box.",
        example="+1 (856) 347-2649",
        generator=_tag_tfn,
    ),
}


TAG_PATTERN = re.compile(r"|".join(re.escape(name) for name in sorted(TAG_DEFINITIONS.keys(), key=len, reverse=True)))


def render_tagged_content(text: str, context: TagContext = None) -> str:
    """Replace tag tokens in text using the provided context."""
    if not text:
        return text

    def _replacement(match: re.Match[str]) -> str:
        tag = match.group(0)
        try:
            return generate_tag_value(tag, context)
        except KeyError:
            return tag
        except Exception:
            return tag

    return TAG_PATTERN.sub(_replacement, text)




def get_tag_definitions() -> List[TagDefinition]:
    """Return tag definitions preserving declaration order."""
    return list(TAG_DEFINITIONS.values())


def generate_tag_value(tag_name: str, context: TagContext = None) -> str:
    """Return a realized tag value for the provided tag name."""
    definition = TAG_DEFINITIONS.get(tag_name)
    if definition is None:
        raise KeyError(f"Unknown tag: {tag_name}")
    return definition.generator(context)


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
R1_NAME_TAGS = ["#NAME#", "#FNAME#", "#UNAME#"]
R1_DATE_TAGS = ["#DATE#", "#DATE1#", "#DATETIME#"]
R1_STRING_TAGS = [
    "#INV#",
    "#UKEY#",
    "#TRX#",
    "#SMLETT#",
    "#LMLETT#",
    "#SCLETT#",
    "#LCLETT#",
    "#SLLETT#",
    "#LLLETT#",
    "#INUM#",
    "#LNUM#",
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

