import base64
from typing import Any, Dict

import pytest

from simple_mailer import mailer


class _DummyCreds:
    token = "token123"


class _DummyResponse:
    status_code = 200

    def json(self) -> Dict[str, Any]:
        return {}


@pytest.fixture(autouse=True)
def _no_request_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mailer.requests, "post", lambda *args, **kwargs: _DummyResponse())


def _decode_raw(raw_payload: str) -> str:
    return base64.urlsafe_b64decode(raw_payload.encode("utf-8")).decode("utf-8")


def test_send_gmail_message_skips_optional_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_post(url: str, headers: Dict[str, str], json: Dict[str, Any], timeout: int):
        captured.update(json)
        return _DummyResponse()

    monkeypatch.setattr(mailer.requests, "post", fake_post)

    mailer.send_gmail_message(
        creds=_DummyCreds(),
        sender_email="sender@example.com",
        to_email="lead@example.com",
        subject="Test",
        body="Body",
        attachments=None,
        advance_header=False,
        force_header=False,
    )

    raw = _decode_raw(captured["raw"])
    assert "X-Sender" not in raw
    assert "Received-SPF" not in raw


def test_send_gmail_message_adds_optional_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_post(url: str, headers: Dict[str, str], json: Dict[str, Any], timeout: int):
        captured.update(json)
        return _DummyResponse()

    monkeypatch.setattr(mailer.requests, "post", fake_post)
    monkeypatch.setattr(mailer, "formatdate", lambda *_args, **_kwargs: "Fri, 19 Sep 2025 00:00:00 -0000")
    monkeypatch.setattr(mailer, "make_msgid", lambda: "<fake-id@example.com>")

    mailer.send_gmail_message(
        creds=_DummyCreds(),
        sender_email="sender@example.com",
        to_email="lead@example.com",
        subject="Test",
        body="Body",
        attachments=None,
        advance_header=True,
        force_header=True,
    )

    raw = _decode_raw(captured["raw"])
    unfolded = raw.replace("\r\n ", " ").replace("\r\n\t", " " ).replace("\n ", " " )
    assert "X-Sender: sender@example.com" in unfolded
    assert "Date: Fri, 19 Sep 2025 00:00:00 -0000" in unfolded
    assert "X-Sender-Identity: sender@example.com" in unfolded
    assert "Message-ID: <fake-id@example.com>" in unfolded
    assert "Received-SPF: Pass (gmail.com: domain of sender@example.com designates 192.0.2.1 as permitted sender)" in unfolded
    assert "Authentication-Results: mx.google.com; spf=pass smtp.mailfrom=sender@example.com; dkim=pass; dmarc=pass" in unfolded
    assert "ARC-Authentication-Results: i=1; mx.google.com; spf=pass; dkim=pass; dmarc=pass" in unfolded
    assert "X-Sender-Reputation-Score: 90" in unfolded

