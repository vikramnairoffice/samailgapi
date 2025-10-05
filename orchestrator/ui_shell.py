"""Feature-flagged entrypoint for the v2 UI orchestrator."""

from __future__ import annotations

import os
from typing import Callable, Optional

import gradio as gr

from ui import gradio_ui

from . import email_manual

LEGACY_FLAG = "LEGACY_UI_SHELL"
_FALSEY_VALUES = {"0", "false", "off", "no", "disable", "disabled"}


def _normalize_flag(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip().lower()


def is_legacy_enabled(flag_value: Optional[str] = None) -> bool:
    """Return True when the legacy UI should be used."""
    raw_value = flag_value if flag_value is not None else os.getenv(LEGACY_FLAG)
    normalized = _normalize_flag(raw_value)

    if normalized is None or normalized == "":
        return True
    return normalized not in _FALSEY_VALUES


def _build_v2_scaffold() -> gr.Blocks:
    """Return the manual mode orchestrator demo layout."""
    return email_manual.build_demo()


def build_ui(
    *,
    legacy_builder: Callable[[], gr.Blocks] = gradio_ui,
    v2_builder: Optional[Callable[[], gr.Blocks]] = None,
) -> gr.Blocks:
    """Return the Blocks instance selected by the legacy feature flag."""
    if is_legacy_enabled():
        return legacy_builder()

    builder = v2_builder or _build_v2_scaffold
    return builder()

