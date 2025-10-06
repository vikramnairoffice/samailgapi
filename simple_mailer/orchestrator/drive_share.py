"""Drive share orchestrator modules for manual and automatic modes."""

from __future__ import annotations

import html as _html_module
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import gradio as gr

from . import modes
from .email_manual import ManualModeAdapters
from manual_mode import ManualAttachmentSpec

_DEFAULT_PREVIEW_EMAIL = "drive-preview@example.com"
_PREVIEW_PLACEHOLDER = (
    "<div style='opacity:0.65;'>Preview will appear after you click "
    "<strong>Prepare Drive Share</strong>.</div>"
)
_TEMPLATE_CHOICES = ["Manual", "Invoice", "HTML Upload"]


@dataclass(frozen=True)
class DriveManualPreview:
    """Container describing attachment preview details for Drive share."""

    asset_names: List[str]
    selected_asset: Optional[str]
    html_preview: str
    text_preview: str


@dataclass(frozen=True)
class DriveManualState:
    """Computed manual Drive share configuration and preview details."""

    delay_seconds: float
    tfn: str
    notify: bool
    message_html: str
    conversion_mode: str
    attachments: Tuple[ManualAttachmentSpec, ...]
    converted_assets: Dict[str, str]
    preview: DriveManualPreview


@dataclass(frozen=True)
class DriveShareAdapters:
    """Bundle of adapter callables used by Drive share orchestrator."""

    create_config: Callable[..., object]
    parse_extra_tags: Callable[[Optional[Sequence[Sequence[str]]]], Dict[str, str]]
    to_attachment_specs: Callable[..., Sequence[ManualAttachmentSpec]]
    attachment_listing: Callable[[Sequence[ManualAttachmentSpec]], Tuple[List[str], Optional[str], str, str]]
    attachment_preview: Callable[[Sequence[ManualAttachmentSpec], str], Tuple[str, str]]

    @classmethod
    def default(cls) -> "DriveShareAdapters":
        manual = ManualModeAdapters.default()
        return cls(
            create_config=manual.create_config,
            parse_extra_tags=manual.parse_extra_tags,
            to_attachment_specs=manual.to_attachment_specs,
            attachment_listing=manual.attachment_listing,
            attachment_preview=manual.attachment_preview,
        )


def _wrap_text_as_html(text: str) -> str:
    escaped = _html_module.escape(text or "")
    return f"<pre style='white-space:pre-wrap; margin:0;'>{escaped}</pre>"


def _normalize_conversion(mode: str) -> str:
    normalized = (mode or "original").strip().lower().replace(" ", "_")
    return normalized or "original"


def _normalize_delay(value: float) -> float:
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(delay, 0.0)


def _ensure_adapters(adapters: Optional[DriveShareAdapters]) -> DriveShareAdapters:
    return adapters or DriveShareAdapters.default()


def _build_preview(specs: Sequence[ManualAttachmentSpec], adapters: DriveShareAdapters) -> DriveManualPreview:
    names, selected, html_preview, text_preview = adapters.attachment_listing(specs)
    return DriveManualPreview(
        asset_names=list(names),
        selected_asset=selected,
        html_preview=html_preview,
        text_preview=text_preview,
    )


