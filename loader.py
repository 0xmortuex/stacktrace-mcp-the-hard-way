"""Load a module's main.py by directory name (the directory names start with digits, so they
cannot be imported with a plain `import`)."""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(dirname: str) -> ModuleType:
    name = "mod_" + dirname.replace("-", "_")
    if name in sys.modules:
        return sys.modules[name]
    path = os.path.join(ROOT, dirname, "main.py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
