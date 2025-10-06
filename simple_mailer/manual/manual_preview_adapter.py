"""Adapter for manual preview rendering and attachment inspection."""

from __future__ import annotations

import html as _html_module

from typing import Dict, List, Optional, Sequence, Tuple

from manual_mode import ManualAttachmentSpec, ManualConfig, preview_attachment

__all__ = [
    "build_snapshot",
    "attachment_listing",
    "attachment_preview",
]


_EMPTY_PREVIEW_MESSAGE = "Nothing to preview yet."


def _ensure_config(config: ManualConfig) -> ManualConfig:
    if not isinstance(config, ManualConfig):
        raise TypeError("config must be a ManualConfig instance.")
    return config


def _wrap_text_as_html(text: str) -> str:
    escaped = _html_module.escape(text or '')
    return f"<pre style='white-space:pre-wrap; margin:0;'>{escaped}</pre>"


def _wrap_preview_container(title: str, inner_html: str) -> str:
    header = (
        f"<div style='font-weight:600; margin-bottom:8px;'>{_html_module.escape(title)}</div>"
        if title
        else ''
    )
    body = inner_html or ''
    return (
        '<div style="max-height:600px; overflow:auto; padding:12px; '
        'border:1px solid rgba(255,255,255,0.15); border-radius:8px; '
        'background:rgba(0,0,0,0.25);">'
        f"{header}{body}</div>"
    )


def _wrap_preview_error(title: str, message: str) -> str:
    body = (
        f"<div style='color:#ff9f9f'>{_html_module.escape(message or 'Preview not available.')}</div>"
    )
    return _wrap_preview_container(title, body)


def build_snapshot(
    config: ManualConfig,
    *,
    preview_email: str,
    selected_attachment_name: Optional[str] = None,
) -> Tuple[List[str], str, Dict[str, str], Dict[str, bool]]:
    """Build preview tabs for manual mode body and attachments."""
    manual_config = _ensure_config(config)
    context = manual_config.build_context(preview_email or '')
    html_map: Dict[str, str] = {}
    choices: List[str] = []
    body_available = False
    attachment_available = False

    try:
        body_rendered, body_kind = manual_config.render_body(context)
    except Exception as exc:  # pragma: no cover - legacy defensive guard
        fragment = _wrap_preview_error('Body Preview', str(exc))
        html_map['Body'] = fragment
        choices.append('Body')
    else:
        if body_rendered:
            if body_kind == 'html':
                fragment = body_rendered
            else:
                fragment = _wrap_text_as_html(body_rendered)
            html_map['Body'] = _wrap_preview_container('Body Preview', fragment)
            choices.append('Body')
            body_available = True
        else:
            html_map['Body'] = _wrap_preview_error('Body Preview', 'No body content available.')
            choices.append('Body')

    attachments = manual_config.attachments if manual_config.attachments_enabled else []
    if attachments:
        target = None
        if selected_attachment_name:
            for spec in attachments:
                if spec.display_name == selected_attachment_name:
                    target = spec
                    break
        if target is None:
            target = attachments[0]
        try:
            kind, payload = preview_attachment(target)
        except Exception as exc:  # pragma: no cover - defensive guard
            fragment = _wrap_preview_error('Attachment Preview', str(exc))
        else:
            if kind == 'html':
                inner = payload
            else:
                inner = _wrap_text_as_html(payload)
            fragment = _wrap_preview_container(
                f"Attachment Preview ({target.display_name})",
                inner,
            )
            attachment_available = True
        html_map['Attachment'] = fragment
        choices.append('Attachment')

    if not choices:
        html_map['Body'] = _wrap_preview_error('Preview', _EMPTY_PREVIEW_MESSAGE)
        choices.append('Body')

    default = 'Body' if 'Body' in choices else choices[0]
    if default == 'Body' and not body_available and 'Attachment' in choices and attachment_available:
        default = 'Attachment'

    meta = {
        'body_available': body_available,
        'attachment_available': attachment_available,
    }
    return choices, default, html_map, meta


def attachment_listing(
    specs: Sequence[ManualAttachmentSpec],
) -> Tuple[List[str], Optional[str], str, str]:
    """Return dropdown entries and initial preview payloads for attachments."""
    names = [spec.display_name for spec in specs]
    if not specs:
        return names, None, '', ''

    kind, payload = preview_attachment(specs[0])
    if kind == 'html':
        return names, names[0], payload, ''
    return names, names[0], '', payload


def attachment_preview(
    specs: Sequence[ManualAttachmentSpec],
    selected_name: str,
) -> Tuple[str, str]:
    """Return HTML/text preview payload for the selected attachment."""
    for spec in specs:
        if spec.display_name == selected_name:
            kind, payload = preview_attachment(spec)
            if kind == 'html':
                return payload, ''
            return '', payload
    return '', ''
