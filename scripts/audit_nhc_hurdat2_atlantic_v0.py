# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline HURDAT2 Atlantic 2026-09 structural science preflight.

No network, no provider permissions, no CAT admission. Input provenance and
original-provider identity must be independently established before use.
Official format: https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-atl-1851-2021.pdf
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

SOURCE_ID = "us.noaa.nhc.hurdat2.atlantic.2026-09"
MAX_BYTES = 16 * 1024 * 1024
MAX_STORMS = 3000
MAX_TRACKS = 2000
STORM_RE = re.compile(r"AL\d{2}(?:18|19|20)\d{2}\Z")
COORD_RE = re.compile(r"(\d+(?:\.\d+)?)([NSEW])\Z")
VALID_STATUS = frozenset({"TD", "TS", "HU", "EX", "SD", "SS", "LO", "WV", "DB"})
VALID_RECORD_ID = frozenset({"", "C", "G", "I", "L", "P", "R", "S", "T", "W"})


class HURDAT2PreflightError(ValueError):
    """File violates the documented Atlantic HURDAT2 structural contract."""


def _int(value: str, label: str, line: int) -> int:
    if not re.fullmatch(r"-?\d+", value):
        raise HURDAT2PreflightError(f"line {line}: malformed {label}")
    return int(value)


def _coord(value: str, axis: str, line: int) -> float:
    match = COORD_RE.fullmatch(value)
    if not match or match.group(2) not in ("NS" if axis == "lat" else "EW"):
        raise HURDAT2PreflightError(f"line {line}: malformed {axis}")
    magnitude = float(match.group(1))
    limit = 90 if axis == "lat" else 180
    if not 0 <= magnitude <= limit:
        raise HURDAT2PreflightError(f"line {line}: out-of-range {axis}")
    return -magnitude if match.group(2) in "SW" else magnitude


def _bounded_number(value: str, label: str, line: int, missing: int, low: int, high: int) -> bool:
    number = _int(value, label, line)
    if number == missing:
        return True
    if not low <= number <= high:
        raise HURDAT2PreflightError(f"line {line}: out-of-range {label}")
    return False


def audit_bytes(raw: bytes) -> dict[str, object]:
    """Validate exact supplied bytes; never infer that they came from NOAA."""
    if not raw or len(raw) > MAX_BYTES or b"\x00" in raw:
        raise HURDAT2PreflightError("empty, oversized or binary input")
    try:
        content = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise HURDAT2PreflightError("non-ASCII input") from exc
    lines = content.splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise HURDAT2PreflightError("empty line in source records")
    rows = [[cell.strip() for cell in row] for row in csv.reader(lines, strict=True)]
    storms = 0
    tracks = 0
    missing_wind = 0
    missing_pressure = 0
    missing_wind_radii = 0
    missing_rmw = 0
    asynoptic = 0
    seen_ids: set[str] = set()
    i = 0
    while i < len(rows):
        header = rows[i]
        if len(header) != 4 or header[-1] != "" or not STORM_RE.fullmatch(header[0]):
            raise HURDAT2PreflightError(f"line {i + 1}: invalid Atlantic storm header")
        storm_id, name = header[:2]
        count = _int(header[2], "track count", i + 1)
        if not name or not 1 <= count <= MAX_TRACKS or storm_id in seen_ids:
            raise HURDAT2PreflightError(f"line {i + 1}: invalid storm identity/count")
        seen_ids.add(storm_id)
        storms += 1
        if storms > MAX_STORMS or len(rows) - i - 1 < count:
            raise HURDAT2PreflightError(f"line {i + 1}: overflow or truncated storm")
        previous: datetime | None = None
        for position in range(i + 1, i + 1 + count):
            row = rows[position]
            line = position + 1
            # Modern Atlantic HURDAT2 has 12 quadrant radii plus RMW.
            if len(row) != 21:
                raise HURDAT2PreflightError(f"line {line}: expected 21 track columns")
            date, hhmm, marker, status, lat, lon = row[:6]
            if not re.fullmatch(r"\d{8}", date) or not re.fullmatch(r"\d{4}", hhmm):
                raise HURDAT2PreflightError(f"line {line}: invalid date/time text")
            try:
                stamp = datetime.strptime(date + hhmm, "%Y%m%d%H%M")
            except ValueError as exc:
                raise HURDAT2PreflightError(f"line {line}: invalid UTC timestamp") from exc
            if previous is not None and stamp <= previous:
                raise HURDAT2PreflightError(f"line {line}: non-increasing UTC timestamp")
            previous = stamp
            if marker not in VALID_RECORD_ID or status not in VALID_STATUS:
                raise HURDAT2PreflightError(f"line {line}: invalid record marker/status")
            _coord(lat, "lat", line)
            _coord(lon, "lon", line)
            missing_wind += _bounded_number(row[6], "1-min wind knots", line, -99, 0, 300)
            missing_pressure += _bounded_number(row[7], "pressure hPa", line, -999, 650, 1150)
            for col in row[8:20]:
                missing_wind_radii += _bounded_number(col, "wind radius nautical miles", line, -999, 0, 3000)
            missing_rmw += _bounded_number(row[20], "RMW nautical miles", line, -999, 0, 3000)
            asynoptic += hhmm not in ("0000", "0600", "1200", "1800")
        tracks += count
        i += count + 1
    if not storms or not tracks:
        raise HURDAT2PreflightError("no records")
    return {
        "source_id": SOURCE_ID,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_bytes": len(raw),
        "storms": storms,
        "tracks": tracks,
        "asynoptic_tracks": asynoptic,
        "missing_wind": missing_wind,
        "missing_pressure": missing_pressure,
        "missing_wind_radii": missing_wind_radii,
        "missing_rmw": missing_rmw,
        "input_provider_provenance": "not_verified",
        "sample_storage": "not_verified",
        "model_admission": "not_admitted",
    }


def audit_path(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return audit_bytes(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_file", type=Path, help="local already-authorized original file outside Git")
    args = parser.parse_args()
    try:
        print(json.dumps(audit_path(args.source_file), sort_keys=True))
    except (OSError, HURDAT2PreflightError) as exc:
        parser.exit(status=2, message=f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
