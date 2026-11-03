# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed original-byte CSV QC for Europe's 2026 sparse wind event index.

The single exact upstream file is publicly identified by its record, key,
published MD5, read-only verified SHA-256 and byte size. This script is an
offline preflight, not source admission or permission for CAT loss modelling.
No original observations or event-row outputs are committed or printed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any

ZENODO_RECORD_ID = 22080546
FILE_KEY = "hazardinfows.csv"
SIZE_BYTES = 32210
PUBLISHER_MD5 = "e58a511d83da230931b57cb9822d8841"
VERIFIED_SHA256 = "35f10da966ad8b6f0bc5fd9dba904bb8251ae11a9f52fe7e10f4f6ff9e2bf787"
EXPECTED_EVENT_COUNT = 234
EXPECTED_HEADER = [
    "hazardtype", "groupname", "start_date", "end_date",
    "minlon", "maxlon", "minlat", "maxlat", "intensity", "intensity unit",
]
EXPECTED_UNIT = "Mean wind speed (m/s)"


class WindEventPreflightError(ValueError):
    """Original byte identity, event row, unit or geometry is invalid."""


def parse_wind_events(raw: bytes) -> dict[str, Any]:
    try:
        decoded = raw.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise WindEventPreflightError(f"invalid UTF-8/CSV input: {exc}") from exc
    if not rows or rows[0] != EXPECTED_HEADER:
        raise WindEventPreflightError("wind source header mismatch")
    if len(rows) <= 1:
        raise WindEventPreflightError("empty wind event list")

    seen: set[str] = set()
    start_dates: list[date] = []
    end_dates: list[date] = []
    for line, row in enumerate(rows[1:], start=2):
        if len(row) != len(EXPECTED_HEADER):
            raise WindEventPreflightError(f"line {line}: wrong column count")
        hazard, event_id, start, end, minlon, maxlon, minlat, maxlat, intensity, unit = row
        if hazard != "ws" or not re.fullmatch(r"ws[0-9]+", event_id):
            raise WindEventPreflightError(f"line {line}: source hazard/event ID invalid")
        if event_id in seen:
            raise WindEventPreflightError(f"line {line}: duplicate event ID")
        seen.add(event_id)
        if unit != EXPECTED_UNIT:
            raise WindEventPreflightError(f"line {line}: unit is not mean wind speed in m/s")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", start) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", end):
            raise WindEventPreflightError(f"line {line}: non-ISO date")
        try:
            begin, finish = date.fromisoformat(start), date.fromisoformat(end)
        except ValueError as exc:
            raise WindEventPreflightError(f"line {line}: impossible date") from exc
        if begin > finish:
            raise WindEventPreflightError(f"line {line}: reversed event dates")
        start_dates.append(begin)
        end_dates.append(finish)
        try:
            west, east, south, north, speed = map(
                float, (minlon, maxlon, minlat, maxlat, intensity)
            )
        except ValueError as exc:
            raise WindEventPreflightError(f"line {line}: non-numeric intensity or geometry") from exc
        if not all(map(math.isfinite, (west, east, south, north, speed))):
            raise WindEventPreflightError(f"line {line}: non-finite numerical field")
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise WindEventPreflightError(f"line {line}: invalid event bounding box")
        if speed <= 0:
            raise WindEventPreflightError(f"line {line}: non-positive mean wind speed")

    return {
        "event_count": len(seen),
        "unique_event_ids": len(seen),
        "first_event_start": min(start_dates).isoformat(),
        "last_event_end": max(end_dates).isoformat(),
        "mean_wind_speed_unit": EXPECTED_UNIT,
        "source_event_not_loss": True,
    }


def audit_original_file(path: Path) -> dict[str, Any]:
    try:
        if not path.is_file() or path.stat().st_size != SIZE_BYTES:
            raise WindEventPreflightError("original byte-size/version mismatch")
        raw = path.read_bytes()
    except OSError as exc:
        raise WindEventPreflightError(f"cannot read original CSV: {exc}") from exc
    if hashlib.sha256(raw).hexdigest() != VERIFIED_SHA256:
        raise WindEventPreflightError("original source SHA-256 mismatch")
    if hashlib.md5(raw).hexdigest() != PUBLISHER_MD5:
        raise WindEventPreflightError("original publisher MD5 mismatch")
    stats = parse_wind_events(raw)
    if stats["event_count"] != EXPECTED_EVENT_COUNT:
        raise WindEventPreflightError("source event-count/version mismatch")
    if stats["first_event_start"] != "2015-01-08" or stats["last_event_end"] != "2025-01-01":
        raise WindEventPreflightError("original event temporal-window mismatch")
    return {
        "zenodo_record_id": ZENODO_RECORD_ID,
        "original_file_key": FILE_KEY,
        "original_size_bytes": SIZE_BYTES,
        "original_sha256_verified": VERIFIED_SHA256,
        "publisher_md5_recomputed": PUBLISHER_MD5,
        "scientific_unit_warning": "mean wind speed is NOT peak wind gust",
        **stats,
        "raw_source_bytes_committed": False,
        "rights_and_science_admitted": False,
        "model_input_approved": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", required=True, type=Path, help="local original CSV file only")
    args = ap.parse_args()
    try:
        report = audit_original_file(args.csv)
    except WindEventPreflightError as exc:
        ap.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
