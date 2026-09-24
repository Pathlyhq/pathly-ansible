# -*- coding: utf-8 -*-
"""Pytest configuration: expose the collection under ansible_collections.*."""

from __future__ import absolute_import, division, print_function

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"


def _ensure_pkg(name, path=None):
    if name in sys.modules:
        mod = sys.modules[name]
    else:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    if path is not None:
        mod.__path__ = [str(path)]
    return mod


_ensure_pkg("ansible_collections")
_ensure_pkg("ansible_collections.pathlyhq")
_ensure_pkg("ansible_collections.pathlyhq.pathly", ROOT)
_ensure_pkg("ansible_collections.pathlyhq.pathly.plugins", PLUGINS)
_ensure_pkg(
    "ansible_collections.pathlyhq.pathly.plugins.module_utils",
    PLUGINS / "module_utils",
)
_ensure_pkg(
    "ansible_collections.pathlyhq.pathly.plugins.modules",
    PLUGINS / "modules",
)
_ensure_pkg(
    "ansible_collections.pathlyhq.pathly.plugins.doc_fragments",
    PLUGINS / "doc_fragments",
)

# Import real modules into the namespace package.
import importlib.util


def _load(fullname, file_path):
    spec = importlib.util.spec_from_file_location(fullname, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


_load(
    "ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api",
    PLUGINS / "module_utils" / "pathly_api.py",
)
_load(
    "ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_common",
    PLUGINS / "module_utils" / "pathly_common.py",
)
_load(
    "ansible_collections.pathlyhq.pathly.plugins.doc_fragments.auth",
    PLUGINS / "doc_fragments" / "auth.py",
)

sys.path.insert(0, str(PLUGINS / "modules"))
sys.path.insert(0, str(ROOT))


class AnsibleExitJson(Exception):
    def __init__(self, kwargs):
        super(AnsibleExitJson, self).__init__(kwargs)
        self.kwargs = kwargs


class AnsibleFailJson(Exception):
    def __init__(self, kwargs):
        super(AnsibleFailJson, self).__init__(kwargs)
        self.kwargs = kwargs


class FakeModule(object):
    def __init__(self, params=None, check_mode=False):
        self.params = params or {}
        self.check_mode = check_mode
        self.warnings = []

    def exit_json(self, **kwargs):
        raise AnsibleExitJson(kwargs)

    def fail_json(self, **kwargs):
        raise AnsibleFailJson(kwargs)

    def warn(self, msg):
        self.warnings.append(msg)
