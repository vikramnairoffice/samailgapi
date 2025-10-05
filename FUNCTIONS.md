# Functions and Classes Reference

This catalog reflects the callable surface as of October 05, 2025.

Each module lists public functions (no leading underscore), the helper/internal functions that other modules may import implicitly, and any classes/dataclasses that form part of the architecture.

**content.py**
- Classes: TagDefinition, ContentManager.
- Public functions: render_tagged_content, expand_spintax, get_tag_definitions, generate_tag_value, generate_r1_tag_entry, generate_business_name, generate_personal_name, generate_sender_name, generate_subject_with_prefix_pattern.
- Internal helpers: _context_lookup, _random_numeric_string, _random_letter_string, _random_upper_alphanumeric, _tag_date_multi, _tag_date_numeric, _tag_datetime, _tag_single_name, _tag_full_name, _tag_unique_name, _tag_email, _tag_content, _tag_invoice, _tag_short_numeric, _tag_long_numeric, _tag_short_mixed_letters, _tag_long_mixed_letters, _tag_short_upper_letters, _tag_long_upper_letters, _tag_short_lower_letters, _tag_long_lower_letters, _tag_uuid, _tag_trx, _tag_address, _tag_full_address, _tag_tfn, _resolve_tag_definition.

**html_randomizer.py**
- Classes: none exposed.
- Public functions: randomize_html.
- Internal helpers: _jitter_channel, _mutate_hex, _mutate_rgb, _rotate_fonts.

**html_renderer.py**
- Classes: PlaywrightUnavailable, PlaywrightHTMLRenderer.
- Public functions: none exposed.
- Internal helpers: none.

**manual_mode.py**
- Classes: _HTMLTextExtractor, ManualAttachmentSpec, ManualConfig.
- Public functions: parse_extra_tags, to_attachment_specs, preview_attachment.
- Internal helpers: _html_to_text, _random_suffix, _finalize_html_payload, _wrap_lines, _text_to_pdf, _ensure_heif_plugin, _save_image, _text_to_image, _image_to_pdf, _trim_rendered_image, _html_to_pdf_rendered, _html_to_image, _text_to_docx, _render_attachment.

**invoice.py**
- Classes: InvoiceGenerator.
- Public functions: none exposed.
- Internal helpers: _download_logo_from_url.

**mailer.py**
- Classes: none exposed.
- Public functions: update_file_stats, load_gmail_token, send_gmail_message, fetch_mailbox_totals_app_password, send_app_password_message, load_token_files, load_app_password_files, load_accounts, read_leads_file, distribute_leads, choose_random_attachments, choose_random_file_from_folder, build_attachments, compose_email, send_single_email, run_campaign, campaign_events.
- Internal helpers: _create_attachment_part, _attach_files, _build_mime_message, _imap_messages_total.

**ui_token_helpers.py**
- Classes: none exposed.
- Public functions: analyze_token_files, ui_error_wrapper, merge_token_sources, build_gmass_preview, gmass_rows_to_markdown, mailbox_rows_to_markdown, authorize_oauth_client, fetch_mailbox_counts, start_manual_campaign, build_manual_config_from_inputs, manual_preview_snapshot, manual_random_sender_name, manual_attachment_listing, manual_attachment_preview_content, start_campaign, run_unified_campaign, run_multi_manual_campaign.
- Internal helpers: _build_output, _format_progress, _fetch_label_total, _extract_update_value, _resolve_manual_body_image_choice.

**gardio_ui.py**
- Classes: Section, LayoutSpec.
- Public functions: create_blueprint, render_notes, build_demo, main.
- Internal helpers: _load_fonts, _line_height, _wrap_lines, _rounded_rectangle, _on_mode_change.

**ui.py**
- Classes: ManualFormControls.
- Public functions: gradio_ui, main.
- Internal helpers: _extract_update_value, _normalize_manual_mode, _manual_category_change, _manual_format_choice, _looks_like_html, _manual_body_image_toggle, _manual_body_image_store_state, _leads_status, _describe_attachment_folder, _map_content_template, _map_subject_template, _gmass_preview_update, _manual_toggle_attachments, _preview_selection_change, _preview_message, _wrap_preview_block, _render_body_fragment, _render_attachment_fragment, _build_preview_document, _write_preview_document, _manual_render_preview, _build_manual_form, _manual_multi_default_config, _manual_multi_accounts_from_tokens, _manual_multi_get_config, _manual_multi_store_current, _manual_multi_prepare_accounts, _manual_multi_sync_accounts, _manual_multi_on_account_change, _manual_multi_capture_config.

**colab_setup.py**
- Classes: none exposed.
- Public functions: install_packages, create_directories, launch_app.
- Internal helpers: _load_requirements.


**manual.manual_preview_adapter.py**
- Classes: none exposed.
- Public functions: build_snapshot, attachment_listing, attachment_preview.
- Internal helpers: none.
