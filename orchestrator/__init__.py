"""Compatibility shim for legacy import orchestrator usage."""

from simple_mailer._compat import bridge as _bridge

_bridge(__name__, 'simple_mailer.orchestrator')
