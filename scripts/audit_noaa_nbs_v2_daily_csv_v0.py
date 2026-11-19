#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline NOAA NBS v2 Science Quality daily ERDDAP CSV screen.

Consumes only caller-supplied local bytes from a separately authorised, fixed
2024-01-01 griddap subset. Never retrieves data, stores source rows, declares
licensing rights, or admits CAT model input. The resulting SHA is an INPUT byte
hash, not a verified original-provider receipt unless independently attested.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path

SOURCE_ID = "noaa.ncei.blended-seawinds.v2.0"
ERDDAP_DATASET = "noaacwBlendedWindsDaily"
EXPECTED_DAY = "2024-01-01"
MAX_BYTES = 131072
MAX_CELLS = 256
FIELDS = ["time", "zlev", "latitude", "longitude", "windspeed", "mask"]
VALID_MASKS = {0, 1, 2, 3, 6, -9999}


class NOAAWindBlocked(ValueError):
    """Unreviewed subset shape, bad source fields or ambiguous science."""


def _float(text: str, label: str) -> float:
    try:
        result = float(text)
    except (ValueError, OverflowError) as exc:
        raise NOAAWindBlocked("invalid " + label) from exc
    if not math.isfinite(result):
        raise NOAAWindBlocked("nonfinite " + label)
    return result


def inspect_nbs_daily_csv(original: bytes) -> dict:
    if type(original) is not bytes or not (0 < len(original) <= MAX_BYTES):
        raise NOAAWindBlocked("bounded input byte size")
    try:
        decoded = original.decode("utf-8")
        if "\x00" in decoded:
            raise NOAAWindBlocked("NUL in CSV")
        rows = list(csv.reader(io.StringIO(decoded, newline=""), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise NOAAWindBlocked("non-strict ERDDAP CSV") from exc
    if len(rows) < 3 or len(rows) > MAX_CELLS + 2:
        raise NOAAWindBlocked("bounded input row count")
    if rows[0] != FIELDS:
        raise NOAAWindBlocked("expected exact Science Quality daily variable list")
    units = rows[1]
    if not (len(units) == len(FIELDS)
            and units[0] == "UTC"
            and units[1] in {"m", "meters"}
            and units[2:5] == ["degrees_north", "degrees_east", "m s-1"]
            and units[5] in {"", "1"}):
        raise NOAAWindBlocked("ERDDAP units do not match reviewed CF attributes")
    seen = set()
    counters = dict(ocean_blended=0, model_flagged=0,
                    inland_or_land=0, missing_wind=0, unknown_mask=0)
    for row in rows[2:]:
        if len(row) != len(FIELDS):
            raise NOAAWindBlocked("invalid data row columns")
        timestamp, zlev, lat, lon, speed, mask = row
        try:
            when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise NOAAWindBlocked("invalid UTC timestamp") from exc
        if (when.tzinfo is None or when.utcoffset() != timezone.utc.utcoffset(when)
                or when.date().isoformat() != EXPECTED_DAY):
            raise NOAAWindBlocked("wrong UTC sample date or timezone")
        z = _float(zlev, "height")
        y = _float(lat, "latitude")
        x = _float(lon, "longitude")
        if z != 10 or not (-89.75 <= y <= 89.75) or not (0 <= x <= 359.75):
            raise NOAAWindBlocked("wrong 10-m grid coordinates")
        if abs(y * 4 - round(y * 4)) > 1e-6 or abs(x * 4 - round(x * 4)) > 1e-6:
            raise NOAAWindBlocked("off-grid 0.25-degree coordinate")
        key = (timestamp, z, y, x)
        if key in seen:
            raise NOAAWindBlocked("duplicate time/location cell")
        seen.add(key)
        if mask.strip() not in {"-9999", "0", "1", "2", "3", "6"}:
            raise NOAAWindBlocked("unreviewed provider mask code")
        code = int(mask)
        value = _float(speed, "windspeed")
        if value == -9999:
            counters["missing_wind"] += 1
        elif not (0 <= value <= 200):
            raise NOAAWindBlocked("implausible or negative windspeed")
        if code == 6:
            counters["model_flagged"] += 1
        elif code == 1:
            if value != -9999:
                counters["ocean_blended"] += 1
        elif code in {0, 2, 3}:
            counters["inland_or_land"] += 1
        else:
            counters["unknown_mask"] += 1
    return {
        "schema": "noaa-nbs-v2-science-quality-daily-mask-screen-v0",
        "source_id": SOURCE_ID,
        "dataset_id": ERDDAP_DATASET,
        "sample_utc_day": EXPECTED_DAY,
        "input_byte_count": len(original),
        "input_byte_sha256": hashlib.sha256(original).hexdigest(),
        "grid_cell_count": len(seen),
        **counters,
        "independent_in_situ_observation_cells_proven": 0,
        "ocean_cells_are_blended_not_independently_observed": True,
        "mask_6_is_model_not_observation": True,
        "era5_direction_lineage_must_be_preserved": True,
        "provider_original_response_verified": False,
        "source_bytes_persisted": False,
        "commercial_use_or_cat_model_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.csv.open("rb") as f:
            report = inspect_nbs_daily_csv(f.read(MAX_BYTES + 1))
    except (OSError, NOAAWindBlocked):
        parser.exit(2, "BLOCKED: NOAA NBS v2 Science Quality daily original input screen\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
