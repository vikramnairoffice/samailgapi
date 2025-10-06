"""Compatibility shim for legacy `import content` usage."""

import sys as _sys
from simple_mailer import content as _module

_sys.modules[__name__] = _module
