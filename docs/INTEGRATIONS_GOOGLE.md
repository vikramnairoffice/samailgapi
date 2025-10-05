# Google Integrations (Design Notes)

Runtime: Colab. Tokens/creds in memory for session only.

## Gmail

- Primary: Gmail REST API `users.messages.send`.
- Scopes: OAuth consent requests full Gmail + Drive (`https://www.googleapis.com/auth/gmail.modify`, `https://www.googleapis.com/auth/drive`); tokens unified across send and share flows.
- Input: MIME message built with subject, body (HTML), R1 headers, attachments (PDF/DOCX/PNG/HEIF) as today.
- App Password path: SMTP to `smtp.gmail.com` (TLS, 587) for accounts using App Password.
- Gmail REST path retains full Gmail API behaviour we rely on today (send pipeline, headers, attachments) with no scope reductions.

## OAuth (3rd Credential Option)

- Upload OAuth client JSON (Desktop/Installed type).
- Flow in Colab: attempt `run_local_server(port=0)`, fall back to `run_console()` if needed.
- Store credentials object in memory (no disk). Token refresh occurs in memory.
- Unified token covers Gmail + Drive without re-consent regardless of which flow initiated auth.

## Google Drive (Share‑only Mode)

Flow per recipient
1) Render asset(s) via existing pipeline.
2) Upload: `files.create` with media upload.
3) Share: `permissions.create` with `type='user'`, `role='reader'`, `emailAddress=lead.email`, `sendNotificationEmail=true`, and optional `emailMessage` from custom message input.
4) Optionally capture the webViewLink to include in logs.

Notes
- OAuth tokens already carry Drive scope, so Drive share never needs a second consent.
- No folder structure required; naming uses existing attachment naming convention.

