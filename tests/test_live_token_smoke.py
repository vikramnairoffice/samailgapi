import os
from types import SimpleNamespace

import pytest

from testing import live_token_smoke as smoke


def test_send_email_invokes_adapter(monkeypatch):
    captured = {}

    def fake_send(creds, sender_email, to_email, subject, body, *, attachments=None, headers=None):
        captured["creds"] = creds
        captured["sender"] = sender_email
        captured["to"] = to_email
        captured["subject"] = subject
        captured["body"] = body
        captured["attachments"] = dict(attachments or {})
        captured["headers"] = dict(headers or {})
        return {"id": "msg-123", "status": "SENT"}

    messages = []

    def recorder(message: str) -> None:
        messages.append(message)

    result = smoke.send_test_email(
        creds=object(),
        sender_email="sender@example.com",
        recipient_email="recipient@example.com",
        reference="ref-abc",
        subject="Invoice",
        body="Body",
        attachments={"invoice.pdf": "path/to/invoice.pdf"},
        send_adapter=fake_send,
        log=recorder,
    )

    assert result == {"id": "msg-123", "status": "SENT"}
    assert captured["headers"]["X-Ref"] == "ref-abc"
    assert len(messages) == 1
    assert "msg-123" in messages[0]


def test_poll_inbox_retries_until_reference_found(monkeypatch):
    calls = []

    responses = iter([
        {"messages": []},
        {"messages": [{"id": "abc123"}]},
    ])

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append({"url": url, "params": dict(params or {})})
        return SimpleNamespace(status_code=200, json=lambda: next(responses), text="OK")

    sleeplog = []

    def fake_sleep(duration):
        sleeplog.append(duration)

    result = smoke.poll_inbox_for_reference(
        creds=SimpleNamespace(token="token"),
        reference="ref-123",
        http_get=fake_get,
        sleep=fake_sleep,
        interval_seconds=0,
        max_wait_seconds=5,
        log=lambda msg: None,
    )

    assert result == {"id": "abc123"}
    assert len(calls) == 2
    assert "ref-123" in calls[0]["params"].get("q", "")


def test_poll_inbox_times_out(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None):
        return SimpleNamespace(status_code=200, json=lambda: {"messages": []}, text="OK")

    with pytest.raises(RuntimeError) as excinfo:
        smoke.poll_inbox_for_reference(
            creds=SimpleNamespace(token="token"),
            reference="ref-404",
            http_get=fake_get,
            sleep=lambda _: None,
            interval_seconds=0,
            max_wait_seconds=1,
            log=lambda msg: None,
        )

    assert "ref-404" in str(excinfo.value)


def test_share_invoice_uploads_and_grants_permission(tmp_path):
    attachment = tmp_path / "invoice.pdf"
    attachment.write_bytes(b"invoice")

    call_log = {"create": [], "permission": []}

    class StubFiles:
        def create(self, *, body, media_body, fields):
            call_log["create"].append({"body": body, "fields": fields, "media_body": media_body})

            class Exec:
                def execute(self_nonlocal):
                    return {"id": "file-123"}

            return Exec()

    class StubPermissions:
        def create(self, *, fileId, body, fields):
            call_log["permission"].append({"fileId": fileId, "body": body, "fields": fields})

            class Exec:
                def execute(self_nonlocal):
                    return {"id": "perm-1", "role": "reader"}

            return Exec()

    class StubDrive:
        def files(self):
            return StubFiles()

        def permissions(self):
            return StubPermissions()

    def fake_factory(_creds):
        return StubDrive()

    result = smoke.share_invoice_via_drive(
        creds=object(),
        invoice_path=str(attachment),
        recipient_email="recipient@example.com",
        drive_factory=fake_factory,
        log=lambda message: None,
    )

    assert result == {"file_id": "file-123", "permission_id": "perm-1"}
    assert call_log["create"][0]["body"]["name"] == "invoice.pdf"
    perm_body = call_log["permission"][0]["body"]
    assert perm_body["emailAddress"] == "recipient@example.com"
    assert perm_body["role"] == "reader"


def test_run_smoke_requires_flag(monkeypatch):
    monkeypatch.delenv("LIVE_TOKEN_SMOKE", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        smoke.run_live_smoke(
            creds=object(),
            sender_email="sender@example.com",
            recipient_email="recipient@example.com",
            env={},
            send_helper=lambda **_: None,
            poll_helper=lambda **_: None,
            drive_helper=lambda **_: None,
        )

    assert "LIVE_TOKEN_SMOKE=1" in str(excinfo.value)


@pytest.mark.live_token
def test_live_smoke_integration_skips_without_flag(monkeypatch):
    monkeypatch.delenv("LIVE_TOKEN_SMOKE", raising=False)
    if not smoke.is_enabled():
        pytest.skip("LIVE_TOKEN_SMOKE=1 required for live smoke harness")

    pytest.fail("Integration should skip when flag missing")