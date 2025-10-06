"""Compatibility shim for legacy `import invoice` usage."""

import sys as _sys
from simple_mailer import invoice as _module

_sys.modules[__name__] = _module