def build_manual_state(
    *,
    message: str,
    message_is_html: bool,
    randomize_html: bool,
    tfn: str,
    notify: bool,
    delay_seconds: float,
    extra_tags: Optional[Sequence[Sequence[str]]],
    attachment_mode: str,
    attachment_files: Optional[Iterable[object]],
    inline_html: str,
    inline_name: str,
    adapters: Optional[DriveShareAdapters] = None,
    preview_email: str = _DEFAULT_PREVIEW_EMAIL,
) -> DriveManualState:
    """Return manual Drive share state using the provided adapters."""
    adapter_bundle = _ensure_adapters(adapters)

    tags = adapter_bundle.parse_extra_tags(extra_tags)
    specs = tuple(
        adapter_bundle.to_attachment_specs(
            attachment_files,
            inline_html=inline_html or "",
            inline_name=inline_name or "",
        )
    )

    conversion = _normalize_conversion(attachment_mode)
    config = adapter_bundle.create_config(
        enabled=True,
        subject="",
        body=message or "",
        body_is_html=bool(message_is_html),
        tfn=tfn or "",
        body_image_enabled=False,
        randomize_html=bool(randomize_html),
        extra_tags=tags,
        attachments=list(specs),
        attachment_mode=conversion,
        attachments_enabled=bool(specs),
    )

    context = config.build_context(preview_email or _DEFAULT_PREVIEW_EMAIL)
    rendered_body, kind = config.render_body(context)
    if kind == "html":
        message_html = rendered_body
    else:
        message_html = _wrap_text_as_html(rendered_body)

    converted_assets = config.build_attachments(context)
    preview = _build_preview(specs, adapter_bundle)

    return DriveManualState(
        delay_seconds=_normalize_delay(delay_seconds),
        tfn=tfn or "",
        notify=bool(notify),
        message_html=message_html,
        conversion_mode=conversion,
        attachments=specs,
        converted_assets=converted_assets,
        preview=preview,
    )


def build_automatic_state(
    *,
    message: str,
    tfn: str,
    notify: bool,
    delay_seconds: float,
    extra_tags: Optional[Sequence[Sequence[str]]],
    attachment_mode: str,
    attachment_files: Optional[Iterable[object]],
    inline_html: str,
    inline_name: str,
    adapters: Optional[DriveShareAdapters] = None,
    randomize_html: bool = False,
    preview_email: str = _DEFAULT_PREVIEW_EMAIL,
) -> DriveManualState:
    """Return automatic Drive share state, forcing HTML body rendering."""
    return build_manual_state(
        message=message,
        message_is_html=True,
        randomize_html=randomize_html,
        tfn=tfn,
        notify=notify,
        delay_seconds=delay_seconds,
        extra_tags=extra_tags,
        attachment_mode=attachment_mode,
        attachment_files=attachment_files,
        inline_html=inline_html,
        inline_name=inline_name,
        adapters=adapters,
        preview_email=preview_email,
    )


def _render_asset_preview(
    adapters: DriveShareAdapters,
    specs: Sequence[ManualAttachmentSpec],
    selected_name: Optional[str],
) -> str:
    if not specs or not selected_name:
        return _PREVIEW_PLACEHOLDER
    html_payload, text_payload = adapters.attachment_preview(specs, selected_name)
    if html_payload:
        return html_payload
    if text_payload:
        return _wrap_text_as_html(text_payload)
    return _PREVIEW_PLACEHOLDER


def _prepare_manual_share(
    adapters: DriveShareAdapters,
    message: str,
    message_is_html: bool,
    randomize_html: bool,
    tfn: str,
    notify: bool,
    delay_seconds: float,
    extra_tags,
    include_assets: bool,
    attachment_mode: str,
    attachment_files,
    inline_html: str,
    inline_name: str,
):
    files = attachment_files if include_assets else None
    inline_payload = inline_html if include_assets else ""

    state = build_manual_state(
        message=message,
        message_is_html=message_is_html,
        randomize_html=randomize_html,
        tfn=tfn,
        notify=notify,
        delay_seconds=delay_seconds,
        extra_tags=extra_tags,
        attachment_mode=attachment_mode,
        attachment_files=files,
        inline_html=inline_payload,
        inline_name=inline_name,
        adapters=adapters,
    )

    asset_choices = state.preview.asset_names
    selected_asset = state.preview.selected_asset
    asset_fragment = (
        state.preview.html_preview
        or (_wrap_text_as_html(state.preview.text_preview) if state.preview.text_preview else _PREVIEW_PLACEHOLDER)
    )

    return (
        state,
        gr.update(choices=asset_choices, value=selected_asset),
        state.message_html,
        asset_fragment,
        gr.update(value="Ready to share."),
    )


