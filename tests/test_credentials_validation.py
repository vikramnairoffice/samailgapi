import pytest

from simple_mailer.credentials import validation


class DummyFile:
    def __init__(self, path):
        self.name = str(path)


def test_normalize_mode_aliases():
    assert validation.normalize_mode('gmail_api') == 'oauth'
    assert validation.normalize_mode('App Password') == 'app_password'
    assert validation.normalize_mode(None) == 'oauth'


def test_validate_files_oauth_counts_files_without_loader(tmp_path):
    first = tmp_path / 'token1.json'
    first.write_text('{}', encoding='utf-8')
    second = tmp_path / 'token2.json'
    second.write_text('{}', encoding='utf-8')

    result = validation.validate_files([DummyFile(first), str(second)], 'oauth')

    assert result.accounts == []
    assert result.errors == []
    assert result.status == '2 token file(s) selected'


def test_validate_files_oauth_uses_loader(tmp_path):
    token_path = tmp_path / 'token.json'
    token_path.write_text('{}', encoding='utf-8')

    calls = []

    def fake_loader(path):
        calls.append(path)
        return 'acct@example.com', object()

    result = validation.validate_files([str(token_path)], 'gmail_api', loader=fake_loader)

    assert calls == [str(token_path)]
    assert len(result.accounts) == 1
    account = result.accounts[0]
    assert account['email'] == 'acct@example.com'
    assert account['auth_type'] == 'oauth'
    assert result.errors == []
    assert result.status == '1 token file(s) selected'


def test_validate_files_in_memory_entries():
    creds = object()
    entry = {
        '__in_memory_oauth__': True,
        'email': 'session@example.com',
        'creds': creds,
        'label': 'Session OAuth',
    }

    result = validation.validate_files([entry], 'oauth')

    assert len(result.accounts) == 1
    account = result.accounts[0]
    assert account['email'] == 'session@example.com'
    assert account['creds'] is creds
    assert account['path'] == 'Session OAuth'
    assert 'in-memory credential' in result.status.lower()
    assert result.errors == []


def test_validate_files_app_password_status(tmp_path):
    creds_path = tmp_path / 'creds.txt'
    creds_path.write_text('user@example.com,pass-123\n', encoding='utf-8')

    result = validation.validate_files([DummyFile(creds_path)], 'app_password')

    assert len(result.accounts) == 1
    account = result.accounts[0]
    assert account['email'] == 'user@example.com'
    assert account['password'] == 'pass-123'
    assert result.errors == []
    assert result.status.startswith('1 app password(s) parsed')


def test_validate_files_app_password_includes_errors(tmp_path):
    creds_path = tmp_path / 'broken.txt'
    creds_path.write_text('missing parts\nno,comma,here\n', encoding='utf-8')

    result = validation.validate_files([str(creds_path)], 'app-password')

    assert result.accounts == []
    assert len(result.errors) == 2
    assert 'issues' in result.status
    assert 'broken.txt' in result.status
