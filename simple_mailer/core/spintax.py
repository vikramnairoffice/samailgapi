"""Tag and spintax rendering adapters forwarding to legacy logic."""

from __future__ import annotations

import random
import re
import string
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Mapping, Optional

from faker import Faker


TagContext = Optional[Mapping[str, str]]
TagGenerator = Callable[[TagContext], str]

fake = Faker()


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
    return "".join(random.choices(string.digits, k=length))


def _random_letter_string(min_length: int, max_length: int, alphabet: str) -> str:
    length = random.randint(min_length, max_length)
    return "".join(random.choices(alphabet, k=length))


def _random_upper_alphanumeric(min_length: int, max_length: int) -> str:
    length = random.randint(min_length, max_length)
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


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
    value = _context_lookup(context, "email")
    if value:
        return value
    return fake.email()


def _tag_content(context: TagContext = None) -> str:
    value = _context_lookup(context, "content")
    if value:
        return value
    return "Content"


def _tag_invoice(_: TagContext = None) -> str:
    prefix = "".join(random.choices(string.ascii_uppercase, k=10))
    mid = _random_numeric_string(7, 8)
    suffix = "".join(random.choices(string.ascii_uppercase, k=5))
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
    return fake.address()


def _tag_tfn(context: TagContext = None) -> str:
    value = _context_lookup(context, "tfn")
    if value:
        return value
    return fake.phone_number()


TAG_DEFINITIONS: Dict[str, TagDefinition] = {
    "{{DATE}}": TagDefinition(
        name="{{DATE}}",
        description="Generates a date in long format.",
        example="11 July, 2025",
        generator=_tag_date_multi,
    ),
    "{{DATE1}}": TagDefinition(
        name="{{DATE1}}",
        description="Generates a date in numeric format.",
        example="07/11/2025",
        generator=_tag_date_numeric,
    ),
    "{{DATE2}}": TagDefinition(
        name="{{DATE2}}",
        description="Generates a date in numeric format.",
        example="11/07/2025",
        generator=_tag_date_numeric,
    ),
    "{{DATE3}}": TagDefinition(
        name="{{DATE3}}",
        description="Generates a date with time.",
        example="11 July, 2025 18:22:33",
        generator=_tag_datetime,
    ),
    "{{DATETIME}}": TagDefinition(
        name="{{DATETIME}}",
        description="Generates a date with time.",
        example="11 July, 2025 18:22:33",
        generator=_tag_datetime,
    ),
    "{{SNAME}}": TagDefinition(
        name="{{SNAME}}",
        description="Generates a single first name.",
        example="Ron",
        generator=_tag_single_name,
    ),
    "{{NAME}}": TagDefinition(
        name="{{NAME}}",
        description="Generates a single first name.",
        example="Ron",
        generator=_tag_single_name,
    ),
    "{{FNAME}}": TagDefinition(
        name="{{FNAME}}",
        description="Generates a full name.",
        example="Ron Smith",
        generator=_tag_full_name,
    ),
    "{{UNAME}}": TagDefinition(
        name="{{UNAME}}",
        description="Generates a unique name (initial + full name).",
        example="R. Ron Smith",
        generator=_tag_unique_name,
    ),
    "{{EMAIL}}": TagDefinition(
        name="{{EMAIL}}",
        description="Generates an email address or uses the provided one.",
        example="example@email.com",
        generator=_tag_email,
    ),
    "{{CONTENT}}": TagDefinition(
        name="{{CONTENT}}",
        description="Gets the main body content entered in the body box using this tag.",
        example="Content",
        generator=_tag_content,
    ),
    "{{INV}}": TagDefinition(
        name="{{INV}}",
        description="Generates a unique sequence number.",
        example="INV-FIGGRWNNFIT-04446407-SJXNE",
        generator=_tag_invoice,
    ),
    "{{INUM}}": TagDefinition(
        name="{{INUM}}",
        description="Generates a short numeric value (5 to 10 digits).",
        example="494500",
        generator=_tag_short_numeric,
    ),
    "{{LNUM}}": TagDefinition(
        name="{{LNUM}}",
        description="Generates a long numeric value (10 to 15 digits).",
        example="0770431750123",
        generator=_tag_long_numeric,
    ),
    "{{SMLETT}}": TagDefinition(
        name="{{SMLETT}}",
        description="Generates a short mixed-case letter string (10 to 15 characters).",
        example="FzsAcgjWqN",
        generator=_tag_short_mixed_letters,
    ),
    "{{LMLETT}}": TagDefinition(
        name="{{LMLETT}}",
        description="Generates a long mixed-case letter string (20 to 30 characters).",
        example="JVyDJmYahbZGHJQUtdBF",
        generator=_tag_long_mixed_letters,
    ),
    "{{SCLETT}}": TagDefinition(
        name="{{SCLETT}}",
        description="Generates a short uppercase letter string (10 to 15 characters).",
        example="EVOUAHLEM",
        generator=_tag_short_upper_letters,
    ),
    "{{LCLETT}}": TagDefinition(
        name="{{LCLETT}}",
        description="Generates a long uppercase letter string (20 to 30 characters).",
        example="PEQLXACTDWRDPHZTT",
        generator=_tag_long_upper_letters,
    ),
    "{{SLLETT}}": TagDefinition(
        name="{{SLLETT}}",
        description="Generates a short lowercase letter string (10 to 15 characters).",
        example="mxsebrvl",
        generator=_tag_short_lower_letters,
    ),
    "{{LLLETT}}": TagDefinition(
        name="{{LLLETT}}",
        description="Generates a long lowercase letter string (20 to 30 characters).",
        example="igxnibvmtqksywep",
        generator=_tag_long_lower_letters,
    ),
    "{{UKEY}}": TagDefinition(
        name="{{UKEY}}",
        description="Generates a unique UUID key.",
        example="1038df95-d2db-4fff-a668-c4cde9f7ec30",
        generator=_tag_uuid,
    ),
    "{{TRX}}": TagDefinition(
        name="{{TRX}}",
        description="Generates a random alphanumeric string (35 to 40 characters).",
        example="2CHCICPY1U0EVU6SMZZ1A3M0GGG05JPNETYYSI",
        generator=_tag_trx,
    ),
    "{{ADDRESS}}": TagDefinition(
        name="{{ADDRESS}}",
        description="Generates a random postal address.",
        example="108 Hemway Center",
        generator=_tag_address,
    ),
    "{{ADDRESS1}}": TagDefinition(
        name="{{ADDRESS1}}",
        description="Generates a random full address.",
        example="3356 Leon Keys Suite 431 Shawton, VY 88912",
        generator=_tag_full_address,
    ),
    "{{TFN}}": TagDefinition(
        name="{{TFN}}",
        description="Retrieves the number entered in the TFN input box.",
        example="+1 (856) 347-2649",
        generator=_tag_tfn,
    ),
}


