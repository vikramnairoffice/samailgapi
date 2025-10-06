"""TXT leads adapter forwarding to the legacy parser behaviour."""
from __future__ import annotations

import os
from typing import List, Union

PathLike = Union[str, os.PathLike[str]]


def _coerce_path(candidate) -> str:
    """Return a filesystem path string for legacy inputs."""
    if hasattr(candidate, "name") and getattr(candidate, "name"):
        return str(getattr(candidate, "name"))
    return str(candidate)


def read(resource: PathLike) -> List[str]:
    """Return non-empty email lines from a TXT leads file."""
    if not resource:
        return []

    path = _coerce_path(resource)
    leads: List[str] = []

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                email = line.strip()
                if email:
                    leads.append(email)
    except OSError as exc:
        message = exc.strerror or str(exc)
        raise RuntimeError(f"Unable to read leads file '{path}': {message}") from exc

    return leads
