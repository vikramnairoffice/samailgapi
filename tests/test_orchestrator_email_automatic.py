import json
from pathlib import Path

import pytest

from orchestrator import email_automatic


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ui_snapshots"


def _collect_components_for_snapshot(demo):
    components = []
    for component in demo.blocks.values():
        comp_type = type(component).__name__
        label = getattr(component, "label", None)
        elem_id = getattr(component, "elem_id", None)
        if label or elem_id:
            components.append({
                "type": comp_type,
                "label": label,
                "elem_id": elem_id,
            })
    components.sort(key=lambda item: (item["type"], item.get("label") or "", item.get("elem_id") or ""))
    return components


def test_build_invoice_config_uses_adapters():
    recorded = {}

    def normalize_template(value, kind):
        recorded.setdefault("templates", []).append((kind, value))
        return f"{kind}-normalized"

    def normalize_sender_type(value):
        recorded["sender"] = value
        return "business"

    def normalize_content_mode(value):
        recorded["content_mode"] = value
        return "invoice"

    def normalize_invoice_format(value):
        recorded["invoice_format"] = value
        return "pdf"

    def sanitize_folder(value):
        recorded["folder"] = value
        return "/tmp/attachments"

    def sanitize_support(value):
        recorded["support"] = value
        return "555-123"

    def sanitize_text(value):
        recorded.setdefault("text", []).append(value)
        return value.strip()

    def sanitize_optional_path(value):
        recorded["path"] = value
        return value.strip()

    adapters = email_automatic.AutomaticModeAdapters(
        normalize_template=normalize_template,
        normalize_sender_type=normalize_sender_type,
        normalize_content_mode=normalize_content_mode,
        normalize_invoice_format=normalize_invoice_format,
        sanitize_folder=sanitize_folder,
        sanitize_support_number=sanitize_support,
        sanitize_text=sanitize_text,
        sanitize_optional_path=sanitize_optional_path,
        coerce_bool=lambda value: bool(value),
    )

    config = email_automatic.build_invoice_config(
        content_template="Own_proven",
        subject_template="Own_last",
        body_template="R1_Tag",
        sender_name_type="Personal",
        email_content_mode="Invoice",
        attachment_folder=" ~/docs ",
        invoice_format=" DOCX ",
        support_number=" 800-555-1212 ",
        adapters=adapters,
    )

    assert config.content_template == "content-normalized"
    assert config.subject_template == "subject-normalized"
    assert config.body_template == "body-normalized"
    assert config.sender_name_type == "business"
    assert config.email_content_mode == "invoice"
    assert config.attachment_folder == "/tmp/attachments"
    assert config.invoice_format == "pdf"
    assert config.support_number == "555-123"

    assert recorded["templates"] == [
        ("content", "Own_proven"),
        ("subject", "Own_last"),
        ("body", "R1_Tag"),
    ]
    assert recorded["sender"] == "Personal"
    assert recorded["content_mode"] == "Invoice"
    assert recorded["invoice_format"] == " DOCX "
    assert recorded["folder"] == " ~/docs "
    assert recorded["support"] == " 800-555-1212 "


def test_build_html_config_extends_base_config():
    recorded = {}

    def normalize_template(value, kind):
        recorded.setdefault("templates", []).append((kind, value))
        return f"{kind}-normalized"

    def normalize_sender_type(value):
        recorded["sender"] = value
        return "business"

    def normalize_content_mode(value):
        recorded["content_mode"] = value
        return "attachment"

    def normalize_invoice_format(value):
        recorded["invoice_format"] = value
        return "png"

    def sanitize_folder(value):
        recorded["folder"] = value
        return "/data"

    def sanitize_support(value):
        recorded["support"] = value
        return ""

    def sanitize_text(value):
        recorded.setdefault("text", []).append(value)
        return value.strip()

    def sanitize_optional_path(value):
        recorded["path"] = value
        return value.strip()

    def coerce_bool(value):
        recorded.setdefault("bools", []).append(value)
        return str(value).lower() in {"1", "true", "yes"}

    adapters = email_automatic.AutomaticModeAdapters(
        normalize_template=normalize_template,
        normalize_sender_type=normalize_sender_type,
        normalize_content_mode=normalize_content_mode,
        normalize_invoice_format=normalize_invoice_format,
        sanitize_folder=sanitize_folder,
        sanitize_support_number=sanitize_support,
        sanitize_text=sanitize_text,
        sanitize_optional_path=sanitize_optional_path,
        coerce_bool=coerce_bool,
    )

    config = email_automatic.build_html_config(
        content_template=" own_last ",
        subject_template=" R1_Tag ",
        body_template=" Own_proven ",
        sender_name_type=" Business ",
        email_content_mode="Attachment",
        attachment_folder=" ./attachments ",
        invoice_format=" HEIF ",
        support_number=" ",
        randomize_html=1,
        inline_png="true",
        html_upload_path=" /tmp/upload.html ",
        inline_html=" <p>Hello</p> ",
        tfn=" 555-999 ",
        adapters=adapters,
    )

    assert config.content_template == "content-normalized"
    assert config.subject_template == "subject-normalized"
    assert config.body_template == "body-normalized"
    assert config.sender_name_type == "business"
    assert config.email_content_mode == "attachment"
    assert config.attachment_folder == "/data"
    assert config.invoice_format == "png"
    assert config.support_number == ""
    assert config.randomize_html is True
    assert config.inline_png is True
    assert config.html_upload_path == "/tmp/upload.html"
    assert config.inline_html == "<p>Hello</p>"
    assert config.tfn == "555-999"

    assert recorded["templates"] == [
        ("content", " own_last "),
        ("subject", " R1_Tag "),
        ("body", " Own_proven "),
    ]
    assert recorded["sender"] == " Business "
    assert recorded["content_mode"] == "Attachment"
    assert recorded["invoice_format"] == " HEIF "
    assert recorded["folder"] == " ./attachments "
    assert recorded["bools"] == [1, "true"]
    assert recorded["path"] == " /tmp/upload.html "
    assert recorded["text"][-2:] == [" <p>Hello</p> ", " 555-999 "]


@pytest.mark.usefixtures("tmp_path")
def test_automatic_mode_ui_snapshot(tmp_path):
    expected_path = FIXTURE_DIR / "orchestrator_automatic.json"
    assert expected_path.exists(), "Missing orchestrator automatic snapshot fixture"

    demo = email_automatic.build_demo()
    try:
        snapshot = {
            "components": _collect_components_for_snapshot(demo),
        }
    finally:
        try:
            demo.close()
        except Exception:
            pass

    expected = json.loads(expected_path.read_text())
    assert snapshot == expected
