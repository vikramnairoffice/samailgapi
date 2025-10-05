"""Adapter facade over manual mode helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from manual_mode import (
    ManualAttachmentSpec,
    ManualConfig,
    parse_extra_tags as _parse_extra_tags,
    preview_attachment as _preview_attachment,
    to_attachment_specs as _to_attachment_specs,
)


__all__ = [
    "ManualAttachmentSpec",
    "ManualConfig",
    "create_config",
    "build_context",
    "render_subject",
    "render_body",
    "build_attachments",
    "resolve_sender_name",
    "render_email",
    "parse_extra_tags",
    "to_attachment_specs",
    "preview_attachment",
]


def create_config(
    data: Mapping[str, Any] | ManualConfig | None = None,
    /,
    **overrides: Any,
) -> ManualConfig:
    """Create a ManualConfig from a mapping or return the instance untouched."""
    if isinstance(data, ManualConfig):
        if overrides:
            raise ValueError("create_config received overrides alongside ManualConfig instance.")
        return data
    source: Mapping[str, Any]
    if data is None:
        source = {}
    elif isinstance(data, Mapping):
        source = data
    else:
        raise TypeError("create_config expects a ManualConfig or mapping of config fields.")
    payload = dict(source)
    payload.update(overrides)
    try:
        return ManualConfig(**payload)  # type: ignore[arg-type]
    except TypeError as exc:  # pragma: no cover - surfaced in tests
        raise ValueError(f"Invalid manual config fields: {exc}") from exc


def _ensure_config(config: ManualConfig) -> ManualConfig:
    if not isinstance(config, ManualConfig):
        raise TypeError("config must be a ManualConfig instance.")
    return config


def build_context(config: ManualConfig, lead_email: str) -> Dict[str, str]:
    """Build the render context for a given recipient."""
    manual_config = _ensure_config(config)
    return manual_config.build_context(lead_email)


def render_subject(config: ManualConfig, context: Dict[str, str]) -> str:
    """Render the subject using the provided context."""
    manual_config = _ensure_config(config)
    return manual_config.render_subject(context)


def render_body(config: ManualConfig, context: Dict[str, str]) -> Tuple[str, str]:
    """Render the body and return payload plus subtype."""
    manual_config = _ensure_config(config)
    return manual_config.render_body(context)


def build_attachments(config: ManualConfig, context: Dict[str, str]) -> Dict[str, str]:
    """Build attachments for the manual config if enabled."""
    manual_config = _ensure_config(config)
    return manual_config.build_attachments(context)


def resolve_sender_name(config: ManualConfig, fallback_type: str = "business") -> str:
    """Resolve the sender name using config preferences."""
    manual_config = _ensure_config(config)
    return manual_config.resolve_sender_name(fallback_type=fallback_type)


def render_email(config: ManualConfig, lead_email: str) -> Dict[str, Any]:
    """Convenience wrapper that renders the entire payload for a lead."""
    manual_config = _ensure_config(config)
    context = manual_config.build_context(lead_email)
    subject = manual_config.render_subject(context)
    body, subtype = manual_config.render_body(context)
    attachments = manual_config.build_attachments(context)
    sender_name = manual_config.resolve_sender_name()
    return {
        "context": context,
        "subject": subject,
        "body": body,
        "body_subtype": subtype,
        "attachments": attachments,
        "sender_name": sender_name,
    }


def parse_extra_tags(rows: Optional[Sequence[Sequence[str]]]) -> Dict[str, str]:
    """Proxy to the manual mode tag parser."""
    return _parse_extra_tags(rows)


def to_attachment_specs(
    files: Optional[Iterable[object]] = None,
    *,
    inline_html: str = "",
    inline_name: str = "",
) -> Sequence[ManualAttachmentSpec]:
    """Proxy to manual attachment spec builder."""
    return _to_attachment_specs(files, inline_html=inline_html, inline_name=inline_name)


def preview_attachment(spec: ManualAttachmentSpec) -> Tuple[str, str]:
    """Proxy preview for attachment specs (html/text)."""
    if not isinstance(spec, ManualAttachmentSpec):
        raise TypeError("preview_attachment expects a ManualAttachmentSpec instance.")
    return _preview_attachment(spec)
