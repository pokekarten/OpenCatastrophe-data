# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Parse PEGELONLINE long-term JSON without inspecting values for tuning.

The selected Dresden acquisition path is the provider's long-term JSON format:
each record contains an ISO-8601 timestamp with an explicit local legal-time
offset plus one raw discharge value. This module validates that provider shape,
converts timestamps to UTC using the explicit source offset, freezes the known
15-minute Dresden source grid, and exposes only deterministic UTC observations
to the existing holdout pairing layer.

The CLI prints summary metadata only. It never echoes target discharge values,
so validation logs do not become an accidental public copy of external data.
Exact file identity remains the responsibility of the acquisition-evidence
layer; parsing does not grant publication rights or admission.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, NamedTuple

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hydrology_window import (
    DRESDEN_HOLDOUT_EXPECTED_DAYS,
    DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE,
    DRESDEN_HOLDOUT_WINDOW_START_UTC,
    pegelonline_long_term_json_time_to_utc,
)

UTC = timezone.utc
DRESDEN_SAMPLING_INTERVAL_SECONDS = 15 * 60
EXPECTED_HOLDOUT_GRID_SLOTS = DRESDEN_HOLDOUT_EXPECTED_DAYS * (
    24 * 60 * 60 // DRESDEN_SAMPLING_INTERVAL_SECONDS
)
EPOCH_UTC = datetime(1970, 1, 1, tzinfo=UTC)


class PegelonlineLongTermJsonError(ValueError):
    """Raised when a long-term PEGELONLINE JSON file fails closed."""


class ParsedObservation(NamedTuple):
    timestamp_utc: datetime
    discharge_m3s: float


def _reject_constant(value: str) -> None:
    raise PegelonlineLongTermJsonError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PegelonlineLongTermJsonError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_long_term_json_bytes(raw: bytes) -> list[Any]:
    """Load provider JSON while rejecting duplicate keys and non-finite numbers."""

    if type(raw) is not bytes or not raw:
        raise PegelonlineLongTermJsonError("provider response must be non-empty bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PegelonlineLongTermJsonError("provider response must be valid UTF-8") from exc
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except PegelonlineLongTermJsonError:
        raise
    except json.JSONDecodeError as exc:
        raise PegelonlineLongTermJsonError(f"provider response is not valid JSON: {exc}") from exc
    if type(payload) is not list:
        raise PegelonlineLongTermJsonError("provider JSON root must be an array")
    return payload


def _finite_discharge(value: Any, where: str) -> float:
    if type(value) not in {int, float}:
        raise PegelonlineLongTermJsonError(f"{where} must be numeric and not boolean")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise PegelonlineLongTermJsonError(f"{where} cannot be represented safely") from exc
    if not math.isfinite(numeric):
        raise PegelonlineLongTermJsonError(f"{where} must be finite")
    return numeric


def _require_dresden_grid(timestamp_utc: datetime, where: str) -> None:
    delta = timestamp_utc - EPOCH_UTC
    seconds = delta.days * 24 * 60 * 60 + delta.seconds
    if seconds % DRESDEN_SAMPLING_INTERVAL_SECONDS != 0:
        raise PegelonlineLongTermJsonError(
            f"{where} is off the frozen 15-minute Dresden sampling grid"
        )


def parse_long_term_json_bytes(raw: bytes) -> tuple[ParsedObservation, ...]:
    """Return unique, chronologically sorted UTC discharge observations."""

    payload = load_long_term_json_bytes(raw)
    observations: list[ParsedObservation] = []
    seen_utc: set[datetime] = set()

    for index, record in enumerate(payload):
        where = f"records[{index}]"
        if type(record) is not dict:
            raise PegelonlineLongTermJsonError(f"{where} must be an object")
        if set(record) != {"timestamp", "value"}:
            raise PegelonlineLongTermJsonError(
                f"{where} must contain exactly timestamp and value"
            )
        timestamp_raw = record["timestamp"]
        if type(timestamp_raw) is not str:
            raise PegelonlineLongTermJsonError(f"{where}.timestamp must be a string")
        try:
            timestamp_utc = pegelonline_long_term_json_time_to_utc(timestamp_raw)
        except ValueError as exc:
            raise PegelonlineLongTermJsonError(f"{where}.timestamp: {exc}") from exc
        _require_dresden_grid(timestamp_utc, f"{where}.timestamp")
        if timestamp_utc in seen_utc:
            raise PegelonlineLongTermJsonError(
                f"duplicate UTC observation timestamp: {timestamp_utc.isoformat()}"
            )
        seen_utc.add(timestamp_utc)
        observations.append(
            ParsedObservation(
                timestamp_utc=timestamp_utc,
                discharge_m3s=_finite_discharge(record["value"], f"{where}.value"),
            )
        )

    observations.sort(key=lambda observation: observation.timestamp_utc)
    return tuple(observations)


def dresden_holdout_observations(
    observations: Iterable[ParsedObservation],
) -> tuple[ParsedObservation, ...]:
    """Trim already parsed observations to the immutable physical UTC holdout."""

    selected: list[ParsedObservation] = []
    previous: datetime | None = None
    for index, observation in enumerate(observations):
        if type(observation) is not ParsedObservation:
            raise PegelonlineLongTermJsonError(
                f"observations[{index}] must be a ParsedObservation"
            )
        if previous is not None and observation.timestamp_utc <= previous:
            raise PegelonlineLongTermJsonError(
                "parsed observations must be strictly increasing in UTC"
            )
        previous = observation.timestamp_utc
        if (
            DRESDEN_HOLDOUT_WINDOW_START_UTC
            <= observation.timestamp_utc
            < DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE
        ):
            selected.append(observation)
    return tuple(selected)


def validation_summary(observations: tuple[ParsedObservation, ...]) -> dict[str, Any]:
    """Return value-free metadata suitable for CLI logs and acquisition review."""

    holdout = dresden_holdout_observations(observations)
    summary: dict[str, Any] = {
        "profile": "pegelonline-long-term-json-validation-v1",
        "source_observation_count": len(observations),
        "holdout_present_grid_slots": len(holdout),
        "holdout_expected_grid_slots": EXPECTED_HOLDOUT_GRID_SLOTS,
        "holdout_missing_grid_slots": EXPECTED_HOLDOUT_GRID_SLOTS - len(holdout),
        "holdout_start_utc": DRESDEN_HOLDOUT_WINDOW_START_UTC.isoformat(),
        "holdout_end_utc_exclusive": DRESDEN_HOLDOUT_WINDOW_END_UTC_EXCLUSIVE.isoformat(),
    }
    if observations:
        summary["source_first_utc"] = observations[0].timestamp_utc.isoformat()
        summary["source_last_utc"] = observations[-1].timestamp_utc.isoformat()
    if holdout:
        summary["holdout_first_present_utc"] = holdout[0].timestamp_utc.isoformat()
        summary["holdout_last_present_utc"] = holdout[-1].timestamp_utc.isoformat()
    return summary


def canonical_summary_bytes(summary: dict[str, Any]) -> bytes:
    try:
        return json.dumps(
            summary,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PegelonlineLongTermJsonError(f"summary is not canonical JSON data: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a saved PEGELONLINE Dresden long-term JSON file and print value-free UTC/grid summary metadata."
        )
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.path.read_bytes()
        observations = parse_long_term_json_bytes(raw)
        summary = validation_summary(observations)
    except (OSError, PegelonlineLongTermJsonError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(canonical_summary_bytes(summary) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
