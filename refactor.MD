# Gmail REST API Refactor Notes

## Overview
- Replaced the previous hybrid SMTP/Gmail service with a single Gmail REST workflow that accepts plain token JSON uploads.
- Removed the `token_manager` caching layer and any app-password logic; credentials now load directly in `mailer.py:67` via `load_gmail_token` and are verified against the Gmail profile endpoint.
- Simplified the UI surface so it only handles token files and streams progress from the new generator (`ui.py:18`, `ui_token_helpers.py:42`).

## Key Changes
- `mailer.py` now exposes
  - `load_gmail_token` for refreshing tokens and extracting the sender email.
  - `send_gmail_message` for composing MIME payloads and POSTing to `https://gmail.googleapis.com/gmail/v1/users/me/messages/send`.
  - `load_token_files` / `campaign_events` to drive a sequential multi-account send loop without queues/threads.
- `ui.py` and `ui_token_helpers.py` were rewritten to drop selection tables and token manager hooks; the UI just uploads tokens, optional leads, and surfaces log/status textboxes.
- Deleted `token_manager.py` and its pytest coverage; added `testing & qa/test_gmail_rest_flow.py` to validate the new helpers with mocks.
- Updated docs (`README.md`) and packaging metadata (`requirements.txt`, `setup.py`) to describe the Gmail-only flow and remove unused dependencies.

## Behavioural Notes
- Multi-account support remains: every uploaded token becomes an entry in the `accounts` list and is processed sequentially.
- GMass seed sending is preserved; leads mode still honours the uploaded file but no longer deletes sent entries.
- Gmail API failures bubble up as simple error strings in the UI log, matching the lean POC approach described in `Rules.MD`.
