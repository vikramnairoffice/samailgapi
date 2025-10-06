"""Compatibility shim for core.html_renderer."""

from simple_mailer.core.html_renderer import (
    PlaywrightHTMLRenderer,
    PlaywrightUnavailable,
    html_renderer,
)

__all__ = ["PlaywrightHTMLRenderer", "PlaywrightUnavailable", "html_renderer"]
