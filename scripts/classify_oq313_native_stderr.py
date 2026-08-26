# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Classify one bounded native OQ3.13 stderr tail without exposing its content.

The classifier is deliberately diagnostic-only. It accepts only a bounded byte tail,
requires a canonical Python traceback header before the terminal non-empty line, and
returns one finite allow-listed class token or ``unclassified``. Messages, paths,
values and arbitrary exception names are never returned.
"""

from __future__ import annotations

import re

MAX_STDERR_CLASSIFIER_TAIL_BYTES = 64 * 1024
UNCLASSIFIED_EXCEPTION_CLASS = "unclassified"

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

_TRACEBACK_HEADER = b"Traceback (most recent call last):"
_TERMINAL_CLASS_RE = re.compile(
    rb"^(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)(?::.*)?$"
)


def classify_terminal_exception(stderr_tail: bytes) -> str:
    """Return only an allow-listed terminal traceback class or ``unclassified``."""

    if type(stderr_tail) is not bytes:
        return UNCLASSIFIED_EXCEPTION_CLASS
    if len(stderr_tail) > MAX_STDERR_CLASSIFIER_TAIL_BYTES:
        return UNCLASSIFIED_EXCEPTION_CLASS
    try:
        stderr_tail.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return UNCLASSIFIED_EXCEPTION_CLASS

    lines = stderr_tail.splitlines()
    nonempty = [(index, line.strip()) for index, line in enumerate(lines) if line.strip()]
    if not nonempty:
        return UNCLASSIFIED_EXCEPTION_CLASS

    terminal_index, terminal_line = nonempty[-1]
    if not any(
        index < terminal_index and line.strip() == _TRACEBACK_HEADER
        for index, line in enumerate(lines)
    ):
        return UNCLASSIFIED_EXCEPTION_CLASS

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
