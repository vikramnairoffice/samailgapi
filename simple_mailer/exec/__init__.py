"""Execution executors for campaign dispatch."""

__all__ = [
    "ThreadPoolExecutor",
    "SerialExecutor",
]

try:
    from .threadpool import ThreadPoolExecutor  # noqa: F401
    from .serial import SerialExecutor  # noqa: F401
except ImportError:
    # During partial installation the modules may not be available yet.
    pass
