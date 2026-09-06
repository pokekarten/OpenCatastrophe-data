#!/usr/bin/env python3
"""Serialization-only wrapper for the frozen independent freMTPL2 run."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).with_name("independent_fremtpl_duration_meanclass.py")
spec = importlib.util.spec_from_file_location("independent_fremtpl_duration_meanclass", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

_original_dumps = module.json.dumps

def _json_default(value):
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

def _safe_dumps(*args, **kwargs):
    kwargs.setdefault("default", _json_default)
    return _original_dumps(*args, **kwargs)

module.json.dumps = _safe_dumps
module.main()
