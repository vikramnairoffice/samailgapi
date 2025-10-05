import os
import html
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import gradio as gr

from mailer import update_file_stats
from content import SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE, get_tag_definitions
from ui_token_helpers import (
    analyze_token_files,
    start_campaign,
    start_manual_campaign,
    build_gmass_preview,
    gmass_rows_to_markdown,
    fetch_mailbox_counts,
    manual_random_sender_name,
    run_unified_campaign,
    run_multi_manual_campaign,
)


_MANUAL_DOC_OPTIONS = ["PDF", "Flat PDF", "Docx"]
_MANUAL_IMAGE_OPTIONS = ["PNG", "HEIF"]
_MANUAL_CATEGORY_OPTIONS = ["Doc", "Image", "Keep Original"]

def _extract_update_value(value):
    if isinstance(value, dict) and value.get('__type__') == 'update':
        return value.get('value')
    return value


def _normalize_manual_mode(label: str) -> str:
    if not label:
        return 'original'
    normalized = label.strip().lower().replace(' ', '_')
    if normalized == 'keep_original':
        return 'original'
    if normalized == 'doc':
        return 'docx'
    return normalized


def _manual_category_change(category, doc_choice, image_choice):
    choice = (category or '').strip().lower().replace(' ', '_')
    if choice == 'doc':
        value = doc_choice or _MANUAL_DOC_OPTIONS[0]
        return (
            gr.update(visible=True, value=value),
            gr.update(visible=False),
            _normalize_manual_mode(value),
        )
    if choice == 'image':
        value = image_choice or _MANUAL_IMAGE_OPTIONS[0]
        return (
            gr.update(visible=False),
            gr.update(visible=True, value=value),
            _normalize_manual_mode(value),
        )
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        'original',
    )


def _manual_format_choice(value):
    return _normalize_manual_mode(value)


def _looks_like_html(text: str) -> bool:
    if not text:
        return False
    snippet = text.strip()[:1024]
    lowered = snippet.lower()
    return lowered.startswith('<!doctype') or '<html' in lowered or '</' in snippet


def _manual_body_image_toggle(is_html, stored_value):
    stored = bool(stored_value)
    if bool(is_html):
        return gr.update(interactive=True, value=stored), stored
    return gr.update(interactive=False, value=False), stored


def _manual_body_image_store_state(current_value, is_html, stored_value):
    stored = bool(stored_value)
    if not bool(is_html):
        return stored
    if isinstance(current_value, dict) and current_value.get('__type__') == 'update':
        current_value = current_value.get('value')
    return bool(current_value)


def _leads_status(leads_file):
    return update_file_stats([], leads_file)[1]

def _describe_attachment_folder(path: str) -> str:
    if not path:
        return "No folder selected."

    folder = os.path.abspath(os.path.expanduser(path.strip()))
    if not os.path.exists(folder):
        return f"Folder not found: {folder}"
    if not os.path.isdir(folder):
        return f"Not a folder: {folder}"

    try:
        files = [entry.path for entry in os.scandir(folder) if entry.is_file()]
    except Exception as exc:
        return f"Folder error: {exc}"

    if not files:
        return f"No files in {folder}"

    return f"{len(files)} file(s) detected in {folder}"

def _map_content_template(choice: str) -> str:
    if choice == "Own_last":
        return "gmass_inboxed"
    if choice == "R1_Tag":
        return "r1_tag"
    return choice

def _map_subject_template(choice: str):
    mapped = _map_content_template(choice)
    return mapped, mapped

def _gmass_preview_update(mode_value, token_files, auth_mode):
    if (mode_value or '').lower() != 'gmass':
        return gr.update(visible=False), "", ""

    status, rows = build_gmass_preview(mode_value, token_files, auth_mode=auth_mode)
    markdown = gmass_rows_to_markdown(rows)
    return gr.update(visible=True), status, markdown

def _manual_toggle_attachments(enabled):
    visible = bool(enabled)
    interactive = visible
    return (
        gr.update(visible=visible, interactive=interactive),
        gr.update(visible=visible, interactive=interactive),
        gr.update(visible=visible, interactive=interactive),
        gr.update(visible=visible, interactive=interactive),
        gr.update(visible=visible, interactive=interactive),
        gr.update(visible=visible, interactive=interactive),
        gr.update(visible=visible, interactive=interactive),
    )





