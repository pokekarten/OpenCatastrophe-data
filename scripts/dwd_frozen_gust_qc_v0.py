#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-source DWD wind-gust QC; statistics are research-only, not CAT inputs.

Read the one already-frozen station 00003 (2010-01-01 to 2011-03-31) historical
original ZIP off-line. Unit FX_10=m/s, missing sentinel -999 and QN meanings
follow the official DWD 10-minute extreme-wind v24.03 description. Output only
per-month aggregate statistics, never individual observations, geometry or
unadmitted source measurements. Do not infer station coverage from filenames.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
import time
from zipfile import ZipFile

from scripts.acquire_dwd_extreme_wind_receipt import (
    FILENAME, EXPECTED_BEGIN_DATE, EXPECTED_END_DATE, EXPECTED_STATION_ID,
    MAX_BYTES, MAX_ROW_BYTES, AcquisitionError, _validate_zip,
)

# Frozen independent DWD source-byte identity, as already recorded by
# scripts/dwd_metadata_temporal_evidence.py. Future version drift must be
# reviewed with a new source digest; never silently accept changed originals.
PINNED_SHA256 = "8b4cf7e26efc8ddde431ca2cfc5251ef7588c9566b41e5490fa372ffa42689a4"
DOCUMENTATION = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/10_minutes/extreme_wind/"
    "DESCRIPTION_obsgermany_climate_10min_extreme_wind_en.pdf"
)
REQUIRED = {"STATIONS_ID", "MESS_DATUM", "QN", "FX_10"}
MISSING = Decimal("-999")
# Up to 1 million records per archive, 1 MiB per decoded CSV line is never allowed.


class GustQCBlocked(ValueError):
    """Input byte identity, timestamps, wind values or safety gate failed."""


def _number(raw: str, *, field: str) -> Decimal:
    try:
        value = Decimal(raw.strip().strip('"'))
    except InvalidOperation as exc:
        raise GustQCBlocked(f"{field}: invalid number") from exc
    if not value.is_finite():
        raise GustQCBlocked(f"{field}: nonfinite value")
    return value


def _decode_row(line: bytes, indexes: dict[str, int], expected_fields: int):
    if not line or len(line) > MAX_ROW_BYTES:
        raise GustQCBlocked("DWD row outside byte bound")
    try:
        cols = [part.strip().strip('"') for part in line.decode("utf-8").rstrip("\r\n").split(";")]
    except UnicodeDecodeError as exc:
        raise GustQCBlocked("DWD row is not UTF-8") from exc
    if len(cols) != expected_fields:
        raise GustQCBlocked("DWD row field count differs from provider header")
    if cols[indexes["STATIONS_ID"]].zfill(5) != EXPECTED_STATION_ID:
        raise GustQCBlocked("DWD station identity differs from pinned original")
    ts = cols[indexes["MESS_DATUM"]]
    if len(ts) != 12 or not ts.isdigit():
        raise GustQCBlocked("DWD timestamp is not YYYYMMDDHHMM")
    try:
        dt = datetime.strptime(ts, "%Y%m%d%H%M")
    except ValueError as exc:
        raise GustQCBlocked("invalid DWD observation timestamp") from exc
    if not (EXPECTED_BEGIN_DATE <= ts[:8] <= EXPECTED_END_DATE):
        raise GustQCBlocked("DWD timestamp outside frozen archive window")
    # This bounded 2010-2011 pilot uses UTC per the original DWD documentation.
    qn_text = cols[indexes["QN"]]
    if not qn_text.lstrip("+").isdigit():
        raise GustQCBlocked("quality level is not an integer")
    qn = int(qn_text)
    gust = _number(cols[indexes["FX_10"]], field="FX_10")
    if gust != MISSING and gust < 0:
        raise GustQCBlocked("wind-gust speed is negative and not DWD missing sentinel")
    return dt, qn, gust


