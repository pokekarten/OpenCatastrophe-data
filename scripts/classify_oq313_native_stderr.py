# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Classify one bounded native OQ3.13 stderr tail without exposing its content.

The classifier is deliberately diagnostic-only. It accepts only a bounded byte tail,
requires a canonical Python traceback header before the terminal non-empty line, and
returns finite allow-listed tokens only. Messages, paths, function names, values and
arbitrary exception names are never returned.
"""

from __future__ import annotations

import re

MAX_STDERR_CLASSIFIER_TAIL_BYTES = 64 * 1024
UNCLASSIFIED_EXCEPTION_CLASS = "unclassified"
UNCLASSIFIED_TRACEBACK_ORIGIN = "unclassified"
UNCLASSIFIED_TRACEBACK_MODULE = "unclassified"

# Keep this finite and conservative. ``InvalidFile`` is defined by the pinned
# OpenQuake 3.13 source in ``openquake.baselib``; the remaining entries are
# standard Python exception classes commonly used at runtime/input boundaries.
ALLOWED_EXCEPTION_CLASSES = frozenset(
    {
        "AssertionError",
        "AttributeError",
        "EOFError",
        "FileNotFoundError",
        "ImportError",
        "IndexError",
        "InvalidFile",
        "KeyError",
        "MemoryError",
        "ModuleNotFoundError",
        "NotImplementedError",
        "OSError",
        "OverflowError",
        "PermissionError",
        "RuntimeError",
        "TypeError",
        "UnicodeDecodeError",
        "ValueError",
        "ZeroDivisionError",
    }
)
PUBLIC_EXCEPTION_CLASS_TOKENS = ALLOWED_EXCEPTION_CLASSES | {
    UNCLASSIFIED_EXCEPTION_CLASS
}

# Traceback-origin tokens deliberately expose only a coarse package boundary from
# the frozen /oq-engine source tree. No path, filename, line number or function is
# returned. Anything outside these fixed OpenQuake packages remains unclassified.
ALLOWED_TRACEBACK_ORIGINS = frozenset(
    {
        "openquake.baselib",
        "openquake.calculators",
        "openquake.commands",
        "openquake.commonlib",
        "openquake.engine",
        "openquake.hazardlib",
        "openquake.risklib",
    }
)
PUBLIC_TRACEBACK_ORIGIN_TOKENS = ALLOWED_TRACEBACK_ORIGINS | {
    UNCLASSIFIED_TRACEBACK_ORIGIN
}

# The pinned OQ3.13 commit contains exactly these public Python modules directly
# under ``openquake/risklib`` (excluding package ``__init__.py`` and tests/data).
# This narrower diagnostic is useful only after the coarse origin is risklib. It
# intentionally returns a finite module token rather than a source path/function.
ALLOWED_RISKLIB_TRACEBACK_MODULES = frozenset(
    {
        "openquake.risklib.asset",
        "openquake.risklib.countries",
        "openquake.risklib.read_nrml",
        "openquake.risklib.riskinput",
        "openquake.risklib.riskmodels",
        "openquake.risklib.scientific",
    }
)
PUBLIC_TRACEBACK_MODULE_TOKENS = ALLOWED_RISKLIB_TRACEBACK_MODULES | {
    UNCLASSIFIED_TRACEBACK_MODULE
}

_TRACEBACK_HEADER = b"Traceback (most recent call last):"
_TERMINAL_CLASS_RE = re.compile(
    rb"^(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)(?::.*)?$"
)
_TRACEBACK_FRAME_RE = re.compile(
    rb'^\s*File "([^"\r\n]+)", line [1-9][0-9]*(?:, in [^\r\n]+)?$'
)
_FROZEN_OQ_PATH_RE = re.compile(
    rb"^/oq-engine/openquake/([A-Za-z_][A-Za-z0-9_]*)/[^\r\n]+$"
)
_FROZEN_RISKLIB_MODULE_PATH_RE = re.compile(
    rb"^/oq-engine/openquake/risklib/([A-Za-z_][A-Za-z0-9_]*)\.py$"
)


def _validated_lines(stderr_tail: bytes) -> list[bytes] | None:
    if type(stderr_tail) is not bytes:
        return None
    if len(stderr_tail) > MAX_STDERR_CLASSIFIER_TAIL_BYTES:
        return None
    try:
        stderr_tail.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    return stderr_tail.splitlines()


def _terminal_context(lines: list[bytes]) -> tuple[int, bytes] | None:
    nonempty = [(index, line.strip()) for index, line in enumerate(lines) if line.strip()]
    if not nonempty:
        return None
    terminal_index, terminal_line = nonempty[-1]
    if not any(
        index < terminal_index and line.strip() == _TRACEBACK_HEADER
        for index, line in enumerate(lines)
    ):
        return None
    return terminal_index, terminal_line


def _final_traceback_path(lines: list[bytes], terminal_index: int) -> bytes | None:
    frame_like_lines = [
        line
        for line in lines[:terminal_index]
        if line.lstrip().startswith(b'File "')
    ]
    if not frame_like_lines:
        return None
    final_frame = _TRACEBACK_FRAME_RE.fullmatch(frame_like_lines[-1])
    if final_frame is None:
        return None
    return final_frame.group(1)


def classify_terminal_exception(stderr_tail: bytes) -> str:
    """Return only an allow-listed terminal traceback class or ``unclassified``."""

    lines = _validated_lines(stderr_tail)
    if lines is None:
        return UNCLASSIFIED_EXCEPTION_CLASS
    context = _terminal_context(lines)
    if context is None:
        return UNCLASSIFIED_EXCEPTION_CLASS
    _terminal_index, terminal_line = context

    match = _TERMINAL_CLASS_RE.fullmatch(terminal_line)
    if match is None:
        return UNCLASSIFIED_EXCEPTION_CLASS
    try:
        class_name = match.group(1).decode("ascii", errors="strict")
    except UnicodeDecodeError:
        return UNCLASSIFIED_EXCEPTION_CLASS
    if class_name not in ALLOWED_EXCEPTION_CLASSES:
        return UNCLASSIFIED_EXCEPTION_CLASS
    return class_name


def classify_traceback_origin(stderr_tail: bytes) -> str:
    """Return only the final allow-listed frozen-OQ package origin.

    The returned token is intentionally coarse. It is derived from the actual final
    canonical Python traceback frame before the terminal exception line and never
    exposes the source path, filename, line number or function name.
    """

    lines = _validated_lines(stderr_tail)
    if lines is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    context = _terminal_context(lines)
    if context is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    terminal_index, _terminal_line = context
    path = _final_traceback_path(lines, terminal_index)
    if path is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN

    oq_path = _FROZEN_OQ_PATH_RE.fullmatch(path)
    if oq_path is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    try:
        package = oq_path.group(1).decode("ascii", errors="strict")
    except UnicodeDecodeError:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    candidate = f"openquake.{package}"
    if candidate not in ALLOWED_TRACEBACK_ORIGINS:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    return candidate


def classify_risklib_traceback_module(stderr_tail: bytes) -> str:
    """Return only the final allow-listed frozen OQ3.13 risklib module token.

    This is deliberately narrower than :func:`classify_traceback_origin`. It returns
    a token only when the actual final canonical traceback frame is one of the fixed
    Python modules present directly under ``openquake/risklib`` at the pinned OQ3.13
    commit. Paths, functions, line numbers and exception messages remain private.
    """

    lines = _validated_lines(stderr_tail)
    if lines is None:
        return UNCLASSIFIED_TRACEBACK_MODULE
    context = _terminal_context(lines)
    if context is None:
        return UNCLASSIFIED_TRACEBACK_MODULE
    terminal_index, _terminal_line = context
    path = _final_traceback_path(lines, terminal_index)
    if path is None:
        return UNCLASSIFIED_TRACEBACK_MODULE

    risklib_path = _FROZEN_RISKLIB_MODULE_PATH_RE.fullmatch(path)
    if risklib_path is None:
        return UNCLASSIFIED_TRACEBACK_MODULE
    try:
        module = risklib_path.group(1).decode("ascii", errors="strict")
    except UnicodeDecodeError:
        return UNCLASSIFIED_TRACEBACK_MODULE
    candidate = f"openquake.risklib.{module}"
    if candidate not in ALLOWED_RISKLIB_TRACEBACK_MODULES:
        return UNCLASSIFIED_TRACEBACK_MODULE
    return candidate