_PREVIEW_CHOICES = ['Body', 'Attachment']

def _preview_selection_change(selected_source):
    value = _extract_update_value(selected_source)
    clean = value if value in _PREVIEW_CHOICES else None
    button_enabled = bool(clean)
    radio_update = gr.update(choices=_PREVIEW_CHOICES, value=clean)
    button_update = gr.update(interactive=button_enabled)
    return radio_update, button_update


def _preview_message(text: str) -> str:
    return f'<div class="preview-empty">{html.escape(text)}</div>'


def _wrap_preview_block(title: str, inner_html: str) -> str:
    heading = html.escape(title)
    return f'<div class="preview-block"><h3>{heading}</h3><div class="preview-body">{inner_html}</div></div>'


def _render_body_fragment(manual_body: str, manual_body_is_html) -> str | None:
    if not manual_body or not manual_body.strip():
        return None
    if bool(manual_body_is_html) or _looks_like_html(manual_body):
        return _wrap_preview_block('Body Preview', manual_body)
    escaped = html.escape(manual_body)
    return _wrap_preview_block('Body Preview', f'<pre>{escaped}</pre>')


def _render_attachment_fragment(manual_inline_html: str) -> str | None:
    if not manual_inline_html or not manual_inline_html.strip():
        return None
    return _wrap_preview_block('Attachment Preview', manual_inline_html)


def _build_preview_document(content: str) -> str:
    template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Email Preview</title>
