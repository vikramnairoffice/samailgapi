import pytest

from simple_mailer.orchestrator import modes, ui_shell


class _DummyMode(modes.Mode):
    def __init__(self, mode_id, title, build_result):
        def _build():
            calls.append(mode_id)
            return build_result

        calls = []
        super().__init__(
            id=mode_id,
            title=title,
            build_ui=_build,
            to_runner_config=lambda payload, adapters=None: {"id": mode_id, "payload": payload},
            run=lambda config, adapters=None: iter(()),
        )
        self._calls = calls

    @property
    def calls(self):
        return self._calls


def test_build_ui_raises_when_no_modes(monkeypatch):
    monkeypatch.setattr(ui_shell.modes, "iter_modes", lambda: [])

    with pytest.raises(RuntimeError):
        ui_shell.build_ui()


def test_build_ui_uses_registered_modes(monkeypatch):
    mode_a = modes.Mode(
        id="manual",
        title="Manual",
        build_ui=lambda: "ui-a",
        to_runner_config=lambda payload, adapters=None: {"mode": "manual", "payload": payload},
        run=lambda config, adapters=None: iter(()),
    )
    mode_b = modes.Mode(
        id="auto",
        title="Automatic",
        build_ui=lambda: "ui-b",
        to_runner_config=lambda payload, adapters=None: {"mode": "auto", "payload": payload},
        run=lambda config, adapters=None: iter(()),
    )
    monkeypatch.setattr(ui_shell.modes, "iter_modes", lambda: [mode_a, mode_b])

    captured = {}

    def fake_tabbed(blocks, titles):
        captured["blocks"] = blocks
        captured["titles"] = titles
        return "tabbed"

    monkeypatch.setattr(ui_shell.gr, "TabbedInterface", fake_tabbed)

    result = ui_shell.build_ui()

    assert result == "tabbed"
    assert captured["blocks"] == ["ui-a", "ui-b"]
    assert captured["titles"] == ["Manual", "Automatic"]

 
