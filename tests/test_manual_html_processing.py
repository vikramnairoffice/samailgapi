from pathlib import Path

import pytest

import manual_mode
from manual_mode import ManualAttachmentSpec, ManualConfig


@pytest.fixture(autouse=True)
def cleanup_tmp(tmp_path):
    original_root = manual_mode._ATTACHMENT_ROOT
    manual_mode._ATTACHMENT_ROOT = tmp_path
    try:
        yield
    finally:
        manual_mode._ATTACHMENT_ROOT = original_root


def test_render_body_randomized_when_enabled(monkeypatch):
    html = "<html><body><h1 style=\"color:#123456\">Hi</h1></body></html>"
    config = ManualConfig(
        enabled=True,
        subject="",
        body=html,
        body_is_html=True,
        tfn="",
        randomize_html=True,
    )
    context = config.build_context('lead@example.com')
    body, subtype = config.render_body(context)
    assert subtype == 'html'
    assert body != html
    assert '#123456' not in body


def test_render_body_unchanged_when_randomization_disabled():
    html = "<html><body><p style='color:#abcdef'>Plain</p></body></html>"
    config = ManualConfig(
        enabled=True,
        subject="",
        body=html,
        body_is_html=True,
        tfn="",
        randomize_html=False,
    )
    context = config.build_context('lead@example.com')
    body, subtype = config.render_body(context)
    assert subtype == 'html'
    assert body == html


def test_attachment_pdf_randomizes_html_before_render(monkeypatch, tmp_path):
    captured = {}

    def fake_render(html: str, destination: Path) -> None:
        captured['html'] = html
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text('pdf', encoding='utf-8')

    monkeypatch.setattr(manual_mode, "_html_to_pdf_rendered", fake_render)

    original_html = '<html><body><p style="color:#101010">Hi</p></body></html>'
    spec = ManualAttachmentSpec(name='inline.html', inline_content=original_html)
    config = ManualConfig(
        enabled=True,
        subject="",
        body="",
        body_is_html=False,
        tfn="",
        attachments=[spec],
        attachments_enabled=True,
        attachment_mode='pdf',
        randomize_html=True,
    )
    context = config.build_context('lead@example.com')
    attachments = config.build_attachments(context)
    assert attachments
    assert captured['html'] != original_html
    assert '#101010' not in captured['html']


def test_html_to_pdf_rendered_uses_playwright(monkeypatch, tmp_path):
    called = {}

    class DummyRenderer:
        def render_pdf(self, html: str, destination: Path) -> None:
            called['html'] = html
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text('pdf', encoding='utf-8')

    dummy = DummyRenderer()
    monkeypatch.setattr(manual_mode, "html_renderer", dummy)

    manual_mode._html_to_pdf_rendered('<html></html>', tmp_path / 'out.pdf')
    assert called['html'] == '<html></html>'
