# API Research Notes (Summary)

Gmail REST
- Endpoint: `users.messages.send`; OAuth consent grants full Gmail scope (`gmail.modify`) alongside Drive.
- MIME build rules: base64url encode raw message; supports attachments.

OAuth Installed App
- Use OAuth client of type Desktop/Installed.
- In Colab, prefer `run_local_server(port=0)`; fallback to `run_console()`.
- Consent includes Drive scope, so the resulting token powers Gmail + Drive flows.

Google Drive
- Upload via `files.create` (multipart or resumable).
- Share via `permissions.create` with `type=user`, `role=reader` and `sendNotificationEmail=true` plus optional custom `emailMessage`.
- Relies on the same OAuth token granted during Gmail auth; no secondary consent screen.



