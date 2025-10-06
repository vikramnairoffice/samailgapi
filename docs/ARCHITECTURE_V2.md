# Architecture v2 (Modular, Adapter-Backed)

Runtime: Google Colab only. The goal is to modularize while reusing today’s engine/UI components through adapters so we preserve behaviour until every guardrail passes.

## High-Level Layout

```
simple_mailer/
  app.py                       # entry for Colab
  orchestrator/
    __init__.py
    ui_shell.py                # orchestrator entrypoint exposing adapter-backed modes
    modes.py                   # registry for orchestrator modes
    adapters.py                # shims forwarding to existing UI components until replaced
  ui_modes/
    email_manual.py            # wraps current manual widgets
    email_automatic.py         # bulk HTML mode reusing existing components
    drive_share.py             # drive workflow reutilizing present routines
    multi_mode.py              # per-credential routing adaptor
  core/
    __init__.py
    leads_csv.py               # CSV reader (extracted from mailer)
    leads_txt.py               # legacy TXT reader
    spintax.py                 # renders CSV/UI tags + logo/product pools, then spintax
    html_randomizer.py         # relocated existing randomizer
    html_renderer.py           # relocated snapshot renderer
    attachments.py             # adapter over manual_mode/build_attachments
    invoice.py                 # reuse current generator
    r1_headers.py              # header utilities moved from mailer/content
    throttling.py              # delay/jitter abstractions matching current behaviour
  credentials/
    __init__.py
    app_password.py            # SMTP (existing logic behind facade)
    token_json.py              # token.json loader
    oauth_json.py              # new flow (in-memory token) sharing validators; consent grants shared Gmail+Drive scopes
  senders/
    __init__.py
    gmail_rest.py              # Gmail REST send (facade over current implementation)
    gmail_smtp.py              # SMTP path for app passwords
  integrations/
    __init__.py
    drive.py                   # upload + permission with legacy code reused
  exec/
    __init__.py
    serial.py                  # single-thread baseline
    threadpool.py              # existing thread executor extracted
    async_exec.py              # optional async executor (feature-flagged)
  tests/
    ...                        # parity + regression suites
```

Notes
- Existing behaviour flows through adapters until the corresponding v2 module reaches parity; only then do we retire the legacy path.
- Each extracted module retains the same input/output contracts as today; adapters wrap translation layers where names differ.
- Gmail REST senders keep full Gmail API scope (send, headers, attachments, threading) unchanged.
- OAuth token carries both Gmail and Drive scopes, so Drive adapters reuse the same credentials without prompting again.
- UI components do not execute business logic; they call orchestrator adapters which in turn invoke core modules.
- Legacy adapter bridges were retired once parity landed (G7-T6); modules now import manual helpers directly.

## Orchestration Flow

1. UI Shell collects config and surfaces adapter-backed modes (legacy components remain accessible through adapters without feature flags).
2. Config passes through adapters that reuse existing validators and builders.
3. Mode runner is selected from the registry (email_manual, email_automatic, drive_share, multi_mode) and bridges to legacy components when necessary.
4. Runner composes work items and dispatches to `exec/*` using the same delay semantics.
5. Send path relies on `senders/gmail_rest.py` (or SMTP for app passwords) whose implementations delegate to today’s mailer code until replacements are stable.
6. Integrations such as Drive share call through adapters wrapping the current logic.
7. Once parity tests succeed, adapters can be flipped to pure v2 implementations without UI impact.

## Compatibility Contracts

- Placeholder behaviour, randomization seeds, and throttling semantics must match the current production path.
- Legacy TXT leads remain supported via adapters even after CSV becomes primary.
- Deterministic seeds are routed through adapters to guarantee identical outputs for guard tests.
- Legacy module-level shims have been removed; callers import directly from the `simple_mailer.*` namespace once parity is proven.

## File Size Guidance

If a file must exceed ~150 LoC because it embeds existing behaviour (e.g., `invoice.py` or `legacy_mailer.py`), add a top-of-file comment explaining the exception and plan to split once parity is confirmed.
