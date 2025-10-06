import json
from pathlib import Path

import pytest

from simple_mailer.orchestrator import drive_share, email_automatic, email_manual, multi_mode

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ui_snapshots"

_MODE_BUILDERS = {
    "email_manual": ("orchestrator_manual.json", email_manual.build_demo),
    "email_automatic": ("orchestrator_automatic.json", email_automatic.build_demo),
    "drive_manual": ("orchestrator_drive_manual.json", drive_share.build_manual_demo),
    "drive_automatic": ("orchestrator_drive_automatic.json", drive_share.build_automatic_demo),
    "multi_mode": ("orchestrator_multi.json", multi_mode.build_demo),
}


def _component_signature(component):
    return {
        "type": type(component).__name__,
        "label": getattr(component, "label", None),
        "elem_id": getattr(component, "elem_id", None),
    }


def _capture_snapshot(builder):
    demo = builder()
    try:
        collected = []
        for component in demo.blocks.values():
            label = getattr(component, "label", None)
            elem_id = getattr(component, "elem_id", None)
            if label or elem_id:
                collected.append(_component_signature(component))
        collected.sort(key=lambda item: (item["type"], item.get("label") or "", item.get("elem_id") or ""))
        return {"exists": True, "components": collected}
    finally:
        try:
            demo.close()
        except Exception:
            pass


@pytest.mark.parametrize("mode", sorted(_MODE_BUILDERS))
def test_ui_mode_snapshot_matches_baseline(mode):
    fixture_name, builder = _MODE_BUILDERS[mode]
    expected_path = FIXTURE_DIR / fixture_name
    assert expected_path.exists(), f"Missing UI snapshot fixture for {mode}"
    expected_snapshot = json.loads(expected_path.read_text())
    actual_snapshot = _capture_snapshot(builder)
    assert actual_snapshot == expected_snapshot, f"Snapshot for {mode} diverged from baseline"

