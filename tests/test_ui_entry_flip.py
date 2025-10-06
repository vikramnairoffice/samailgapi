import gradio as gr
import pytest

from simple_mailer.orchestrator import ui_shell
from simple_mailer import ui


LEGACY_FLAG = "SIMPLE_MAILER_UI_SHELL"


def _make_sentinel(label):
    class _Sentinel:
        def __init__(self):
            self.label = label

    return _Sentinel()


@pytest.fixture(autouse=True)
def _reset_flag(monkeypatch):
    monkeypatch.delenv(LEGACY_FLAG, raising=False)


def test_gradio_ui_uses_orchestrator(monkeypatch):
    sentinel = _make_sentinel("orchestrator")
    monkeypatch.setattr(ui_shell, "build_ui", lambda: sentinel)

    result = ui.gradio_ui()

    assert result is sentinel


def test_gradio_ui_ignores_legacy_flag(monkeypatch):
    sentinel = _make_sentinel("flagged")
    monkeypatch.setattr(ui_shell, "build_ui", lambda: sentinel)
    monkeypatch.setenv(LEGACY_FLAG, "0")

    result = ui.gradio_ui()

    assert result is sentinel


def test_main_launches_orchestrator(monkeypatch):
    launch_calls = []

    class _DummyBlocks:
        def launch(self, *args, **kwargs):
            launch_calls.append((args, kwargs))

    monkeypatch.setattr(ui_shell, "build_ui", lambda: _DummyBlocks())

    ui.main()

    assert launch_calls
