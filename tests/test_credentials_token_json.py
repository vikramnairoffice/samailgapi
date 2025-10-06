import types

import pytest

from simple_mailer.credentials import token_json


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class DummyCreds:
    def __init__(self, token="token-123", valid=True, expired=False, refresh_token=None):
        self.token = token
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refreshed = False

    def refresh(self, request):
        self.refreshed = True
        self.valid = True
        self.token = self.token or "refreshed-token"


def test_load_returns_email_and_credentials(monkeypatch, tmp_path):
    target = tmp_path / "token.json"
    target.write_text("{}", encoding="utf-8")

    dummy_creds = DummyCreds()

    def fake_from_file(path, scopes):
        assert path == str(target)
        assert tuple(scopes) == token_json.DEFAULT_SCOPES
        return dummy_creds

    monkeypatch.setattr(token_json.Credentials, "from_authorized_user_file", fake_from_file)

    captured = {}

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return DummyResponse(payload={"emailAddress": "account@example.com"})

    monkeypatch.setattr(token_json.requests, "get", fake_get)

    email, creds = token_json.load(target)

    assert email == "account@example.com"
    assert creds is dummy_creds
    assert captured["url"] == token_json.PROFILE_URL
    assert captured["headers"]["Authorization"] == f"Bearer {dummy_creds.token}"
    assert captured["timeout"] == 15


def test_load_raises_when_missing_token(monkeypatch, tmp_path):
    target = tmp_path / "missing.json"
    target.write_text("{}", encoding="utf-8")

    dummy_creds = DummyCreds(token="", valid=True)

    def fake_from_file(path, scopes):
        return dummy_creds

    monkeypatch.setattr(token_json.Credentials, "from_authorized_user_file", fake_from_file)

    with pytest.raises(RuntimeError):
        token_json.load(target)


def test_load_refreshes_expired_credentials(monkeypatch, tmp_path):
    target = tmp_path / "token.json"
    target.write_text("{}", encoding="utf-8")

    dummy_creds = DummyCreds(token="token-abc", valid=False, expired=True, refresh_token="refresh")

    def fake_from_file(path, scopes):
        return dummy_creds

    monkeypatch.setattr(token_json.Credentials, "from_authorized_user_file", fake_from_file)

    def fake_get(url, headers, timeout):
        return DummyResponse(payload={"emailAddress": "account@example.com"})

    monkeypatch.setattr(token_json.requests, "get", fake_get)

    email, creds = token_json.load(target)

    assert email == "account@example.com"
    assert creds is dummy_creds
    assert dummy_creds.refreshed is True
