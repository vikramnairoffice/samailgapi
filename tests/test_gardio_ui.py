import io
import hashlib
from pathlib import Path

import pytest

import gardio_ui


def test_blueprint_dimensions():
    image = gardio_ui.create_blueprint("email_manual")
    assert image.size == gardio_ui.CANVAS_SIZE


def test_guard_focus_is_subset():
    available = set(gardio_ui.FEATURE_CHOICES)
    for spec in gardio_ui.LAYOUT_SPECS.values():
        missing = [item for item in spec.guard_focus if item not in available]
        assert not missing, f"Guard focus not in feature choices: {missing}"

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gardio_blueprints"


def _hash_image(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return hashlib.sha256(buffer.getvalue()).hexdigest()


@pytest.mark.parametrize("layout", [
    "email_manual",
    "email_automatic",
    "drive_share",
    "multi_mode",
])
def test_blueprint_snapshots_match_baseline(layout):
    expected_path = FIXTURE_DIR / f"{layout}.png"
    assert expected_path.exists(), f"Missing baseline fixture for {layout}"
    expected_hash = hashlib.sha256(expected_path.read_bytes()).hexdigest()
    actual = gardio_ui.create_blueprint(layout)
    actual_hash = _hash_image(actual)
    assert actual_hash == expected_hash, f"Blueprint for {layout} diverged from baseline"