def build_manual_demo(*, adapters: Optional[DriveShareAdapters] = None) -> gr.Blocks:
    """Return Gradio Blocks layout for Drive manual mode."""
    adapter_bundle = _ensure_adapters(adapters)

    with gr.Blocks() as demo:
        state_holder = gr.State()

        with gr.Group(elem_id="drive-manual-root"):
            with gr.Row():
                with gr.Column(elem_id="drive-manual-config"):
                    delay = gr.Number(label="Delay (seconds)", value=0.0, minimum=0)
                    tfn = gr.Textbox(label="TFN Number", placeholder="Optional TFN override")
                    notify = gr.Checkbox(label="Send Notification Email", value=True)
                    message_is_html = gr.Checkbox(label="Message Uses HTML", value=False)
                    randomize_html = gr.Checkbox(label="Randomize HTML Styling", value=False)
                    message = gr.Textbox(
                        label="Custom Message",
                        lines=8,
                        placeholder="Custom Drive share message (tags supported)",
                    )
                    extra_tags = gr.Dataframe(
                        headers=["Tag", "Value"],
                        datatype=["str", "str"],
                        row_count=(1, "dynamic"),
                        type="array",
                        label="Additional Tags",
                    )
                    include_assets = gr.Checkbox(label="Include Assets", value=False)
                    attachment_mode = gr.Dropdown(
                        choices=["original", "pdf", "html"],
                        value="original",
                        label="Asset Conversion",
                    )
                    attachment_files = gr.Files(
                        label="Drive Assets",
                        file_count="multiple",
                    )
                    inline_name = gr.Textbox(label="Inline Asset Name", value="drive.html")
                    inline_html = gr.Textbox(label="Inline Asset HTML", lines=6)
                    prepare = gr.Button("Prepare Drive Share", variant="secondary")
                with gr.Column(elem_id="drive-manual-preview"):
                    asset_selection = gr.Dropdown(
                        label="Asset Selection",
                        choices=[],
                    )
                    message_preview = gr.HTML(label="Message Preview", value=_PREVIEW_PLACEHOLDER)
                    asset_preview = gr.HTML(label="Asset Preview", value=_PREVIEW_PLACEHOLDER)
                    run_log = gr.Textbox(label="Run Log", lines=10)

        prepare.click(
            lambda *args: _prepare_manual_share(adapter_bundle, *args),
            inputs=[
                message,
                message_is_html,
                randomize_html,
                tfn,
                notify,
                delay,
                extra_tags,
                include_assets,
                attachment_mode,
                attachment_files,
                inline_html,
                inline_name,
            ],
            outputs=[state_holder, asset_selection, message_preview, asset_preview, run_log],
        )

        asset_selection.change(
            lambda state, selected: _render_asset_preview(adapter_bundle, getattr(state, "attachments", ()), selected),
            inputs=[state_holder, asset_selection],
            outputs=asset_preview,
        )

    return demo


def _prepare_automatic_share(
    adapters: DriveShareAdapters,
    template_choice: str,
    html_upload,
    custom_html: str,
    randomize_html: bool,
    tfn: str,
    notify: bool,
    delay_seconds: float,
    attachment_mode: str,
    attachment_files,
):
    upload_payload = ""
    if html_upload:
        file_obj = html_upload[0] if isinstance(html_upload, (list, tuple)) else html_upload
        path = getattr(file_obj, "name", None)
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    upload_payload = handle.read()
            except OSError:
                upload_payload = ""

    base_html = (custom_html or "").strip() or upload_payload.strip()
    if not base_html:
        base_html = f"<p>{_html_module.escape(template_choice or 'Template')}</p>"

    state = build_automatic_state(
        message=base_html,
        tfn=tfn,
        notify=notify,
        delay_seconds=delay_seconds,
        extra_tags=None,
        attachment_mode=attachment_mode,
        attachment_files=attachment_files,
        inline_html="",
        inline_name="drive.html",
        adapters=adapters,
        randomize_html=randomize_html,
    )

    asset_choices = state.preview.asset_names
    selected_asset = state.preview.selected_asset
    asset_fragment = (
        state.preview.html_preview
        or (_wrap_text_as_html(state.preview.text_preview) if state.preview.text_preview else _PREVIEW_PLACEHOLDER)
    )

    return (
        state,
        gr.update(choices=asset_choices, value=selected_asset),
        state.message_html,
        asset_fragment,
        gr.update(value="Ready to share."),
    )


