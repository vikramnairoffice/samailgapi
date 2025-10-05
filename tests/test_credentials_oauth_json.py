import types

import pytest

from credentials import oauth_json


CLIENT_JSON = '{"installed": {"client_id": "abc", "client_secret": "xyz", "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"], "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}'


def test_initialize_runs_flow_and_returns_email_and_credentials():
    dummy_creds = types.SimpleNamespace(token="access", refresh_token="refresh")

    class DummyFlow:
        def run_console(self):
            return dummy_creds

    captured = {}

    def fake_factory(config, scopes):
        captured["config"] = config
        captured["scopes"] = tuple(scopes)
        return DummyFlow()

    def fake_profile_fetcher(creds):
        assert creds is dummy_creds
        return "user@example.com"

    email, creds = oauth_json.initialize(
        CLIENT_JSON,
        flow_factory=fake_factory,
        profile_fetcher=fake_profile_fetcher,
    )

    assert email == "user@example.com"
    assert creds is dummy_creds
    assert captured["config"]["installed"]["client_id"] == "abc"
    assert "https://mail.google.com/" in captured["scopes"]


def test_initialize_rejects_invalid_json():
    with pytest.raises(ValueError, match="client JSON"):
        oauth_json.initialize("not json at all")


def test_initialize_requires_profile_email():
    class DummyFlow:
        def run_console(self):
            return types.SimpleNamespace(token="abc")

    def fake_factory(config, scopes):
        return DummyFlow()

    with pytest.raises(RuntimeError, match="email"):
        oauth_json.initialize(
            CLIENT_JSON,
            flow_factory=fake_factory,
            profile_fetcher=lambda creds: "",
        )


def test_initialize_raises_when_flow_fails():
    class DummyFlow:
        def run_console(self):
            raise RuntimeError("boom")

    def fake_factory(config, scopes):
        return DummyFlow()

    with pytest.raises(RuntimeError, match="consent"):
        oauth_json.initialize(
            CLIENT_JSON,
            flow_factory=fake_factory,
            profile_fetcher=lambda creds: "user@example.com",
        )
