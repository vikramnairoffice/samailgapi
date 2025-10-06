import gradio as gr
import pytest

from simple_mailer.orchestrator import ui_shell
from simple_mailer import ui


FEATURE_FLAG = "SIMPLE_MAILER_UI_SHELL"


def _make_sentinel(label):
    class _Sentinel:
        def __init__(self):
            self.label = label

    return _Sentinel()


@pytest.fixture(autouse=True)
def _reset_flag(monkeypatch):
    monkeypatch.delenv(FEATURE_FLAG, raising=False)


def test_gradio_ui_defaults_to_legacy_layout(monkeypatch):
    sentinel = _make_sentinel("orchestrator")
    monkeypatch.setattr(ui_shell, "build_ui", lambda: sentinel)

    result = ui.gradio_ui()

    assert result is not sentinel
    assert isinstance(result, gr.Blocks)
    result.close()


def test_gradio_ui_uses_orchestrator_when_flag_set(monkeypatch):
    sentinel = _make_sentinel("orchestrator")
    monkeypatch.setattr(ui_shell, "build_ui", lambda: sentinel)
    monkeypatch.setenv(FEATURE_FLAG, "1")

    result = ui.gradio_ui()

    assert result is sentinel
