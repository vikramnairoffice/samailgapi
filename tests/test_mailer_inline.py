import base64
from pathlib import Path

import pytest

import mailer


class _DummyInvoiceGen:
    def __init__(self, image_path: Path):
        self._image_path = image_path

    def generate_for_recipient(self, lead_email: str, support_number: str, fmt: str) -> str:
        assert fmt == 'png'
        return str(self._image_path)


@pytest.fixture()
def inline_image(tmp_path: Path) -> Path:
    image_path = tmp_path / "inline.png"
    image_path.write_bytes(b"\x89PNGtestdata")
    return image_path


def test_send_single_email_inline_includes_body_html(monkeypatch: pytest.MonkeyPatch, inline_image: Path) -> None:
    captured = {}

    def fake_send(creds, from_header, to_email, subject, body, attachments=None, advance_header=False, force_header=False, body_subtype='plain'):
        captured['body'] = body
        captured['attachments'] = attachments
        captured['body_subtype'] = body_subtype
        captured['from_header'] = from_header
        captured['subject'] = subject

    monkeypatch.setattr(mailer, 'send_gmail_message', fake_send)
    monkeypatch.setattr(mailer, 'compose_email', lambda account_email, config: ('Subject', 'Line one\nLine two', f'Sender <{account_email}>'))

    account = {
        'email': 'sender@example.com',
        'creds': object(),
        'auth_type': 'oauth',
    }
    config = {
        'email_content_mode': 'Inline Invoice',
        'inline_body_enabled': True,
        'support_number': '',
        'advance_header': False,
        'force_header': False,
        'sender_name_type': 'business',
    }

    success, message = mailer.send_single_email(account, 'lead@example.com', config, _DummyInvoiceGen(inline_image))

    assert success is True
    assert 'Sent to lead@example.com' in message
    assert captured['attachments'] == {}
    assert captured['body_subtype'] == 'html'
    assert 'Line one' in captured['body']
    assert '<br />' in captured['body']
    assert 'data:image/png;base64,' in captured['body']
    encoded = captured['body'].split('data:image/png;base64,', 1)[1].split('"', 1)[0]
    assert base64.b64decode(encoded) == b"\x89PNGtestdata"


def test_send_single_email_inline_can_skip_body(monkeypatch: pytest.MonkeyPatch, inline_image: Path) -> None:
    captured = {}

    def fake_send(creds, from_header, to_email, subject, body, attachments=None, advance_header=False, force_header=False, body_subtype='plain'):
        captured['body'] = body
        captured['attachments'] = attachments
        captured['body_subtype'] = body_subtype

    monkeypatch.setattr(mailer, 'send_gmail_message', fake_send)
    monkeypatch.setattr(mailer, 'compose_email', lambda account_email, config: ('Subject', 'Body should vanish', f'Sender <{account_email}>'))

    account = {
        'email': 'sender@example.com',
        'creds': object(),
        'auth_type': 'oauth',
    }
    config = {
        'email_content_mode': 'Inline Invoice',
        'inline_body_enabled': False,
        'support_number': '',
        'advance_header': False,
        'force_header': False,
        'sender_name_type': 'business',
    }

    success, _ = mailer.send_single_email(account, 'lead@example.com', config, _DummyInvoiceGen(inline_image))

    assert success is True
    assert captured['attachments'] == {}
    assert captured['body_subtype'] == 'html'
    assert 'Body should vanish' not in captured['body']
    assert 'data:image/png;base64,' in captured['body']
