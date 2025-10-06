"""Multi-mode orchestrator embedding email and drive flows behind an account switcher."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

import gradio as gr

from . import drive_share, email_automatic, email_manual, modes


@dataclass(frozen=True)
class MultiModeBuilders:
    """Collection of builders used to compose the multi-mode UI."""

    manual: Callable[[], gr.Blocks]
    automatic: Callable[[], gr.Blocks]
    drive_manual: Callable[[], gr.Blocks]
    drive_automatic: Callable[[], gr.Blocks]

    @classmethod
    def default(cls) -> "MultiModeBuilders":
        return cls(
            manual=email_manual.build_demo,
            automatic=email_automatic.build_demo,
            drive_manual=drive_share.build_manual_demo,
            drive_automatic=drive_share.build_automatic_demo,
        )


def _extract_account_name(entry: object) -> Optional[str]:
    raw_name = getattr(entry, "orig_name", None) or getattr(entry, "name", None)
    if not raw_name:
        return None
    base = os.path.basename(str(raw_name))
    stem, _ = os.path.splitext(base)
    clean = stem.strip()
    return clean or None


def collect_account_names(token_files: Optional[Sequence[object]]) -> List[str]:
    """Return ordered list of unique account names derived from uploaded token files."""
    accounts: List[str] = []
    for entry in token_files or []:
        name = _extract_account_name(entry)
        if not name or name in accounts:
            continue
        accounts.append(name)
    return accounts


def select_active_account(accounts: Sequence[str], requested: Optional[str]) -> Optional[str]:
    """Return the requested account when available, otherwise the first option."""
    if requested and requested in accounts:
        return requested
    if accounts:
        return accounts[0]
    return None


def _dropdown_payload(accounts: Sequence[str], active: Optional[str]) -> dict:
    visible = bool(accounts)
    return gr.update(
        choices=list(accounts),
        value=active if visible else None,
        visible=visible,
    )


def sync_accounts(
    token_files: Optional[Sequence[object]],
    current_active: Optional[str],
) -> Tuple[dict, List[str], Optional[str], dict, dict]:
    """Normalize uploaded token files into selector + visibility updates."""
    accounts = collect_account_names(token_files)
    active = select_active_account(accounts, current_active)
    dropdown_update = _dropdown_payload(accounts, active)
    notice_update = gr.update(visible=not accounts)
    container_update = gr.update(visible=bool(accounts))
    return dropdown_update, accounts, active, notice_update, container_update


def _format_active_message(active: Optional[str]) -> str:
    if not active:
        return "No account selected."
    return f"Configuring account: {active}"


def _build_tabbed_interface(builders: MultiModeBuilders) -> gr.TabbedInterface:
    manual = builders.manual()
    automatic = builders.automatic()
    drive_manual = builders.drive_manual()
    drive_automatic = builders.drive_automatic()
    return gr.TabbedInterface(
        [manual, automatic, drive_manual, drive_automatic],
        ["Email Manual", "Email Automatic", "Drive Manual", "Drive Automatic"],
    )


def build_demo(*, builders: Optional[MultiModeBuilders] = None) -> gr.Blocks:
    """Return the multi-mode Blocks layout with account switching controls."""
    builders = builders or MultiModeBuilders.default()

    with gr.Blocks() as demo:
        accounts_state = gr.State(value=[])
        active_account_state = gr.State(value=None)

        token_files = gr.Files(
            label="Account Tokens",
            file_count="multiple",
            elem_id="multi-token-files",
        )
        notice = gr.Markdown(
            "Upload account tokens to enable multi mode.",
            elem_id="multi-account-notice",
        )
        account_selector = gr.Dropdown(
            label="Account",
            choices=[],
            value=None,
            visible=False,
            elem_id="multi-account-dropdown",
        )
        active_label = gr.Markdown(
            _format_active_message(None),
            elem_id="multi-active-account",
        )
        with gr.Column(visible=False, elem_id="multi-mode-tabs") as tab_container:
            _build_tabbed_interface(builders)

        def _on_tokens_change(files, active_value):
            dropdown_update, accounts, active, notice_update, container_update = sync_accounts(files, active_value)
            label_update = gr.update(value=_format_active_message(active))
            return dropdown_update, accounts, active, notice_update, container_update, label_update

        token_files.change(
            _on_tokens_change,
            inputs=[token_files, active_account_state],
            outputs=[
                account_selector,
                accounts_state,
                active_account_state,
                notice,
                tab_container,
                active_label,
            ],
        )

        def _on_account_change(selected, accounts):
            active = select_active_account(accounts, selected)
            return active, gr.update(value=_format_active_message(active))

        account_selector.change(
            _on_account_change,
            inputs=[account_selector, accounts_state],
            outputs=[active_account_state, active_label],
        )

    return demo


MODE_MULTI_MODE = modes.Mode(
    id='multi_mode',
    title='Multi Mode',
    build_ui=build_demo,
    to_runner_config=lambda payload, adapters=None: payload,
    run=lambda config, adapters=None: iter(()),
)

MODES = {
    'multi_mode': MODE_MULTI_MODE,
}

modes.register_mode(MODE_MULTI_MODE)

__all__ = [
    "MultiModeBuilders",
    "build_demo",
    "collect_account_names",
    "select_active_account",
    "sync_accounts",
    "MODES",
]
