import re
from datetime import datetime

import pytest

from simple_mailer.content import (
    R1_DELIMITER,
    R1_KEYWORD_CHOICES,
    R1_PREFIX_CHOICES,
    TAG_DEFINITIONS,
    content_manager,
    generate_tag_value,
)

PREFIX_SET = set(R1_PREFIX_CHOICES)
KEYWORD_SET = set(R1_KEYWORD_CHOICES)

DATE_FORMATS = [
    "%d %B, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%d %B, %Y %H:%M:%S",
    "%d %b %Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
]

INV_PATTERN = re.compile(r"^INV-[A-Z]{10}-\d{7,8}-[A-Z]{5}$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
TRX_PATTERN = re.compile(r"^[A-Z0-9]{35,40}$")
DIGIT_PATTERN = re.compile(r"^\d{5,15}$")
LETTER_PATTERN = re.compile(r"^[A-Za-z]{10,30}$")


def _extract_core_parts(value: str):
    parts = value.split(R1_DELIMITER)
    if parts[0] in PREFIX_SET:
        assert len(parts) == 5
        return parts[1:], parts[0]
    assert len(parts) == 4
    return parts, None


def _is_date_component(value: str) -> bool:
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def _is_string_component(value: str) -> bool:
    if INV_PATTERN.fullmatch(value):
        return True
    if UUID_PATTERN.fullmatch(value):
        return True
    if TRX_PATTERN.fullmatch(value):
        return True
    if DIGIT_PATTERN.fullmatch(value):
        return True
    if value.isupper() and len(value) >= 10:
        return True
    if value.islower() and len(value) >= 10:
        return True
    if LETTER_PATTERN.fullmatch(value):
        if not (value[0].isupper() and value[1:].islower()):
            return True
    return False


@pytest.mark.parametrize("_", range(20))
def test_r1_tag_returns_same_subject_and_body(_) -> None:
    subject, body = content_manager.get_subject_and_body("r1_tag", "r1_tag")
    assert subject == body

    core_parts, prefix = _extract_core_parts(subject)
    if prefix is not None:
        assert prefix in PREFIX_SET

    keyword = next((part for part in core_parts if part in KEYWORD_SET), None)
    assert keyword is not None
    remaining = list(core_parts)
    remaining.remove(keyword)

    date_values = [part for part in remaining if _is_date_component(part)]
    assert len(date_values) == 1
    remaining.remove(date_values[0])

    string_values = [part for part in remaining if _is_string_component(part)]
    assert len(string_values) == 1
    remaining.remove(string_values[0])

    assert len(remaining) == 1
    name_value = remaining[0]
    assert isinstance(name_value, str)
    assert name_value


def test_r1_tag_generates_varied_outputs() -> None:
    outputs = {content_manager.get_subject_and_body("r1_tag", "r1_tag")[0] for _ in range(50)}
    assert len(outputs) > 1


def test_generate_tag_value_uses_context_overrides() -> None:
    context = {"content": "Hello body", "tfn": "123-456"}
    assert generate_tag_value("{{CONTENT}}", context) == "Hello body"
    assert generate_tag_value("{{TFN}}", context) == "123-456"


def test_generate_tag_value_all_tags_return_strings() -> None:
    context = {"content": "Body", "tfn": "999"}
    for definition in TAG_DEFINITIONS.values():
        value = generate_tag_value(definition.name, context)
        assert isinstance(value, str)
        assert value


def test_generate_tag_value_unknown_tag_raises() -> None:
    with pytest.raises(KeyError):
        generate_tag_value("{{UNKNOWN}}")
