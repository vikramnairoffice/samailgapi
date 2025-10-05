# Async/Threading Plan (Colab‑Compatible)

Goals
- Speed up rendering/sending without breaking current behaviour.
- Stage changes so we can rollback to today’s threaded behaviour instantly.

## Phase 0 — Isolation (no behaviour change)

- Extract current multithreading into `exec/threadpool.py` with interface:
  - `execute(tasks, per_task_fn, delay_ms, max_workers) -> event iterator`
- Serial baseline in `exec/serial.py` with the same interface.
- Runners call through the executor abstraction only.

## Phase 1 — Nested Async (opt‑in)

- Add `exec/async_exec.py` using `asyncio` with `nest_asyncio` for Colab.
- Rules:
  - CPU‑bound rendering (HTML→PNG/HEIF/PDF) stays in thread pool via `run_in_executor`.
  - I/O‑bound API calls (Gmail REST and Drive) use async HTTP client wrappers or run in executor until wrappers exist.
  - Maintain per‑account sequencing if required; global concurrency cap stays.

## Fallback

- A feature flag selects executor: `serial` (safe), `threadpool` (current), or `async` (experimental).
- Tests execute all three where feasible to ensure parity.

