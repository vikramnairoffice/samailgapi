from pathlib import Path
import hashlib

LAYOUTS = [
    "email_manual",
    "email_automatic",
    "drive_share",
    "multi_mode",
]

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "gardio_blueprints"
DOC_PATH = Path(__file__).parents[1] / "docs" / "BLUEPRINT_AUDIT.md"


def _parse_audit_table(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        if line.startswith("| Layout"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        layout, sha_value, status = parts[:3]
        rows[layout] = {"sha": sha_value, "status": status.lower()}
    return rows


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_blueprint_audit_matches_fixtures():
    assert DOC_PATH.exists(), "docs/BLUEPRINT_AUDIT.md is missing"
    audit_rows = _parse_audit_table(DOC_PATH.read_text())

    for layout in LAYOUTS:
        fixture_path = FIXTURES_DIR / f"{layout}.png"
        assert fixture_path.exists(), f"Missing blueprint fixture for {layout}"
        expected_hash = _hash_file(fixture_path)
        assert layout in audit_rows, f"{layout} missing from blueprint audit doc"
        row = audit_rows[layout]
        assert row["sha"] == expected_hash, (
            f"{layout} hash mismatch: doc has {row['sha']}, expected {expected_hash}"
        )
        assert row["status"] == "match", (
            f"{layout} status should be match when hashes align (found {row['status']})"
        )
