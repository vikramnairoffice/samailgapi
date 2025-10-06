from simple_mailer.credentials import app_password


def test_load_parses_valid_entries(tmp_path):
    target = tmp_path / "creds.txt"
    target.write_text(
        "user1@example.com,pass-1\n" "bad-line\n" " user2@example.com , pass-2 \n",
        encoding="utf-8",
    )

    accounts, errors = app_password.load(target)

    assert len(accounts) == 2
    first, second = accounts
    assert first["email"] == "user1@example.com"
    assert first["password"] == "pass-1"
    assert first["path"].endswith("creds.txt:1")
    assert second["email"] == "user2@example.com"
    assert second["password"] == "pass-2"
    assert errors == ["creds.txt line 2: invalid entry"]


def test_load_reports_file_errors(tmp_path):
    target = tmp_path / "missing.txt"

    accounts, errors = app_password.load(target)

    assert accounts == []
    assert errors and "missing.txt" in errors[0]
