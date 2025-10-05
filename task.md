# Refactor Task Board (Multi-Agent Ready)

Use this board to coordinate parallel sessions. Each task lists its prerequisites and whether it can run alongside others. Update status inline (TODO -> IN_PROGRESS -> BLOCKED/REVIEW/COMPLETE).

## Concurrency Rules
- Never start work on a task unless all dependencies are COMPLETE.
- When two tasks are marked Parallel OK, they can be assigned to different agents simultaneously.
- If a task becomes BLOCKED, note the reason and ping in the playbook before picking a different card.
- Keep guardrail tests green after every change; run relevant parity suites before marking COMPLETE.

## Legend
- **ID**: unique handle for hand-off.
- **Parallel**: Parallel OK / Sequenced Only.
- **Deliverables**: specific artefacts, tests, or docs needed for completion.

## Agent Tracking
- Log each assignment here before touching a task card.
- Update Status to IN_PROGRESS when work begins and COMPLETE when finished (match board casing).
- Include quick notes for blockers or hand-off context.

| Task ID | Agent | Status | Notes |
|---------|-------|--------|-------|
| G0-T2 | Codex | COMPLETE | Snapshot fixtures & README note added |
| G0-T3 | Codex | COMPLETE | Design doc + implementation ticket posted |
| G1C-T1 | Codex | COMPLETE | Manual adapter + parity tests + docs |
| G1C-T2 | Codex | COMPLETE | Preview + attachment adapter, tests, docs refreshed |
| G1B-T2 | Codex | COMPLETE | SMTP adapter, tests, docs |
| G1A-T2 | Codex | COMPLETE | Spintax adapter + tests + docs |
| G2-T1 | Codex | COMPLETE | ui_shell scaffold + tests + docs updates |
| G2-T2 | Codex | COMPLETE | Manual orchestrator module + tests + snapshot |
| G2-T3 | Codex | COMPLETE | Automatic modes orchestrator + tests + snapshot |
| G2-T4 | Codex | COMPLETE | Drive modes orchestrator + tests + snapshots |
| G2-T5 | Codex | COMPLETE | Multi mode orchestrator + tests + doc note |


---

## Gate 0 - Guardrails & Snapshots (blocking, run sequentially)
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G0-T1 | Parity Suite Expansion | Add send/content/invoice/header/delay/randomizer parity tests; ensure deterministic seeds documented. | None | Sequenced Only | Updated tests in tests/, doc note in docs/TESTING_STRATEGY.md | COMPLETE |
| G0-T2 | UI Snapshot Baselines | Capture manual/automatic/drive/multi Gardio blueprints + Gradio snapshots; check into fixtures. | G0-T1 | Sequenced Only | Snapshot fixtures, README coverage note | COMPLETE |
| G0-T3 | Live Token Smoke Spec | Design opt-in live-token harness (send + retrieve + drive share) without implementation; document plan. | G0-T1 | Sequenced Only | Design doc entry in docs/TESTING_STRATEGY.md, task ticket for implementation | COMPLETE |

## Gate 1 - Adapter Layer (lanes can run in parallel after Gate 0)

### Lane A - Data & Content
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G1A-T1 | Leads Reader Extraction | Create core/leads_csv.py and core/leads_txt.py adapters; hook parity tests. | G0-T1 | Parallel OK | Adapter modules, tests, doc note in docs/INTERFACES.md | COMPLETE |
| G1A-T2 | Spintax & Tag Facade | Move tag render/expand logic into core/spintax.py; add adapter tests. | G1A-T1 | Parallel OK (once task claimed) | New module, unit tests, interface doc updates | COMPLETE |
| G1A-T3 | Attachments & Invoice Adapters | Wrap attachment builders + InvoiceGenerator into core/attachments.py/core/invoice.py. | G1A-T1 | Parallel OK | Adapter modules, parity tests, docs updated | COMPLETE |

