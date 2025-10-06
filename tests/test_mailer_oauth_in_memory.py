import types

from simple_mailer import mailer


def test_load_accounts_accepts_in_memory_entries():
    dummy_creds = types.SimpleNamespace(token="abc")
    entries = [{
        "__in_memory_oauth__": True,
        "email": "tester@example.com",
        "creds": dummy_creds,
        "label": "in-memory 1",
    }]

    accounts, errors = mailer.load_accounts(entries, auth_mode="gmail_api")

    assert not errors
    assert accounts and accounts[0]["email"] == "tester@example.com"
    assert accounts[0]["creds"] is dummy_creds
    assert accounts[0]["path"] == "in-memory 1"


def test_load_accounts_reports_invalid_in_memory_entries():
    entries = [{"__in_memory_oauth__": True, "email": "", "creds": None, "label": "broken"}]

    accounts, errors = mailer.load_accounts(entries, auth_mode="gmail_api")

    assert not accounts
    assert errors and "broken" in errors[0]
