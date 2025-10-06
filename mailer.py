"""Compatibility shim for legacy `import mailer` usage."""

import sys as _sys
from simple_mailer import mailer as _module

_sys.modules[__name__] = _module
