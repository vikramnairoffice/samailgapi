# Architecture

## Overview
This project is a web-based, single-user email sending application designed for dispatching personalized emails via the Gmail REST API. It features a Gradio UI for easy configuration, dynamic content generation, and on-the-fly invoice creation.

## Components

- **`ui.py` (Gradio Web Interface):** The application's main entry point. It provides a simple web UI for:
    - Uploading Gmail API token files and lead lists.
    - Configuring sending parameters like mode (GMass/Leads), content templates, and attachment types.
    - Starting the email campaign.
    - Monitoring live progress and viewing logs and a final summary.

- **`mailer.py` (Core Orchestrator):** The backend engine that manages the email sending workflow. Its responsibilities include:
    - **Authentication**: Loading and validating Gmail API tokens from user-uploaded files.
    - **Lead Management**: Reading leads from a file or using a default list for GMass-style sending.
    - **Workflow Management**: Orchestrating the campaign by iterating through accounts and leads sequentially.
    - **Sending**: Using the Gmail REST API to send emails. It constructs the full message, including headers, body, and attachments.
    - **Event Generation**: Yielding events (progress, errors, completion) back to the UI layer.

- **`ui_token_helpers.py` (UI-Backend Connector):** A helper module that sits between the Gradio UI and the mailer engine. 
    - It receives UI events (like button clicks) and calls the appropriate functions in `mailer.py`.
    - It formats the events yielded by the mailer into user-friendly strings for display in the UI's log and status boxes.

- **`content.py` (Content Generation):** Responsible for creating dynamic email content.
    - It uses a template-based system to generate unique subjects and bodies for each email, helping to improve deliverability.
    - It also includes logic for generating dynamic sender names.

- **`invoice.py` (Attachment Generator):** Generates personalized attachments.
    - It can create styled invoices in PDF, PNG, or HEIC format.
    - It personalizes invoices with recipient-specific data and can include a random logo and user-provided support numbers.

## Data Flow

1.  **Configuration (UI):** The user interacts with the Gradio UI in `ui.py`, uploading token files and a leads list, and setting various sending options.
2.  **Initiation (`ui.py` -> `ui_token_helpers.py`):** Clicking the "Start Sending" button triggers the `start_campaign` function in `ui_token_helpers.py`.
3.  **Campaign Orchestration (`ui_token_helpers.py` -> `mailer.py`):** 
    - `start_campaign` calls the `campaign_events` generator in `mailer.py`, passing along all the configuration from the UI.
4.  **Execution (`mailer.py`):**
    - `campaign_events` first validates the uploaded Gmail tokens.
    - It prepares the lead assignments for each account based on the selected mode.
    - It then calls `run_campaign`, which begins the sequential process of sending emails.
    - For each email, it calls `compose_email` (using `content.py`) and `build_attachments` (using `invoice.py` or selecting a static file).
    - It sends the final message using `send_gmail_message`.
5.  **Feedback (mailer.py -> ui_token_helpers.py -> UI):**
    - Throughout the process, `run_campaign` yields dictionary events (e.g., `{'kind': 'progress', ...}`).
    - `start_campaign` in `ui_token_helpers.py` catches these events, formats them into human-readable strings, and yields them to the Gradio UI.
    - The UI automatically updates the log, status, and summary text boxes with the new information.

## Design Principles

- **Simplicity**: The architecture avoids complexity like multi-threading or persistent connections, opting for a straightforward, sequential sending process that is easy to debug and manage.
- **Separation of Concerns**: Each module has a clear and distinct responsibility (UI, core logic, content generation, UI-to-backend communication).
- **Web-based Interface**: Gradio provides an accessible and cross-platform UI without the need for a complex frontend setup.
- **Gmail REST API Focus**: The application is built exclusively for the Gmail API, simplifying the sending logic and avoiding the complexities of SMTP.