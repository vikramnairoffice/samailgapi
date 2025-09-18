# Project Features

## Core Capabilities
- **Authentication**: Gmail API via direct upload of token JSON files.
- **Sending Modes**: 
    - **GMass-style**: Sends emails to a default seed list of recipients from each authenticated account.
    - **Leads Mode**: Distributes a list of leads from a file among the authenticated accounts.
- **Content Generation**: Dynamic generation of subject lines and email bodies using multiple templates (`own_proven`, `gmass_inboxed`).
- **Dynamic Sender Names**: Generates sender names in "business" or "personal" style.
- **Attachments**: 
    - **Static**: Randomly attaches a PDF or image from local `./pdfs` or `./images` directories.
    - **Personalized Invoices**: Generates personalized invoices on-the-fly in PDF, PNG, or HEIF format.
- **Gmail API Integration**: 
    - Loads and validates Gmail token files.
    - Refreshes expired tokens automatically.
    - Sends emails using the Gmail REST API.
- **Progress & Error Reporting**: Live updates in the UI with logs, status, and a final summary.
- **Gradio UI**: A simple, one-page web interface for configuration, file uploads, and monitoring the sending process.

## Authentication Details
- **Gmail API Token Upload**:
  - Users can upload one or more `token.json` files.
  - The system validates each token, extracts the associated email address using the Gmail API, and handles token refreshing.

## Sending Flow
- The UI triggers the campaign, passing the configuration to the backend.
- The backend validates tokens and prepares the lead assignments based on the selected mode (GMass or Leads).
- It iterates through each account and its assigned leads, sending emails sequentially.
- For each email, it generates content, sender name, and attachments (static or invoice).
- It uses the Gmail REST API to send the composed message.
- Progress, successes, and failures are yielded back to the UI in real-time.

## Attachments & Invoices
- **Static Attachments**: Randomly selects one PDF from `./pdfs` or one image from `./images` if the "Attachment" mode is selected.
- **Invoice Generation**: 
  - If "Invoice" mode is selected, it generates a personalized invoice for each recipient.
  - Invoices are highly customizable, including a random logo from the `./logos` directory, company details, and recipient-specific information.
  - Supports output in PDF, PNG, or HEIF formats.
  - Can include support phone numbers provided by the user.

## UI Features
- **Token Upload**: A file uploader for multiple Gmail `token.json` files.
- **Leads Upload**: An optional file uploader for a list of leads.
- **Configuration**: Radio buttons and text inputs to configure:
    - Sending Mode (gmass/leads)
    - Content Template
    - Sender Name Style
    - Email Content (Attachment/Invoice)
    - Attachment/Invoice Format
    - Support Numbers for invoices
- **Live Feedback**: Text boxes for live logs, status updates, and a final summary of the campaign.

## Environment & Setup
- **Colab Setup Script (`colab_setup.py`)**: Automates the installation of dependencies and creation of necessary directories (`pdfs/`, `images/`, `logos/`, `gmail_tokens/`).
- **Packaging (`setup.py`)**: Defines project dependencies and provides a console script entry point (`simple-mailer=ui:main`) for easy execution.
