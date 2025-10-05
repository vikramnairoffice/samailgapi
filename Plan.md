Architecture v2 Refactor Plan (Colab runtime)

This plan highlights sequential gates and the parallel lanes available once a gate is cleared. See task.md for detailed tickets and ownership.

Gate 0 - Guardrails & Snapshots (blocking)
- Extend parity tests for send/content/invoice/headers/delay/randomizer before touching runtime code.
- Capture Gardio blueprint exports and UI snapshots for manual, automatic, drive, and multi-mode layouts. All later work depends on this gate being green.
- Design the optional live-token smoke harness so implementation can begin once adapters land.

Gate 1 - Adapter Layer (no behaviour change; lanes may run in parallel after Gate 0)
- Lane A - Data/content adapters: extract leads_csv, leads_txt, spintax/tag helpers, attachments, invoice facades.
- Lane B - Sending/execution adapters: wrap Gmail REST + SMTP paths, extract threadpool executor, add serial baseline.
- Lane C - Manual mode facade: expose ManualConfig helpers, previews, attachment conversions.
- Keep legacy entry points; each adapter stays behind feature flags until it passes the guard suite.

Gate 2 - UI Orchestrator Decomposition (depends on the adapters each mode needs)
- Build ui_shell scaffold with feature flag to flip between legacy and v2 instantly.
- Migrate modes in order: email_manual -> email_automatic (HTML/Invoice) -> drive_share (manual + automatic) -> multi_mode (including Drive multi mode).

Gate 3 - Credentials Harmonisation (may start alongside late Gate 1 items once guardrails exist)
- Add OAuth in-memory token flow sharing validators across token_json and app_password loaders.
- Update UI copy to remind users that a single consent covers Gmail + Drive scopes.

Gate 4 - Feature Integration Guarding (after Gates 1-3 for the relevant surfaces)
- Run integrated parity suite (send + drive) with adapters active; document any temporary gaps in Known_Issues.md.
- Implement the optional live-token smoke test that sends and retrieves via Gmail API when creds are supplied.

Gate 5 - Execution Strategy (optional, after Gate 1 extraction)
- Add async executor behind feature flag; keep threadpool default until async path meets parity expectations.

Gate 6 - Cleanup & Documentation
- Retire duplicated legacy wiring once adapters are the single integration surface and guard suites are green.
- Update docs, Gardio blueprint annotations, fixtures, and feature flags at each milestone before closing this gate.
