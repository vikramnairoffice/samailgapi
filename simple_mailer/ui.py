"""Gradio entrypoint delegating to the orchestrator UI shell."""

from __future__ import annotations

import gradio as gr

from simple_mailer.orchestrator import ui_shell


def gradio_ui() -> gr.Blocks | gr.TabbedInterface:
    """Return the orchestrator UI component."""
    return ui_shell.build_ui()


def main() -> None:
    app = gradio_ui()
    if hasattr(app, "launch"):
        app.launch()
    else:
        raise RuntimeError("UI shell did not return a launchable Gradio interface.")


__all__ = ["gradio_ui", "main"]


if __name__ == "__main__":
    main()
