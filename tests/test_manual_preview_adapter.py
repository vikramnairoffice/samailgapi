import types

import manual_mode
import pytest

from manual.manual_config_adapter import create_config, to_attachment_specs
from manual.manual_preview_adapter import (
    build_snapshot,
    attachment_listing,
    attachment_preview,
)


class DummyFile(types.SimpleNamespace):
    def __iter__(self):
        return iter(())


@pytest.fixture(autouse=True)
def reset_manual_attachment_root(tmp_path, monkeypatch):
    monkeypatch.setattr(manual_mode, "_ATTACHMENT_ROOT", tmp_path)
    monkeypatch.setattr(manual_mode, "_random_suffix", lambda: "fixed")
    monkeypatch.setattr(manual_mode, "_finalize_html_payload", lambda html, enable_random, seed: html)


def test_build_snapshot_with_html_body():
    config = create_config(
        enabled=True,
        subject="",
        body="<p>Hello {{email}}</p>",
        body_is_html=True,
        tfn="",
        attachments_enabled=False,
        attachments=[],
        randomize_html=False,
    )

    choices, default, html_map, meta = build_snapshot(
        config,
        preview_email="lead@example.com",
        selected_attachment_name=None,
    )

    assert choices == ["Body"]
    assert default == "Body"
    assert meta == {"body_available": True, "attachment_available": False}
    assert "Hello" in html_map["Body"]
    assert "Body Preview" in html_map["Body"]


def test_build_snapshot_defaults_to_attachment_when_only_attachment(tmp_path):
    html_file = tmp_path / "sample.html"
    html_file.write_text("<div>Attachment Preview</div>", encoding="utf-8")

    specs = to_attachment_specs([DummyFile(name=str(html_file), orig_name="sample.html")])
    config = create_config(
        enabled=True,
        subject="",
        body="",
        body_is_html=False,
        tfn="",
        attachments_enabled=True,
        attachments=specs,
        attachment_mode="original",
        randomize_html=False,
    )

    choices, default, html_map, meta = build_snapshot(
        config,
        preview_email="lead@example.com",
        selected_attachment_name="sample.html",
    )

    assert choices == ["Body", "Attachment"]
    assert default == "Attachment"
    assert meta == {"body_available": False, "attachment_available": True}
    assert "Attachment Preview" in html_map["Attachment"]
    assert "sample.html" in html_map["Attachment"]
    assert "No body content available" in html_map["Body"]


def test_attachment_listing_returns_first_preview_html(tmp_path):
    inline_html = "<p>Inline</p>"
    specs = to_attachment_specs([], inline_html=inline_html, inline_name="inline.html")

    names, default, html_payload, text_payload = attachment_listing(specs)

    assert names == ["inline.html"]
    assert default == "inline.html"
    assert html_payload == inline_html
    assert text_payload == ""


def test_attachment_preview_returns_payloads(tmp_path):
    inline_html = "<p>Inline</p>"
    specs = to_attachment_specs([], inline_html=inline_html, inline_name="inline.html")

    html_payload, text_payload = attachment_preview(specs, "inline.html")

    assert html_payload == inline_html
    assert text_payload == ""

    missing_html, missing_text = attachment_preview(specs, "missing.html")
    assert missing_html == ""
    assert missing_text == ""
