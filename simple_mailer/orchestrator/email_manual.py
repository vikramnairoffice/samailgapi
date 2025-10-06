"""Manual mode UI orchestrator bridging adapters to Gradio components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import gradio as gr

from . import modes
from simple_mailer.manual import manual_config_adapter, manual_preview_adapter
from manual_mode import ManualAttachmentSpec, ManualConfig
from simple_mailer.ui_token_helpers import manual_random_sender_name
from simple_mailer.content import DEFAULT_SENDER_NAME_TYPE, SENDER_NAME_TYPES

DEFAULT_PREVIEW_EMAIL = "preview@example.com"
_PREVIEW_PLACEHOLDER = (
    "<div style='opacity:0.7;'>Preview will appear after you click "
    "<strong>Update Preview</strong>.</div>"
)


@dataclass(frozen=True)
class ManualModeAdapters:
    """Bundle of adapter callables used by the manual mode orchestrator."""

    create_config: Callable[..., ManualConfig]
    parse_extra_tags: Callable[[Optional[Sequence[Sequence[str]]]], Dict[str, str]]
    to_attachment_specs: Callable[..., Sequence[ManualAttachmentSpec]]
    preview_snapshot: Callable[[ManualConfig, str, Optional[str]], Tuple[List[str], str, Dict[str, str], Dict[str, bool]]]
    attachment_listing: Callable[[Sequence[ManualAttachmentSpec]], Tuple[List[str], Optional[str], str, str]]
    attachment_preview: Callable[[Sequence[ManualAttachmentSpec], str], Tuple[str, str]]
    random_sender_name: Callable[[str], str]

    @classmethod
    def default(cls) -> "ManualModeAdapters":
        return cls(
            create_config=manual_config_adapter.create_config,
            parse_extra_tags=manual_config_adapter.parse_extra_tags,
            to_attachment_specs=lambda files, *, inline_html="", inline_name="": manual_config_adapter.to_attachment_specs(
                files,
                inline_html=inline_html,
                inline_name=inline_name,
            ),
            preview_snapshot=manual_preview_adapter.build_snapshot,
            attachment_listing=manual_preview_adapter.attachment_listing,
            attachment_preview=manual_preview_adapter.attachment_preview,
            random_sender_name=manual_random_sender_name,
        )


@dataclass(frozen=True)
class ManualPreviewState:
    """Container for preview choices and rendered HTML fragments."""

    choices: List[str]
    default: str
    html_map: Dict[str, str]
    meta: Dict[str, bool]
    attachments: Tuple[ManualAttachmentSpec, ...]


def _normalize_attachment_mode(value: str) -> str:
    normalized = (value or "original").strip().lower()
    return normalized or "original"


def _normalize_sender_type(value: str) -> str:
    return value or DEFAULT_SENDER_NAME_TYPE


def build_manual_config(
    *,
    subject: str,
    body: str,
    body_is_html: bool,
    body_image_enabled: bool,
    randomize_html: bool,
    tfn: str,
    extra_tags: Optional[Sequence[Sequence[str]]],
    attachment_enabled: bool,
    attachment_mode: str,
    attachment_files: Optional[Sequence[object]],
    inline_html: str,
    inline_name: str,
    sender_name: str,
    change_name: bool,
    sender_type: str,
    adapters: Optional[ManualModeAdapters] = None,
) -> Tuple[ManualConfig, Tuple[ManualAttachmentSpec, ...]]:
    """Construct a ManualConfig instance and return it with attachment specs."""
    adapters = adapters or ManualModeAdapters.default()
    tag_mapping = adapters.parse_extra_tags(extra_tags)
    specs = tuple(
        adapters.to_attachment_specs(
            attachment_files,
            inline_html=inline_html or "",
            inline_name=inline_name or "",
        )
    )
    payload = {
        "enabled": True,
        "subject": subject or "",
        "body": body or "",
        "body_is_html": bool(body_is_html),
        "body_image_enabled": bool(body_image_enabled),
        "randomize_html": bool(randomize_html),
        "tfn": tfn or "",
        "extra_tags": tag_mapping,
        "attachments": specs,
        "attachment_mode": _normalize_attachment_mode(attachment_mode),
        "attachments_enabled": bool(attachment_enabled),
        "sender_name": sender_name or "",
        "change_name_every_time": bool(change_name),
        "sender_name_type": _normalize_sender_type(sender_type),
    }
    config = adapters.create_config(**payload)
    return config, specs


def build_preview_state(
    *,
    subject: str,
    body: str,
    body_is_html: bool,
    body_image_enabled: bool,
    randomize_html: bool,
    tfn: str,
    extra_tags: Optional[Sequence[Sequence[str]]],
    attachment_enabled: bool,
    attachment_mode: str,
    attachment_files: Optional[Sequence[object]],
    inline_html: str,
    inline_name: str,
    sender_name: str,
    change_name: bool,
    sender_type: str,
    selected_attachment_name: Optional[str],
    adapters: Optional[ManualModeAdapters] = None,
) -> ManualPreviewState:
    """Return rendered preview data for the manual mode inputs."""
    adapters = adapters or ManualModeAdapters.default()
    config, attachments = build_manual_config(
        subject=subject,
        body=body,
        body_is_html=body_is_html,
        body_image_enabled=body_image_enabled,
        randomize_html=randomize_html,
        tfn=tfn,
        extra_tags=extra_tags,
        attachment_enabled=attachment_enabled,
        attachment_mode=attachment_mode,
        attachment_files=attachment_files,
        inline_html=inline_html,
        inline_name=inline_name,
        sender_name=sender_name,
        change_name=change_name,
        sender_type=sender_type,
        adapters=adapters,
    )
    choices, default_choice, html_map, meta = adapters.preview_snapshot(
        config,
        preview_email=DEFAULT_PREVIEW_EMAIL,
        selected_attachment_name=selected_attachment_name,
    )
    return ManualPreviewState(
        choices=list(choices),
        default=default_choice,
        html_map=dict(html_map),
        meta=dict(meta),
        attachments=attachments,
    )


def _handle_preview(
    subject,
    body,
    body_is_html,
    body_image_enabled,
    randomize_html,
    tfn,
    extra_tags,
    attachment_enabled,
    attachment_mode,
    attachment_files,
    inline_html,
    inline_name,
    sender_name,
    change_name,
    sender_type,
    current_preview_target,
    selected_attachment_name,
    *,
    adapters: ManualModeAdapters,
):
    state = build_preview_state(
        subject=subject,
        body=body,
        body_is_html=bool(body_is_html),
        body_image_enabled=bool(body_image_enabled),
        randomize_html=bool(randomize_html),
        tfn=tfn or "",
        extra_tags=extra_tags,
        attachment_enabled=bool(attachment_enabled),
        attachment_mode=attachment_mode or "",
        attachment_files=attachment_files,
        inline_html=inline_html or "",
        inline_name=inline_name or "",
        sender_name=sender_name or "",
        change_name=bool(change_name),
        sender_type=sender_type or "",
        selected_attachment_name=selected_attachment_name,
        adapters=adapters,
    )

    choices = state.choices or ["Body"]
    if current_preview_target in choices:
        target = current_preview_target
    elif state.default in choices:
        target = state.default
    else:
        target = choices[0]

    attachment_names = [
        spec.display_name
        for spec in state.attachments
        if getattr(spec, "display_name", "")
    ]
    attachment_value = None
    if attachment_names:
        if selected_attachment_name in attachment_names:
            attachment_value = selected_attachment_name
        else:
            attachment_value = attachment_names[0]

    preview_update = gr.update(choices=choices, value=target)
    attachment_update = gr.update(choices=attachment_names, value=attachment_value)
    html_value = state.html_map.get(target, _PREVIEW_PLACEHOLDER)
    if not html_value:
        html_value = _PREVIEW_PLACEHOLDER
    return preview_update, attachment_update, html_value


def build_demo(adapters: Optional[ManualModeAdapters] = None) -> gr.Blocks:
    """Construct the manual mode demo Blocks layout."""
    adapters = adapters or ManualModeAdapters.default()

    def _preview_callback(*args):
        return _handle_preview(*args, adapters=adapters)

    with gr.Blocks(title="Simple Gmail REST Mailer (Manual Mode)") as demo:
        with gr.Group(elem_id="manual-mode-root"):
            gr.Markdown("## Manual Email Mode")
            with gr.Row():
                with gr.Column(scale=2, elem_id="manual-config-panel"):
                    sender_type = gr.Radio(
                        choices=SENDER_NAME_TYPES,
                        value=DEFAULT_SENDER_NAME_TYPE,
                        label="Sender Name Style",
                    )
                    change_name = gr.Checkbox(
                        label="Change Name Every Send",
                        value=True,
                    )
                    sender_name = gr.Textbox(
                        label="Sender Name",
                        placeholder="Optional fixed sender name",
                    )
                    pick_sender = gr.Button(
                        "Pick Random Name",
                        variant="secondary",
                    )
                    subject = gr.Textbox(
                        label="Subject",
                        placeholder="Subject line",
                    )
                    body_is_html = gr.Checkbox(
                        label="Body Uses HTML",
                        value=False,
                    )
                    body_image_enabled = gr.Checkbox(
                        label="Render HTML Body as Image",
                        value=False,
                    )
                    randomize_html = gr.Checkbox(
                        label="Randomize HTML Styling",
                        value=False,
                    )
                    body = gr.Textbox(
                        label="Body",
                        lines=12,
                        placeholder="Paste body content (supports tags)",
                    )
                    tfn = gr.Textbox(
                        label="TFN Number",
                        placeholder="Optional",
                    )
                    extra_tags = gr.Dataframe(
                        headers=["Tag", "Value"],
                        datatype=["str", "str"],
                        row_count=(1, "dynamic"),
                        type="array",
                        label="Additional Tags",
                    )
                    attachment_enabled = gr.Checkbox(
                        label="Include Attachment",
                        value=False,
                    )
                    attachment_mode = gr.Dropdown(
                        choices=["original", "pdf", "flat_pdf", "docx", "png", "heif"],
                        value="original",
                        label="Attachment Mode",
                    )
                    attachment_files = gr.Files(
                        label="Attachment Files",
                        file_count="multiple",
                    )
                    inline_name = gr.Textbox(
                        label="Inline Attachment Name",
                        value="inline.html",
                    )
                    inline_html = gr.Textbox(
                        label="Inline Attachment HTML",
                        lines=6,
                    )
                with gr.Column(scale=1, elem_id="manual-preview-panel"):
                    preview_target = gr.Radio(
                        choices=["Body"],
                        value="Body",
                        label="Preview Source",
                    )
                    attachment_choice = gr.Dropdown(
                        choices=[],
                        value=None,
                        label="Attachment Selection",
                    )
                    preview_button = gr.Button(
                        "Update Preview",
                        variant="secondary",
                    )
                    preview_html = gr.HTML(
                        label="Preview",
                        value=_PREVIEW_PLACEHOLDER,
                    )

        pick_sender.click(
            lambda sender_type_value: adapters.random_sender_name(sender_type_value or DEFAULT_SENDER_NAME_TYPE),
            inputs=sender_type,
            outputs=sender_name,
        )

        preview_button.click(
            _preview_callback,
            inputs=[
                subject,
                body,
                body_is_html,
                body_image_enabled,
                randomize_html,
                tfn,
                extra_tags,
                attachment_enabled,
                attachment_mode,
                attachment_files,
                inline_html,
                inline_name,
                sender_name,
                change_name,
                sender_type,
                preview_target,
                attachment_choice,
            ],
            outputs=[preview_target, attachment_choice, preview_html],
        )

    return demo


MODE_EMAIL_MANUAL = modes.Mode(
    id='email_manual',
    title='Email Manual',
    build_ui=build_demo,
    to_runner_config=lambda payload, adapters=None: payload,
    run=lambda config, adapters=None: iter(()),
)

MODES = {
    'email_manual': MODE_EMAIL_MANUAL,
}

modes.register_mode(MODE_EMAIL_MANUAL)

__all__ = [
    "DEFAULT_PREVIEW_EMAIL",
    "ManualModeAdapters",
    "ManualPreviewState",
    "build_manual_config",
    "build_preview_state",
    "build_demo",
    "MODES",
]
