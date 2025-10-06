# Migration Plan (Guardrail-First)

## Phase A – Establish Guardrails
- Ship parity tests that cover sending, content, invoices, HTML randomizer, headers, attachments, and delays.
- Capture UI snapshots (manual, automatic, drive share, multi-mode) and Gardio blueprint exports for visual regression.
- Freeze baseline fixtures before touching architecture.

## Phase B – Build Adapter Layer (No Behaviour Change)
- Create façade modules that forward to existing `mailer.py`, `content.py`, and `manual_mode.py` logic via the new interfaces.
- Extract `core/leads_txt.py`, `core/leads_csv.py`, `core/attachments.py`, `senders/gmail_rest.py`, `exec/threadpool.py` while routing legacy entry points through adapters.
- Keep original module paths intact until guardrails confirm parity; adapters become the sole integration surface.

## Phase C – UI Orchestrator Modes
- Introduce `orchestrator/ui_shell.py` and `ui_modes/*`, each backed by shared components reused from the current Gradio layout.
- Migrate `email_manual` first (feature flag on/off), then `email_automatic` (Bulk HTML), followed by `drive_share` and `multi_mode`.
- Preserve the ability to flip back to the legacy UI shell until parity is confirmed; retire it once Gate 6 completes.

## Phase D – Credential Convergence
- Add `credentials/oauth_json.py` (in-memory tokens) while keeping token JSON and app-password flows untouched.
- Document shared Gmail/Drive scopes in UX copy so users understand a single consent enables both send and share flows.
- Share validation helpers across all credential adapters to avoid regressions.

## Phase E – Feature Guard Integration
- Reuse existing invoice generator, attachment builders, and Drive share logic via adapters; confirm guard suite passes with adapters in place.
- Document fallback paths and parity checkpoints in `FEATURE_GUARD.md` after each integration.

## Phase F – Execution Options (Optional)
- Slot in `exec/serial.py` baseline and feature-flagged `exec/async_exec.py`; default remains threadpool until parity confirmed.

## Phase G – Cleanup & Docs
- Remove redundant wiring only after adapters are the single source of truth and guard suites are green.
- Update documentation, Gardio blueprint notes, and fixtures to reflect final module locations.
