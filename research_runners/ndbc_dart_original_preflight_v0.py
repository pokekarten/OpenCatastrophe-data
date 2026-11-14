#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed NDBC DART plain-text sample screen (never a downloader).

The operator supplies separately authorized, already acquired source bytes and an
independent station/date request identity. Hashing local bytes does NOT verify
that they originated at NDBC. No raw observation rows are emitted or persisted.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 1_048_576
MAX_ROWS = 10_000
MAX_DAYS = 7
_STATION = re.compile(r"[A-Za-z0-9]{4,8}\Z")
_HEIGHT = re.compile(r"\d+(?:\.\d+)?\Z")
_HEADER = "YYYY MM DD hh mm ss T HEIGHT (meters)"


class DARTPreflightError(ValueError):
    """Data do not satisfy this narrow local screening contract."""


def _date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise DARTPreflightError("request date must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DARTPreflightError("invalid request date") from exc


def preflight(path: Path, *, station: str, start: str, end: str) -> dict:
    """Validate a small local NDBC-format body, returning aggregate-only evidence."""
    if not _STATION.fullmatch(station):
        raise DARTPreflightError("invalid station identity")
    start_day, end_day = _date(start), _date(end)
    if not start_day <= end_day or (end_day - start_day).days > MAX_DAYS:
        raise DARTPreflightError("request window invalid or exceeds seven days")
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise DARTPreflightError("input must be a regular non-symlink local file")
    byte_count = path.stat().st_size
    if not 0 < byte_count <= MAX_BYTES:
        raise DARTPreflightError("local response outside byte limit")
    raw = path.read_bytes()
    if len(raw) != byte_count:
        raise DARTPreflightError("input changed during read")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        body = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise DARTPreflightError("non-ASCII or binary response") from exc
    if "\x00" in body or "<" in body or ">" in body:
        raise DARTPreflightError("HTML, markup or binary contamination")
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    expected = [f"station {station}", f"start {start}", f"end {end}", _HEADER]
    if len(lines) < 5 or lines[:4] != expected:
        raise DARTPreflightError("NDBC response header/request identity mismatch")
    if len(lines) - 4 > MAX_ROWS:
        raise DARTPreflightError("too many observations")
    counts: Counter[str] = Counter()
    seen: set[tuple[datetime, str]] = set()
    newest: datetime | None = None
    oldest: datetime | None = None
    previous: datetime | None = None
    minimum: float | None = None
    maximum: float | None = None
    gaps: list[float] = []
    for line in lines[4:]:
        fields = line.split()
        if len(fields) != 8 or not all(re.fullmatch(r"\d{2,4}", f) for f in fields[:6]):
            raise DARTPreflightError("invalid observation row layout")
        if fields[6] not in ("1", "2", "3") or not _HEIGHT.fullmatch(fields[7]):
            raise DARTPreflightError("invalid measurement type or height")
        try:
            stamp = datetime(*(int(x) for x in fields[:6]), tzinfo=timezone.utc)
        except ValueError as exc:
            raise DARTPreflightError("invalid observation timestamp") from exc
        if not start_day <= stamp.date() <= end_day:
            raise DARTPreflightError("observation outside request date window")
        key = (stamp, fields[6])
        if key in seen:
            raise DARTPreflightError("duplicate observation timestamp and type")
        seen.add(key)
        if previous is not None:
            if stamp > previous:
                raise DARTPreflightError("timestamps not descending")
            gaps.append((previous - stamp).total_seconds())
        newest = newest or stamp
        oldest = stamp
        previous = stamp
        height = float(fields[7])
        if height > 12_000:
            raise DARTPreflightError("implausible water-column height")
        minimum = height if minimum is None else min(minimum, height)
        maximum = height if maximum is None else max(maximum, height)
        counts[fields[6]] += 1
    if not seen:
        raise DARTPreflightError("no observations")
    return {
        "profile": "noaa-ndbc-dart-original-format-screen-v0",
        "source_id": "noaa.ndbc.dart",
        "station": station,
        "requested_start_utc_date": start,
        "requested_end_utc_date": end,
        "input_bytes": byte_count,
        "input_sha256": digest,
        "observations": len(seen),
        "count_by_type": {k: counts[k] for k in ("1", "2", "3")},
        "newest_utc": newest.isoformat(),
        "oldest_utc": oldest.isoformat(),
        "minimum_water_column_m": minimum,
        "maximum_water_column_m": maximum,
        "largest_observed_gap_seconds": max(gaps, default=None),
        "response_format_checked": True,
        "original_provider_provenance_verified": False,
        "station_deployment_and_qc_verified": False,
        "dataset_and_service_rights_verified": False,
        "scientific_completeness_verified": False,
        "raw_observation_rows_exported": False,
        "source_bytes_persisted_by_script": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, required=True, help="local acquired file; no network access")
    ap.add_argument("--station", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args(argv)
    try:
        receipt = preflight(args.file, station=args.station, start=args.start, end=args.end)
    except (DARTPreflightError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
