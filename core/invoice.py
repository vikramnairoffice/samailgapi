"""Invoice adapter wrapping the legacy generator implementation."""
from __future__ import annotations

from typing import Any

from invoice import InvoiceGenerator as _LEGACY_GENERATOR


class InvoiceGenerator:
    """Proxy around the legacy invoice generator."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._delegate = _LEGACY_GENERATOR(*args, **kwargs)

    def generate_for_recipient(self, email: str, phone_numbers: str, fmt: str) -> str:
        return self._delegate.generate_for_recipient(email, phone_numbers, fmt)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._delegate, item)


__all__ = ["InvoiceGenerator", "_LEGACY_GENERATOR"]