def build_automatic_demo(*, adapters: Optional[DriveShareAdapters] = None) -> gr.Blocks:
    """Return Gradio Blocks layout for Drive automatic mode."""
    adapter_bundle = _ensure_adapters(adapters)

    with gr.Blocks() as demo:
        state_holder = gr.State()

        with gr.Group(elem_id="drive-automatic-root"):
            with gr.Row():
                with gr.Column(elem_id="drive-automatic-config"):
                    delay = gr.Number(label="Delay (seconds)", value=0.0, minimum=0)
                    tfn = gr.Textbox(label="TFN Number", placeholder="Optional TFN override")
                    notify = gr.Checkbox(label="Send Notification Email", value=True)
                    template_choice = gr.Dropdown(
                        label="Template Choice",
                        choices=_TEMPLATE_CHOICES,
                        value=_TEMPLATE_CHOICES[0],
                    )
                    html_upload = gr.Files(label="HTML Upload", file_count="single")
                    custom_html = gr.Textbox(label="Custom HTML", lines=8)
                    randomize_html = gr.Checkbox(label="Randomize HTML Styling", value=False)
                    attachment_mode = gr.Dropdown(
                        choices=["original", "pdf", "html"],
                        value="original",
                        label="Asset Conversion",
                    )
                    attachment_files = gr.Files(label="Drive Assets", file_count="multiple")
                    prepare = gr.Button("Prepare Drive Share", variant="secondary")
                with gr.Column(elem_id="drive-automatic-preview"):
                    asset_selection = gr.Dropdown(label="Asset Selection", choices=[])
                    message_preview = gr.HTML(label="Message Preview", value=_PREVIEW_PLACEHOLDER)
                    asset_preview = gr.HTML(label="Asset Preview", value=_PREVIEW_PLACEHOLDER)
                    run_log = gr.Textbox(label="Run Log", lines=10)

        prepare.click(
            lambda *args: _prepare_automatic_share(adapter_bundle, *args),
            inputs=[
                template_choice,
                html_upload,
                custom_html,
                randomize_html,
                tfn,
                notify,
                delay,
                attachment_mode,
                attachment_files,
            ],
            outputs=[state_holder, asset_selection, message_preview, asset_preview, run_log],
        )

        asset_selection.change(
            lambda state, selected: _render_asset_preview(adapter_bundle, getattr(state, "attachments", ()), selected),
            inputs=[state_holder, asset_selection],
            outputs=asset_preview,
        )

    return demo


MODE_DRIVE_MANUAL = modes.Mode(
    id='drive_share_manual',
    title='Drive Manual',
    build_ui=build_manual_demo,
    to_runner_config=lambda payload, adapters=None: payload,
    run=lambda config, adapters=None: iter(()),
)

MODE_DRIVE_AUTOMATIC = modes.Mode(
    id='drive_share_automatic',
    title='Drive Automatic',
    build_ui=build_automatic_demo,
    to_runner_config=lambda payload, adapters=None: payload,
    run=lambda config, adapters=None: iter(()),
)

MODES = {
    'drive_share_manual': MODE_DRIVE_MANUAL,
    'drive_share_automatic': MODE_DRIVE_AUTOMATIC,
}

modes.register_mode(MODE_DRIVE_MANUAL)
modes.register_mode(MODE_DRIVE_AUTOMATIC)

__all__ = [
    "DriveManualPreview",
    "DriveManualState",
    "DriveShareAdapters",
    "build_manual_state",
    "build_automatic_state",
    "build_manual_demo",
    "build_automatic_demo",
    "MODES",
]
