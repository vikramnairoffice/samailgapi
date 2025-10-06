# UI Orchestrator Spec (Adapter-Bridged Gradio Modes)

Principles
- Reuse existing Gradio components through adapters; avoid behavioural drift while reshaping layout.
- Orchestrator normalizes config, forwards through adapters, and invokes engine runners.
- Gmail REST pipeline retains full scope (send, headers, attachments, threading) with no behavioural change.
- Tokens/creds live in memory per session; no disk persistence.
- Single consent covers Gmail + Drive scopes; credential UI simply routes the shared token to the relevant adapters.
- Legacy UI shell has been retired; the orchestrator layout is always active.
- Manual config and preview helpers now import directly from `manual.manual_config_adapter` and `manual.manual_preview_adapter`; the legacy adapter bridge was removed after parity.

## Setup View

- Credential mode chips mirror the mockups: `Gmail + Drive Token`, `Gmail + Drive JSON Credential`, `Gmail App pass`. Each chip maps to the same adapter-backed loaders described above (token JSON, OAuth client, or app password list).
- Central credential drop zone accommodates OAuth JSON or TXT lists and feeds the existing `update_file_stats` helpers so the status banner remains intact.
- Sending mode toggle (`Email`, `Drive`) determines which orchestrator mode registry is surfaced next without altering the underlying feature flags.
- Lead uploader emphasises CSV input (`email,fname,lname`) with the current lead status banner; TXT ingestion continues to route through the legacy adapter for parity.
- Credential status and leads status boxes reuse the streaming text outputs already provided by `ui_token_helpers`.

## Modes (registered via `modes.py`)

Interface
```
class Mode:
    id: str
    title: str
    def build_ui(self, gr, adapters): ...          # returns components dict reused from legacy UI
    def to_runner_config(self, ui_values, adapters): ...  # normalize to engine config using shared helpers
    def run(self, config, adapters): ...           # yields progress events (str or dict)
```

Available modes
- `email_automatic_invoice`: retains delay, GMass vs Leads selector, automatic/manual switch, template chips (`Own Proven`, `Own Last`, `R1_Tags`), sender style buttons, attachment vs invoice toggle with explicit format buttons (PDF/DOCX/PNG/HEIF), GMass preview, and run log output just like legacy automatic mode.
- `email_automatic_html`: extends the automatic card with TFN input, HTML body upload, randomizer + inline PNG checkboxes, attachment conversion (`Doc`/`Image`, downstream format buttons), and an HTML attachment upload tray so the same manual bulk helpers remain in play.
- `email_manual`: keeps sender style controls, change-name toggle, subject/body editors with tag guidance, extra tag repeater, attachment conversion area, TFN input, and the dedicated preview panel (`Body` vs `Attachment`).
- `multi_mode`: account dropdown plus mode selector; once an account is chosen it embeds the email manual/automatic and drive manual/automatic workspaces so per-account overrides reuse the same components.
- `drive_share_manual`: delay control, TFN input, custom message textbox with tag support, notification toggle, conversion buttons (PDF/HTML), and run log all forwarding to current Drive manual helpers.
- `drive_share_automatic`: shares the manual layout but swaps the message textbox for template chips and HTML upload drop zone so existing automatic Drive routines plug in unchanged.

## Eventing and Feedback

- All runners yield dictionaries `{kind, account, lead, message, meta}` identical to current campaign generator.
- Orchestrator formats to log/status/summary components exactly as today; adapters translate when required.
- Preview panels (body, attachment, GMass) reuse current rendering helpers and are snapshot-tested; manual preview remains a separate surface matching the mockup card.

## Validation Rules

- Credential selection explicit; adapters share validation across App Password, Token JSON, OAuth.
- CSV must include header `email,fname,lname`; adapters map TXT files into CSV-like structures for parity tests.
- Spintax placeholders that are missing still render empty strings; randomizer seeded through shared config to ensure parity.
- Legacy UI shell was retired in Gate 6; the orchestrator layout is always active.
