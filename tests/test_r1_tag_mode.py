import re
from datetime import datetime

import pytest

from content import content_manager, DEFAULT_SUBJECTS


D1_PATTERN = re.compile(r"^[A-Z][a-z]+ \d{1,2} -\d{4}$")
D2_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")
N1_PATTERN = re.compile(r"^[A-Z][a-z]+ [A-Z][a-z]+$")
N2_PATTERN = re.compile(r"^[A-Z][A-Z][a-z]+[A-Z][a-z]+$")
T1_PATTERN = re.compile(r"^INV[A-Z0-9]{26}$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _classify_component(component: str) -> str:
    if D1_PATTERN.fullmatch(component) or D2_PATTERN.fullmatch(component):
        return "date"
    if T1_PATTERN.fullmatch(component) or UUID_PATTERN.fullmatch(component):
        return "token"
    if component in DEFAULT_SUBJECTS:
        return "keyword"
    if N1_PATTERN.fullmatch(component) or N2_PATTERN.fullmatch(component):
        return "name"
    raise AssertionError(f"Unexpected component format: {component}")


@pytest.mark.parametrize("_", range(10))
def test_r1_tag_returns_same_subject_and_body(_) -> None:
    subject, body = content_manager.get_subject_and_body("r1_tag")
    assert subject == body
    parts = subject.split(" | ")
    assert len(parts) == 4
    categories = {_classify_component(part) for part in parts}
    assert categories == {"date", "name", "token", "keyword"}


def test_r1_tag_generates_varied_outputs() -> None:
    outputs = {content_manager.get_subject_and_body("r1_tag")[0] for _ in range(20)}
    assert len(outputs) > 1
