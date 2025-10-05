# Feature Guard and Parity Matrix (Colab-only)

Purpose: guarantee zero feature loss while we refactor to a modular UI and engine backed by adapters.

## Scope Rules
- Runtime: Google Colab only (per Rules.md).
- All existing flows remain available via adapters until v2 replacements pass parity.
- Gmail REST integration keeps full Gmail API scope (send, headers, attachments, threading) with no reductions.
- Missing placeholder data must render as empty text (unchanged).

## 1. Existing Features - Must Remain 1:1
- Credential paths: Gmail token JSON, OAuth JSON, and App Password TXT (parity on validation messages and status banners).
- Lead ingestion: TXT legacy reader plus CSV primary (email,fname,lname).
- Multithreading: threadpool semantics preserved; serial/async stay feature-flagged.
- Delay function: same defaults and jitter rules routed through throttling adapters.
- Automatic mode templates: Own Proven, Own Last, R1_Tag selections with identical logic.
- Sender name styles: Business/Personal outputs with deterministic seed behaviour.
- Manual mode: HTML editor, inline image toggle, attachment conversions, extra tag support, inline PNG preview.
- Invoice mode: {{TFN}} support, PDF/PNG/HEIF/DOCX outputs via InvoiceGenerator.
- Attachment pool selection: identical randomisation and folder override rules.
- GMass preview and mailbox metrics: same URLs and formatting.
- R1 headers and advanced header toggles: matching behaviour and defaults.
- Randomize HTML styling: same algorithm seeded via shared config.
- Multi mode: per-account overrides using existing config semantics.

Acceptance checks:
- Guardrail test suite (unit/integration/visual) must stay green before feature flags flip.
- Any drift recorded in docs/Known_Issues.md with owner and remediation plan.

## 2. Drive Mode Parity Checklist
- Conversion matrix: HTML body to PDF, PNG, HEIF, DOCX using existing manual conversion helpers.
- Inline rendering: respect randomizer and inline PNG options when generating Drive assets.
- TFN and custom message: identical placeholder expansion and tag rendering before upload.
- Notification toggle: honour user selection (sendNotificationEmail=true/false) with identical default copy.
- Permission semantics: type=user, role=reader, same custom email message handling and logging.
- Multi-mode alignment: Drive manual/automatic modes embedded per account with the same configuration persistence as email multi mode.
- Event log: Drive share emits the same kind/account/lead/message payloads as the legacy flow.
- Event log: Drive share emits the same {kind, account, lead, message} payloads as the legacy flow.
## 3. New or Changed Features - Must Integrate Without Regressions
- OAuth desktop flow as third credential option (tokens in memory, shared Gmail + Drive scopes).
- CSV leads as primary input; TXT handled via adapter for backward compatibility.
- Tag placeholders rendered before spintax ({{FNAME}}, {{LNAME}}, {{TFN}}, {{LOGO}}, {{Product}}).
- Automatic HTML expansion: upload body and attachment pools with identical random selection.
- Drive share UX refresh: new orchestrator layout reuses legacy logic; no behavioural drift tolerated.

## 4. Documentation and Blueprint Sync
- After each gate, update FEATURES.md, Plan.md, task.md status, Gardio blueprint annotations, and parity fixture notes.
- Do not retire legacy entry points until adapters, docs, and guard suites confirm equivalence.
