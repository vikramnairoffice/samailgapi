import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator import email_manual


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ui_snapshots"


@dataclass
class DummySpec:
    display_name: str


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


def test_build_manual_config_uses_adapter_helpers():
    recorded = {}

    def fake_parse(rows):
        recorded["parse"] = rows
        return {"foo": "bar"}

    def fake_specs(files, *, inline_html="", inline_name=""):
        recorded["specs"] = {
            "files": files,
            "inline_html": inline_html,
            "inline_name": inline_name,
        }
        return (DummySpec("doc.pdf"),)

    def fake_create_config(data=None, **overrides):
        payload = dict(data or {})
        payload.update(overrides)
        recorded["config"] = payload
        return "CONFIG"

    adapters = email_manual.ManualModeAdapters(
        create_config=fake_create_config,
        parse_extra_tags=fake_parse,
        to_attachment_specs=fake_specs,
        preview_snapshot=lambda *_, **__: ([], "Body", {}, {}),
        attachment_listing=lambda *_, **__: ([], None, "", ""),
        attachment_preview=lambda *_, **__: ("", ""),
        random_sender_name=lambda *_: "Random",
    )

    config, attachments = email_manual.build_manual_config(
        subject="Subject",
        body="Body",
        body_is_html=True,
        body_image_enabled=True,
        randomize_html=True,
        tfn="1234",
        extra_tags=[["foo", "bar"], ["", "skip"]],
        attachment_enabled=True,
        attachment_mode="pdf",
        attachment_files=("file1", "file2"),
        inline_html="<p>inline</p>",
        inline_name="inline.html",
        sender_name="Alice",
        change_name=True,
        sender_type="business",
        adapters=adapters,
    )

    assert config == "CONFIG"
    assert attachments == (DummySpec("doc.pdf"),)
    assert recorded["parse"] == [["foo", "bar"], ["", "skip"]]
    assert recorded["specs"] == {
        "files": ("file1", "file2"),
        "inline_html": "<p>inline</p>",
        "inline_name": "inline.html",
    }
    assert recorded["config"]["subject"] == "Subject"
    assert recorded["config"]["body"] == "Body"
    assert recorded["config"]["body_is_html"] is True
    assert recorded["config"]["body_image_enabled"] is True
    assert recorded["config"]["randomize_html"] is True
    assert recorded["config"]["tfn"] == "1234"
    assert recorded["config"]["extra_tags"] == {"foo": "bar"}
    assert recorded["config"]["attachments"] == (DummySpec("doc.pdf"),)
    assert recorded["config"]["attachments_enabled"] is True
    assert recorded["config"]["attachment_mode"] == "pdf"
    assert recorded["config"]["sender_name"] == "Alice"
    assert recorded["config"]["change_name_every_time"] is True
    assert recorded["config"]["sender_name_type"] == "business"


def test_build_preview_state_uses_snapshot(monkeypatch):
    call_args = {}
    spec = DummySpec("doc.pdf")

    def fake_parse(rows):
        return {}

    def fake_specs(files, *, inline_html="", inline_name=""):
        return (spec,)

    def fake_create_config(data=None, **overrides):
        payload = dict(data or {})
        payload.update(overrides)
        return payload

    def fake_snapshot(config, preview_email, selected_attachment_name):
        call_args["config_subject"] = config.get("subject")
        call_args["preview_email"] = preview_email
        call_args["selected_attachment"] = selected_attachment_name
        return (
            ["Body", "Attachment"],
            "Attachment",
            {"Body": "<p>body</p>", "Attachment": "<div>att</div>"},
            {"attachment_available": True},
        )

    adapters = email_manual.ManualModeAdapters(
        create_config=fake_create_config,
        parse_extra_tags=fake_parse,
        to_attachment_specs=fake_specs,
        preview_snapshot=fake_snapshot,
        attachment_listing=lambda *_, **__: ([], None, "", ""),
        attachment_preview=lambda *_, **__: ("", ""),
        random_sender_name=lambda *_: "Random",
    )

    result = email_manual.build_preview_state(
        subject="Subject",
        body="Body",
        body_is_html=False,
        body_image_enabled=False,
        randomize_html=False,
        tfn="",
        extra_tags=None,
        attachment_enabled=True,
        attachment_mode="original",
        attachment_files=(),
        inline_html="",
        inline_name="inline.html",
        sender_name="",
        change_name=False,
        sender_type="business",
        selected_attachment_name="doc.pdf",
        adapters=adapters,
    )

    assert call_args["config_subject"] == "Subject"
    assert call_args["preview_email"] == email_manual.DEFAULT_PREVIEW_EMAIL
    assert call_args["selected_attachment"] == "doc.pdf"
    assert result.choices == ["Body", "Attachment"]
    assert result.default == "Attachment"
    assert result.html_map["Body"] == "<p>body</p>"
    assert result.html_map["Attachment"] == "<div>att</div>"
    assert result.meta == {"attachment_available": True}
    assert result.attachments == (spec,)


@pytest.mark.usefixtures("tmp_path")
def test_manual_mode_ui_snapshot(tmp_path):
    expected_path = FIXTURE_DIR / "orchestrator_manual.json"
    assert expected_path.exists(), "Missing orchestrator manual snapshot fixture"

    demo = email_manual.build_demo()
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
