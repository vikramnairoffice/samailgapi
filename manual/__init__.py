"""Compatibility shim for legacy import manual helpers."""

from simple_mailer._compat import bridge as _bridge

_bridge(__name__, 'simple_mailer.manual')
