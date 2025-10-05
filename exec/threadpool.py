from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any, Callable, Iterable, Iterator, List, Optional


@dataclass
class _WorkerError:
    error: BaseException


class ThreadPoolExecutor:
    """Simple thread-based streaming executor safe for Colab runtime."""

    def __init__(self, max_workers: Optional[int] = None, thread_name_prefix: str = "MailerWorker") -> None:
        if max_workers is not None and max_workers <= 0:
            raise ValueError("max_workers must be a positive integer")
        self._max_workers = max_workers
        self._thread_name_prefix = thread_name_prefix

    def stream(self, items: Iterable[Any], worker: Callable[[Any], Iterable[Any]]) -> Iterator[Any]:
        work: List[Any] = list(items)
        if not work:
            return iter(())

        queue: Queue[Any] = Queue()
        sentinel = object()

        def _run(item: Any, index: int) -> None:
            try:
                for result in worker(item):
                    queue.put(result)
            except Exception as exc:  # pragma: no cover - defensive path
                queue.put(_WorkerError(exc))
            finally:
                queue.put(sentinel)

        threads: List[Thread] = []
        for position, item in enumerate(work, 1):
            if self._max_workers is not None and position > self._max_workers:
                position = ((position - 1) % self._max_workers) + 1
            name = f"{self._thread_name_prefix}-{position}"
            thread = Thread(target=_run, args=(item, position), name=name, daemon=True)
            thread.start()
            threads.append(thread)

        active = len(threads)

        def _iterator() -> Iterator[Any]:
            nonlocal active
            try:
                while active:
                    item = queue.get()
                    if item is sentinel:
                        active -= 1
                        continue
                    if isinstance(item, _WorkerError):
                        raise RuntimeError(
                            f"ThreadPoolExecutor worker raised {item.error.__class__.__name__}: {item.error}"
                        ) from item.error
                    yield item
            finally:
                for thread in threads:
                    thread.join()

        return _iterator()
