"""Top-level package exposing the simple mailer runtime modules."""

from importlib import import_module

from . import colab_setup, content, credentials, core, invoice, mailer, orchestrator, senders, ui, ui_token_helpers

exec_adapters = import_module('.exec', __name__)

globals()['exec'] = exec_adapters

__all__ = [
    "mailer",
    "ui",
    "invoice",
    "content",
    "ui_token_helpers",
    "colab_setup",
    "core",
    "credentials",
    "orchestrator",
    "senders",
    "exec",
]
