import types
from pathlib import Path

import pytest

import mailer


class DummyFile:
    def __init__(self, path):
        self.name = str(path)


def test_load_accounts_app_password_success(tmp_path):
    creds_path = tmp_path / "app_creds.txt"
    creds_path.write_text("account@example.com,pass-123\n", encoding="utf-8")

    accounts, errors = mailer.load_accounts([DummyFile(creds_path)], auth_mode="app_password")

    assert errors == []
    assert len(accounts) == 1
    account = accounts[0]
    assert account["auth_type"] == "app_password"
    assert account["email"] == "account@example.com"
    assert account["password"] == "pass-123"
    assert str(creds_path) in account['path']


def test_load_accounts_app_password_invalid_line(tmp_path):
    creds_path = tmp_path / "broken.txt"
    creds_path.write_text("missing,fields,extra\njust_email@example.com\n", encoding="utf-8")

    accounts, errors = mailer.load_accounts([str(creds_path)], auth_mode="app_password")

    assert accounts == []
    assert len(errors) == 2
    assert "broken.txt" in errors[0]


def test_send_app_password_message(monkeypatch):
    captured = {}

    class DummySMTP:
        def __init__(self, host, port):
            captured["init"] = (host, port)

        def ehlo(self):
            captured.setdefault("ehlo", 0)
            captured["ehlo"] += 1

        def starttls(self, context=None):
            captured["starttls"] = context

        def login(self, user, password):
            captured["login"] = (user, password)

        def sendmail(self, from_email, to_email, message):
            captured["sendmail"] = (from_email, to_email, message)

        def quit(self):
            captured["quit"] = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.quit()

    monkeypatch.setattr(mailer.smtplib, "SMTP", DummySMTP)

    mailer.send_app_password_message(
        login_email='account@example.com',
        from_header='Display Name <account@example.com>',
        app_password='pass-123',
        to_email='lead@example.com',
        subject='Hello',
        body='Body text',
        attachments=None,
        advance_header=False,
        force_header=False,
    )

    assert captured["init"][0] == "smtp.gmail.com"
    assert captured["init"][1] == 587
    assert captured["login"] == ("account@example.com", "pass-123")
    assert captured['sendmail'][0] == 'account@example.com'
    assert captured['sendmail'][1] == 'lead@example.com'
    assert 'starttls' in captured
    assert captured['starttls'] is not None
    payload = captured['sendmail'][2]
    assert 'Subject: Hello' in payload
    assert 'From: Display Name <account@example.com>' in payload


def test_fetch_mailbox_totals_app_password(monkeypatch):
    class DummyIMAP:
        def __init__(self, host):
            self.host = host
            self.selected = []

        def login(self, email, password):
            self.email = email
            self.password = password

        def select(self, mailbox, readonly=True):
            self.selected.append(mailbox)
            return "OK", [b"42"]

        def status(self, mailbox, flags):
            if mailbox == "INBOX":
                return "OK", [b"(MESSAGES 10)"]
            return "OK", [b"(MESSAGES 4)"]

        def logout(self):
            self.logged_out = True

    dummy_imap = DummyIMAP("smtp.gmail.com")

    def imap_factory(host):
        assert host == "imap.gmail.com"
        return dummy_imap

    monkeypatch.setattr(mailer.imaplib, "IMAP4_SSL", imap_factory)

    inbox, sent = mailer.fetch_mailbox_totals_app_password("account@example.com", "pass-123")

    assert inbox == 10
    assert sent == 4
    assert dummy_imap.selected == ["INBOX", "[Gmail]/Sent Mail"]