def summarize(path: Path, *, expected_sha256: str = PINNED_SHA256) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise GustQCBlocked("source ZIP must be an ordinary local file, not symlink")
    if not 0 < path.stat().st_size <= MAX_BYTES:
        raise GustQCBlocked("source ZIP size exceeds frozen acquisition limit")
    observed_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed_sha != expected_sha256:
        raise GustQCBlocked("original DWD ZIP SHA-256 differs from pinned research asset")
    try:
        # Reuse the exact original archive's CRC, native-header, station, temporal
        # bounds, payload safety, ZIP expansion and member-count validation.
        inspection = _validate_zip(str(path), deadline=time.monotonic() + 90,
                                   monotonic=time.monotonic)
    except (AcquisitionError, OSError) as exc:
        raise GustQCBlocked("original DWD ZIP source structural gate failed") from exc
    months: dict[str, dict] = defaultdict(lambda: {
        "records": 0, "missing_fx_10": 0, "quality_level_counts": Counter(),
        "valid_fx_10": 0, "qn_2_3_fx_10": 0,
        "max_fx_10_mps_all_quality": None,
        "max_fx_10_mps_qn_2_3": None,
    })
    last: datetime | None = None
    unobserved_expected_slots = 0
    non_ten_minute_intervals = 0
    with ZipFile(path, "r") as archive:
        with archive.open(inspection["product_member"]) as raw:
            try:
                header = raw.readline(MAX_ROW_BYTES + 1).decode("utf-8-sig").rstrip("\r\n")
            except UnicodeDecodeError as exc:
                raise GustQCBlocked("DWD header is not UTF-8") from exc
            cols = [part.strip().strip('"') for part in header.split(";")]
            if not REQUIRED.issubset(cols) or len(cols) != len(set(cols)):
                raise GustQCBlocked("DWD source lacks unique expected field names")
            indexes = {c: cols.index(c) for c in REQUIRED}
            total = 0
            for raw_line in raw:
                if not raw_line.strip():
                    continue
                dt, qn, gust = _decode_row(raw_line, indexes, len(cols))
                if last is not None:
                    delta = dt - last
                    if delta <= timedelta(0):
                        raise GustQCBlocked("non-increasing or duplicate DWD timestamps")
                    if int(delta.total_seconds()) % 600:
                        non_ten_minute_intervals += 1
                    else:
                        unobserved_expected_slots += max(0, int(delta.total_seconds() // 600) - 1)
                last = dt
                m = months[dt.strftime("%Y-%m")]
                m["records"] += 1
                m["quality_level_counts"][str(qn)] += 1
                total += 1
                if total > 1_000_000:
                    raise GustQCBlocked("too many original source rows")
                if gust == MISSING:
                    m["missing_fx_10"] += 1
                    continue
                m["valid_fx_10"] += 1
                old = m["max_fx_10_mps_all_quality"]
                m["max_fx_10_mps_all_quality"] = gust if old is None else max(gust, old)
                # Only QN=2/3 values are retained in a separately identified
                # subset. QN=1 is not treated as equal-quality calibration data.
                if qn in (2, 3):
                    m["qn_2_3_fx_10"] += 1
                    old = m["max_fx_10_mps_qn_2_3"]
                    m["max_fx_10_mps_qn_2_3"] = gust if old is None else max(gust, old)
    if total != inspection["product_row_count"]:
        raise GustQCBlocked("source row count changed after original structural check")
    if non_ten_minute_intervals:
        raise GustQCBlocked("DWD timestamps not aligned with 10-minute cadence")
    output = []
    for month, m in sorted(months.items()):
        counts = m["quality_level_counts"]
        if sum(counts.values()) != m["records"] or m["missing_fx_10"] + m["valid_fx_10"] != m["records"]:
            raise GustQCBlocked("DWD monthly counts do not conserve source observations")
        output.append({
            "month_utc": month,
            "records_observed": m["records"],
            "fx_10_missing": m["missing_fx_10"],
            "fx_10_nonmissing": m["valid_fx_10"],
            "quality_level_counts": dict(sorted(counts.items())),
            "qn_2_3_fx_10_nonmissing": m["qn_2_3_fx_10"],
            "max_fx_10_mps_all_quality": (
                str(m["max_fx_10_mps_all_quality"]) if m["max_fx_10_mps_all_quality"] is not None else None),
            "max_fx_10_mps_qn_2_3": (
                str(m["max_fx_10_mps_qn_2_3"]) if m["max_fx_10_mps_qn_2_3"] is not None else None),
        })
    return {
        "profile": "opencatastrophe-dwd-station-gust-research-v0",
        "source_archive": FILENAME,
        "station_id": EXPECTED_STATION_ID,
        "source_zip_sha256": observed_sha,
        "source_document": DOCUMENTATION,
        "observations": total,
        "missing_fx_10": sum(m["fx_10_missing"] for m in output),
        "unobserved_10min_slots_between_records": unobserved_expected_slots,
        "timestamp_basis": "UTC_2010_2011_DWD",
        "gust_variable": "FX_10",
        "gust_unit": "m/s",
        "missing_sentinel": "-999",
        "months": output,
        "raw_observation_rows_persisted": False,
        "model_input_approved": False,
        "geographic_station_metadata_validated": False,
        "vulnerability_loss_calibration_validated": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path,
                        help="exact frozen original DWD ZIP in ephemeral local workspace")
    args = parser.parse_args(argv)
    try:
        result = summarize(args.source_zip)
    except (GustQCBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
