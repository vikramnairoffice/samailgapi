# Functions and Classes Reference

This document enumerates all public and helper functions/classes by module.

## `content.py`
- **`generate_business_name()`**: Generates a business-style sender name.
- **`generate_personal_name()`**: Generates a personal-style sender name (e.g., "John D. E.").
- **`generate_sender_name(name_type)`**: A wrapper that calls the appropriate name generator based on the `name_type`.
- **`generate_subject_with_prefix_pattern()`**: Creates a dynamic subject line with a random base, prefix, and pattern.
- **`class ContentManager`**: 
    - Manages the generation of email subjects and bodies.
    - `get_subject_and_body(template_mode)`: Returns a tuple of (subject, body) based on the selected template (`own_proven` or `gmass_inboxed`).
- **`content_manager`**: A global instance of `ContentManager`.

## `invoice.py`
- **`class InvoiceGenerator`**:
    - `convert_pdf_to_image(pdf_path, output_path, dpi)`: Converts a PDF file to a PNG image.
    - `convert_pdf_to_heic(pdf_path, output_path, dpi)`: Converts a PDF file to a HEIC image.
    - `get_random_logo()`: Selects a random logo from the `logos/` directory.
    - `generate_invoice_data()`: Creates a dictionary of randomized data for an invoice.
    - `create_pdf(filename)`: Generates and saves a styled PDF invoice.
    - `generate_for_recipient(recipient_email, phone_numbers_input, output_format)`: The main method to generate a personalized invoice for a specific recipient in the desired format (PDF, PNG, or HEIC).

## `mailer.py`
- **`update_file_stats(token_files, leads_file)`**: Returns status strings for the uploaded token and lead files.
- **`update_attachment_stats(include_pdfs, include_images)`**: Returns a summary of available static attachments.
- **`load_gmail_token(token_path)`**: Loads, validates, and refreshes a Gmail token from a file.
- **`send_gmail_message(creds, sender_email, to_email, subject, body, attachments)`**: Sends an email using the Gmail REST API.
- **`load_token_files(token_files)`**: Processes uploaded token files, returning a list of valid accounts and any errors.
- **`read_leads_file(leads_file)`**: Reads emails from a leads file.
- **`distribute_leads(leads, account_count, leads_per_account)`**: Distributes leads among the available accounts.
- **`choose_random_attachments(include_pdfs, include_images)`**: Selects random static attachments.
- **`build_attachments(config, invoice_gen, lead_email)`**: Determines whether to use a static attachment or generate an invoice.
- **`compose_email(account_email, config)`**: Generates the subject, body, and `From` header for an email.
- **`send_single_email(account, lead_email, config, invoice_gen)`**: A wrapper to compose and send a single email, handling errors.
- **`run_campaign(accounts, mode, leads, leads_per_account, config)`**: The core sequential campaign runner that iterates through accounts and leads.
- **`campaign_events(...)`**: The main generator function that orchestrates the entire campaign, yielding events for UI updates.

## `ui_token_helpers.py`
- **`analyze_token_files(token_files)`**: A UI helper to get a status string for uploaded tokens.
- **`ui_error_wrapper(func)`**: A decorator to catch exceptions in the campaign generator and format them for the UI.
- **`start_campaign(...)`**: The main entry point for the Gradio UI. It calls `mailer.campaign_events` and formats the yielded events into strings for the UI's log, status, and summary boxes.

## `ui.py`
- **`gradio_ui()`**: Builds the entire Gradio web interface, including all components and event handlers.
- **`main()`**: The entry point to launch the Gradio application.

## `colab_setup.py`
- **`install_packages()`**: Installs required Python packages.
- **`create_directories()`**: Creates the necessary directories (`pdfs`, `images`, `logos`, `gmail_tokens`).
- **`launch_app()`**: Imports and runs the main UI application.

## `setup.py`
- Contains standard project setup configuration for packaging and distribution, including dependencies and entry points.
