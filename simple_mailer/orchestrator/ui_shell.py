"""UI entrypoint for the v2 orchestrator."""

from __future__ import annotations

from typing import Callable, Optional

import gradio as gr

from . import modes


def build_ui(*, v2_builder: Optional[Callable[[], gr.Blocks]] = None) -> gr.TabbedInterface:
    """Assemble the orchestrator UI from registered modes."""
    if v2_builder is not None:
        return v2_builder()

    mode_list = list(modes.iter_modes())
    if not mode_list:
        raise RuntimeError("No orchestrator modes registered.")

    blocks = [mode.build_ui() for mode in mode_list]
    titles = [mode.title for mode in mode_list]
    return gr.TabbedInterface(blocks, titles)


__all__ = ["build_ui"]

