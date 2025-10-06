from simple_mailer.orchestrator import ui_shell


def _tracking_builder(label, calls):
    def _inner():
        calls.append(label)
        return label

    return _inner


def test_build_ui_uses_v2_builder():
    calls = []
    v2_builder = _tracking_builder("v2", calls)

    result = ui_shell.build_ui(v2_builder=v2_builder)

    assert result == "v2"
    assert calls == ["v2"]


def test_build_ui_defaults_to_internal_scaffold(monkeypatch):
    calls = []

    def fake_scaffold():
        calls.append("internal")
        return "internal"

    monkeypatch.setattr(ui_shell, "_build_v2_scaffold", fake_scaffold)

    result = ui_shell.build_ui()

    assert result == "internal"
    assert calls == ["internal"]
