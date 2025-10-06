from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator


class SerialExecutor:
    """Synchronous executor mirroring the threadpool interface."""

    def stream(self, items: Iterable[Any], worker: Callable[[Any], Iterable[Any]]) -> Iterator[Any]:
        def _iterator() -> Iterator[Any]:
            for item in items:
                try:
                    for result in worker(item):
                        yield result
                except Exception as exc:  # pragma: no cover - defensive path
                    raise RuntimeError(
                        f"SerialExecutor worker raised {exc.__class__.__name__}: {exc}"
                    ) from exc
        return _iterator()
