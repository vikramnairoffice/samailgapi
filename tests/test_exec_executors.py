import threading
import time

import pytest

from exec.threadpool import ThreadPoolExecutor
from exec.serial import SerialExecutor


def test_threadpool_stream_collects_results() -> None:
    items = [1, 2, 3, 4]
    seen_threads: set[str] = set()

    def worker(value: int):
        seen_threads.add(threading.current_thread().name)
        time.sleep(0.01)
        yield value * 2

    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="TestPool")
    results = list(executor.stream(items, worker))

    assert len(results) == len(items)
    assert set(results) == {2, 4, 6, 8}
    assert len(seen_threads) >= 2
    assert all(name.startswith("TestPool") for name in seen_threads)


def test_threadpool_stream_propagates_exceptions() -> None:
    def worker(_: int):
        raise ValueError("boom")
        yield

    executor = ThreadPoolExecutor(max_workers=1)

    with pytest.raises(RuntimeError, match="worker raised ValueError: boom"):
        list(executor.stream([1], worker))


def test_serial_executor_stream_runs_inline() -> None:
    items = [1, 2, 3]
    recorded_threads: list[str] = []

    def worker(value: int):
        recorded_threads.append(threading.current_thread().name)
        yield value + 1

    executor = SerialExecutor()
    results = list(executor.stream(items, worker))

    assert results == [2, 3, 4]
    assert recorded_threads == [threading.current_thread().name] * len(items)
