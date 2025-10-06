import base64
from email.parser import BytesParser
from types import SimpleNamespace

from simple_mailer import mailer


def test_send_gmail_message_posts_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        })

        class _Response:
            status_code = 200

            def json(self):
                return {"id": "abc123"}

        return _Response()

    monkeypatch.setattr(mailer.requests, "post", fake_post)

    creds = SimpleNamespace(token="ya29.token")
    result = mailer.send_gmail_message(
        creds,
        "Sender <sender@example.com>",
        "lead@example.com",
        "Hello",
        "<b>Body</b>",
        attachments={},
        advance_header=True,
        force_header=True,
        body_subtype="html",
    )

    assert result == {"id": "abc123"}
    assert captured["url"] == mailer.GMAIL_SEND_URL
    assert captured["headers"]["Authorization"] == "Bearer ya29.token"
    assert captured["timeout"] == 15

    raw_bytes = base64.urlsafe_b64decode(captured["json"]["raw"].encode("utf-8"))
    message = BytesParser().parsebytes(raw_bytes)

    assert message["To"] == "lead@example.com"
    assert message["From"] == "Sender <sender@example.com>"
    assert message["Subject"] == "Hello"
    assert message["X-Sender"] == "Sender <sender@example.com>"
    assert message["Message-ID"]
    assert message["Received-SPF"]
    assert message["Authentication-Results"]
    assert message["ARC-Authentication-Results"]
    assert message["X-Sender-Reputation-Score"]

    assert any(
        part.get_content_type() == "text/html"
        for part in message.walk()
        if part.get_content_maintype() == "text"
    )


def test_compose_email_respects_template_fallbacks(monkeypatch):
    calls = {}

    def fake_get_subject_and_body(subject_choice, body_choice):
        calls["subject_choice"] = subject_choice
        calls["body_choice"] = body_choice
        return "Subject", "Body"

    def fake_generate_sender(name_type):
        calls["sender_name_type"] = name_type
        return "Sender Person"

    monkeypatch.setattr(mailer.content_manager, "get_subject_and_body", fake_get_subject_and_body)
    monkeypatch.setattr(mailer, "generate_sender_name", fake_generate_sender)

    subject, body, from_header = mailer.compose_email(
        "user@example.com",
        {
            "content_template": "own_proven",
            "subject_template": "",
            "body_template": None,
            "sender_name_type": "personal",
        },
    )

    assert subject == "Subject"
    assert body == "Body"
    assert from_header == "Sender Person <user@example.com>"
    assert calls["subject_choice"] == "own_proven"
    assert calls["body_choice"] == "own_proven"
    assert calls["sender_name_type"] == "personal"


def test_send_single_email_uses_invoice_generator_and_send(tmp_path, monkeypatch):
    invoice_calls = []
    invoice_path = tmp_path / "generated.pdf"
    invoice_path.write_bytes(b"invoice")

    def fake_compose(account_email, config):
        return "Subject", "Body", f"Sender <{account_email}>"

    compose_calls = []

    def tracked_compose(account_email, config):
        compose_calls.append(account_email)
        return fake_compose(account_email, config)

    class DummyInvoice:
        def generate_for_recipient(self, lead_email, support_number, invoice_format):
            invoice_calls.append((lead_email, support_number, invoice_format))
            return str(invoice_path)

    send_calls = []

    def fake_send_gmail(creds, from_header, to_email, subject, body, attachments, advance_header, force_header, body_subtype):
        send_calls.append(
            {
                "creds": creds,
                "from_header": from_header,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "attachments": attachments,
                "advance_header": advance_header,
                "force_header": force_header,
                "body_subtype": body_subtype,
            }
        )

    monkeypatch.setattr(mailer, "compose_email", tracked_compose)
    monkeypatch.setattr(mailer, "send_gmail_message", fake_send_gmail)

    account = {"email": "sender@example.com", "creds": SimpleNamespace(token="token")}
    config = {
        "email_content_mode": "invoice",
        "invoice_format": "pdf",
        "support_number": "999-123",
        "sender_name_type": "business",
        "advance_header": False,
        "force_header": False,
    }

    success, message = mailer.send_single_email(account, "lead@example.com", config, DummyInvoice())

    assert success is True
    assert message == "Sent to lead@example.com"
    assert compose_calls == ["sender@example.com"]
    assert invoice_calls == [("lead@example.com", "999-123", "pdf")]
    assert send_calls

    send_call = send_calls[0]
    assert send_call["to_email"] == "lead@example.com"
    assert send_call["from_header"] == "Sender <sender@example.com>"
    assert send_call["attachments"] == {"generated.pdf": str(invoice_path)}
    assert send_call["body_subtype"] == "plain"


def test_campaign_events_uses_default_delay_for_invalid_input(monkeypatch):
    accounts = [{"email": "sender@example.com", "creds": SimpleNamespace(token="token")}]  # oauth path

    def fake_load_accounts(token_files, auth_mode="oauth"):
        return accounts, []

    def fake_load_default_recipients():
        return ["lead@example.com"]

    captured = {}

    def fake_run_campaign(accounts_arg, mode, leads, config, delay):
        captured.update(
            {
                "accounts": accounts_arg,
                "mode": mode,
                "leads": leads,
                "config": config,
                "delay": delay,
            }
        )
        return iter(())

    monkeypatch.setattr(mailer, "load_accounts", fake_load_accounts)
    monkeypatch.setattr(mailer, "load_default_gmass_recipients", fake_load_default_recipients)
    monkeypatch.setattr(mailer, "run_campaign", fake_run_campaign)

    events = list(
        mailer.campaign_events(
            token_files=["token.json"],
            leads_file=None,
            send_delay_seconds="not-a-number",
            mode="gmass",
        )
    )

    assert captured["delay"] == mailer.SEND_DELAY_SECONDS
    assert captured["mode"] == "gmass"
    assert captured["leads"] == ["lead@example.com"]
    assert events and events[-1]["kind"] == "done"


def test_campaign_events_clamps_negative_delay(monkeypatch):
    accounts = [{"email": "sender@example.com", "creds": SimpleNamespace(token="token")}]  # oauth path

    def fake_load_accounts(token_files, auth_mode="oauth"):
        return accounts, []

    def fake_load_default_recipients():
        return ["lead@example.com"]

    def fake_run_campaign(accounts_arg, mode, leads, config, delay):
        assert delay == 0.0
        yield {
            "account": accounts_arg[0]["email"],
            "lead": leads[0],
            "success": True,
            "message": "sent",
        }

    monkeypatch.setattr(mailer, "load_accounts", fake_load_accounts)
    monkeypatch.setattr(mailer, "load_default_gmass_recipients", fake_load_default_recipients)
    monkeypatch.setattr(mailer, "run_campaign", fake_run_campaign)

    events = list(
        mailer.campaign_events(
            token_files=["token.json"],
            leads_file=None,
            send_delay_seconds=-3,
            mode="gmass",
        )
    )

    progress_events = [event for event in events if event["kind"] == "progress"]
    assert progress_events
    assert progress_events[0]["successes"] == 1
    assert progress_events[0]["total"] == 1
    assert events[-1]["kind"] == "done"
