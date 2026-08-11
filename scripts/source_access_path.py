# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed normalization helpers for source-access request paths."""

from __future__ import annotations

from urllib.parse import unquote

MAX_PERCENT_DECODE_PASSES = 16


class PercentDecodeError(ValueError):
    """Raised when nested percent-encoding does not converge safely."""


def stable_percent_decode(value: str) -> str:
    """Decode nested percent-encoding to a fixed point within a hard bound.

    The bound prevents attacker-controlled nesting from turning validation into
    unbounded work. Callers must apply traversal/URL/query checks to the fully
    normalized return value.
    """
    if type(value) is not str:
        raise PercentDecodeError("percent-decoded value must be text")

    current = value
    for _ in range(MAX_PERCENT_DECODE_PASSES):
        decoded = unquote(current)
        if decoded == current:
            return decoded
        current = decoded

    raise PercentDecodeError(
        f"percent-encoding did not converge within {MAX_PERCENT_DECODE_PASSES} passes"
    )
