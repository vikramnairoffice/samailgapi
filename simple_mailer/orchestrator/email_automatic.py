"""Automatic email mode orchestrator helpers for HTML and invoice flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import gradio as gr

from . import modes
from simple_mailer.content import DEFAULT_SENDER_NAME_TYPE, SENDER_NAME_TYPES

_TEMPLATE_DISPLAY_CHOICES = ("own_proven", "Own_last", "R1_Tag")
_TEMPLATE_ALIAS_MAP = {
    "gmass_inboxed": "own_last",
    "own-last": "own_last",
    "own_last": "own_last",
    "r1-tag": "r1_tag",
    "r1_tag": "r1_tag",
}
_DEFAULT_TEMPLATE = "own_proven"
_EMAIL_CONTENT_MODES = {"attachment", "invoice"}
_INVOICE_FORMATS = {"pdf", "docx", "png", "heif"}
_ATTACHMENT_CONVERSION_CHOICES = ("Doc", "Image", "Keep Original")
_DOCUMENT_FORMAT_CHOICES = ("PDF", "Flat PDF", "Docx")
_IMAGE_FORMAT_CHOICES = ("PNG", "HEIF")
_PREVIEW_PLACEHOLDER = (
    "<div style='opacity:0.7;'>Preview will appear after configuration is submitted." "</div>"
)


@dataclass(frozen=True)
class AutomaticConfig:
    """Normalized configuration shared by automatic email modes."""

    content_template: str
    subject_template: str
    body_template: str
    sender_name_type: str
    email_content_mode: str
    attachment_folder: str
    invoice_format: str
    support_number: str


@dataclass(frozen=True)
class AutomaticInvoiceConfig(AutomaticConfig):
    """Normalized configuration for invoice-based automatic mode."""


@dataclass(frozen=True)
class AutomaticHtmlConfig(AutomaticConfig):
    """Normalized configuration for HTML automatic mode with preview toggles."""

    randomize_html: bool
    inline_png: bool
    html_upload_path: str
    inline_html: str
    tfn: str


@dataclass(frozen=True)
class AutomaticModeAdapters:
    """Bundle of normalization helpers so tests can stub edge cases."""

    normalize_template: Callable[[Optional[str], str], str]
    normalize_sender_type: Callable[[Optional[str]], str]
    normalize_content_mode: Callable[[Optional[str]], str]
    normalize_invoice_format: Callable[[Optional[str]], str]
    sanitize_folder: Callable[[Optional[str]], str]
    sanitize_support_number: Callable[[Optional[str]], str]
    sanitize_text: Callable[[Optional[str]], str]
    sanitize_optional_path: Callable[[Optional[str]], str]
    coerce_bool: Callable[[object], bool]

    @classmethod
    def default(cls) -> "AutomaticModeAdapters":
        return cls(
            normalize_template=_normalize_template,
            normalize_sender_type=_normalize_sender_type,
            normalize_content_mode=_normalize_content_mode,
            normalize_invoice_format=_normalize_invoice_format,
            sanitize_folder=_sanitize_folder,
            sanitize_support_number=_sanitize_text,
            sanitize_text=_sanitize_text,
            sanitize_optional_path=_sanitize_optional_path,
            coerce_bool=_coerce_bool,
        )


def _normalize_template(value: Optional[str], kind: str) -> str:
    raw = (value or "").strip().lower().replace(" ", "_")
    if not raw:
        return _DEFAULT_TEMPLATE
    resolved = _TEMPLATE_ALIAS_MAP.get(raw, raw)
    if resolved not in {"own_proven", "own_last", "r1_tag"}:
        raise ValueError(f"Unsupported {kind} template: {value!r}")
    return resolved


def _normalize_sender_type(value: Optional[str]) -> str:
    candidate = (value or DEFAULT_SENDER_NAME_TYPE).strip().lower()
    if not candidate:
        return DEFAULT_SENDER_NAME_TYPE
    for choice in SENDER_NAME_TYPES:
        if choice.lower() == candidate:
            return choice
    raise ValueError(f"Unsupported sender name type: {value!r}")


def _normalize_content_mode(value: Optional[str]) -> str:
    candidate = (value or "attachment").strip().lower()
    if candidate in _EMAIL_CONTENT_MODES:
        return candidate
    raise ValueError(f"Unsupported email content mode: {value!r}")


def _normalize_invoice_format(value: Optional[str]) -> str:
    candidate = (value or "pdf").strip().lower()
    if candidate in _INVOICE_FORMATS:
        return candidate
    raise ValueError(f"Unsupported invoice format: {value!r}")


def _sanitize_folder(value: Optional[str]) -> str:
    return (value or "").strip()


def _sanitize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _sanitize_optional_path(value: Optional[str]) -> str:
    return (value or "").strip()


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"", "0", "false", "no", "off"}:
        return False
    raise ValueError(f"Cannot interpret boolean value: {value!r}")


def _build_base_config(
    *,
    content_template: Optional[str],
    subject_template: Optional[str],
    body_template: Optional[str],
    sender_name_type: Optional[str],
    email_content_mode: Optional[str],
    attachment_folder: Optional[str],
    invoice_format: Optional[str],
    support_number: Optional[str],
    adapters: Optional[AutomaticModeAdapters],
) -> AutomaticConfig:
    adapters = adapters or AutomaticModeAdapters.default()
    content_value = adapters.normalize_template(content_template, "content")
    subject_value = adapters.normalize_template(
        subject_template if subject_template is not None else content_template,
        "subject",
    )
    body_value = adapters.normalize_template(
        body_template if body_template is not None else content_template,
        "body",
    )
    sender_value = adapters.normalize_sender_type(sender_name_type)
    mode_value = adapters.normalize_content_mode(email_content_mode)
    folder_value = adapters.sanitize_folder(attachment_folder)
    invoice_value = adapters.normalize_invoice_format(invoice_format)
    support_value = adapters.sanitize_support_number(support_number)
    return AutomaticConfig(
        content_template=content_value,
        subject_template=subject_value,
        body_template=body_value,
        sender_name_type=sender_value,
        email_content_mode=mode_value,
        attachment_folder=folder_value,
        invoice_format=invoice_value,
        support_number=support_value,
    )


def build_invoice_config(
    *,
    content_template: Optional[str],
    subject_template: Optional[str],
    body_template: Optional[str],
    sender_name_type: Optional[str],
    email_content_mode: Optional[str],
    attachment_folder: Optional[str],
    invoice_format: Optional[str],
    support_number: Optional[str],
    adapters: Optional[AutomaticModeAdapters] = None,
) -> AutomaticInvoiceConfig:
    config = _build_base_config(
        content_template=content_template,
        subject_template=subject_template,
        body_template=body_template,
        sender_name_type=sender_name_type,
        email_content_mode=email_content_mode,
        attachment_folder=attachment_folder,
        invoice_format=invoice_format,
        support_number=support_number,
        adapters=adapters,
    )
    if config.email_content_mode != "invoice":
        raise ValueError("Invoice mode requires email_content_mode to be 'invoice'.")
    return AutomaticInvoiceConfig(**config.__dict__)


def build_html_config(
    *,
    content_template: Optional[str],
    subject_template: Optional[str],
    body_template: Optional[str],
    sender_name_type: Optional[str],
    email_content_mode: Optional[str],
    attachment_folder: Optional[str],
    invoice_format: Optional[str],
    support_number: Optional[str],
    randomize_html: object,
    inline_png: object,
    html_upload_path: Optional[str],
    inline_html: Optional[str],
    tfn: Optional[str],
    adapters: Optional[AutomaticModeAdapters] = None,
) -> AutomaticHtmlConfig:
    config = _build_base_config(
        content_template=content_template,
        subject_template=subject_template,
        body_template=body_template,
        sender_name_type=sender_name_type,
        email_content_mode=email_content_mode,
        attachment_folder=attachment_folder,
        invoice_format=invoice_format,
        support_number=support_number,
        adapters=adapters,
    )
    if config.email_content_mode != "attachment":
        raise ValueError("HTML mode expects email_content_mode to be 'attachment'.")
    adapters = adapters or AutomaticModeAdapters.default()
    randomize_value = adapters.coerce_bool(randomize_html)
    inline_png_value = adapters.coerce_bool(inline_png)
    upload_path = adapters.sanitize_optional_path(html_upload_path)
    inline_html_value = adapters.sanitize_text(inline_html)
    tfn_value = adapters.sanitize_text(tfn)
    return AutomaticHtmlConfig(
        **config.__dict__,
        randomize_html=randomize_value,
        inline_png=inline_png_value,
        html_upload_path=upload_path,
        inline_html=inline_html_value,
        tfn=tfn_value,
    )


def build_demo(adapters: Optional[AutomaticModeAdapters] = None) -> gr.Blocks:
    """Construct Gradio layout for automatic email modes."""
    adapters = adapters or AutomaticModeAdapters.default()
    with gr.Blocks(title="Simple Gmail REST Mailer (Automatic Modes)") as demo:
        with gr.Group(elem_id="automatic-mode-root"):
            gr.Markdown("## Automatic Email Modes")
            mode_selector = gr.Radio(
                choices=["Invoice", "HTML"],
                value="Invoice",
                label="Mode Selection",
            )
            with gr.Tabs(elem_id="automatic-mode-tabs"):
                with gr.TabItem("Invoice", id="automatic-invoice-tab"):
                    with gr.Row():
                        with gr.Column(scale=2, elem_id="automatic-invoice-config"):
                            invoice_subject_template = gr.Radio(
                                choices=_TEMPLATE_DISPLAY_CHOICES,
                                value=_TEMPLATE_DISPLAY_CHOICES[0],
                                label="Subject Template",
                            )
                            invoice_body_template = gr.Radio(
                                choices=_TEMPLATE_DISPLAY_CHOICES,
                                value=_TEMPLATE_DISPLAY_CHOICES[0],
                                label="Body Template",
                            )
                            invoice_sender_type = gr.Radio(
                                choices=SENDER_NAME_TYPES,
                                value=DEFAULT_SENDER_NAME_TYPE,
                                label="Sender Name Style",
                            )
                            invoice_content_mode = gr.Radio(
                                choices=["Attachment", "Invoice"],
                                value="Invoice",
                                label="Email Content",
                            )
                            attachment_folder = gr.Textbox(
                                label="Attachment Folder",
                                placeholder="Optional path to attachments",
                            )
                            invoice_format = gr.Radio(
                                choices=sorted(_INVOICE_FORMATS),
                                value="pdf",
                                label="Invoice Format",
                            )
                            support_number = gr.Textbox(
                                label="Support Number",
                                placeholder="Optional",
                            )
                        with gr.Column(scale=1, elem_id="automatic-invoice-preview"):
                            with gr.Accordion("GMass Deliverability Preview", open=False):
                                gmass_status = gr.Textbox(
                                    label="GMass Status",
                                    interactive=False,
                                    lines=2,
                                )
                                gmass_urls = gr.Markdown(
                                    label="GMass Deliverability URLs",
                                )
                with gr.TabItem("HTML", id="automatic-html-tab"):
                    with gr.Row():
                        with gr.Column(scale=2, elem_id="automatic-html-config"):
                            html_subject_template = gr.Radio(
                                choices=_TEMPLATE_DISPLAY_CHOICES,
                                value=_TEMPLATE_DISPLAY_CHOICES[0],
                                label="HTML Subject Template",
                            )
                            html_body_template = gr.Radio(
                                choices=_TEMPLATE_DISPLAY_CHOICES,
                                value=_TEMPLATE_DISPLAY_CHOICES[0],
                                label="HTML Body Template",
                            )
                            html_sender_type = gr.Radio(
                                choices=SENDER_NAME_TYPES,
                                value=DEFAULT_SENDER_NAME_TYPE,
                                label="HTML Sender Name Style",
                            )
                            randomize_html = gr.Checkbox(
                                label="Randomize HTML Styling",
                                value=False,
                            )
                            inline_png = gr.Checkbox(
                                label="Attach Inline PNG",
                                value=False,
                            )
                            html_upload = gr.File(
                                label="HTML Upload",
                                file_types=[".html", ".htm"],
                            )
                            inline_html = gr.Textbox(
                                label="Inline HTML Override",
                                lines=6,
                                placeholder="Optional inline HTML",
                            )
                            tfn_number = gr.Textbox(
                                label="TFN Number",
                                placeholder="Optional",
                            )
                            attachment_conversion = gr.Radio(
                                choices=_ATTACHMENT_CONVERSION_CHOICES,
                                value=_ATTACHMENT_CONVERSION_CHOICES[-1],
                                label="Attachment Conversion",
                            )
                            document_format = gr.Radio(
                                choices=_DOCUMENT_FORMAT_CHOICES,
                                value=_DOCUMENT_FORMAT_CHOICES[0],
                                label="Document Format",
                                visible=False,
                            )
                            image_format = gr.Radio(
                                choices=_IMAGE_FORMAT_CHOICES,
                                value=_IMAGE_FORMAT_CHOICES[0],
                                label="Image Format",
                                visible=False,
                            )
                        with gr.Column(scale=1, elem_id="automatic-html-preview"):
                            gr.HTML(
                                label="HTML Preview",
                                value=_PREVIEW_PLACEHOLDER,
                            )
            gr.Button("Generate Preview", variant="secondary")
            gr.HTML(
                label="Preview Output",
                value=_PREVIEW_PLACEHOLDER,
            )
    # Variables kept to satisfy future wiring and make lint happy.
    _ = (
        adapters,
        mode_selector,
        invoice_subject_template,
        invoice_body_template,
        invoice_sender_type,
        invoice_content_mode,
        attachment_folder,
        invoice_format,
        support_number,
        gmass_status,
        gmass_urls,
        html_subject_template,
        html_body_template,
        html_sender_type,
        randomize_html,
        inline_png,
        html_upload,
        inline_html,
        tfn_number,
        attachment_conversion,
        document_format,
        image_format,
    )
    return demo


MODE_EMAIL_AUTOMATIC = modes.Mode(
    id='email_automatic',
    title='Email Automatic',
    build_ui=build_demo,
    to_runner_config=lambda payload, adapters=None: payload,
    run=lambda config, adapters=None: iter(()),
)

MODES = {
    'email_automatic': MODE_EMAIL_AUTOMATIC,
}

modes.register_mode(MODE_EMAIL_AUTOMATIC)

__all__ = [
    "AutomaticConfig",
    "AutomaticInvoiceConfig",
    "AutomaticHtmlConfig",
    "AutomaticModeAdapters",
    "build_invoice_config",
    "build_html_config",
    "build_demo",
    "MODES",
]
