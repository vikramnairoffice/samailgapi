import json
from pathlib import Path

import pytest

import ui

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ui_snapshots"


def _is_descendant(component, ancestor):
    parent = getattr(component, "parent", None)
    while parent is not None:
        if parent is ancestor:
            return True
        parent = getattr(parent, "parent", None)
    return False


def _component_signature(component):
    return {
        "type": type(component).__name__,
        "label": getattr(component, "label", None),
        "elem_id": getattr(component, "elem_id", None),
    }


def _collect_components(demo, root):
    collected = []
    for component in demo.blocks.values():
        if component is root:
            continue
        if _is_descendant(component, root):
            label = getattr(component, "label", None)
            elem_id = getattr(component, "elem_id", None)
            if label or elem_id:
                collected.append(_component_signature(component))
    collected.sort(key=lambda item: (item["type"], item.get("label") or "", item.get("elem_id") or ""))
    return collected


def _find_tab(blocks, predicate):
    for component in blocks:
        if predicate(component):
            return component
    return None


def _capture_mode_snapshot(mode):
    demo = ui.gradio_ui()
    try:
        blocks = list(demo.blocks.values())
        if mode in {"manual", "automatic"}:
            mode_tabs = _find_tab(
                blocks,
                lambda comp: type(comp).__name__ == "Tabs" and getattr(comp, "elem_id", None) == "mode-tabs",
            )
            if mode_tabs is None:
                return {"exists": False, "reason": "mode-tabs not found"}
            target_tab = _find_tab(
                mode_tabs.children,
                lambda tab: getattr(tab, "label", None) == ("Manual" if mode == "manual" else "Automatic"),
            )
            if target_tab is None:
                return {"exists": False, "reason": f"{mode} tab missing"}
            return {
                "exists": True,
                "components": _collect_components(demo, target_tab),
            }
        if mode == "multi":
            target_tab = _find_tab(
                blocks,
                lambda comp: type(comp).__name__ == "Tab" and getattr(comp, "label", None) == "Multi Mode",
            )
            if target_tab is None:
                return {"exists": False, "reason": "Multi Mode tab missing"}
            return {
                "exists": True,
                "components": _collect_components(demo, target_tab),
            }
        if mode == "drive":
            drive_tab = _find_tab(
                blocks,
                lambda comp: (getattr(comp, "label", None) or "").lower().startswith("drive"),
            )
            if drive_tab is None:
                return {"exists": False, "reason": "Drive mode not present"}
            return {
                "exists": True,
                "components": _collect_components(demo, drive_tab),
            }
        return {"exists": False, "reason": f"Unhandled mode: {mode}"}
    finally:
        try:
            demo.close()
        except Exception:
            pass


@pytest.mark.parametrize("mode", ["manual", "automatic", "drive", "multi"])
def test_ui_mode_snapshot_matches_baseline(mode):
    expected_path = FIXTURE_DIR / f"{mode}.json"
    assert expected_path.exists(), f"Missing UI snapshot fixture for {mode}"
    expected_snapshot = json.loads(expected_path.read_text())
    actual_snapshot = _capture_mode_snapshot(mode)
    assert actual_snapshot == expected_snapshot, f"Snapshot for {mode} diverged from baseline"

