import os

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
    manual_attachment_listing,
    manual_attachment_preview_content,
    manual_random_sender_name,
    manual_preview_snapshot,
    run_unified_campaign,
)


_MANUAL_DOC_OPTIONS = ["PDF", "Flat PDF", "Docx"]
_MANUAL_IMAGE_OPTIONS = ["PNG", "HEIF"]
_MANUAL_CATEGORY_OPTIONS = ["Doc", "Image", "Keep Original"]


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


def _manual_body_image_toggle(is_html):
    enabled = bool(is_html)
    if enabled:
        return gr.update(interactive=True)
    return gr.update(value=False, interactive=False)


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
    if not visible:
        return (
            gr.update(visible=False, value=None),
            gr.update(visible=False, value=_MANUAL_CATEGORY_OPTIONS[0]),
            gr.update(visible=False, value=_MANUAL_DOC_OPTIONS[0]),
            gr.update(visible=False, value=_MANUAL_IMAGE_OPTIONS[0]),
            gr.update(value='original'),
            gr.update(visible=False, choices=[], value=None),
            gr.update(visible=False, value=''),
            gr.update(visible=False, value=""),
        )
    return (
        gr.update(visible=True, value=None),
        gr.update(visible=True, value=_MANUAL_CATEGORY_OPTIONS[0]),
        gr.update(visible=True, value=_MANUAL_DOC_OPTIONS[0]),
        gr.update(visible=False, value=_MANUAL_IMAGE_OPTIONS[0]),
        gr.update(value=_normalize_manual_mode(_MANUAL_DOC_OPTIONS[0])),
        gr.update(visible=False, choices=[], value=None),
        gr.update(visible=True, value='inline.html'),
        gr.update(visible=True, value=""),
    )


def _manual_refresh_attachments(files, inline_html, inline_name):
    names, default, *_ = manual_attachment_listing(files, inline_html, inline_name)
    has_files = bool(names)
    dropdown_update = gr.update(
        visible=has_files,
        choices=names,
        value=default if has_files else None,
    )
    return (dropdown_update,)

def _manual_update_preview(
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
    selected_attachment,
    current_mode,
):
    choices, default, html_map = manual_preview_snapshot(
        manual_body=manual_body,
        manual_body_is_html=manual_body_is_html,
        manual_body_image_enabled=manual_body_image_enabled,
        manual_randomize_html=manual_randomize_html,
        manual_tfn=manual_tfn,
        manual_extra_tags=manual_extra_tags,
        manual_attachment_enabled=manual_attachment_enabled,
        manual_attachment_mode=manual_attachment_mode,
        manual_attachment_files=manual_attachment_files,
        manual_inline_html=manual_inline_html,
        manual_inline_name=manual_inline_name,
        selected_attachment_name=selected_attachment,
    )

    if choices:
        selected_mode = current_mode if current_mode in choices else (default or choices[0])
        preview_html = html_map.get(selected_mode, '')
        mode_update = gr.update(choices=choices, value=selected_mode, visible=True)
        refresh_update = gr.update(visible=True)
        html_update = gr.update(value=preview_html, visible=bool(preview_html))
    else:
        mode_update = gr.update(choices=[], value=None, visible=False)
        refresh_update = gr.update(visible=False)
        html_update = gr.update(value='', visible=False)
        html_map = {}

    return mode_update, refresh_update, html_update, html_map


def _manual_switch_preview(selected_mode, cached_map):
    data = cached_map or {}
    html_value = data.get(selected_mode or '', '')
    return gr.update(value=html_value, visible=bool(html_value))


