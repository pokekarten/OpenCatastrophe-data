# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Classify one bounded native OQ3.13 stderr tail without exposing its content.

The classifier is deliberately diagnostic-only. It accepts only a bounded byte tail,
requires a canonical Python traceback header before the terminal non-empty line, and
returns finite allow-listed tokens only. Messages, line numbers, arbitrary function
names, values and arbitrary exception names are never returned.
"""

from __future__ import annotations

import re

MAX_STDERR_CLASSIFIER_TAIL_BYTES = 64 * 1024
UNCLASSIFIED_EXCEPTION_CLASS = "unclassified"
UNCLASSIFIED_TRACEBACK_ORIGIN = "unclassified"
UNCLASSIFIED_TRACEBACK_NO_HEADER = "unclassified.no_traceback_header"
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS = "unclassified.multiple_traceback_headers"
UNCLASSIFIED_TRACEBACK_TERMINAL_SHAPE = "unclassified.terminal_shape"
UNCLASSIFIED_TRACEBACK_MULTILINE_EXCEPTION = "unclassified.multiline_exception"

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

# The pinned OQ3.13 commit contains exactly these public Python modules directly
# under ``openquake/risklib`` (excluding package ``__init__.py`` and tests/data).
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

# Only names statically present at the pinned OQ3.13 asset.py source are eligible
# for the extra discriminator. Common dunder names are deliberately excluded
# because a traceback does not carry the owning class, so they would not provide
# an unambiguous source-level discriminator. The public token remains finite and
# never contains caller/provider-controlled text.
ALLOWED_RISKLIB_ASSET_TRACEBACK_FUNCTIONS = frozenset(
    {
        "_add_asset",
        "_csv_header",
        "_get_exposure",
        "_minimal_tagcol",
        "_populate_from",
        "_read_csv",
        "add",
        "add_tags",
        "add_tagname",
        "aggregateby",
        "agg_shape",
        "arr_value",
        "assets2array",
        "assets_by_site",
        "build_asset_array",
        "check",
        "extend",
        "gen_tags",
        "get_agg_values",
        "get_aggkey",
        "get_aids_by_tag",
        "get_case_similar",
        "get_mesh_assets_by_site",
        "get_tag",
        "get_tagdict",
        "get_tagidx",
        "get_tagvalues",
        "get_units",
        "get_value_fields",
        "num_taxonomies_by_site",
        "read",
        "read_headers",
        "reduce",
        "reduce_also",
        "retrofitted",
        "to_dframe",
        "value",
    }
)
ALLOWED_RISKLIB_ASSET_TRACEBACK_TOKENS = frozenset(
    f"openquake.risklib.asset.{name}"
    for name in ALLOWED_RISKLIB_ASSET_TRACEBACK_FUNCTIONS
)

# Traceback-origin tokens expose only a fixed package boundary, except for the
# direct risklib module set above and the finite asset.py source discriminator.
# When strict terminal-context validation rejects a traceback, a finite refined
# ``unclassified.*`` sentinel may expose only which structural gate rejected it.
# No source text or caller/provider-controlled value enters those sentinels.
UNCLASSIFIED_TRACEBACK_CONTEXT_TOKENS = frozenset(
    {
        UNCLASSIFIED_TRACEBACK_NO_HEADER,
        UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS,
        UNCLASSIFIED_TRACEBACK_TERMINAL_SHAPE,
        UNCLASSIFIED_TRACEBACK_MULTILINE_EXCEPTION,
    }
)
ALLOWED_TRACEBACK_ORIGINS = (
    frozenset(
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
    | ALLOWED_RISKLIB_TRACEBACK_MODULES
    | ALLOWED_RISKLIB_ASSET_TRACEBACK_TOKENS
)
PUBLIC_TRACEBACK_ORIGIN_TOKENS = (
    ALLOWED_TRACEBACK_ORIGINS
    | UNCLASSIFIED_TRACEBACK_CONTEXT_TOKENS
    | {UNCLASSIFIED_TRACEBACK_ORIGIN}
)

_TRACEBACK_HEADER = b"Traceback (most recent call last):"
_TERMINAL_CLASS_RE = re.compile(
    rb"^(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)(?::.*)?$"
)
_TRACEBACK_FRAME_RE = re.compile(
    rb'^\s*File "([^"\r\n]+)", line [1-9][0-9]*(?:, in ([A-Za-z_][A-Za-z0-9_]*|<module>))?$'
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
    if len(stderr_tail) >= MAX_STDERR_CLASSIFIER_TAIL_BYTES:
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

    # Fail closed unless this is one bounded canonical traceback segment. A Python
    # exception message may contain embedded newlines, including text that looks
    # exactly like another traceback header or frame. Multiple headers are therefore
    # ambiguous without parsing Python's full exception-chain grammar and cannot be
    # used as bounded public diagnostic evidence here.
    header_indexes = [
        index
        for index, line in enumerate(lines[:terminal_index])
        if line.strip() == _TRACEBACK_HEADER
    ]
    if len(header_indexes) != 1:
        return None
    header_index = header_indexes[0]

    terminal_raw = lines[terminal_index]
    if terminal_raw != terminal_raw.lstrip():
        return None
    if _TERMINAL_CLASS_RE.fullmatch(terminal_line) is None:
        return None

    # The first rendered exception line terminates the traceback-frame region.
    # If another class-like unindented line appears before the chosen terminal,
    # the remaining text can be a multiline exception message. Do not let any
    # frame-looking message continuation override the real final Python frame.
    for line in lines[header_index + 1 : terminal_index]:
        stripped = line.strip()
        if not stripped or line != line.lstrip() or b":" not in stripped:
            continue
        if _TERMINAL_CLASS_RE.fullmatch(stripped) is not None:
            return None

    return terminal_index, terminal_line


def _terminal_context_rejection_token(lines: list[bytes]) -> str:
    """Return only a finite structural reason for terminal-context rejection."""

    nonempty = [(index, line.strip()) for index, line in enumerate(lines) if line.strip()]
    if not nonempty:
        return UNCLASSIFIED_TRACEBACK_TERMINAL_SHAPE
    terminal_index, terminal_line = nonempty[-1]

    header_indexes = [
        index
        for index, line in enumerate(lines[:terminal_index])
        if line.strip() == _TRACEBACK_HEADER
    ]
    if not header_indexes:
        return UNCLASSIFIED_TRACEBACK_NO_HEADER
    if len(header_indexes) != 1:
        return UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS
    header_index = header_indexes[0]

    terminal_raw = lines[terminal_index]
    if terminal_raw != terminal_raw.lstrip():
        return UNCLASSIFIED_TRACEBACK_TERMINAL_SHAPE
    if _TERMINAL_CLASS_RE.fullmatch(terminal_line) is None:
        return UNCLASSIFIED_TRACEBACK_TERMINAL_SHAPE

    for line in lines[header_index + 1 : terminal_index]:
        stripped = line.strip()
        if not stripped or line != line.lstrip() or b":" not in stripped:
            continue
        if _TERMINAL_CLASS_RE.fullmatch(stripped) is not None:
            return UNCLASSIFIED_TRACEBACK_MULTILINE_EXCEPTION

    # Keep the generic fail-closed sentinel if this helper and the authoritative
    # terminal-context predicate ever disagree after a future code change.
    return UNCLASSIFIED_TRACEBACK_ORIGIN


def _final_traceback_frame(
    lines: list[bytes], terminal_index: int
) -> tuple[bytes, bytes | None] | None:
    header_indexes = [
        index
        for index, line in enumerate(lines[:terminal_index])
        if line.strip() == _TRACEBACK_HEADER
    ]
    if len(header_indexes) != 1:
        return None
    header_index = header_indexes[0]
    frame_like_lines = [
        line
        for line in lines[header_index + 1 : terminal_index]
        if line.lstrip().startswith(b'File "')
    ]
    if not frame_like_lines:
        return None
    final_frame = _TRACEBACK_FRAME_RE.fullmatch(frame_like_lines[-1])
    if final_frame is None:
        return None
    return final_frame.group(1), final_frame.group(2)


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
    """Return only the final allow-listed frozen-OQ package/module discriminator.

    Direct ``openquake.risklib`` Python frames use one of six finite module tokens.
    For the exact pinned ``openquake/risklib/asset.py`` frame only, a statically
    allow-listed function name may further refine that token. If strict terminal
    context is rejected, a finite ``unclassified.*`` structural reason may replace
    the generic sentinel. No path, line number, arbitrary function name or message
    is returned.
    """

    lines = _validated_lines(stderr_tail)
    if lines is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    context = _terminal_context(lines)
    if context is None:
        return _terminal_context_rejection_token(lines)
    terminal_index, _terminal_line = context

    frame = _final_traceback_frame(lines, terminal_index)
    if frame is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    path, function_bytes = frame

    risklib_path = _FROZEN_RISKLIB_MODULE_PATH_RE.fullmatch(path)
    if risklib_path is not None:
        try:
            module = risklib_path.group(1).decode("ascii", errors="strict")
        except UnicodeDecodeError:
            return UNCLASSIFIED_TRACEBACK_ORIGIN
        candidate = f"openquake.risklib.{module}"
        if candidate not in ALLOWED_RISKLIB_TRACEBACK_MODULES:
            return UNCLASSIFIED_TRACEBACK_ORIGIN
        if candidate == "openquake.risklib.asset" and function_bytes is not None:
            try:
                function_name = function_bytes.decode("ascii", errors="strict")
            except UnicodeDecodeError:
                return candidate
            refined = f"{candidate}.{function_name}"
            if refined in ALLOWED_RISKLIB_ASSET_TRACEBACK_TOKENS:
                return refined
        return candidate

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
