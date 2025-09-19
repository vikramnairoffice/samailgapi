import os

import gradio as gr

from mailer import update_file_stats
from content import SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE
from ui_token_helpers import analyze_token_files, start_campaign, build_gmass_preview, gmass_rows_to_markdown, fetch_mailbox_counts


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


def _gmass_preview_update(mode_value, token_files, auth_mode):
    if (mode_value or '').lower() != 'gmass':
        return gr.update(visible=False), "", ""

    status, rows = build_gmass_preview(mode_value, token_files, auth_mode=auth_mode)
    markdown = gmass_rows_to_markdown(rows)
    return gr.update(visible=True), status, markdown


def gradio_ui():
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

                leads_per_account = gr.Number(
                    label='Leads per Account (Leads Mode)',
                    value=10,
                    precision=0
                )

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

                with gr.Group(visible=True) as gmass_preview_group:
                    gmass_status = gr.Textbox(
                        label='GMass Status',
                        interactive=False,
                        lines=2
                    )
                    gmass_urls_display = gr.Markdown(
                        label='GMass Deliverability URLs'
                    )
            with gr.Column():
                content_template_choice = gr.Radio(
                    ["own_proven", "Own_last", "R1_Tag"],
                    value="own_proven",
                    label="Content Template"
                )
                content_template_value = gr.State("own_proven")

                content_template_choice.change(
                    _map_content_template,
                    inputs=content_template_choice,
                    outputs=content_template_value
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

        mode.change(
            _gmass_preview_update,
            inputs=[mode, token_files, auth_mode],
            outputs=[gmass_preview_group, gmass_status, gmass_urls_display]
        )
        token_files.change(
            _gmass_preview_update,
            inputs=[mode, token_files, auth_mode],
            outputs=[gmass_preview_group, gmass_status, gmass_urls_display]
        )
        auth_mode.change(
            _gmass_preview_update,
            inputs=[mode, token_files, auth_mode],
            outputs=[gmass_preview_group, gmass_status, gmass_urls_display]
        )

        start_btn = gr.Button("Start Sending", variant="primary")

        log_box = gr.Textbox(label="Log", value="", interactive=False, lines=15)
        status_box = gr.Textbox(label="Status", value="Idle", interactive=False)
        summary_box = gr.Textbox(label="Summary", value="", interactive=False)

        start_btn.click(
            start_campaign,
            inputs=[
                token_files,
                leads_file,
                leads_per_account,
                send_delay_seconds,
                mode,
                email_content_mode,
                attachment_folder,
                invoice_format,
                support_number,
                advance_header,
                force_header,
                sender_name_type,
                content_template_value,
                auth_mode,
            ],
            outputs=[log_box, status_box, summary_box, gmass_status, gmass_urls_display]
        )

    return demo


def main():
    app = gradio_ui()
    app.launch()


if __name__ == "__main__":
    main()


