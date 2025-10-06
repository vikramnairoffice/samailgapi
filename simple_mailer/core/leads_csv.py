"""CSV leads adapter providing structured recipient rows."""
from __future__ import annotations

import csv
import os
from typing import Dict, List, Union

PathLike = Union[str, os.PathLike[str]]


def _coerce_path(candidate) -> str:
    if hasattr(candidate, "name") and getattr(candidate, "name"):
        return str(getattr(candidate, "name"))
    return str(candidate)


def read(resource: PathLike) -> List[Dict[str, str]]:
    """Parse a CSV file into lead dictionaries (email/fname/lname)."""
    if not resource:
        return []

    path = _coerce_path(resource)
    rows: List[Dict[str, str]] = []

    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return []

            normalised = [
                (header or "").strip().lower()
                for header in reader.fieldnames
            ]
            reader.fieldnames = normalised

            for raw_row in reader:
                email = (raw_row.get("email") or "").strip()
                if not email:
                    continue

                rows.append({
                    "email": email,
                    "fname": (raw_row.get("fname") or "").strip(),
                    "lname": (raw_row.get("lname") or "").strip(),
                })
    except OSError as exc:
        message = exc.strerror or str(exc)
        raise RuntimeError(f"Unable to read leads CSV '{path}': {message}") from exc

    return rows
