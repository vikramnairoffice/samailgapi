import gradio as gr

from mailer import update_attachment_stats, update_file_stats
from content import SENDER_NAME_TYPES, DEFAULT_SENDER_NAME_TYPE
from ui_token_helpers import analyze_token_files, start_campaign


def _leads_status(leads_file):
    return update_file_stats([], leads_file)[1]


def _refresh_attachment_stats(choice):
    include_pdfs = choice == 'pdf'
    include_images = choice == 'image'
    return update_attachment_stats(include_pdfs, include_images)


def gradio_ui():
    with gr.Blocks(title="Simple Gmail REST Mailer") as demo:
        gr.Markdown("# Simple Gmail REST Mailer")

        with gr.Row():
            with gr.Column():
                token_files = gr.Files(
                    label="Gmail Token JSON Files",
                    file_types=[".json"],
                    file_count="multiple"
                )
                token_stats = gr.Textbox(
                    label="Token Status",
                    value="Upload Gmail token JSON files to begin.",
                    interactive=False,
                    lines=3
                )
                token_files.change(analyze_token_files, inputs=token_files, outputs=token_stats)

                leads_file = gr.File(label="Leads File (one email per line)")
                leads_stats = gr.Textbox(
                    label="Leads Status",
                    value="Using default GMass seed list.",
                    interactive=False,
                    lines=2
                )
                leads_file.change(_leads_status, inputs=leads_file, outputs=leads_stats)

                leads_per_account = gr.Number(
                    label="Leads per Account (Leads Mode)",
                    value=10,
                    precision=0
                )

                mode = gr.Radio(
                    ["gmass", "leads"],
                    value="gmass",
                    label="Sending Mode"
                )

            with gr.Column():
                content_template = gr.Radio(
                    ["own_proven", "gmass_inboxed"],
                    value="own_proven",
                    label="Content Template"
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

                attachment_format = gr.Radio(
                    ["pdf", "image"],
                    value="pdf",
                    label="Attachment Format"
                )
                invoice_format = gr.Radio(
                    ["pdf", "image", "heic"],
                    value="pdf",
                    label="Invoice Format"
                )

                attachment_stats = gr.Textbox(
                    label="Attachment Stats",
                    value=_refresh_attachment_stats("pdf"),
                    interactive=False,
                    lines=2
                )
                attachment_format.change(
                    _refresh_attachment_stats,
                    inputs=attachment_format,
                    outputs=attachment_stats
                )

                support_number = gr.Textbox(
                    label="Support Numbers (one per line)",
                    placeholder="Optional"
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
                mode,
                email_content_mode,
                attachment_format,
                invoice_format,
                support_number,
                sender_name_type,
                content_template,
            ],
            outputs=[log_box, status_box, summary_box]
        )

    return demo


def main():
    app = gradio_ui()
    app.launch()


if __name__ == "__main__":
    main()

