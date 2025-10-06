import importlib

import gradio as gr
import pytest

from simple_mailer.orchestrator import modes


_EXPECTED_MODES = [
    ("simple_mailer.orchestrator.email_manual", "email_manual", "Email Manual", "build_demo"),
    ("simple_mailer.orchestrator.email_automatic", "email_automatic", "Email Automatic", "build_demo"),
    ("simple_mailer.orchestrator.drive_share", "drive_share_manual", "Drive Manual", "build_manual_demo"),
    ("simple_mailer.orchestrator.drive_share", "drive_share_automatic", "Drive Automatic", "build_automatic_demo"),
    ("simple_mailer.orchestrator.multi_mode", "multi_mode", "Multi Mode", "build_demo"),
]


@pytest.mark.parametrize("module_path, expected_id, expected_title, builder_name", _EXPECTED_MODES)
def test_orchestrator_module_exposes_mode(module_path, expected_id, expected_title, builder_name):
    module = importlib.import_module(module_path)
    mode_map = getattr(module, "MODES", None)
    assert isinstance(mode_map, dict), f"{module_path} must define MODES mapping"

    assert expected_id in mode_map, f"{module_path} missing mode {expected_id}"
    mode = mode_map[expected_id]

    assert isinstance(mode, modes.Mode)
    assert mode.id == expected_id
    assert mode.title == expected_title

    builder = getattr(module, builder_name)
    assert mode.build_ui is builder

    ui_instance = mode.build_ui()
    assert ui_instance is not None
    if isinstance(ui_instance, gr.Blocks):
        ui_instance.close()

