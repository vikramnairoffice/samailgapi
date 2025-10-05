import base64
from pathlib import Path

import pytest

import manual_mode
from manual_mode import ManualAttachmentSpec, ManualConfig


@pytest.fixture(autouse=True)
def reset_attachment_root(tmp_path, monkeypatch):
    monkeypatch.setattr(manual_mode, "_ATTACHMENT_ROOT", tmp_path)


def test_render_body_randomized_when_enabled(monkeypatch):
    calls = {}

    def fake_finalize(raw_html, enable_random, seed):
        calls["args"] = (raw_html, enable_random, seed)
        return "randomized-html"

    monkeypatch.setattr(manual_mode, "_finalize_html_payload", fake_finalize)

    config = ManualConfig(
        enabled=True,
        subject="",
        body="<div>Hi</div>",
        body_is_html=True,
        tfn="",
        randomize_html=True,
    )

    context = config.build_context("lead@example.com")
    body, subtype = config.render_body(context)

    assert subtype == "html"
    assert body == "randomized-html"
    assert calls["args"][1] is True


def test_render_body_plain_text_ignores_image_flag():
    config = ManualConfig(
        enabled=True,
        subject="",
        body="Plain text body",
        body_is_html=False,
        tfn="",
        body_image_enabled=True,
    )

    context = config.build_context("lead@example.com")
    body, subtype = config.render_body(context)

    assert subtype == "plain"
    assert body == "Plain text body"


def test_attachment_pdf_randomizes_html_before_render(monkeypatch):
    captured = {}

    def fake_finalize(html, enable_random, seed):
        captured["finalized"] = html + "-final"
        return captured["finalized"]

    def fake_render(html, destination: Path) -> None:
        captured["rendered"] = html
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(manual_mode, "_finalize_html_payload", fake_finalize)
    monkeypatch.setattr(manual_mode, "_html_to_pdf_rendered", fake_render)

    spec = ManualAttachmentSpec(name="inline.html", inline_content="<p>Item</p>")
    config = ManualConfig(
        enabled=True,
        subject="",
        body="",
        body_is_html=False,
        tfn="",
        attachments=[spec],
        attachments_enabled=True,
        attachment_mode="pdf",
        randomize_html=True,
    )

    context = config.build_context("lead@example.com")
    attachments = config.build_attachments(context)

    assert attachments
    assert captured["rendered"] == captured["finalized"]


def test_render_body_inline_png(monkeypatch):
    payload = b"\x89PNG-inline"
    calls = {}

    def fake_html_to_image(html, destination, image_format="PNG", zoom=2.0):
        calls["html"] = html
        calls["format"] = image_format
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

    monkeypatch.setattr(manual_mode, "_html_to_image", fake_html_to_image)

    config = ManualConfig(
        enabled=True,
        subject="",
        body="<div>Inline</div>",
        body_is_html=True,
        body_image_enabled=True,
        tfn="",
    )

    context = config.build_context("lead@example.com")
    body, subtype = config.render_body(context)

    assert subtype == "html"
    assert body.startswith("<img src=\"data:image/png;base64,")
    encoded = body.split(",", 1)[1].split("\"", 1)[0]
    assert base64.b64decode(encoded) == payload
    assert calls["html"] == "<div>Inline</div>"
    assert calls["format"] == "PNG"
