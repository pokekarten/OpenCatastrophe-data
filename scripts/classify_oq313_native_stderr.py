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

from scripts import classify_oq313_multiheader_first_segment as multiheader_structure

MAX_STDERR_CLASSIFIER_TAIL_BYTES = 64 * 1024
UNCLASSIFIED_EXCEPTION_CLASS = "unclassified"
UNCLASSIFIED_TRACEBACK_ORIGIN = "unclassified"
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS = "unclassified.multiple_traceback_headers"
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_PREFIX = (
    "unclassified.multiple_traceback_headers.first_origin"
)
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_PREFIX = (
    "unclassified.multiple_traceback_headers.first_segment_frame_origin"
)
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_STRUCTURE_PREFIX = (
    "unclassified.multiple_traceback_headers.first_segment_structure"
)
UNCLASSIFIED_TRACEBACK_TERMINAL_SHAPE = "unclassified.terminal_shape"
UNCLASSIFIED_TRACEBACK_MULTILINE_EXCEPTION = "unclassified.multiline_exception"

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

UNCLASSIFIED_TRACEBACK_CONTEXT_TOKENS = frozenset(
    {
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
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_TOKENS = frozenset(
    f"{UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_PREFIX}.{origin}"
    for origin in ALLOWED_TRACEBACK_ORIGINS
)
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_TOKENS = frozenset(
    f"{UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_PREFIX}.{origin}"
    for origin in ALLOWED_TRACEBACK_ORIGINS
)
ALLOWED_MULTIHEADER_FIRST_SEGMENT_STRUCTURES = frozenset(
    {
        multiheader_structure.NO_CANONICAL_FRAME,
        multiheader_structure.MALFORMED_FRAME,
        multiheader_structure.CANONICAL_FRAME_OUTSIDE_FROZEN_OQ,
    }
)
UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_STRUCTURE_TOKENS = frozenset(
    f"{UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_STRUCTURE_PREFIX}.{token}"
    for token in ALLOWED_MULTIHEADER_FIRST_SEGMENT_STRUCTURES
)
PUBLIC_TRACEBACK_ORIGIN_TOKENS = (
    ALLOWED_TRACEBACK_ORIGINS
    | UNCLASSIFIED_TRACEBACK_CONTEXT_TOKENS
    | UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_TOKENS
    | UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_TOKENS
    | UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_STRUCTURE_TOKENS
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

    for line in lines[header_index + 1 : terminal_index]:
        stripped = line.strip()
        if not stripped or line != line.lstrip() or b":" not in stripped:
            continue
        if _TERMINAL_CLASS_RE.fullmatch(stripped) is not None:
            return None

    return terminal_index, terminal_line


def _first_traceback_origin_from_multiple_headers(lines: list[bytes]) -> str | None:
    """Return only the first real traceback origin from an ambiguous multi-header tail."""

    exact_headers = [
        index for index, line in enumerate(lines) if line == _TRACEBACK_HEADER
    ]
    if len(exact_headers) < 2:
        return None
    first_header, second_header = exact_headers[0], exact_headers[1]

    terminal_index: int | None = None
    for index in range(first_header + 1, second_header):
        line = lines[index]
        stripped = line.strip()
        if not stripped or line != line.lstrip():
            continue
        if _TERMINAL_CLASS_RE.fullmatch(stripped) is not None:
            terminal_index = index
            break
    if terminal_index is None:
        return None

    segment = b"\n".join(lines[first_header : terminal_index + 1]) + b"\n"
    origin = classify_traceback_origin(segment)
    if origin not in ALLOWED_TRACEBACK_ORIGINS:
        return None
    return origin


def _origin_from_frame(path: bytes, function_bytes: bytes | None) -> str | None:
    """Map one canonical frame to an existing finite frozen-OQ origin token."""

    risklib_path = _FROZEN_RISKLIB_MODULE_PATH_RE.fullmatch(path)
    if risklib_path is not None:
        try:
            module = risklib_path.group(1).decode("ascii", errors="strict")
        except UnicodeDecodeError:
            return None
        candidate = f"openquake.risklib.{module}"
        if candidate not in ALLOWED_RISKLIB_TRACEBACK_MODULES:
            return None
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
        return None
    try:
        package = oq_path.group(1).decode("ascii", errors="strict")
    except UnicodeDecodeError:
        return None
    candidate = f"openquake.{package}"
    if candidate not in ALLOWED_TRACEBACK_ORIGINS:
        return None
    return candidate


def _first_segment_frame_origin_from_multiple_headers(lines: list[bytes]) -> str | None:
    """Return only a labelled frame candidate from the first exact-header segment.

    This evidence is deliberately weaker than ``first_origin``. A segment without a
    terminal exception class is not promoted to a real traceback. We expose only the
    finite frozen-OQ origin of its last canonical frame before any unindented
    exception-class line, and the caller labels the token ``first_segment_frame_origin``
    so it cannot be confused with terminal/root origin or message continuation text.
    """

    exact_headers = [
        index for index, line in enumerate(lines) if line == _TRACEBACK_HEADER
    ]
    if len(exact_headers) < 2:
        return None
    first_header, second_header = exact_headers[0], exact_headers[1]

    frame_scan_end = second_header
    for index in range(first_header + 1, second_header):
        line = lines[index]
        stripped = line.strip()
        if not stripped or line != line.lstrip():
            continue
        if _TERMINAL_CLASS_RE.fullmatch(stripped) is not None:
            frame_scan_end = index
            break

    frame_like_lines = [
        line
        for line in lines[first_header + 1 : frame_scan_end]
        if line.lstrip().startswith(b'File "')
    ]
    if not frame_like_lines:
        return None
    final_frame = _TRACEBACK_FRAME_RE.fullmatch(frame_like_lines[-1])
    if final_frame is None:
        return None
    return _origin_from_frame(final_frame.group(1), final_frame.group(2))


def _first_segment_structure_from_multiple_headers(lines: list[bytes]) -> str | None:
    """Return one reviewed #751 structural token after stronger gates fail."""

    reconstructed_tail = b"\n".join(lines) + b"\n"
    structure = multiheader_structure.classify_first_segment_structure(
        reconstructed_tail
    )
    if structure not in ALLOWED_MULTIHEADER_FIRST_SEGMENT_STRUCTURES:
        return None
    candidate = (
        f"{UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_STRUCTURE_PREFIX}."
        f"{structure}"
    )
    if candidate not in UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_STRUCTURE_TOKENS:
        return None
    return candidate


def _terminal_context_rejection_token(lines: list[bytes]) -> str:
    """Return only a finite structural reason for canonical-context rejection."""

    nonempty = [
        (index, line.strip()) for index, line in enumerate(lines) if line.strip()
    ]
    if not nonempty:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    terminal_index, terminal_line = nonempty[-1]

    header_indexes = [
        index
        for index, line in enumerate(lines[:terminal_index])
        if line.strip() == _TRACEBACK_HEADER
    ]
    if not header_indexes:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    if len(header_indexes) != 1:
        first_origin = _first_traceback_origin_from_multiple_headers(lines)
        if first_origin is not None:
            return (
                f"{UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_ORIGIN_PREFIX}."
                f"{first_origin}"
            )
        first_segment_frame_origin = _first_segment_frame_origin_from_multiple_headers(lines)
        if first_segment_frame_origin is not None:
            return (
                f"{UNCLASSIFIED_TRACEBACK_MULTIPLE_HEADERS_FIRST_SEGMENT_FRAME_ORIGIN_PREFIX}."
                f"{first_segment_frame_origin}"
            )
        first_segment_structure = _first_segment_structure_from_multiple_headers(lines)
        if first_segment_structure is not None:
            return first_segment_structure
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
    """Return only a finite frozen-OQ traceback/structural-origin discriminator."""

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
    origin = _origin_from_frame(frame[0], frame[1])
    if origin is None:
        return UNCLASSIFIED_TRACEBACK_ORIGIN
    return origin
