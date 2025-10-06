"""UI entrypoint for the v2 orchestrator."""

from __future__ import annotations

from typing import Callable, Optional

import gradio as gr

from . import email_manual


def _build_v2_scaffold() -> gr.Blocks:
    """Return the manual mode orchestrator demo layout."""
    return email_manual.build_demo()


def build_ui(*, v2_builder: Optional[Callable[[], gr.Blocks]] = None) -> gr.Blocks:
    """Return the Blocks instance for the v2 orchestrator."""
    builder = v2_builder or _build_v2_scaffold
    return builder()
