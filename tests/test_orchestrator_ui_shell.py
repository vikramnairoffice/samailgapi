import os

import pytest

from orchestrator import ui_shell


def _tracking_builder(label, calls):
    def _inner():
        calls.append(label)
        return label

    return _inner


def test_build_ui_defaults_to_legacy(monkeypatch):
    monkeypatch.delenv(ui_shell.LEGACY_FLAG, raising=False)
    legacy_calls = []
    v2_calls = []

    legacy_builder = _tracking_builder("legacy", legacy_calls)
    v2_builder = _tracking_builder("v2", v2_calls)

    result = ui_shell.build_ui(legacy_builder=legacy_builder, v2_builder=v2_builder)

    assert result == "legacy"
    assert legacy_calls == ["legacy"]
    assert v2_calls == []


@pytest.mark.parametrize("flag_value", ["0", "false", "False", "OFF", "no"])
def test_build_ui_switches_to_v2_when_flag_disabled(monkeypatch, flag_value):
    monkeypatch.setenv(ui_shell.LEGACY_FLAG, flag_value)
    legacy_calls = []
    v2_calls = []

    legacy_builder = _tracking_builder("legacy", legacy_calls)
    v2_builder = _tracking_builder("v2", v2_calls)

    result = ui_shell.build_ui(legacy_builder=legacy_builder, v2_builder=v2_builder)

    assert result == "v2"
    assert legacy_calls == []
    assert v2_calls == ["v2"]


@pytest.mark.parametrize("flag_value", ["1", "true", "True", "ON"])
def test_build_ui_respects_truthy_flag(monkeypatch, flag_value):
    monkeypatch.setenv(ui_shell.LEGACY_FLAG, flag_value)
    legacy_calls = []
    v2_calls = []

    legacy_builder = _tracking_builder("legacy", legacy_calls)
    v2_builder = _tracking_builder("v2", v2_calls)

    result = ui_shell.build_ui(legacy_builder=legacy_builder, v2_builder=v2_builder)

    assert result == "legacy"
    assert legacy_calls == ["legacy"]
    assert v2_calls == []
