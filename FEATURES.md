# Project Features

This summary matches the current codebase as of October 05, 2025 and is aligned with the v2 refactor guardrails.

**Guardrail Strategy**
- Behavioural parity is enforced through automated tests for sending, content generation, invoices, headers, delays, and randomizer outputs.
- The Gardio blueprint UI (`gardio_ui.py`) provides a visual checklist to confirm each feature group before flipping callers during refactor stages.
- Feature flags and mode toggles keep new orchestrators behind adapters so existing workflows remain runnable while components are broken apart and reshaped.
- Deterministic seeds, preview exports, and the manual preview tests (`preview_tests.py`) ensure UI rewrites surface differences immediately.

**Authentication & Accounts**
- Supports Gmail OAuth token JSON uploads with automatic refresh and validation.
- Maintains legacy app-password parsing, including mailbox metrics via IMAP for visibility.
- Quick status summaries (`update_file_stats`, `analyze_token_files`) surface account readiness and error hints inside the UI.

**Leads & Targeting**
- GMass-style seed recipients load by default for smoke runs and parity checks.
- CSV lead ingestion enforces the `email,fname,lname` schema; TXT uploads remain available for legacy lists.
- Leads distribute evenly across accounts with optional per-account manual caps guarded by the orchestrator adapters.

**Content & Personalization**
- Subject and body spintax templates (`ContentManager`) deliver `own_proven`, `own_last`, and `r1_tag` modes with tag expansion.
- Full tag catalog covers contact details, invoice numbers, TFNs, UUIDs, timestamps, and dynamic email fields.
- Sender name generation supports business and personal formats plus deterministic overrides during tests.
- R1 randomizer headers and HTML randomization (color/font jitter) preserve inboxing experiments while remaining seedable.

**Attachments & Invoice Generation**
- Static attachment pools draw from `./pdfs` and `./images` with optional random selection.
- Invoice generation (`InvoiceGenerator`) builds personalized PDF, PNG, and HEIF outputs with randomized logos and support numbers.
- Manual mode attachments can be transformed to PDF, flat PDF, PNG, HEIF, or DOCX using snapshot rendering and text conversion helpers.
- Inline HTML bodies may be rasterized to PNG for image-only sends while preserving original markup previews.

**UI Modes & Workflows**
- Manual email mode keeps the HTML editor, inline image toggle, sender style controls, and attachment conversion options.
- Automatic bulk HTML mode randomizes from uploaded body and attachment pools without exposing the editor.
- Drive share mode uploads creative assets, applies Drive permissions, and returns share links per lead.
- Multi-mode dashboard assigns a send mode per account and synchronizes manual configs when toggling accounts.
- Live preview widgets render bodies, attachments, and GMass previews with fallbacks when content is missing.

**Campaign Execution & Monitoring**
- Campaign generator streams structured events for logs, status, and summary panels in real time.
- Gmail REST sending preserves delay semantics, threading model, and optional advanced headers for reputation tests.
- Manual campaign runner reuses the same pipeline while injecting manual configs and attachment specs.
- Mailbox metrics and GMass preview reports render as markdown for quick verification during parity checks.

**Integrations & Tooling**
- Google Drive share workflow remains intact alongside invoice generation and attachment randomizers.
- Playwright-backed renderer snapshots HTML for previews, PDF export, and image conversion when available.
- Optional HTML randomizer and snapshotting fall back gracefully when Playwright is absent.

**Environment & Setup**
- Colab setup script installs dependencies, prepares asset directories, and launches the UI entry point.
- Packaging exposes the `simple-mailer` console script for launching the Gradio interface locally.
- Deterministic seeds and feature guard exports can be captured via the Gardio blueprint for documentation.