<style>
body {
    margin: 0;
    padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: #f9fafb;
    color: #1f2933;
}
.preview-container {
    max-width: 900px;
    margin: 0 auto;
}
.preview-block {
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1);
    padding: 24px;
}
.preview-block h3 {
    margin-top: 0;
}
.preview-body pre {
    white-space: pre-wrap;
    word-break: break-word;
}
</style>
</head>
<body>
<div class="preview-container">
{content}
</div>
</body>
</html>
"""
    return template.replace('{content}', content)


def _write_preview_document(fragment: str) -> Path:
    document = _build_preview_document(fragment)
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(document)
        return Path(temp_file.name)


def _manual_render_preview(
    preview_source,
    manual_body,
    manual_body_is_html,
    manual_inline_html,
):
    source = (_extract_update_value(preview_source) or '').strip()
    if source == 'Body':
        fragment = _render_body_fragment(manual_body, manual_body_is_html)
        empty_message = 'No Body HTML provided'
    elif source == 'Attachment':
        fragment = _render_attachment_fragment(manual_inline_html)
        empty_message = 'No Attachment HTML provided'
    else:
        return gr.update(value=_preview_message('Select Body or Attachment to preview.'), visible=True)

    if not fragment:
        return gr.update(value=_preview_message(empty_message), visible=True)

    notice_html = ''
    try:
        preview_path = _write_preview_document(fragment)
        webbrowser.open(preview_path.as_uri(), new=2)
        notice_html = _preview_message('Preview opened in a new browser tab. Allow pop-ups if nothing appeared.')
    except Exception as exc:
        notice_html = _preview_message(f'Could not open preview automatically: {exc}')

    return gr.update(value=f"{fragment}{notice_html}", visible=True)


@dataclass
class ManualFormControls:
    sender_type: object
    change_name: object
    sender_name: object
    pick_sender: object
    subject: object
    body_is_html: object
    randomize_html: object
    body_image_enabled: object
    body: object
    tfn: object
    extra_tags: object
    attachment_enabled: object
    attachment_category: object
    doc_format: object
    image_format: object
    attachment_mode: object
    attachment_files: object
    inline_html: object
    inline_name: object
    preview_mode: object
    preview_button: object
    preview_html: object


def _build_manual_form(prefix: str, tag_table_md: str, *, visible: bool = True):
    with gr.Tabs(visible=visible) as tabs:
        with gr.TabItem('Setup', id=f"{prefix}_setup"):
            sender_type = gr.Radio(
                SENDER_NAME_TYPES,
                value=DEFAULT_SENDER_NAME_TYPE,
                label='Sender Name Style'
            )
            change_name = gr.Checkbox(
                label='Change name every time',
                value=True
            )
            with gr.Row():
                sender_name = gr.Textbox(
                    label='Sender Name',
                    placeholder='Optional fixed sender name'
                )
                pick_sender = gr.Button(
                    'Pick Random',
                    variant='secondary'
                )
            subject = gr.Textbox(
                label='Subject',
                placeholder='Subject line'
            )
            body_is_html = gr.Checkbox(
                label='Body Content as HTML',
                value=False
            )
            randomize_html = gr.Checkbox(
                label='Randomize HTML styling',
                value=False,
                info='Apply subtle style tweaks to each send (HTML only).'
            )
            body_image_enabled = gr.Checkbox(
                label='Convert HTML body to inline PNG',
                value=False,
                info='Renders the body HTML into a PNG and embeds it as an inline image.',
                interactive=False
            )
            body = gr.Textbox(
                label='Body',
                placeholder='Paste email body (supports tags)',
                lines=12
            )
            tfn = gr.Textbox(
                label='TFN Number',
                placeholder='Optional'
            )
            extra_tags = gr.Dataframe(
                headers=['Tag', 'Value'],
                row_count=(1, 'dynamic'),
                datatype=['str', 'str'],
                type='array',
                label='Additional Tags'
            )
            attachment_enabled = gr.Checkbox(
                label='Include Attachment',
                value=False
            )
            with gr.Row():
                with gr.Column():
                    attachment_category = gr.Radio(
                        _MANUAL_CATEGORY_OPTIONS,
                        value=_MANUAL_CATEGORY_OPTIONS[0],
                        label='Attachment Conversion Type',
                        visible=False
                    )
                    doc_format = gr.Radio(
                        _MANUAL_DOC_OPTIONS,
                        value=_MANUAL_DOC_OPTIONS[0],
                        label='Document Formats',
                        visible=False
                    )
                    image_format = gr.Radio(
                        _MANUAL_IMAGE_OPTIONS,
                        value=_MANUAL_IMAGE_OPTIONS[0],
                        label='Image Formats',
                        visible=False
                    )
                with gr.Column():
                    attachment_mode = gr.Textbox(
                        value=_normalize_manual_mode(_MANUAL_DOC_OPTIONS[0]),
                        label='Resolved Attachment Mode',
                        visible=False,
                        interactive=False
                    )
                    inline_name = gr.Textbox(
                        label='Inline Attachment Name',
                        value='inline.html',
                        visible=False
                    )
                    inline_html = gr.Textbox(
                        label='Inline Attachment HTML',
                        placeholder='Paste HTML snippet to send as an attachment',
                        lines=8,
                        visible=False
                    )
                    attachment_files = gr.Files(
                        label='Attachment Files',
                        file_types=['.html', '.txt', '.pdf', '.docx', '.csv', '.md', '.json'],
                        file_count='multiple',
                        visible=False
                    )
            with gr.Accordion('Available Tags', open=False):
                gr.Markdown(tag_table_md)

        with gr.TabItem('Preview', id=f"{prefix}_preview"):
            with gr.Group():
                with gr.Row():
                    preview_mode = gr.Radio(
                        label='Preview Source',
                        choices=['Body', 'Attachment'],
                        value=None,
                        scale=8
                    )
                    preview_button = gr.Button(
                        'Preview',
                        variant='secondary',
                        interactive=False,
                        scale=1
                    )
                preview_html = gr.HTML(
                    label='Preview',
                    value=_preview_message('Preview opens in your browser. Select Body or Attachment, then click Preview.'),
                    visible=True
                )

    controls = ManualFormControls(
        sender_type=sender_type,
        change_name=change_name,
        sender_name=sender_name,
        pick_sender=pick_sender,
        subject=subject,
        body_is_html=body_is_html,
        randomize_html=randomize_html,
        body_image_enabled=body_image_enabled,
        body=body,
        tfn=tfn,
        extra_tags=extra_tags,
        attachment_enabled=attachment_enabled,
        attachment_category=attachment_category,
        doc_format=doc_format,
        image_format=image_format,
        attachment_mode=attachment_mode,
        attachment_files=attachment_files,
        inline_html=inline_html,
        inline_name=inline_name,
        preview_mode=preview_mode,
        preview_button=preview_button,
        preview_html=preview_html
    )
    return tabs, controls



def _manual_multi_default_config():
    return {
        'manual_subject': '',
        'manual_body': '',
        'manual_body_is_html': False,
        'manual_body_image_enabled': False,
        'manual_randomize_html': False,
        'manual_tfn': '',
        'manual_extra_tags': [],
        'manual_attachment_enabled': False,
        'manual_attachment_mode': 'original',
        'manual_attachment_files': [],
        'manual_inline_html': '',
        'manual_inline_name': 'inline.html',
        'manual_sender_name': '',
        'manual_change_name': True,
        'manual_sender_type': DEFAULT_SENDER_NAME_TYPE,
        'manual_category': 'Keep Original',
        'manual_doc_choice': _MANUAL_DOC_OPTIONS[0],
        'manual_image_choice': _MANUAL_IMAGE_OPTIONS[0],
    }


def _manual_multi_accounts_from_tokens(token_files):
    accounts = []
    for entry in token_files or []:
        name = getattr(entry, 'orig_name', None) or getattr(entry, 'name', '')
        if not name:
            continue
        base = os.path.splitext(os.path.basename(str(name)))[0]
        if not base or base in accounts:
            continue
        accounts.append(base)
    return accounts


def _manual_multi_get_config(state, account):
    base = _manual_multi_default_config()
    if not account:
        return base
    state = state or {}
    stored = state.get(account) or {}
    merged = base.copy()
    merged.update(stored)
    return merged


def _manual_multi_store_current(state, account, **kwargs):
    state = dict(state or {})
    if not account:
        return state
    config = _manual_multi_get_config(state, account)
    updated = config.copy()
    for key, value in kwargs.items():
        clean_value = _extract_update_value(value)
        if key == 'manual_attachment_files':
            updated[key] = list(clean_value or [])
        elif key == 'manual_extra_tags':
            updated[key] = clean_value or []
        else:
            updated[key] = clean_value
    state[account] = updated
    return state


def _manual_multi_prepare_accounts(token_files, state):
    accounts = _manual_multi_accounts_from_tokens(token_files)
    if not accounts:
        return gr.update(choices=[], value=None, visible=False), {}
    state = state or {}
    populated = {acc: _manual_multi_get_config(state, acc) for acc in accounts}
    return gr.update(choices=accounts, value=accounts[0], visible=True), populated


def _manual_multi_sync_accounts(token_files, state):
    dropdown_update, populated = _manual_multi_prepare_accounts(token_files, state)
    has_accounts = bool(populated)
    message_update = gr.update(visible=not has_accounts)
    tabs_update = gr.update(visible=has_accounts)
    return dropdown_update, populated, message_update, tabs_update


def _manual_multi_on_account_change(state, account):
    config = _manual_multi_get_config(state, account)
    attachment_enabled = bool(config.get('manual_attachment_enabled'))
    category = config.get('manual_category', 'Keep Original')
    doc_choice = config.get('manual_doc_choice', _MANUAL_DOC_OPTIONS[0])
    image_choice = config.get('manual_image_choice', _MANUAL_IMAGE_OPTIONS[0])
    body_image_enabled = bool(config.get('manual_body_image_enabled'))
    attachment_files = list(config.get('manual_attachment_files') or [])
    inline_html = config.get('manual_inline_html', '')
    inline_name = config.get('manual_inline_name', 'inline.html')

    updated_state = _manual_multi_store_current(state, account)

    doc_visible = attachment_enabled and category == 'Doc'
    image_visible = attachment_enabled and category == 'Image'

    return (
        gr.update(value=config.get('manual_subject', '')),
        gr.update(value=config.get('manual_body', '')),
        gr.update(value=bool(config.get('manual_body_is_html'))),
        gr.update(value=body_image_enabled),
        gr.update(value=bool(config.get('manual_randomize_html'))),
        gr.update(value=config.get('manual_tfn', '')),
        gr.update(value=config.get('manual_extra_tags') or []),
        gr.update(value=attachment_enabled),
        gr.update(value=category, visible=attachment_enabled),
        gr.update(value=doc_choice, visible=doc_visible),
        gr.update(value=image_choice, visible=image_visible),
        gr.update(value=config.get('manual_attachment_mode', 'original')),
        gr.update(value=attachment_files if attachment_enabled else None, visible=attachment_enabled),
        gr.update(value=inline_html, visible=attachment_enabled),
        gr.update(value=inline_name, visible=attachment_enabled),
        gr.update(choices=_PREVIEW_CHOICES, value=None),
        gr.update(interactive=False),
        gr.update(value=_preview_message('Preview opens in your browser. Select Body or Attachment, then click Preview.'), visible=True),
        gr.update(value=config.get('manual_sender_name', '')),
        gr.update(value=bool(config.get('manual_change_name', True))),
        gr.update(value=config.get('manual_sender_type', DEFAULT_SENDER_NAME_TYPE)),
        body_image_enabled,
        updated_state,
    )


def _manual_multi_capture_config(
    state,
    account,
    manual_subject,
    manual_body,
    manual_body_is_html,
    manual_body_image_enabled,
    manual_randomize_html,
    manual_tfn,
    manual_extra_tags,
    manual_attachment_enabled,
    manual_attachment_mode,
    manual_attachment_files,
    manual_inline_html,
    manual_inline_name,
    manual_sender_name,
    manual_change_name,
    manual_sender_type,
    manual_category,
    manual_doc_choice,
    manual_image_choice,
):
    return _manual_multi_store_current(
        state,
        account,
        manual_subject=manual_subject,
        manual_body=manual_body,
        manual_body_is_html=bool(manual_body_is_html),
        manual_body_image_enabled=bool(manual_body_image_enabled),
        manual_randomize_html=bool(manual_randomize_html),
        manual_tfn=manual_tfn,
        manual_extra_tags=manual_extra_tags,
        manual_attachment_enabled=bool(manual_attachment_enabled),
        manual_attachment_mode=manual_attachment_mode,
        manual_attachment_files=manual_attachment_files,
        manual_inline_html=manual_inline_html,
        manual_inline_name=manual_inline_name,
        manual_sender_name=manual_sender_name,
        manual_change_name=bool(manual_change_name),
        manual_sender_type=manual_sender_type,
        manual_category=manual_category,
        manual_doc_choice=manual_doc_choice,
        manual_image_choice=manual_image_choice,
    )


def gradio_ui():
    tag_lines = ['| Tag | Example | Description |', '| --- | --- | --- |']
    for tag_def in get_tag_definitions():
        tag_lines.append(f"| `{tag_def.name}` | {tag_def.example} | {tag_def.description} |")
    tag_table_md = '\n'.join(tag_lines)

    with gr.Blocks(title="Simple Gmail REST Mailer") as demo:
        gr.Markdown("# Simple Gmail REST Mailer")

        with gr.Tabs(elem_id='page-tabs') as page_tabs:
            with gr.TabItem('Setup', id='page_setup'):
                with gr.Row():
                    with gr.Column():
                        auth_mode = gr.Radio(
                            ['gmail_api', 'app_password'],
                            value='gmail_api',
                            label='Credential Mode',
                            info='gmail_api: upload OAuth tokens; app_password: upload TXT lines with email,password'
                        )
                        token_files = gr.Files(
                            label='Credential Files',
                            file_types=['.json', '.txt'],
                            file_count='multiple'
                        )
                        token_stats = gr.Textbox(
                            label='Credential Status',
                            value='Upload Gmail credentials to begin.',
                            interactive=False,
                            lines=3
                        )
                        token_files.change(
                            analyze_token_files,
                            inputs=[token_files, auth_mode],
                            outputs=token_stats,
                        )
                        auth_mode.change(
                            analyze_token_files,
                            inputs=[token_files, auth_mode],
                            outputs=token_stats,
                        )

                        check_mailboxes_btn = gr.Button(
                            'Check Inbox/Sent Counts',
                            variant='secondary'
                        )
                        mailbox_status = gr.Textbox(
                            label='Mailbox Status',
                            value='Click the button to preview inbox and sent totals.',
                            interactive=False,
                            lines=2
                        )
                        mailbox_preview = gr.Markdown(
                            label='Mailbox Counts'
                        )
                        check_mailboxes_btn.click(
                            fetch_mailbox_counts,
                            inputs=[token_files, auth_mode],
                            outputs=[mailbox_status, mailbox_preview]
                        )

                        leads_file = gr.File(label='Leads File (one email per line)')
                        leads_stats = gr.Textbox(
                            label='Leads Status',
                            value='Using default GMass seed list.',
                            interactive=False,
                            lines=2
                        )
                        leads_file.change(_leads_status, inputs=leads_file, outputs=leads_stats)

            with gr.TabItem('Sending Modes', id='page_modes'):
                send_delay_seconds = gr.Number(
                    label='Delay Between Emails (seconds)',
                    value=4.5,
                    precision=1
                )
                mode = gr.Radio(
                    ['gmass', 'leads'],
                    value='gmass',
                    label='Sending Mode'
                )

                active_ui_mode = gr.State('automatic')

                with gr.Tabs(elem_id='mode-tabs') as mode_tabs:
                    with gr.TabItem('Automatic', id='mode_automatic') as automatic_tab:
                        subject_template_choice = gr.Radio(
                            ["own_proven", "Own_last", "R1_Tag"],
                            value="own_proven",
                            label="Subject Template"
                        )
                        subject_template_value = gr.State("own_proven")
                        content_template_value = gr.State("own_proven")
                        subject_template_choice.change(
                            _map_subject_template,
                            inputs=subject_template_choice,
                            outputs=[subject_template_value, content_template_value]
                        )

                        body_template_choice = gr.Radio(
                            ["own_proven", "Own_last", "R1_Tag"],
                            value="own_proven",
                            label="Body Template"
                        )
                        body_template_value = gr.State("own_proven")
                        body_template_choice.change(
                            _map_content_template,
                            inputs=body_template_choice,
                            outputs=body_template_value
                        )

                        sender_name_type = gr.Radio(
                            SENDER_NAME_TYPES,
                            value=DEFAULT_SENDER_NAME_TYPE,
                            label="Sender Name Style"
                        )

                        email_content_mode = gr.Radio(
                            ["Attachment", "Invoice"],
                            value="Attachment",
                            label="Email Content"
                        )

                        with gr.Row():
                            attachment_folder = gr.Textbox(
                                label="Attachment Folder",
                                placeholder="Optional path to attachments"
                            )
                            invoice_format = gr.Radio(
                                ["pdf", "docx"],
                                value="pdf",
                                label="Invoice Format"
                            )

                        support_number = gr.Textbox(
                            label="Support Numbers (one per line)",
                            placeholder="Optional"
                        )

                        with gr.Accordion("GMass Deliverability Preview", open=False):
                            gmass_preview_group = gr.Group(visible=False)
                            with gmass_preview_group:
                                gmass_status = gr.Textbox(
                                    label='GMass Status',
                                    interactive=False,
                                    lines=2
                                )
                                gmass_urls_display = gr.Markdown(
                                    label='GMass Deliverability URLs'
                                )

                    with gr.TabItem('Manual', id='mode_manual') as manual_tab:
                        manual_tabs, manual_form = _build_manual_form('manual', tag_table_md)
                        manual_body_image_state = gr.State(False)

                advance_header = gr.Checkbox(
                    label="Advanced Header Pack",
                    value=False,
                    info="Adds X-Sender and Message-ID headers for testing"
                )

                force_header = gr.Checkbox(
                    label="Force Auth Headers",
                    value=False,
                    info="Forges SPF/DKIM/DMARC success markers for controlled tests"
                )

            with gr.TabItem('Multi Mode', id='page_multi') as multi_tab:
                multi_account_state = gr.State({})
                multi_body_image_state = gr.State(False)
                multi_notice = gr.Markdown(
                    "Upload credential files on the Setup page to manage individual account configurations.",
                    visible=True
                )
                multi_account_selector = gr.Dropdown(
                    label='Account',
                    choices=[],
                    value=None,
                    visible=False
                )
                multi_tabs, multi_form = _build_manual_form('multi', tag_table_md, visible=False)
                multi_start_btn = gr.Button("Start Multi Send", variant="primary")

        start_btn = gr.Button("Start Sending", variant="primary")

        run_output = gr.Textbox(
            label="Run Output",
            value="Status: Idle",
            interactive=False,
            lines=15,
        )

        automatic_tab.select(lambda: 'automatic', outputs=active_ui_mode)
        manual_tab.select(lambda: 'manual', outputs=active_ui_mode)
        multi_tab.select(lambda: 'multi', outputs=active_ui_mode)

        manual_form.pick_sender.click(
            manual_random_sender_name,
            inputs=manual_form.sender_type,
            outputs=manual_form.sender_name,
        )

        manual_form.body_is_html.change(
            _manual_body_image_toggle,
            inputs=[manual_form.body_is_html, manual_body_image_state],
            outputs=[manual_form.body_image_enabled, manual_body_image_state],
        )

        manual_form.body_image_enabled.change(
            _manual_body_image_store_state,
            inputs=[manual_form.body_image_enabled, manual_form.body_is_html, manual_body_image_state],
            outputs=manual_body_image_state,
        )

        manual_form.attachment_enabled.change(
            _manual_toggle_attachments,
            inputs=manual_form.attachment_enabled,
            outputs=[
                manual_form.attachment_files,
                manual_form.attachment_category,
                manual_form.doc_format,
                manual_form.image_format,
                manual_form.attachment_mode,
                manual_form.inline_name,
                manual_form.inline_html,
            ],
        )

        manual_form.attachment_category.change(
            _manual_category_change,
            inputs=[manual_form.attachment_category, manual_form.doc_format, manual_form.image_format],
            outputs=[manual_form.doc_format, manual_form.image_format, manual_form.attachment_mode],
        )

        manual_form.doc_format.change(
            _manual_format_choice,
            inputs=manual_form.doc_format,
            outputs=manual_form.attachment_mode,
        )

        manual_form.image_format.change(
            _manual_format_choice,
            inputs=manual_form.image_format,
            outputs=manual_form.attachment_mode,
        )


        manual_form.preview_mode.change(
            _preview_selection_change,
            inputs=manual_form.preview_mode,
            outputs=[manual_form.preview_mode, manual_form.preview_button],
        )

        manual_form.preview_button.click(
            _manual_render_preview,
            inputs=[
                manual_form.preview_mode,
                manual_form.body,
                manual_form.body_is_html,
                manual_form.inline_html,
            ],
            outputs=manual_form.preview_html,
        )

        token_files.change(
            _gmass_preview_update,
            inputs=[mode, token_files, auth_mode],
            outputs=[gmass_preview_group, gmass_status, gmass_urls_display],
        )
        auth_mode.change(
            _gmass_preview_update,
            inputs=[mode, token_files, auth_mode],
            outputs=[gmass_preview_group, gmass_status, gmass_urls_display],
        )
        mode.change(
            _gmass_preview_update,
            inputs=[mode, token_files, auth_mode],
            outputs=[gmass_preview_group, gmass_status, gmass_urls_display],
        )

        multi_form.pick_sender.click(
            manual_random_sender_name,
            inputs=multi_form.sender_type,
            outputs=multi_form.sender_name,
        )

        multi_form.body_is_html.change(
            _manual_body_image_toggle,
            inputs=[multi_form.body_is_html, multi_body_image_state],
            outputs=[multi_form.body_image_enabled, multi_body_image_state],
        )

        multi_form.body_image_enabled.change(
            _manual_body_image_store_state,
            inputs=[multi_form.body_image_enabled, multi_form.body_is_html, multi_body_image_state],
            outputs=multi_body_image_state,
        )

        multi_form.attachment_enabled.change(
            _manual_toggle_attachments,
            inputs=multi_form.attachment_enabled,
            outputs=[
                multi_form.attachment_files,
                multi_form.attachment_category,
                multi_form.doc_format,
                multi_form.image_format,
                multi_form.attachment_mode,
                multi_form.inline_name,
                multi_form.inline_html,
            ],
        )

        multi_form.attachment_category.change(
            _manual_category_change,
            inputs=[multi_form.attachment_category, multi_form.doc_format, multi_form.image_format],
            outputs=[multi_form.doc_format, multi_form.image_format, multi_form.attachment_mode],
        )

        multi_form.doc_format.change(
            _manual_format_choice,
            inputs=multi_form.doc_format,
            outputs=multi_form.attachment_mode,
        )

        multi_form.image_format.change(
            _manual_format_choice,
            inputs=multi_form.image_format,
            outputs=multi_form.attachment_mode,
        )


        multi_form.preview_mode.change(
            _preview_selection_change,
            inputs=multi_form.preview_mode,
            outputs=[multi_form.preview_mode, multi_form.preview_button],
        )

        multi_form.preview_button.click(
            _manual_render_preview,
            inputs=[
                multi_form.preview_mode,
                multi_form.body,
                multi_form.body_is_html,
                multi_form.inline_html,
            ],
            outputs=multi_form.preview_html,
        )

        multi_account_selector.change(
            _manual_multi_on_account_change,
            inputs=[multi_account_state, multi_account_selector],
            outputs=[
                multi_form.subject,
                multi_form.body,
                multi_form.body_is_html,
                multi_form.body_image_enabled,
                multi_form.randomize_html,
                multi_form.tfn,
                multi_form.extra_tags,
                multi_form.attachment_enabled,
                multi_form.attachment_category,
                multi_form.doc_format,
                multi_form.image_format,
                multi_form.attachment_mode,
                multi_form.attachment_files,
                multi_form.inline_html,
                multi_form.inline_name,
                multi_form.preview_mode,
                multi_form.preview_button,
                multi_form.preview_html,
                multi_form.sender_name,
                multi_form.change_name,
                multi_form.sender_type,
                multi_body_image_state,
                multi_account_state,
            ],
        )

        token_files.change(
            _manual_multi_sync_accounts,
            inputs=[token_files, multi_account_state],
            outputs=[multi_account_selector, multi_account_state, multi_notice, multi_tabs],
        )

        multi_capture_inputs = [
            multi_account_state,
            multi_account_selector,
            multi_form.subject,
            multi_form.body,
            multi_form.body_is_html,
            multi_form.body_image_enabled,
            multi_form.randomize_html,
            multi_form.tfn,
            multi_form.extra_tags,
            multi_form.attachment_enabled,
            multi_form.attachment_mode,
            multi_form.attachment_files,
            multi_form.inline_html,
            multi_form.inline_name,
            multi_form.sender_name,
            multi_form.change_name,
            multi_form.sender_type,
            multi_form.attachment_category,
            multi_form.doc_format,
            multi_form.image_format,
        ]

        for trigger in (
            multi_form.subject,
            multi_form.body,
            multi_form.body_is_html,
            multi_form.body_image_enabled,
            multi_form.randomize_html,
            multi_form.tfn,
            multi_form.extra_tags,
            multi_form.attachment_enabled,
            multi_form.attachment_mode,
            multi_form.attachment_files,
            multi_form.inline_html,
            multi_form.inline_name,
            multi_form.sender_name,
            multi_form.change_name,
            multi_form.sender_type,
            multi_form.attachment_category,
            multi_form.doc_format,
            multi_form.image_format,
        ):
            trigger.change(
                _manual_multi_capture_config,
                inputs=multi_capture_inputs,
                outputs=[multi_account_state],
            )

        start_btn.click(
            run_unified_campaign,
            inputs=[
                active_ui_mode,
                token_files,
                leads_file,
                send_delay_seconds,
                mode,
                email_content_mode,
                attachment_folder,
                invoice_format,
                support_number,
                manual_form.subject,
                manual_form.body,
                manual_form.body_is_html,
                manual_form.body_image_enabled,
                manual_body_image_state,
                manual_form.randomize_html,
                manual_form.tfn,
                manual_form.extra_tags,
                manual_form.attachment_enabled,
                manual_form.attachment_mode,
                manual_form.attachment_files,
                manual_form.inline_html,
                manual_form.inline_name,
                manual_form.sender_name,
                manual_form.change_name,
                manual_form.sender_type,
                advance_header,
                force_header,
                auth_mode,
                sender_name_type,
                content_template_value,
                subject_template_value,
                body_template_value,
            ],
            outputs=[run_output, gmass_status, gmass_urls_display]
        )

        multi_start_btn.click(
            run_multi_manual_campaign,
            inputs=[
                multi_account_state,
                token_files,
                leads_file,
                send_delay_seconds,
                mode,
                auth_mode,
                advance_header,
                force_header,
            ],
            outputs=[run_output, gmass_status, gmass_urls_display]
        )

    return demo

def main():
    app = gradio_ui()
    app.launch()

if __name__ == "__main__":
    main()
