# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed normalization helpers for source-access request paths."""

from __future__ import annotations

import string
from urllib.parse import unquote

MAX_PERCENT_DECODE_PASSES = 16
_HEX_DIGITS = frozenset(string.hexdigits)


class PercentDecodeError(ValueError):
    """Raised when percent-encoding cannot be normalized safely."""


def _validate_percent_escapes(value: str) -> None:
    """Require every percent marker to be one complete ``%HH`` escape."""
    index = 0
    while index < len(value):
        if value[index] != "%":
            index += 1
            continue
        if index + 2 >= len(value) or value[index + 1] not in _HEX_DIGITS or value[index + 2] not in _HEX_DIGITS:
            raise PercentDecodeError("malformed percent escape in request path")
        index += 3


def _reject_control_characters(value: str) -> None:
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise PercentDecodeError("control character in percent-decoded request path")


def stable_percent_decode(value: str) -> str:
    """Decode nested percent-encoding to a fixed point within a hard bound.

    Every encoded layer must use strict ``%HH`` grammar. The bound prevents
    attacker-controlled nesting from turning validation into unbounded work,
    and decoded C0/DEL controls fail closed before downstream URL/request/log
    consumers can interpret them differently. Callers must apply traversal,
    URL and query checks to the fully normalized return value.
    """
    if type(value) is not str:
        raise PercentDecodeError("percent-decoded value must be text")

    current = value
    for _ in range(MAX_PERCENT_DECODE_PASSES):
        _validate_percent_escapes(current)
        decoded = unquote(current)
        _reject_control_characters(decoded)
        if decoded == current:
            return decoded
        current = decoded

    raise PercentDecodeError(
        f"percent-encoding did not converge within {MAX_PERCENT_DECODE_PASSES} passes"
    )
