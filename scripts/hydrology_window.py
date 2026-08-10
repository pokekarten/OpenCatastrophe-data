# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed time/completeness primitives for the Dresden hydrology holdout.

This module implements only preregistered rules that are independent of the
retrieved target values:

- PEGELONLINE timestamps are interpreted as year-round Central European
  standard time (fixed UTC+01:00), never as a daylight-saving timezone;
- the source sampling interval is supplied explicitly by the caller after it
  has been frozen from source metadata;
- a 24-hour comparison window is valid only when at least 90% of its expected
  source observations are present and finite;
- duplicate, off-grid or out-of-window timestamps fail closed.

It deliberately does not choose the GloFAS 24-hour timestamp convention,
aggregate discharge, interpolate missing values or compute skill metrics.
Those steps remain blocked until the retrieved artifact metadata identifies
the comparison window unambiguously.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Iterable, NamedTuple

SECONDS_PER_DAY = 24 * 60 * 60
PEGELONLINE_STANDARD_OFFSET = timezone(timedelta(hours=1))
UTC = timezone.utc


class HydrologyWindowError(ValueError):
    """Raised when a hydrology comparison-window contract fails closed."""


class WindowCompleteness(NamedTuple):
    expected_count: int
    present_count: int
    finite_count: int
    required_finite_count: int
    finite_fraction: float
    valid: bool


def pegelonline_standard_time_to_utc(value: str) -> datetime:
    """Interpret a PEGELONLINE local timestamp as fixed CET (UTC+01:00)."""

    if type(value) is not str or not value.strip():
        raise HydrologyWindowError("PEGELONLINE timestamp must be a non-empty string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HydrologyWindowError("PEGELONLINE timestamp must be ISO-8601 local time") from exc
    if parsed.tzinfo is not None or parsed.utcoffset() is not None:
        raise HydrologyWindowError(
            "PEGELONLINE source timestamp must be timezone-naive before fixed CET conversion"
        )
    return parsed.replace(tzinfo=PEGELONLINE_STANDARD_OFFSET).astimezone(UTC)


def expected_observations_per_24h(sampling_interval_seconds: int) -> int:
    """Return the exact number of source slots in one 24-hour comparison window."""

    if type(sampling_interval_seconds) is not int or sampling_interval_seconds <= 0:
        raise HydrologyWindowError("sampling_interval_seconds must be a positive integer")
    if SECONDS_PER_DAY % sampling_interval_seconds != 0:
        raise HydrologyWindowError(
            "sampling interval must divide the 24-hour comparison window exactly"
        )
    return SECONDS_PER_DAY // sampling_interval_seconds


def assess_source_window(
    observations: Iterable[tuple[datetime, float | int]],
    *,
    window_start_utc: datetime,
    sampling_interval_seconds: int,
) -> WindowCompleteness:
    """Assess the preregistered 90% source-observation completeness rule.

    ``window_start_utc`` identifies the start of the already-established
    GloFAS-aligned 24-hour interval. This function does not infer, shift or
    search for that boundary.
    """

    if not isinstance(window_start_utc, datetime):
        raise HydrologyWindowError("window_start_utc must be a datetime")
    if window_start_utc.tzinfo is None or window_start_utc.utcoffset() != timedelta(0):
        raise HydrologyWindowError("window_start_utc must be timezone-aware UTC")
    if window_start_utc.microsecond != 0:
        raise HydrologyWindowError("window_start_utc must be aligned to whole seconds")

    expected_count = expected_observations_per_24h(sampling_interval_seconds)
    window_end_utc = window_start_utc + timedelta(days=1)
    seen: set[datetime] = set()
    finite_count = 0

    try:
        iterator = iter(observations)
    except TypeError as exc:
        raise HydrologyWindowError("observations must be an iterable of timestamp/value pairs") from exc

    for index, item in enumerate(iterator):
        if type(item) not in {tuple, list} or len(item) != 2:
            raise HydrologyWindowError(
                f"observations[{index}] must be a two-item timestamp/value pair"
            )
        timestamp, value = item
        if not isinstance(timestamp, datetime):
            raise HydrologyWindowError(f"observations[{index}] timestamp must be a datetime")
        if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
            raise HydrologyWindowError(f"observations[{index}] timestamp must be timezone-aware UTC")
        if timestamp.microsecond != 0:
            raise HydrologyWindowError(f"observations[{index}] timestamp must use whole seconds")
        if timestamp < window_start_utc or timestamp >= window_end_utc:
            raise HydrologyWindowError(f"observations[{index}] timestamp is outside the 24-hour window")
        delta = timestamp - window_start_utc
        delta_seconds = delta.days * SECONDS_PER_DAY + delta.seconds
        if delta_seconds % sampling_interval_seconds != 0:
            raise HydrologyWindowError(f"observations[{index}] timestamp is off the frozen sampling grid")
        if timestamp in seen:
            raise HydrologyWindowError(f"duplicate source timestamp: {timestamp.isoformat()}")
        seen.add(timestamp)

        if type(value) not in {int, float}:
            raise HydrologyWindowError(f"observations[{index}] value must be numeric and not boolean")
        try:
            numeric = float(value)
        except OverflowError as exc:
            raise HydrologyWindowError(f"observations[{index}] value cannot be represented safely") from exc
        if math.isfinite(numeric):
            finite_count += 1

    present_count = len(seen)
    required_finite_count = (9 * expected_count + 9) // 10
    finite_fraction = finite_count / expected_count
    return WindowCompleteness(
        expected_count=expected_count,
        present_count=present_count,
        finite_count=finite_count,
        required_finite_count=required_finite_count,
        finite_fraction=finite_fraction,
        valid=finite_count >= required_finite_count,
    )
