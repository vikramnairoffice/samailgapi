"""Shared credential validation helpers used across UI modes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


_APP_PASSWORD_ALIASES = {"app_password", "app-password", "app password"}
_OAUTH_ALIASES = {
    "oauth",
    "oauth_json",
    "oauth-json",
    "oauth memory",
    "oauth-memory",
    "gmail",
    "gmail api",
    "gmail_api",
    "gmail-api",
}


@dataclass
class ValidationResult:
    mode: str
    accounts: List[Dict[str, Any]]
    errors: List[str]
    status: str


_DEF_IN_MEMORY_LABEL = "in-memory credential"


def normalize_mode(auth_mode: Optional[str]) -> str:
    text = (auth_mode or "oauth").strip().lower()
    if text in _APP_PASSWORD_ALIASES:
        return "app_password"
    if text in _OAUTH_ALIASES:
        return "oauth"
    return "oauth"


def partition_token_inputs(entries: Optional[Sequence[Any]]) -> Tuple[List[Dict[str, Any]], List[Any], List[str]]:
    in_memory_accounts: List[Dict[str, Any]] = []
    file_inputs: List[Any] = []
    errors: List[str] = []

    for entry in entries or []:
        if isinstance(entry, dict) and entry.get("__in_memory_oauth__"):
            email = (entry.get("email") or "").strip()
            creds = entry.get("creds")
            label = (entry.get("label") or email or _DEF_IN_MEMORY_LABEL).strip() or _DEF_IN_MEMORY_LABEL
            if email and creds is not None:
                in_memory_accounts.append(
                    {
                        "email": email,
                        "creds": creds,
                        "path": label,
                        "auth_type": "oauth",
                        "__in_memory_oauth__": True,
                    }
                )
            else:
                errors.append(f"{label}: in-memory credential is missing required data")
        else:
            file_inputs.append(entry)

    return in_memory_accounts, file_inputs, errors


def load_oauth_entries(file_inputs: Sequence[Any], *, loader: Optional[Callable[[str], Tuple[str, Any]]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    accounts: List[Dict[str, Any]] = []
    errors: List[str] = []

    if loader is None:
        return accounts, errors

    for file_obj in file_inputs or []:
        path = _coerce_path(file_obj)
        try:
            email, creds = loader(path)
        except Exception as exc:  # pragma: no cover - defensive to surface loader errors
            errors.append(f"{os.path.basename(path)}: {exc}")
            continue
        accounts.append({"email": email, "creds": creds, "path": path, "auth_type": "oauth"})

    return accounts, errors


def load_app_password_entries(file_inputs: Sequence[Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    accounts: List[Dict[str, Any]] = []
    errors: List[str] = []

    for file_obj in file_inputs or []:
        path = _coerce_path(file_obj)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    if line.count(",") != 1:
                        errors.append(f"{os.path.basename(path)} line {line_number}: invalid entry")
                        continue
                    email, password = (segment.strip() for segment in line.split(",", 1))
                    if not email or not password:
                        errors.append(f"{os.path.basename(path)} line {line_number}: invalid entry")
                        continue
                    accounts.append(
                        {
                            "email": email,
                            "password": password,
                            "path": f"{path}:{line_number}",
                            "auth_type": "app_password",
                        }
                    )
        except Exception as exc:
            errors.append(f"{os.path.basename(path)}: {exc}")

    return accounts, errors


def validate_files(
    token_files: Optional[Sequence[Any]],
    auth_mode: Optional[str],
    *,
    loader: Optional[Callable[[str], Tuple[str, Any]]] = None,
) -> ValidationResult:
    mode = normalize_mode(auth_mode)
    in_memory_accounts, file_inputs, in_memory_errors = partition_token_inputs(token_files)

    if mode == "app_password":
        parsed_accounts, parse_errors = load_app_password_entries(file_inputs)
        base_message = _format_app_password_status(parsed_accounts)
    else:
        parsed_accounts, parse_errors = load_oauth_entries(file_inputs, loader=loader)
        base_message = _format_oauth_status(file_inputs, in_memory_accounts)

    accounts = list(parsed_accounts) + list(in_memory_accounts)
    errors = list(parse_errors) + list(in_memory_errors)
    status = _append_error_summary(base_message, errors)
    return ValidationResult(mode=mode, accounts=accounts, errors=errors, status=status)


def _coerce_path(entry: Any) -> str:
    name = getattr(entry, "name", None)
    return str(name or entry)


def _format_oauth_status(file_inputs: Sequence[Any], in_memory_accounts: Sequence[Dict[str, Any]]) -> str:
    file_count = len(file_inputs or [])
    if file_count:
        return f"{file_count} token file(s) selected"
    memory_count = len(in_memory_accounts or [])
    if memory_count:
        return f"{memory_count} in-memory credential(s) ready"
    return "No token files uploaded"


def _format_app_password_status(accounts: Sequence[Dict[str, Any]]) -> str:
    count = len(accounts or [])
    if count:
        return f"{count} app password(s) parsed"
    return "No app password entries found"


def _append_error_summary(base_message: str, errors: Sequence[str]) -> str:
    if not errors:
        return base_message
    snippets = "; ".join(str(error) for error in errors[:3])
    suffix = f"; issues: {snippets}"
    if len(errors) > 3:
        suffix += "; more issues omitted"
    return f"{base_message}{suffix}" if base_message else suffix.lstrip("; ")
