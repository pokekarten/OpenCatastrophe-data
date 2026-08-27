# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Classify only the structure of the first segment in ambiguous OQ3.13 stderr.

This helper is diagnostic-only. It never returns a path, function, line, message,
provider value, or arbitrary package name.
"""

from __future__ import annotations

import re

MAX_TAIL_BYTES = 64 * 1024
NO_CANONICAL_FRAME = "no_canonical_frame"
MALFORMED_FRAME = "malformed_frame"
CANONICAL_FRAME_OUTSIDE_FROZEN_OQ = "canonical_frame_outside_frozen_oq"
UNCLASSIFIED = "unclassified"
PUBLIC_TOKENS = frozenset(
    {NO_CANONICAL_FRAME, MALFORMED_FRAME, CANONICAL_FRAME_OUTSIDE_FROZEN_OQ, UNCLASSIFIED}
)

_TRACEBACK_HEADER = b"Traceback (most recent call last):"
_FRAME_LIKE = b'File "'
_FRAME_RE = re.compile(
    rb'^\s*File "([^"\r\n]+)", line [1-9][0-9]*(?:, in ([A-Za-z_][A-Za-z0-9_]*|<module>))?$'
)
_FROZEN_OQ_PATH_RE = re.compile(
    rb"^/oq-engine/openquake/[A-Za-z_][A-Za-z0-9_]*/[^\r\n]+$"
)
_TERMINAL_CLASS_RE = re.compile(
    rb"^(?:[A-Za-z_][A-Za-z0-9_]*\.)*[A-Za-z_][A-Za-z0-9_]*(?::.*)?$"
)


def classify_first_segment_structure(stderr_tail: bytes) -> str:
    """Return one finite structural token for a multi-header first segment."""

    if type(stderr_tail) is not bytes or len(stderr_tail) >= MAX_TAIL_BYTES:
        return UNCLASSIFIED
    try:
        stderr_tail.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return UNCLASSIFIED

    lines = stderr_tail.splitlines()
    headers = [index for index, line in enumerate(lines) if line == _TRACEBACK_HEADER]
    if len(headers) < 2:
        return UNCLASSIFIED
    first_header, second_header = headers[0], headers[1]

    scan_end = second_header
    for index in range(first_header + 1, second_header):
        line = lines[index]
        stripped = line.strip()
        if not stripped or line != line.lstrip():
            continue
        if _TERMINAL_CLASS_RE.fullmatch(stripped) is not None:
            scan_end = index
            break

    frame_like = [
        line
        for line in lines[first_header + 1 : scan_end]
        if line.lstrip().startswith(_FRAME_LIKE)
    ]
    if not frame_like:
        return NO_CANONICAL_FRAME

    final_frame = _FRAME_RE.fullmatch(frame_like[-1])
    if final_frame is None:
        return MALFORMED_FRAME
    if _FROZEN_OQ_PATH_RE.fullmatch(final_frame.group(1)) is None:
        return CANONICAL_FRAME_OUTSIDE_FROZEN_OQ

    # Existing stronger classifiers own allow-listed frozen-OQ origins. This
    # helper intentionally refuses to duplicate or widen that authority.
    return UNCLASSIFIED
