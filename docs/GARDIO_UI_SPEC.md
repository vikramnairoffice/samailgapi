# Gardio UI Sketchpad Design (2025-10-05)

Purpose
- Provide a guard-rail focused workspace inside Gradio to validate refactored flows without losing any v1 behaviour.
- Give refactor contributors a shared canvas to iterate on layout ideas while checking the Feature Guard matrix.

Key Concepts
- Sketchpad Blueprint: A generated background image that visualises the layout regions for Setup, Mode Workspace, Guard Checklist, and Event Log.
- Mode Tabs: Switch between Manual Email, Automatic Bulk HTML, Drive Share, and Multi Mode. Each mode surfaces only its unique inputs per docs/UI_ORCHESTRATOR_SPEC.md.
- Feature Guard Checklist: Mirrors the parity items in docs/FEATURE_GUARD.md; contributors tick off items as they confirm parity.
- Notes Panel: Auto-updated Markdown with hints, validation rules, and outstanding parity tests for the selected mode.

Layout Sections
1. Global Setup
   - Credential mode chips: Gmail + Drive Token, Gmail + Drive JSON Credential, Gmail App pass.
   - Shared credential drop zone sized for OAuth JSON or app-password TXT files with status readout reused from today's UI helpers.
   - Sending mode switch (Email, Drive) that routes into the matching workspace without altering the underlying adapter contract.
   - Lead uploader block that enforces CSV (email,fname,lname) while keeping the existing lead status banner.
2. Mode Workspace
   - Automatic/Invoice email view retains delay controls, GMass vs Leads toggle, template selectors, sender style chips, attachment/invoice format toggles, GMass preview surface, and run log outputs positioned per the new mockups.
   - Automatic/HTML view extends the automatic card with TFN input, HTML body upload, randomizer + inline PNG checkboxes, attachment conversion options, and seed-respecting toggles matching ManualConfig inputs.
   - Manual view mirrors the legacy manual editor (sender controls, subject/body with tag hints, extra tag grid, attachment conversion area) plus the separate preview panel (Body vs Attachment).
   - Multi mode shell keeps the account dropdown and mode selector while embedding whichever mode workspace is active for the chosen account.
   - Drive share views (manual and automatic) expose delay, TFN, notification toggle, custom message or HTML upload, and conversion format buttons exactly as today's Drive helpers.
3. Guard Checklist
   - Quick toggles for Sender Style, Randomizer on/off, Invoice format, Manual vs Automatic invariants.
4. Event Stream
   - Structured log of runner events: {kind, account, lead, message}.

Interactions
- Selecting a mode regenerates the Sketchpad background with highlighted regions unique to that mode.
- Contributors can free-draw on the Sketchpad to propose adjustments while still seeing the canonical regions.
- Checklist state is preserved per session so contributors can snapshot parity progress via the download button.

Data Model
- LayoutSpec: dataclass describing section bounding boxes, guard notes, and validation prompts.
- FEATURE_GUARDS: ordered list grouped by feature families (Credentials, Leads, Content, Send Pipeline, Attachments/Invoices).

Output
- A runnable gardio_ui.py module exposing build_demo() and main() for launching in Colab.
- Optional pytest that asserts blueprint dimensions and checklist integrity.
Usage
- Launch locally/Colab: python gardio_ui.py.
- Import inside notebooks: from gardio_ui import build_demo then build_demo().launch(share=True) if remote validation needed.
- Run focused tests: python -m pytest tests/test_gardio_ui.py.

Feature Guard Alignment
- Credential parity toggles persist within the checklist to track App Password, Token JSON, and OAuth JSON equivalence; reminder text notes that OAuth tokens already cover both Gmail and Drive flows.
- Leads section enforces CSV header plus TXT legacy access per Feature Guard section 1.
- Content bullets include Spintax placeholders, HTML randomizer, GMass preview requirements, and the new UI chips for selecting invoice versus HTML bodies.
- Attachments and Invoice notes keep Support No. and format parity visible, reflecting the explicit PDF/DOCX/PNG/HEIF controls shown in the mockups.
- Event stream reminder ties back to R1 headers, delay, and Drive share outputs for regression capture.
