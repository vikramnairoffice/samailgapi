# G4-T2 Live Token Smoke Implementation

Linked design: docs/TESTING_STRATEGY.md (G0-T3 Live Token Smoke Spec)

## Goal
Ship an opt-in Colab harness that proves Gmail send + inbox retrieval + Drive share using real OAuth tokens without destabilising parity tests.

## Guardrails
- Only execute when `LIVE_TOKEN_SMOKE=1`.
- Abort early with clear message if token bundle missing scopes or network unavailable.
- Leave legacy parity suites untouched; live run must be optional.

## TDD Plan
1. Add unit/mocked integration tests covering send, poll, and drive-share helpers (simulate API responses).
2. Add `@pytest.mark.live_token` integration that is skipped unless env flag set.
3. Implement harness behind feature flag once tests fail.
4. Run live harness manually with staging token and capture artefacts for docs.

## Implementation Tasks
- [x] Build Gmail send helper using existing adapter entry point with optional dry-run logging.
- [x] Add inbox poller with timeout + retry for matching `X-Ref` header; expose configurable max wait.
- [x] Create Drive share helper targeting invoice fixture; verify permission role = `reader`.
- [x] Wire harness runner that sequences send -> poll -> share -> cleanup (conditional) with structured logging.
- [x] Document opt-in flow and troubleshooting in README + Known_Issues if needed.

## Open Questions
- What mailbox/address should receive the smoke message?
- Should Drive cleanup delete file or leave behind for auditing?
- Do we need rate limiting between Gmail send and poll to avoid quota hits?
