"""Delay helpers shared by orchestrators and legacy mailer."""

from __future__ import annotations

import time
from typing import Any

DEFAULT_SEND_DELAY_SECONDS = 4.5

__all__ = ["DEFAULT_SEND_DELAY_SECONDS", "coerce_delay", "sleep"]

def coerce_delay(value: Any, *, default: float = DEFAULT_SEND_DELAY_SECONDS) -> float:
    """Convert an arbitrary input into a non-negative delay in seconds."""
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return float(default)
    if delay < 0:
        return 0.0
    return delay

def sleep(delay_seconds: float) -> None:
    """Sleep for the requested duration when positive."""
    if delay_seconds > 0:
        time.sleep(delay_seconds)
