"""Compatibility shim for legacy import core usage."""

from simple_mailer._compat import bridge as _bridge

_bridge(__name__, 'simple_mailer.core')
