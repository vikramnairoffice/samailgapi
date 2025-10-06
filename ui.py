"""Compatibility shim for legacy `import ui` usage."""

import sys as _sys
from simple_mailer import ui as _module

_sys.modules[__name__] = _module

if __name__ == "__main__":
    _module.main()
