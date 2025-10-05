# Multi-Agent Development Playbook

Intent: enable many parallel sessions (humans or AI agents) to refactor safely without stepping on each other.

## Rules of Engagement
- Touch one module or one UI mode per task (single-responsibility changes).
- Keep files under ~150 LoC when possible; add an EXCEPTION: comment if a legacy adapter must exceed that while parity is proven.
- Only call across modules through documented interfaces; add adapters instead of new cross-imports.
- Do not ship feature changes without explicit approval recorded in the task board.

## Task Selection & Coordination
- Review Plan.md for gate status. Gate 0 (guardrails) must be green before starting any Gate 1+ work.
- Claim a task from task.md. Respect the Parallel flag: Sequenced Only tasks block parallel work; Parallel OK cards can run concurrently once dependencies show completed IDs.
- Update the task row with status (IN_PROGRESS, BLOCKED, REVIEW, COMPLETE). If blocked, add a short note describing the dependency or failing test.
- Snapshots and parity tests must pass locally before moving a task to REVIEW.

## Workflow Expectations
1. Extend or add tests first (TDD). Guardrail parity tests live under tests/; visual baselines live under Gardio fixtures.
2. Implement adapters or UI changes behind feature flags so legacy paths remain available.
3. Run relevant suites (unit, parity, snapshots, optional smoke) before hand-off.
4. Document behaviour deltas in docs/Known_Issues.md and link the task ID.

## Interface Contracts
- UI modes must satisfy the Mode interface in docs/UI_ORCHESTRATOR_SPEC.md.
- Engine adapters adhere to the function signatures listed in docs/INTERFACES.md.
- Credential loaders share validation helpers defined during Gate 3.

## Communication & Handoff
- Reference task IDs in commit/patch descriptions and review notes.
- Use the Feature Guard checklist (docs/FEATURE_GUARD.md) to confirm every legacy behaviour still passes.
- When a behaviour change is unavoidable, record the rationale in the task row and flag it for approval before merging.
