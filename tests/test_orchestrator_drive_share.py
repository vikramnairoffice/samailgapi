import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from simple_mailer.orchestrator import drive_share


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
            components.append(
                {
                    "type": comp_type,
                    "label": label,
                    "elem_id": elem_id,
                }
            )
    components.sort(key=lambda item: (item["type"], item.get("label") or "", item.get("elem_id") or ""))
    return components


def test_build_manual_state_wires_adapters(monkeypatch):
    recorded = {}

    def fake_parse(rows):
        recorded["parse"] = rows
        return {"foo": "bar"}

    dummy_spec = DummySpec("asset.txt")

    def fake_specs(files, *, inline_html="", inline_name=""):
        recorded["specs"] = {
            "files": files,
            "inline_html": inline_html,
            "inline_name": inline_name,
        }
        return (dummy_spec,)

    class DummyConfig:
        attachments = (dummy_spec,)
        attachments_enabled = True

        def __init__(self, payload):
            recorded["config_payload"] = payload
            self.payload = payload

        def build_context(self, email):
            recorded["context_email"] = email
            merged = {"email": email, "tfn": self.payload.get("tfn", "")}
            merged.update(self.payload.get("extra_tags", {}))
            return merged

        def render_body(self, context):
            recorded["body_context"] = context
            return ("Rendered body", "plain")

        def build_attachments(self, context):
            recorded["attachments_context"] = context
            return {"asset.txt": "/tmp/asset.txt"}

    payload = {}

    def fake_create_config(*_, **cfg):
        nonlocal payload
        payload = dict(cfg)
        return DummyConfig(payload)

    def fake_listing(specs):
        recorded["listing_specs"] = tuple(specs)
        names = [spec.display_name for spec in specs]
        selected = names[0] if names else None
        return (names, selected, "<div>asset</div>", "")

    adapters = drive_share.DriveShareAdapters(
        create_config=fake_create_config,
        parse_extra_tags=fake_parse,
        to_attachment_specs=fake_specs,
        attachment_listing=fake_listing,
        attachment_preview=lambda specs, name: ("<div>asset</div>", ""),
    )

    state = drive_share.build_manual_state(
        message="Hello {{foo}}",
        message_is_html=False,
        randomize_html=False,
        tfn="1234",
        notify=True,
        delay_seconds=2.5,
        extra_tags=[["foo", "bar"]],
        attachment_mode="pdf",
        attachment_files=("file-1",),
        inline_html="<p>inline</p>",
        inline_name="inline.html",
        adapters=adapters,
        preview_email="lead@example.com",
    )

    assert recorded["parse"] == [["foo", "bar"]]
    assert recorded["specs"] == {
        "files": ("file-1",),
        "inline_html": "<p>inline</p>",
        "inline_name": "inline.html",
    }
    assert payload["attachment_mode"] == "pdf"
    assert payload["attachments_enabled"] is True
    assert payload["extra_tags"] == {"foo": "bar"}
    assert recorded["context_email"] == "lead@example.com"
    assert recorded["body_context"]["foo"] == "bar"
    assert recorded["attachments_context"]["email"] == "lead@example.com"
    assert state.message_html.startswith("<pre")
    assert state.converted_assets == {"asset.txt": "/tmp/asset.txt"}
    assert state.preview.asset_names == ["asset.txt"]
    assert state.preview.selected_asset == "asset.txt"


def test_build_manual_state_handles_html_body():
    dummy_spec = DummySpec("asset.html")

    class DummyConfig:
        attachments = (dummy_spec,)
        attachments_enabled = True

        def __init__(self, payload):
            self.payload = payload

        def build_context(self, email):
            return {"email": email, **self.payload.get("extra_tags", {})}

        def render_body(self, context):
            return ("<p>Hello</p>", "html")

        def build_attachments(self, context):
            return {}

    adapters = drive_share.DriveShareAdapters(
        create_config=lambda **cfg: DummyConfig(cfg),
        parse_extra_tags=lambda rows: {},
        to_attachment_specs=lambda files, *, inline_html="", inline_name="": (dummy_spec,),
        attachment_listing=lambda specs: ([spec.display_name for spec in specs], specs[0].display_name, "<div>asset</div>", ""),
        attachment_preview=lambda specs, name: ("<div>asset</div>", ""),
    )

    state = drive_share.build_manual_state(
        message="<p>Hello</p>",
        message_is_html=True,
        randomize_html=False,
        tfn="",
        notify=False,
        delay_seconds=0,
        extra_tags=None,
        attachment_mode="original",
        attachment_files=None,
        inline_html="",
        inline_name="",
        adapters=adapters,
    )

    assert state.message_html == "<p>Hello</p>"


def test_build_automatic_state_forces_html(monkeypatch):
    called = {}

    def fake_build_manual(**kwargs):
        called.update(kwargs)
        return "STATE"

    monkeypatch.setattr(drive_share, "build_manual_state", fake_build_manual)

    result = drive_share.build_automatic_state(
        message="Hello",
        tfn="",
        notify=False,
        delay_seconds=1.0,
        extra_tags=None,
        attachment_mode="original",
        attachment_files=None,
        inline_html="",
        inline_name="",
        adapters=None,
        randomize_html=True,
    )

    assert result == "STATE"
    assert called["message_is_html"] is True
    assert called["randomize_html"] is True


@pytest.mark.usefixtures("tmp_path")
def test_drive_manual_ui_snapshot(tmp_path):
    expected_path = FIXTURE_DIR / "orchestrator_drive_manual.json"
    assert expected_path.exists(), "Missing orchestrator drive manual snapshot fixture"

    demo = drive_share.build_manual_demo()
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


@pytest.mark.usefixtures("tmp_path")
def test_drive_automatic_ui_snapshot(tmp_path):
    expected_path = FIXTURE_DIR / "orchestrator_drive_automatic.json"
    assert expected_path.exists(), "Missing orchestrator drive automatic snapshot fixture"

    demo = drive_share.build_automatic_demo()
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

