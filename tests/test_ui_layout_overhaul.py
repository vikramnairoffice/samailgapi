import types

import gradio as gr

from simple_mailer import ui
from simple_mailer.orchestrator import multi_mode


def _find_root_tabs(app: gr.Blocks) -> gr.Blocks:
    for component in app.blocks.values():
        if component.__class__.__name__ == "Tabs" and getattr(component, "children", None):
            return component
    raise AssertionError("Root tabs container not found")


def test_gradio_ui_exposes_mode_tabs():
    app = ui.gradio_ui()
    try:
        tabs = _find_root_tabs(app)
        labels = [tab.label for tab in tabs.children]
        assert labels == ["Email Manual", "Email Automatic", "Drive Manual", "Drive Automatic", "Multi Mode"]
    finally:
        app.close()


def test_collect_account_names_prefers_orig_name():
    files = [
        types.SimpleNamespace(name="C:/tmp/alpha.json", orig_name="alpha.json"),
        types.SimpleNamespace(name="C:/tmp/beta.json", orig_name=None),
        types.SimpleNamespace(name="C:/tmp/sub/gamma.TXT", orig_name="gamma_special.txt"),
    ]
    assert multi_mode.collect_account_names(files) == ["alpha", "beta", "gamma_special"]


def test_sync_accounts_sets_selector_visibility(monkeypatch):
    files = [types.SimpleNamespace(name="C:/tokens/delta.json", orig_name="delta.json")]
    dropdown_update, accounts, active, notice_update, container_update = multi_mode.sync_accounts(files, None)
    assert dropdown_update["value"] == "delta"
    assert accounts == ["delta"]
    assert active == "delta"
    assert notice_update["visible"] is False
    assert container_update["visible"] is True

