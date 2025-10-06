"""Mode registry for the orchestrator UI shell."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Iterator


@dataclass(frozen=True)
class Mode:
    """Descriptor for a UI mode exposed in the orchestrator shell."""

    id: str
    title: str
    build_ui: Callable[[], object]
    to_runner_config: Callable[[object, object | None], object]
    run: Callable[[object, object | None], Iterable[object]]


_MODE_REGISTRY: Dict[str, Mode] = OrderedDict()


def register_mode(mode: Mode) -> None:
    """Register a mode; reject duplicate identifiers."""
    if mode.id in _MODE_REGISTRY:
        raise ValueError(f"Mode '{mode.id}' is already registered.")
    _MODE_REGISTRY[mode.id] = mode


def get_mode(mode_id: str) -> Mode:
    """Return a registered mode by identifier."""
    try:
        return _MODE_REGISTRY[mode_id]
    except KeyError as exc:
        raise KeyError(f"Unknown mode '{mode_id}'.") from exc


def iter_modes() -> Iterator[Mode]:
    """Yield registered modes in registration order."""
    return iter(_MODE_REGISTRY.values())


__all__ = [
    "Mode",
    "register_mode",
    "get_mode",
    "iter_modes",
]