def gradio_ui():
    tag_lines = ['| Tag | Example | Description |', '| --- | --- | --- |']
    for tag_def in get_tag_definitions():
        tag_lines.append(f"| `{tag_def.name}` | {tag_def.example} | {tag_def.description} |")
    tag_table_md = '\n'.join(tag_lines)

    with gr.Blocks(title="Simple Gmail REST Mailer") as demo:
        gr.Markdown("# Simple Gmail REST Mailer")

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
                token_files.change(analyze_token_files, inputs=[token_files, auth_mode], outputs=token_stats)
                auth_mode.change(analyze_token_files, inputs=[token_files, auth_mode], outputs=token_stats)

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

            with gr.Column():
                active_ui_mode = gr.State('automated')
                with gr.Tabs() as ui_mode_tabs:
                    with gr.TabItem('Automated Mode', id='automated') as automated_tab:
                        with gr.Tabs() as automated_mode_tabs:
                            with gr.TabItem('Setup', id='automated_setup'):
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

                                attachment_folder = gr.Textbox(
                                    label="Attachment Folder Path",
                                    placeholder="Paste Drive folder path (e.g. /content/drive/MyDrive/attachments)",
                                    lines=1
                                )
                                attachment_status = gr.Textbox(
                                    label="Attachment Folder Status",
                                    value=_describe_attachment_folder(""),
                                    interactive=False,
                                    lines=2
                                )
                                attachment_folder.change(
                                    _describe_attachment_folder,
                                    inputs=attachment_folder,
                                    outputs=attachment_status
                                )

                                invoice_format = gr.Radio(
                                    ["pdf", "image", "heif"],
                                    value="pdf",
                                    label="Invoice Format"
                                )

                                support_number = gr.Textbox(
                                    label="Support Numbers (one per line)",
                                    placeholder="Optional"
                                )

                            

                            with gr.TabItem('Preview', id='automated_preview'):
                                with gr.Group(visible=True) as gmass_preview_group:
                                    gmass_status = gr.Textbox(
                                        label='GMass Status',
                                        interactive=False,
                                        lines=2
                                    )
                                    gmass_urls_display = gr.Markdown(
                                        label='GMass Deliverability URLs'
                                    )
                    with gr.TabItem('Manual Mode', id='manual') as manual_tab:
                        with gr.Tabs() as manual_mode_tabs:
                            with gr.TabItem('Setup', id='manual_setup'):
                                manual_sender_type = gr.Radio(
                                    SENDER_NAME_TYPES,
                                    value=DEFAULT_SENDER_NAME_TYPE,
                                    label="Sender Name Style"
                                )
                                manual_change_name = gr.Checkbox(
                                    label="Change name every time",
                                    value=True
                                )
                                with gr.Row():
                                    manual_sender_name = gr.Textbox(
                                        label="Sender Name",
                                        placeholder="Optional fixed sender name"
                                    )
                                    manual_pick_sender = gr.Button(
                                        'Pick Random',
                                        variant='secondary'
                                    )
                                manual_subject = gr.Textbox(
                                    label="Subject",
                                    placeholder="Subject line"
                                )
                                manual_body_is_html = gr.Checkbox(
                                    label="Body Content as HTML",
                                    value=False
                                )
                                manual_randomize_html = gr.Checkbox(
                                    label="Randomize HTML styling",
                                    value=False,
                                    info="Apply subtle style tweaks to each send (HTML only)."
                                )
                                manual_body_image_enabled = gr.Checkbox(
                                    label="Convert HTML body to inline PNG",
                                    value=False,
                                    info="Renders the body HTML into a PNG and embeds it as an inline image.",
                                    interactive=False
                                )
                                manual_body = gr.Textbox(
                                    label="Body",
                                    placeholder="Paste email body (supports tags)",
                                    lines=12
                                )
                                manual_tfn = gr.Textbox(
                                    label="TFN Number",
                                    placeholder="Optional"
                                )
                                manual_extra_tags = gr.Dataframe(
                                    headers=["Tag", "Value"],
                                    row_count=(1, "dynamic"),
                                    datatype=["str", "str"],
                                    type='array',
                                    label="Additional Tags"
                                )

                                manual_attachment_enabled = gr.Checkbox(
                                    label="Include Attachment",
                                    value=False
                                )


                                with gr.Row():
                                    with gr.Column():
                                        manual_attachment_category = gr.Radio(
                                            _MANUAL_CATEGORY_OPTIONS,
                                            value=_MANUAL_CATEGORY_OPTIONS[0],
                                            label="Attachment Conversion Type",
                                            visible=False
                                        )
                                        manual_doc_format = gr.Radio(
                                            _MANUAL_DOC_OPTIONS,
                                            value=_MANUAL_DOC_OPTIONS[0],
                                            label="Document Formats",
                                            visible=False
                                        )
                                        manual_image_format = gr.Radio(
                                            _MANUAL_IMAGE_OPTIONS,
                                            value=_MANUAL_IMAGE_OPTIONS[0],
                                            label="Image Formats",
                                            visible=False
                                        )
                                    with gr.Column():
                                        manual_attachment_mode = gr.Textbox(
                                            value=_normalize_manual_mode(_MANUAL_DOC_OPTIONS[0]),
                                            label="Resolved Attachment Mode",
                                            visible=False,
                                            interactive=False
                                        )
                                        manual_inline_name = gr.Textbox(
                                            label="Inline Attachment Name",
                                            value="inline.html",
                                            visible=False
                                        )
                                        manual_inline_html = gr.Textbox(
                                            label="Inline Attachment HTML",
                                            placeholder="Paste HTML snippet to send as an attachment",
                                            lines=8,
                                            visible=False
                                        )
                                        manual_attachment_files = gr.Files(
                                            label="Attachment Files",
                                            file_types=['.html', '.txt', '.pdf', '.docx', '.csv', '.md', '.json'],
                                            file_count='multiple',
                                            visible=False
                                        )
                                        manual_attachment_dropdown = gr.Dropdown(
                                            label="Preview Attachment",
                                            choices=[],
                                            value=None,
                                            visible=False
                                        )
                                with gr.Accordion("Available Tags", open=False):
                                    gr.Markdown(tag_table_md)


                            with gr.TabItem('Preview', id='manual_preview'):
                                with gr.Group():
                                    with gr.Row():
                                        manual_preview_mode = gr.Radio(
                                            label="Preview Source",
                                            choices=[],
                                            value=None,
                                            visible=False,
                                            scale=8,
                                        )
                                        manual_preview_refresh = gr.Button(
                                            "Refresh Preview",
                                            variant="secondary",
                                            visible=False,
                                            scale=1,
                                        )
                                    manual_preview_html = gr.HTML(
                                        label="Preview",
                                        value="",
                                        visible=False,
                                    )

                                manual_preview_data = gr.State({})
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

        automated_tab.select(lambda: 'automated', outputs=active_ui_mode)
        manual_tab.select(lambda: 'manual', outputs=active_ui_mode)

        manual_pick_sender.click(
            manual_random_sender_name,
            inputs=manual_sender_type,
            outputs=manual_sender_name,
        )

        manual_body_is_html.change(
            _manual_body_image_toggle,
            inputs=manual_body_is_html,
            outputs=manual_body_image_enabled,
        )

        manual_attachment_enabled.change(
            _manual_toggle_attachments,
            inputs=manual_attachment_enabled,
            outputs=[
                manual_attachment_files,
                manual_attachment_category,
                manual_doc_format,
                manual_image_format,
                manual_attachment_mode,
                manual_attachment_dropdown,
                manual_inline_name,
                manual_inline_html,
            ],
        )

        manual_attachment_category.change(
            _manual_category_change,
            inputs=[manual_attachment_category, manual_doc_format, manual_image_format],
            outputs=[manual_doc_format, manual_image_format, manual_attachment_mode],
        )

        manual_doc_format.change(
            _manual_format_choice,
            inputs=manual_doc_format,
            outputs=manual_attachment_mode,
        )

        manual_image_format.change(
            _manual_format_choice,
            inputs=manual_image_format,
            outputs=manual_attachment_mode,
        )

        for trigger in (manual_attachment_files, manual_inline_html, manual_inline_name):
            trigger.change(
                _manual_refresh_attachments,
                inputs=[manual_attachment_files, manual_inline_html, manual_inline_name],
                outputs=[manual_attachment_dropdown],
            )

        preview_inputs = [
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
            manual_attachment_dropdown,
            manual_preview_mode,
        ]
        preview_outputs = [
            manual_preview_mode,
            manual_preview_refresh,
            manual_preview_html,
            manual_preview_data,
        ]

        for trigger in (
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
            manual_attachment_dropdown,
        ):
            trigger.change(
                _manual_update_preview,
                inputs=preview_inputs,
                outputs=preview_outputs,
            )

        manual_preview_refresh.click(
            _manual_update_preview,
            inputs=preview_inputs,
            outputs=preview_outputs,
        )

        manual_preview_mode.change(
            _manual_switch_preview,
            inputs=[manual_preview_mode, manual_preview_data],
            outputs=manual_preview_html,
        )

        for trigger in (mode, token_files, auth_mode):
            trigger.change(
                _gmass_preview_update,
                inputs=[mode, token_files, auth_mode],
                outputs=[gmass_preview_group, gmass_status, gmass_urls_display],
            )

        start_btn = gr.Button("Start Sending", variant="primary")

        run_output = gr.Textbox(
            label="Run Output",
            value="Status: Idle",
            interactive=False,
            lines=15,
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

    return demo

def main():
    app = gradio_ui()
    app.launch()

if __name__ == "__main__":
    main()











