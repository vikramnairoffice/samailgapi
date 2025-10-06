"""Compatibility shim for legacy `import ui_token_helpers` usage."""

import sys as _sys
from simple_mailer import ui_token_helpers as _module

_sys.modules[__name__] = _module
