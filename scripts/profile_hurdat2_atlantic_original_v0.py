# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Strict, offline structural receipt for *original* Atlantic HURDAT2 text.

No downloading, repairing malformed provider rows, admission or model use.
The input must remain in authorized external storage. Synthetic fixtures only
belong in Git. This preflight is deliberately not a storm-footprint generator.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

SOURCE_ID = "us.noaa.nhc.hurdat2.atlantic.2026-09"
MAX_ORIGINAL_BYTES = 12 * 1024 * 1024
HEADER = re.compile(r"AL[0-9]{2}[0-9]{4}")
HEMISPHERE = re.compile(r"([0-9]+(?:\.[0-9]+)?)([NSEW])")
STATUSES = frozenset({"TD", "TS", "HU", "EX", "SD", "SS", "LO", "WV", "DB"})
MARKERS = frozenset({"", "C", "G", "I", "L", "P", "R", "S", "T", "W"})


class Hurdat2StructureError(ValueError):
    """A byte-identifiable original does not satisfy the syntax preflight."""


def _fields(line: str) -> list[str]:
    values = [piece.strip() for piece in line.split(",")]
    if values and values[-1] == "":
        values.pop()  # NHC commonly ends rows with one trailing comma.
    return values


def _coordinate(raw: str, axis: str, line: int) -> float:
    match = HEMISPHERE.fullmatch(raw)
    if not match or match.group(2) not in ("NS" if axis == "latitude" else "EW"):
        raise Hurdat2StructureError(f"line {line}: invalid {axis} hemisphere")
    value = float(match.group(1))
    if value > (90 if axis == "latitude" else 180):
        raise Hurdat2StructureError(f"line {line}: {axis} out of bounds; do not silently wrap")
    return -value if match.group(2) in "SW" else value


def _measurement(raw: str, line: int, name: str) -> int | None:
    if not re.fullmatch(r"-?[0-9]+", raw):
        raise Hurdat2StructureError(f"line {line}: invalid {name}")
    value = int(raw)
    if value in {-999, -99}:
        return None
    if value < 0:
        raise Hurdat2StructureError(f"line {line}: negative {name}")
    return value


def profile_original(raw: bytes) -> dict[str, object]:
    """Compute an original-byte receipt and check record syntax, not science."""
    if type(raw) is not bytes or not raw or len(raw) > MAX_ORIGINAL_BYTES:
        raise Hurdat2StructureError("original must be nonempty bytes within the 12 MiB cap")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise Hurdat2StructureError("HURDAT2 original must be ASCII text") from exc
    lines = text.splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise Hurdat2StructureError("blank lines are not valid HURDAT2 records")
    storm_ids: set[str] = set()
    storms = fixes = 0
    min_time = max_time = None
    index = 0
    while index < len(lines):
        line = index + 1
        fields = _fields(lines[index])
        if len(fields) != 3 or not HEADER.fullmatch(fields[0]):
            raise Hurdat2StructureError(f"line {line}: invalid Atlantic storm header")
        storm_id, name, count_raw = fields
        if not re.fullmatch(r"[A-Z0-9 -]{1,30}", name):
            raise Hurdat2StructureError(f"line {line}: invalid storm name")
        if storm_id in storm_ids:
            raise Hurdat2StructureError(f"line {line}: duplicate storm id {storm_id}")
        storm_ids.add(storm_id)
        if not re.fullmatch(r"[1-9][0-9]*", count_raw):
            raise Hurdat2StructureError(f"line {line}: invalid positive track count")
        count = int(count_raw)
        if count > len(lines) - index - 1:
            raise Hurdat2StructureError(f"line {line}: truncated storm track")
        previous = None
        year = int(storm_id[-4:])
        for offset in range(count):
            position = index + offset + 1
            data_line = position + 1
            data = _fields(lines[position])
            if len(data) not in {20, 21}:
                raise Hurdat2StructureError(f"line {data_line}: expected 20 or 21 fix fields")
            try:
                stamp = datetime.strptime(data[0] + data[1], "%Y%m%d%H%M")
            except ValueError as exc:
                raise Hurdat2StructureError(f"line {data_line}: invalid UTC datetime") from exc
            if stamp.year not in {year, year + 1}:
                raise Hurdat2StructureError(f"line {data_line}: year mismatches storm id")
            if previous is not None and stamp <= previous:
                raise Hurdat2StructureError(f"line {data_line}: duplicate/out-of-order fix time")
            previous = stamp
            if data[2] not in MARKERS or data[3] not in STATUSES:
                raise Hurdat2StructureError(f"line {data_line}: unknown marker or storm status")
            if (stamp.hour % 6 != 0 or stamp.minute != 0) and not data[2]:
                raise Hurdat2StructureError(f"line {data_line}: non-synoptic fix requires a marker")
            _coordinate(data[4], "latitude", data_line)
            _coordinate(data[5], "longitude", data_line)
            for pos, field in enumerate(data[6:], start=6):
                _measurement(field, data_line, f"column {pos + 1}")
            fixes += 1
            min_time = stamp if min_time is None else min(min_time, stamp)
            max_time = stamp if max_time is None else max(max_time, stamp)
        storms += 1
        index += count + 1
    return {
        "source_id": SOURCE_ID,
        "original_sha256": hashlib.sha256(raw).hexdigest(),
        "original_bytes": len(raw),
        "storm_count": storms,
        "track_fix_count": fixes,
        "first_fix_utc": min_time.replace(tzinfo=timezone.utc).isoformat(),
        "last_fix_utc": max_time.replace(tzinfo=timezone.utc).isoformat(),
        "verification": "syntactic_preflight_only_no_scientific_or_rights_admission",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="authorized external original HURDAT2 file")
    args = parser.parse_args()
    if args.input.stat().st_size > MAX_ORIGINAL_BYTES:
        parser.error("input exceeds 12 MiB")
    try:
        profile = profile_original(args.input.read_bytes())
    except (Hurdat2StructureError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(profile, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
