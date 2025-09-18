from types import SimpleNamespace

import pytest
import ui_token_helpers as helpers


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_mailbox_counts_preview_success(monkeypatch):
    accounts = [
        {
            'email': 'first@example.com',
            'creds': SimpleNamespace(token='token-1'),
            'path': 'first.json',
        }
    ]

    monkeypatch.setattr(helpers, 'load_token_files', lambda files: (accounts, []))

    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers['Authorization']))
        label_id = url.rsplit('/', 1)[-1]
        if label_id == 'INBOX':
            return FakeResponse(payload={'messagesTotal': 12})
        if label_id == 'SENT':
            return FakeResponse(payload={'messagesTotal': 5})
        raise AssertionError(f'unexpected label {label_id}')

    monkeypatch.setattr(helpers.requests, 'get', fake_get)

    status, markdown = helpers.fetch_mailbox_counts(['first.json'])

    assert status == 'Mailbox counts ready for 1 account(s).'
    assert markdown == '- first@example.com - Inbox: 12 | Sent: 5'
    assert calls == [
        ('https://gmail.googleapis.com/gmail/v1/users/me/labels/INBOX', 'Bearer token-1'),
        ('https://gmail.googleapis.com/gmail/v1/users/me/labels/SENT', 'Bearer token-1'),
    ]


def test_mailbox_counts_handles_token_errors(monkeypatch):
    monkeypatch.setattr(helpers, 'load_token_files', lambda files: ([], ['broken token']))

    status, markdown = helpers.fetch_mailbox_counts(['missing.json'])

    assert status == 'No Gmail token files available. Issues: broken token'
    assert markdown == ''


def test_mailbox_counts_reports_fetch_failure(monkeypatch):
    accounts = [
        {
            'email': 'first@example.com',
            'creds': SimpleNamespace(token='token-1'),
            'path': 'first.json',
        }
    ]

    monkeypatch.setattr(helpers, 'load_token_files', lambda files: (accounts, []))

    def fake_get(url, headers, timeout):
        return FakeResponse(status_code=500, payload={}, text='boom')

    monkeypatch.setattr(helpers.requests, 'get', fake_get)

    status, markdown = helpers.fetch_mailbox_counts(['first.json'])

    assert status == (
        'Failed to collect mailbox counts for uploaded tokens. '
        'Issues: first@example.com: Gmail label fetch failed (INBOX): 500 - boom'
    )
    assert markdown == ''
