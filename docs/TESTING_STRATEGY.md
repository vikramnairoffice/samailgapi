# Testing Strategy (Guardrail-Driven TDD)

Principles
- Every refactor step must extend or reuse tests before swapping implementations.
- Randomized paths run with fixed seeds in parity mode so adapters can be validated against legacy outputs.
- Focus on tests that protect behaviour, configuration compatibility, and UI contracts.

## Unit Tests

- core/leads_csv: parses header email,fname,lname, handles missing/blank values  empty strings, matches legacy parser fixtures.
- core/spintax: adapter tests assert tag context overrides, injected RNG control, and the combined render+spintax helper stay aligned with legacy outputs.
- core/attachments: chooses static vs invoice using manual_mode adapter; validates conversion matrix (PDF/PNG/HEIF/DOCX).
- credentials/*: token/app password/OAuth loaders share validation tests to guarantee identical error messaging (see tests/test_credentials_validation.py).
- OAuth fixtures assert shared Gmail+Drive scope availability so adapters never request duplicate consent.
- senders/gmail_rest: builds MIME with headers/attachments; parity fixtures compare generated payloads with legacy outputs.
- senders/gmail_smtp: guards required credentials, normalises headers, and wraps legacy SMTP send + mailbox metrics errors for actionable messages.
- orchestrator/modes: ensures adapters pass through configuration without mutation.
- orchestrator/ui_shell: feature flag guard (`SIMPLE_MAILER_UI_SHELL=1`) keeps legacy layout default until the new shell is ready.
- `tests/test_mailer_parity.py`: locks Gmail send headers, compose fallbacks, invoice attachments, and delay handling with mocked network and filesystem boundaries.

## Integration Tests

- CSV end-to-end send (dry-run) comparing serialized events between legacy and adapter paths.
- Automatic bulk HTML with fixed seed verifying selection order matches current implementation.
- Drive share flow with mocked API verifying permission calls are identical.
- UI mode toggles (manual, automatic, drive, multi) exercised via Gradio test harness to confirm shared components render.

## Visual & Snapshot Tests

- Gardio blueprint exports diffed against baseline per mode.
- Blueprint audit checks docs/BLUEPRINT_AUDIT.md hashes against fixtures via tests/test_docs_blueprint_audit.py.
- Manual preview snapshots (preview_tests.py) executed under fixed seed; failures block adapter swaps.

## Live Smoke (optional, when tokens provided)

### G0-T3 Live Token Smoke Spec

### Harness usage (G4-T2)
- Live harness code lives in `testing/live_token_smoke.py`.
- Tests guard helper behaviour in `tests/test_live_token_smoke.py`; mocked paths run by default.
- Set `LIVE_TOKEN_SMOKE=1` and rerun the test module with `-k live_smoke_integration` to exercise the real token flow.
- Expect Gmail + Drive network calls; only run in staging mailboxes with verified tokens.

- Scope: opt-in harness that exercises Gmail send, inbox retrieval, and Drive share using a real OAuth token without touching production parity tests.
- Trigger: run only when `LIVE_TOKEN_SMOKE=1` inside Colab; guard with try/skip messaging when env flag or token bundle missing.
- Preconditions: requires seeded Gmail token JSON with send+read scopes and Drive scope; harness validates scopes before running.
- Sequence: (1) send single invoice email via adapter path, (2) poll inbox for matching subject/id, (3) create Drive share and confirm permission grant, (4) clean up artefacts when cleanup flag set.
- Assertions: compare payload headers/body to snapshot fixture, confirm Gmail message status is `SENT`, ensure Drive file shares expected user with `reader` role.
- Error handling: emit actionable failures (missing env, scope mismatch, API errors) and capture raw response payloads for debugging.
- TDD hooks: plan separate integration tests per phase with mock transport, plus live harness marked `@pytest.mark.live_token` to avoid accidental CI runs.
- Next steps: implementation tracked by G4-T2 ticket; see `docs/G4-T2_live_token_smoke.md` for execution checklist.

- Controlled inbox send verifying headers/body/attachments from adapter path match legacy.
- Skipped by default in CI; opt-in via environment flag in Colab.

## Regression Workflow

1. Add or update parity test capturing current behaviour.
2. Introduce adapter or new module; ensure both legacy and new paths run side-by-side.
3. Flip feature flag only when parity suite, snapshots, and documentation updates are complete.

## Deterministic Seeds

- `tests/test_html_randomizer.py` uses seeds 7, 9, and 42 to preserve colour and font order mutations for parity runs.
- `tests/test_mailer_parity.py` relies on patched RNG boundaries; no random seeds required because subject/body generation is stubbed for deterministic assertions.