LEGACY_TAG_ALIASES: Dict[str, str] = {
    f"#{name[2:-2]}#": name for name in TAG_DEFINITIONS.keys()
}

TAG_PATTERN = re.compile(
    "|".join(
        re.escape(name)
        for name in sorted(
            [*TAG_DEFINITIONS.keys(), *LEGACY_TAG_ALIASES.keys()],
            key=len,
            reverse=True,
        )
    )
)


_SPINTAX_PATTERN = re.compile(r"\{([^{}]+)\}")
_SPINTAX_MAX_ITERATIONS = 1000


def _resolve_tag_definition(tag_name: str) -> Optional[TagDefinition]:
    definition = TAG_DEFINITIONS.get(tag_name)
    if definition is not None:
        return definition
    canonical_name = LEGACY_TAG_ALIASES.get(tag_name)
    if canonical_name is not None:
        return TAG_DEFINITIONS.get(canonical_name)
    return None


def render_tags(text: str, context: TagContext = None) -> str:
    """Replace tag tokens in text using the provided context."""
    if not text:
        return text

    def _replacement(match: re.Match[str]) -> str:
        tag = match.group(0)
        definition = _resolve_tag_definition(tag)
        if definition is None:
            return tag
        try:
            return definition.generator(context)
        except Exception:
            return tag

    return TAG_PATTERN.sub(_replacement, text)


def expand_spintax(text: str, rng: Optional[random.Random] = None) -> str:
    """Resolve {a|b|c} style spintax expressions within text."""
    if not isinstance(text, str):
        return text
    if "{" not in text or "}" not in text:
        return text

    chooser = rng.choice if rng is not None else random.choice
    result = text
    for _ in range(_SPINTAX_MAX_ITERATIONS):
        if "{" not in result or "}" not in result:
            break

        def _replace(match: re.Match[str]) -> str:
            options = match.group(1).split("|")
            if not options:
                return match.group(0)
            return chooser(options)

        updated = _SPINTAX_PATTERN.sub(_replace, result)
        if updated == result:
            break
        result = updated

    return result


def expand(text: str, data: TagContext = None, rng: Optional[random.Random] = None) -> str:
    """Render tags and then resolve spintax expressions."""
    rendered = render_tags(text, data)
    return expand_spintax(rendered, rng)


def get_tag_definitions() -> List[TagDefinition]:
    """Return tag definitions preserving declaration order."""
    return list(TAG_DEFINITIONS.values())


def generate_tag_value(tag_name: str, context: TagContext = None) -> str:
    """Return a realized tag value for the provided tag name."""
    definition = _resolve_tag_definition(tag_name)
    if definition is None:
        raise KeyError(f"Unknown tag: {tag_name}")
    return definition.generator(context)


__all__ = [
    "TagContext",
    "TagDefinition",
    "TAG_DEFINITIONS",
    "LEGACY_TAG_ALIASES",
    "render_tags",
    "expand_spintax",
    "expand",
    "get_tag_definitions",
    "generate_tag_value",
]
