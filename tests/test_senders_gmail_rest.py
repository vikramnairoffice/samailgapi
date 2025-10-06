from types import SimpleNamespace

from simple_mailer import mailer
import pytest

from simple_mailer.senders import gmail_rest


def test_send_forwards_to_mailer(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_send(creds, sender_email, to_email, subject, body, attachments, advance_header, force_header, body_subtype):
        captured.update(
            {
                "creds": creds,
                "sender_email": sender_email,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "attachments": attachments,
                "advance_header": advance_header,
                "force_header": force_header,
                "body_subtype": body_subtype,
            }
        )
        return {"id": "abc123"}

    monkeypatch.setattr(mailer, "send_gmail_message", fake_send)

    creds = SimpleNamespace(token="ya29.token")
    result = gmail_rest.send(
        creds,
        "Sender <sender@example.com>",
        "lead@example.com",
        "Hello",
        "Body",
        attachments={"invoice.pdf": "/tmp/invoice.pdf"},
        headers={"advance_header": True, "force_header": True, "body_subtype": "html"},
    )

    assert result == {"id": "abc123"}
    assert captured["creds"] is creds
    assert captured["sender_email"] == "Sender <sender@example.com>"
    assert captured["to_email"] == "lead@example.com"
    assert captured["subject"] == "Hello"
    assert captured["body"] == "Body"
    assert captured["attachments"] == {"invoice.pdf": "/tmp/invoice.pdf"}
    assert captured["advance_header"] is True
    assert captured["force_header"] is True
    assert captured["body_subtype"] == "html"


def test_send_defaults_headers_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_send(creds, sender_email, to_email, subject, body, attachments, advance_header, force_header, body_subtype):
        captured.update(
            {
                "attachments": attachments,
                "advance_header": advance_header,
                "force_header": force_header,
                "body_subtype": body_subtype,
            }
        )
        return {"id": "xyz789"}

    monkeypatch.setattr(mailer, "send_gmail_message", fake_send)

    creds = SimpleNamespace(token="ya29.token")
    result = gmail_rest.send(
        creds,
        "Sender <sender@example.com>",
        "lead@example.com",
        "Hello",
        "Body",
    )

    assert result == {"id": "xyz789"}
    assert captured["attachments"] == {}
    assert captured["advance_header"] is False
    assert captured["force_header"] is False
    assert captured["body_subtype"] == "plain"
