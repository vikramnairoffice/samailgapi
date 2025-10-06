"""Utilities for bridging legacy import paths to the simple_mailer package."""
from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
from types import ModuleType

class _AliasLoader(importlib.abc.Loader):
    """Loader that returns the target module without re-executing it."""

    def __init__(self, target_name: str) -> None:
        self._target_name = target_name

    def create_module(self, spec):  # pragma: no cover - importlib protocol
        module = importlib.import_module(self._target_name)
        sys.modules[spec.name] = module
        return module

    def exec_module(self, module):  # pragma: no cover - module already initialised
        return None


class _AliasFinder(importlib.abc.MetaPathFinder):
    """Meta path finder that proxies alias prefix modules to target prefix modules."""

    def __init__(self, alias_prefix: str, target_prefix: str) -> None:
        self.alias_prefix = alias_prefix
        self.target_prefix = target_prefix

    def find_spec(self, fullname: str, path, target=None):  # pragma: no cover - importlib hook
        if not fullname.startswith(self.alias_prefix + "."):
            return None
        suffix = fullname[len(self.alias_prefix) + 1 :]
        target_name = f"{self.target_prefix}.{suffix}"
        spec = importlib.util.find_spec(target_name)
        if spec is None:
            return None
        loader = _AliasLoader(target_name)
        new_spec = importlib.machinery.ModuleSpec(fullname, loader, origin=spec.origin)
        new_spec.submodule_search_locations = spec.submodule_search_locations
        return new_spec


def _finder_registered(alias_prefix: str, target_prefix: str) -> bool:
    for finder in sys.meta_path:
        if isinstance(finder, _AliasFinder) and finder.alias_prefix == alias_prefix and finder.target_prefix == target_prefix:
            return True
    return False


def bridge(alias_name: str, target_name: str) -> ModuleType:
    """Register lias_name as a compatibility view of 	arget_name."""

    module = importlib.import_module(target_name)
    sys.modules[alias_name] = module
    if not _finder_registered(alias_name, target_name):
        sys.meta_path.insert(0, _AliasFinder(alias_name, target_name))
    return module
