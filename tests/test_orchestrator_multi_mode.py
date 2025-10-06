import json
from dataclasses import dataclass
from pathlib import Path

import gradio as gr
import pytest

from simple_mailer.orchestrator import multi_mode


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ui_snapshots"


@dataclass
class DummyFile:
    name: str
    orig_name: str | None = None


def _collect_multi_components(demo: gr.Blocks):
    components = []
    for component in demo.blocks.values():
        elem_id = getattr(component, "elem_id", None)
        if not elem_id or not elem_id.startswith("multi-"):
            continue
        components.append(
            {
                "type": type(component).__name__,
                "label": getattr(component, "label", None),
                "elem_id": elem_id,
            }
        )
    components.sort(key=lambda item: item["elem_id"])
    return components

def _capture_snapshot(builder):
    demo = builder()
    try:
        return {
            "exists": True,
            "components": _collect_multi_components(demo),
        }
    finally:
        try:
            demo.close()
        except Exception:
            pass



def test_collect_account_names_extracts_unique_basenames():
    files = [
        DummyFile(name="alpha.json"),
        DummyFile(name="/tmp/beta.TOKEN"),
        DummyFile(name="gamma.json", orig_name="delta.json"),
        DummyFile(name="alpha.json"),
        DummyFile(name=""),
    ]

    result = multi_mode.collect_account_names(files)

    assert result == ["alpha", "beta", "delta"]


def test_sync_accounts_returns_updates_with_active_selection():
    files = [DummyFile(name="acct-one.json"), DummyFile(name="acct-two.json")]

    dropdown_update, accounts, active, notice_update, container_update = multi_mode.sync_accounts(files, None)

    assert dropdown_update["choices"] == ["acct-one", "acct-two"]
    assert dropdown_update["value"] == "acct-one"
    assert dropdown_update["visible"] is True
    assert accounts == ["acct-one", "acct-two"]
    assert active == "acct-one"
    assert notice_update["visible"] is False
    assert container_update["visible"] is True


def test_select_active_account_defaults_when_missing():
    accounts = ["alpha", "beta"]

    selected = multi_mode.select_active_account(accounts, "gamma")

    assert selected == "alpha"


def test_build_demo_uses_provided_builders():
    calls = []

    def make_builder(tag):
        def _builder():
            calls.append(tag)
            with gr.Blocks() as demo:
                gr.Markdown(f"{tag} placeholder")
            return demo

        return _builder

    builders = multi_mode.MultiModeBuilders(
        manual=make_builder("manual"),
        automatic=make_builder("automatic"),
        drive_manual=make_builder("drive-manual"),
        drive_automatic=make_builder("drive-automatic"),
    )

    demo = multi_mode.build_demo(builders=builders)
    try:
        assert calls == ["manual", "automatic", "drive-manual", "drive-automatic"]
    finally:
        try:
            demo.close()
        except Exception:
            pass



