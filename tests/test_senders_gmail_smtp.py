import pytest

from simple_mailer import mailer

from simple_mailer.senders import gmail_smtp


def test_send_forwards_to_mailer(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_send_app_password_message(**kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(mailer, "send_app_password_message", fake_send_app_password_message)

    gmail_smtp.send(
        email="account@example.com",
        password="pass-123",
        to_email="lead@example.com",
        subject="Hello",
        body="Body",
        from_header="Sender <account@example.com>",
        attachments={"invoice.pdf": "/tmp/invoice.pdf"},
        headers={"advance_header": True, "force_header": True, "body_subtype": "html"},
    )

    assert captured["login_email"] == "account@example.com"
    assert captured["from_header"] == "Sender <account@example.com>"
    assert captured["app_password"] == "pass-123"
    assert captured["to_email"] == "lead@example.com"
    assert captured["subject"] == "Hello"
    assert captured["body"] == "Body"
    assert captured["attachments"] == {"invoice.pdf": "/tmp/invoice.pdf"}
    assert captured["advance_header"] is True
    assert captured["force_header"] is True
    assert captured["body_subtype"] == "html"


def test_send_defaults_headers_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_send_app_password_message(**kwargs):
        captured.update(kwargs)
        return "ok"

    monkeypatch.setattr(mailer, "send_app_password_message", fake_send_app_password_message)

    gmail_smtp.send(
        email="account@example.com",
        password="pass-123",
        to_email="lead@example.com",
        subject="Hello",
        body="Body",
    )

    assert captured["from_header"] == "account@example.com"
    assert captured["attachments"] == {}
    assert captured["advance_header"] is False
    assert captured["force_header"] is False
    assert captured["body_subtype"] == "plain"


def test_mailbox_totals_returns_named_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mailer,
        "fetch_mailbox_totals_app_password",
        lambda email, password: (7, 3),
    )

    metrics = gmail_smtp.mailbox_totals("account@example.com", "pass-123")

    assert metrics == {"inbox": 7, "sent": 3}


def test_send_validates_inputs() -> None:
    with pytest.raises(ValueError, match="email is required"):
        gmail_smtp.send(
            email="",
            password="pass-123",
            to_email="lead@example.com",
            subject="Hello",
            body="Body",
        )

    with pytest.raises(ValueError, match="app password is required"):
        gmail_smtp.send(
            email="account@example.com",
            password="",
            to_email="lead@example.com",
            subject="Hello",
            body="Body",
        )


def test_mailbox_totals_validates_inputs() -> None:
    with pytest.raises(ValueError, match="email is required"):
        gmail_smtp.mailbox_totals("", "pass-123")

    with pytest.raises(ValueError, match="app password is required"):
        gmail_smtp.mailbox_totals("account@example.com", "")


def test_send_wraps_mailer_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**kwargs):
        raise RuntimeError("bad state")

    monkeypatch.setattr(mailer, "send_app_password_message", boom)

    with pytest.raises(RuntimeError, match="SMTP send failed: bad state"):
        gmail_smtp.send(
            email="account@example.com",
            password="pass-123",
            to_email="lead@example.com",
            subject="Hello",
            body="Body",
        )


def test_mailbox_totals_wraps_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(email, password):
        raise RuntimeError("imap down")

    monkeypatch.setattr(mailer, "fetch_mailbox_totals_app_password", boom)

    with pytest.raises(RuntimeError, match="SMTP mailbox metrics failed: imap down"):
        gmail_smtp.mailbox_totals("account@example.com", "pass-123")
