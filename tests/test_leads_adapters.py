from simple_mailer import mailer
from simple_mailer.core import leads_txt, leads_csv


def test_leads_txt_matches_legacy_reader(tmp_path):
    leads_path = tmp_path / "sample_leads.txt"
    leads_path.write_text("  alpha@example.com  \n\nBravo@example.com\n  \ncharlie@example.com ", encoding="utf-8")

    legacy = mailer.read_leads_file(str(leads_path))
    adapter = leads_txt.read(str(leads_path))

    assert adapter == legacy


def test_leads_csv_reads_expected_fields(tmp_path):
    csv_path = tmp_path / "leads.csv"
    csv_path.write_text(
        "email,fname,lname\n"
        "alice@example.com,Alice,\n"
        "bob@example.com,,Builder\n"
        " ,Ignored,Row\n"
        "carol@example.com,Carol,Carpenter\n",
        encoding="utf-8",
    )

    rows = leads_csv.read(str(csv_path))

    assert rows == [
        {"email": "alice@example.com", "fname": "Alice", "lname": ""},
        {"email": "bob@example.com", "fname": "", "lname": "Builder"},
        {"email": "carol@example.com", "fname": "Carol", "lname": "Carpenter"},
    ]


def test_leads_csv_trims_whitespace(tmp_path):
    csv_path = tmp_path / "leads_trim.csv"
    csv_path.write_text(
        "Email , FName , LName \n"
        " dave@example.com , Dave , Delta \n",
        encoding="utf-8",
    )

    rows = leads_csv.read(str(csv_path))

    assert rows == [{"email": "dave@example.com", "fname": "Dave", "lname": "Delta"}]
