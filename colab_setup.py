"""Compatibility shim for legacy `import colab_setup` usage."""

import sys as _sys
from simple_mailer import colab_setup as _module

_sys.modules[__name__] = _module
