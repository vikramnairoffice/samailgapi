Architecture v2 Completion Plan (Colab runtime)

Overview
- Objective: finish migration to the modular package described in docs/ARCHITECTURE_V2.md while keeping current behaviour intact.
- Scope: restructure packaging, add legacy adapter bridges, switch the UI entrypoint, relocate remaining core utilities, consolidate credential loaders, and refresh docs/tests.
- Guardrails: keep parity suites green after each milestone and document any temporary gaps in docs/Known_Issues.md before proceeding.

Milestones
1. Package Skeleton & Legacy Stubs
   - Create the `simple_mailer/` package with orchestrator, ui_modes, adapters, core, credentials, senders, exec subpackages mirroring docs/ARCHITECTURE_V2.md.
   - Provide import shims so existing scripts (ui.py, mailer.py, manual_mode.py) continue to work during the migration.
   - Update setup.py packaging metadata and adjust tests to import from the new namespace.

2. Adapter Bridge & Wiring Cleanup
   - Implement adapters/legacy_mailer.py and adapters/legacy_manual_mode.py to proxy through existing implementations (retired in G7-T6 once parity confirmed).
   - Route orchestrator and manual mode modules through the adapters and retire direct calls once parity is confirmed.
   - Capture any behavioural drift in docs/FEATURE_GUARD.md and Known_Issues.md.

3. UI Entry Migration
   - Update ui.py to mount simple_mailer.orchestrator.ui_shell.build_ui behind a feature flag with legacy fallback.
   - Keep snapshots and Gardio blueprints in sync while verifying the new entrypoint via tests.

4. Core Utility Relocation
   - Move html_randomizer.py, html_renderer.py, header helpers, and throttling logic into simple_mailer/core.
   - Update content, mailer, and manual modules to consume the relocated utilities and refresh affected tests.

5. Credential Module Consolidation
   - Extract token_json and app_password helpers into simple_mailer/credentials alongside oauth_json and validation.
   - Harmonise ui_token_helpers and mailer credential loaders to use the adapter surface.

6. Docs, Tests, and Cleanup
   - Refresh README, docs/INTERFACES.md, docs/FEATURE_GUARD.md, and packaging notes to reflect the new structure.
   - Update task.md statuses, run the full pytest suite, and remove obsolete legacy wiring once adapters fully replace direct calls.

Optional Follow-up
- Revisit Gate 5 async executor once the modular architecture is live and parity-verified.