### Lane B - Sending & Execution
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G1B-T1 | Gmail REST Facade | Create senders/gmail_rest.py adapter forwarding to legacy send flow. | G0-T1 | Parallel OK | Adapter module, unit tests, interface doc update | COMPLETE |
| G1B-T2 | SMTP/App Password Adapter | Expose app-password sending + mailbox metrics via adapters. | G1B-T1 | Parallel OK | Adapter module, tests, error-handling docs | COMPLETE |
| G1B-T3 | Executor Extraction | Move threadpool + serial executor into exec/ package; update callers. | G1B-T1 | Parallel OK | exec/threadpool.py, exec/serial.py, tests | COMPLETE |

### Lane C - Manual Mode
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G1C-T1 | ManualConfig Facade | Wrap manual mode helpers into adapter exposing config/build/render APIs. | G0-T1 | Parallel OK | Adapter module, parity tests, docs | COMPLETE |
| G1C-T2 | Preview & Attachment Adapter | Extract manual preview + attachment conversion pipelines, ensure snapshot parity. | G1C-T1, G0-T2 | Parallel OK | Adapter module, updated snapshots, docs | COMPLETE |

## Gate 2 - UI Orchestrator Decomposition (start once dependent adapters complete)
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G2-T1 | ui_shell Scaffold | Create new orchestrator/ui_shell.py with feature flag + legacy fallback. | G1A-T1, G1B-T1 | Sequenced Only | Scaffold module, integration test, docs | COMPLETE |
| G2-T2 | Email Manual Mode Adapter | Rebuild manual mode UI via orchestrator, reusing adapters. | G2-T1, G1C-T2 | Sequenced Only | Mode module, UI tests, updated snapshots | COMPLETE |
| G2-T3 | Email Automatic Modes | Implement HTML + Invoice automatic modes under orchestrator. | G2-T1, G1A-T2, G1A-T3 | Parallel OK | Mode modules, tests, snapshots | COMPLETE |
| G2-T4 | Drive Modes | Implement drive manual + automatic orchestrator modes, including conversions. | G2-T1, G1A-T3, G1B-T1 | Parallel OK | Mode modules, drive tests, snapshots | COMPLETE |
| G2-T5 | Multi Mode & Drive Multi | Build account switcher embedding per-mode UIs (including Drive). | G2-T2, G2-T3, G2-T4 | Sequenced Only | Mode module, integration tests, docs | COMPLETE |

## Gate 3 - Credentials Harmonisation
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G3-T1 | OAuth In-Memory Flow | Implement credentials/oauth_json adapter + UI integration. | G0-T1, G2-T1 | Sequenced Only | Adapter module, tests, UX copy updates | COMPLETE |
| G3-T2 | Shared Validation Library | Unify credential validation + status messaging across modes. | G3-T1 | Parallel OK | Shared helpers, tests, doc updates | COMPLETE |

## Gate 4 - Feature Integration Guarding
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G4-T1 | Integrated Parity Runbook | Execute full suite (email + drive) with adapters; document results. | Gates 1-3 complete for relevant modules | Sequenced Only | Runbook entry, Known_Issues.md updates | TODO |
| G4-T2 | Live Token Smoke Implementation | Implement opt-in test using real token (send + receive + drive share). | G0-T3, G4-T1 | Sequenced Only | Test harness, README instructions, env flag docs | TODO |

## Gate 5 - Execution Strategy (optional)
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G5-T1 | Async Executor Prototype | Add async executor + feature flag; ensure parity tests cover it. | G1B-T3 | Parallel OK | exec/async_exec.py, tests, docs | TODO |

## Gate 6 - Cleanup & Documentation
| ID | Title | Summary | Dependencies | Parallel | Deliverables | Status |
|----|-------|---------|--------------|---------|--------------|--------|
| G6-T1 | Legacy Path Retirement | Remove unused legacy wiring once adapters proven. | Gates 1-4 | Sequenced Only | Code removal, changelog, doc updates | TODO |
| G6-T2 | Final Docs & Blueprint Audit | Refresh docs/blueprints/tests to reflect finished architecture. | G6-T1 | Sequenced Only | Doc sweep, blueprint diff report | TODO |










