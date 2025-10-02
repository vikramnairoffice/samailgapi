from pathlib import Path

import base64
import io
import pytest

HTML_BANNER = "
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>HTML banner</title>
  <style>
    :root {
      --bg: #0f172a;
      --fg: #e2e8f0;
      --accent: #38bdf8;
    }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, \"Segoe UI\", Roboto, Ubuntu, Cantarell, \"Helvetica Neue\", Arial, \"Noto Sans\", \"Apple Color Emoji\", \"Segoe UI Emoji\";
      background: #f8fafc;
    }
    .html-banner {
      background: linear-gradient(135deg, var(--bg), #1e293b);
      color: var(--fg);
      padding: clamp(16px, 5vw, 36px);
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 16px;
      align-items: center;
      border-radius: 14px;
      box-shadow: 0 10px 20px rgba(2, 6, 23, 0.2);
      max-width: 1100px;
      margin: 24px auto;
    }
    .banner-text h1 {
      margin: 0 0 6px 0;
      font-size: clamp(22px, 4vw, 36px);
      letter-spacing: 0.2px;
    }
    .banner-text p {
      margin: 0;
      opacity: 0.9;
      font-size: clamp(14px, 1.6vw, 18px);
    }
    .banner-cta {
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }
    .banner-cta a {
      text-decoration: none;
      background: var(--accent);
      color: #0b1020;
      padding: 10px 16px;
      border-radius: 10px;
      font-weight: 600;
      border: 2px solid transparent;
      transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, border-color 0.15s ease;
      display: inline-block;
    }
    .banner-cta a:hover {
      transform: translateY(-1px);
      box-shadow: 0 8px 18px rgba(56, 189, 248, 0.35);
      background: #67e8f9;
    }
    .banner-cta a:active {
      transform: translateY(0);
    }
    @media (max-width: 640px) {
      .html-banner {
        grid-template-columns: 1fr;
        text-align: left;
      }
      .banner-cta {
        justify-self: start;
      }
    }
  </style>
</head>
<body>
  <section class=\"html-banner\" role=\"banner\" aria-label=\"Promotional banner\">
    <div class=\"banner-text\">
      <h1>HTML banner</h1>
      <p>Clean, responsive, and copy-paste friendly. Replace this text with your message.</p>
    </div>
    <div class=\"banner-cta\">
      <a href=\"#\" aria-label=\"Learn more\">Learn more</a>
    </div>
  </section>
</body>
</html>
"


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

def test_render_body_inline_png(monkeypatch, tmp_path):
def test_render_body_png_preserves_layout():
    config = ManualConfig(
        enabled=True,
        subject='',
        body=HTML_BANNER,
        body_is_html=True,
        body_image_enabled=True,
        tfn='',
        randomize_html=False,
    )
    context = config.build_context('lead@example.com')
    body, subtype = config.render_body(context)
    assert subtype == 'html'
    payload = body.split(',', 1)[1].split('"', 1)[0]
    image = Image.open(io.BytesIO(base64.b64decode(payload)))
    assert image.width >= 1000
    assert image.height >= 600
    top_left = image.getpixel((10, 10))
    assert top_left != (255, 255, 255)


    calls = {}

    def fake_html_to_image(html, destination, image_format='PNG', zoom=2.0):
        calls['html'] = html
        calls['format'] = image_format
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"\x89PNGinline")

    monkeypatch.setattr(manual_mode, '_html_to_image', fake_html_to_image)

    config = ManualConfig(
        enabled=True,
        subject='',
        body='<div>Inline</div>',
        body_is_html=True,
        body_image_enabled=True,
        tfn='',
        randomize_html=False,
    )

    context = config.build_context('lead@example.com')
    body, subtype = config.render_body(context)

    assert subtype == 'html'
    assert body.startswith('<img src="data:image/png;base64,')
    payload = body.split(',', 1)[1].split('"', 1)[0]
    assert base64.b64decode(payload) == b"\x89PNGinline"
    assert calls['format'] == 'PNG'
    assert '<div>Inline</div>' in calls['html']

def test_render_body_plain_text_ignores_image_flag():
    config = ManualConfig(
        enabled=True,
        subject='',
        body='Plain text body',
        body_is_html=False,
        body_image_enabled=True,
        tfn='',
        randomize_html=False,
    )

    context = config.build_context('lead@example.com')
    body, subtype = config.render_body(context)

    assert subtype == 'plain'
    assert body == 'Plain text body'
