import types

import pytest

from ui_token_helpers import authorize_oauth_client, merge_token_sources


def test_authorize_oauth_client_appends_account(monkeypatch):
    dummy_creds = types.SimpleNamespace(token="token-value")

    def fake_initialize(client_json, **kwargs):
        assert "client" in client_json
        return "user@example.com", dummy_creds

    monkeypatch.setattr("ui_token_helpers.oauth_json.initialize", fake_initialize)

    message, updated = authorize_oauth_client("client json", [], auth_mode="gmail_api")

    assert "user@example.com" in message
    assert updated and updated[0]["email"] == "user@example.com"
    assert updated[0]["creds"] is dummy_creds
    assert updated[0]["__in_memory_oauth__"] is True


def test_authorize_oauth_client_returns_error_when_disabled():
    message, updated = authorize_oauth_client("client json", [], auth_mode="app_password")
    assert "Enable" in message
    assert updated == []


def test_authorize_oauth_client_propagates_error(monkeypatch):
    def fake_initialize(client_json, **kwargs):
        raise RuntimeError("bad stuff")

    monkeypatch.setattr("ui_token_helpers.oauth_json.initialize", fake_initialize)

    message, updated = authorize_oauth_client("client json", [], auth_mode="gmail_api")
    assert "bad stuff" in message
    assert updated == []


def test_merge_token_sources_combines_lists():
    uploads = [types.SimpleNamespace(name="file.json")]
    memory = [{"__in_memory_oauth__": True, "email": "a@b", "creds": object()}]

    combined = merge_token_sources(uploads, memory)

    assert combined[:1] == uploads
    assert combined[1:] == memory


def test_merge_token_sources_handles_none_inputs():
    combined = merge_token_sources(None, None)
    assert combined == []
    combined = merge_token_sources([], None)
    assert combined == []
    combined = merge_token_sources(None, [{"email": "x", "creds": object()}])
    assert combined and combined[0]["email"] == "x"
