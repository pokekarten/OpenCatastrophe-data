#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact original, timestamp-aligned two-station DWD FX_10 research comparison.

Both real source ZIP SHA-256 identities were previously established independently
by #956/#992. This reports a *zero-lag* statistical Pearson association and
shared gust threshold counts; no observed rows, coordinates, station names,
modeled geographic field, event attribution or insurance loss estimates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import sys
import zipfile

from scripts.acquire_dwd_extreme_wind_receipt import FILENAME as FIRST_FILE
from scripts.dwd_frozen_gust_qc_v0 import PINNED_SHA256 as FIRST_SHA
from scripts.probe_dwd_station00348_original_v0 import (
    WIND_FILE as SECOND_FILE, PINNED_WIND_SHA256 as SECOND_SHA,
    _snapshot, _zip_open, MAX_WIND_EXPANDED, SecondStationBlocked,
)

SITES = (("00003", FIRST_FILE, FIRST_SHA),
         ("00348", SECOND_FILE, SECOND_SHA))
REQUIRED = ("STATIONS_ID", "MESS_DATUM", "QN", "FX_10")
START = datetime(2010, 1, 1)
END = datetime(2011, 3, 31, 23, 50)
FIRST_ROWS = 65_520
SECOND_ROWS = 87_588
THRESHOLDS_MPS = (15.0, 20.0, 25.0)
MAX_SINGLE_LINE = 4096


class PairedWindBlocked(ValueError):
    """The two original ZIP assets do not support a safe paired-time comparison."""


def _extract(path: Path, *, station: str, filename: str, digest: str,
             expected_full_count: int) -> dict:
    try:
        raw = _snapshot(path, filename, 8 * 1024 * 1024)
    except (OSError, ValueError) as exc:
        raise PairedWindBlocked("original source failed safe bounded file snapshot") from exc
    if hashlib.sha256(raw).hexdigest() != digest:
        raise PairedWindBlocked("original DWD source ZIP changed from frozen SHA")
    samples = {}
    missing_common = 0
    all_rows = 0
    qn_common = Counter()
    first = last = None
    try:
        with _zip_open(raw, max_expanded=MAX_WIND_EXPANDED) as z:
            candidates = []
            for info in z.infolist():
                if info.is_dir() or not info.filename.endswith(".txt"):
                    continue
                with z.open(info) as handle:
                    raw_header = handle.readline(MAX_SINGLE_LINE + 1)
                if len(raw_header) > MAX_SINGLE_LINE:
                    raise PairedWindBlocked("source product header exceeds bounded length")
                fields = [x.strip().strip('"') for x in
                          raw_header.decode("utf-8-sig").strip().split(";")]
                if len(fields) == len(set(fields)) and set(REQUIRED).issubset(fields):
                    candidates.append(info)
            if len(candidates) != 1:
                raise PairedWindBlocked("original ZIP contains no unique expected DWD product")
            with z.open(candidates[0]) as reader:
                header = [x.strip().strip('"') for x in
                          reader.readline(MAX_SINGLE_LINE + 1).decode("utf-8-sig").strip().split(";")]
                indexes = [header.index(k) for k in REQUIRED]
                for line in reader:
                    if not line.strip():
                        continue
                    if len(line) > MAX_SINGLE_LINE:
                        raise PairedWindBlocked("source data line exceeds bounded length")
                    fields = [v.strip().strip('"') for v in
                              line.decode("utf-8").rstrip("\r\n").split(";")]
                    if len(fields) != len(header):
                        raise PairedWindBlocked("native DWD product field count drifted")
                    station_raw, stamp, quality, speed = (fields[i] for i in indexes)
                    if station_raw.zfill(5) != station:
                        raise PairedWindBlocked("original station ID changed")
                    if len(stamp) != 12 or not stamp.isascii() or not stamp.isdigit():
                        raise PairedWindBlocked("DWD source timestamp shape invalid")
                    try:
                        time = datetime.strptime(stamp, "%Y%m%d%H%M")
                    except ValueError as exc:
                        raise PairedWindBlocked("invalid original source timestamp") from exc
                    if time.minute % 10 != 0:
                        raise PairedWindBlocked("timestamp not on DWD 10-minute grid")
                    if last is not None and time - last != timedelta(minutes=10):
                        raise PairedWindBlocked("original DWD archive has missing or unordered timestamps")
                    if first is None:
                        first = time
                    last = time
                    if quality not in ("1", "2", "3"):
                        raise PairedWindBlocked("unreviewed original quality level")
                    try:
                        gust = Decimal(speed)
                    except InvalidOperation as exc:
                        raise PairedWindBlocked("original source gust is not numeric") from exc
                    if not gust.is_finite() or (gust < 0 and gust != Decimal("-999")):
                        raise PairedWindBlocked("invalid DWD gust observation")
                    all_rows += 1
                    if all_rows > SECOND_ROWS:
                        raise PairedWindBlocked("source observation count exceeds second-station cap")
                    if START <= time <= END:
                        if time in samples:
                            raise PairedWindBlocked("original source contains duplicate UTC timestamp")
                        samples[time] = (None if gust == Decimal("-999") else float(gust),
                                         int(quality))
                        qn_common[quality] += 1
                        if gust == Decimal("-999"):
                            missing_common += 1
            # Force CRC validation of all other original source ZIP members.
            for info in z.infolist():
                if info.is_dir() or info == candidates[0]:
                    continue
                with z.open(info) as member:
                    while member.read(65_536):
                        pass
    except (OSError, UnicodeError, RuntimeError, zipfile.BadZipFile,
            SecondStationBlocked) as exc:
        raise PairedWindBlocked("original source ZIP text or CRC check failed") from exc
    if all_rows != expected_full_count or not samples:
        raise PairedWindBlocked("original DWD row count or shared period is incomplete")
    return {
        "station": station,
        "source_sha256": digest,
        "full_source_rows": all_rows,
        "shared_samples": samples,
        "shared_missing": missing_common,
        "shared_qn_counts": dict(sorted(qn_common.items())),
    }


def _paired_stats(first: dict, second: dict) -> dict:
    a, b = first["shared_samples"], second["shared_samples"]
    expected = int((END - START).total_seconds() // 600) + 1
    if (set(a) != set(b) or len(a) != expected or
            min(a) != START or max(a) != END or
            first["shared_missing"] or second["shared_missing"]):
        raise PairedWindBlocked("shared original series lack full one-to-one nonmissing timestamps")
    ordered = sorted(a)
    x = [a[t][0] for t in ordered]
    y = [b[t][0] for t in ordered]
    if any(value is None for value in x + y):
        raise PairedWindBlocked("DWD paired source has unexpected missing gust")
    n = len(x)
    mean_x = math.fsum(x) / n
    mean_y = math.fsum(y) / n
    x_centered = [v - mean_x for v in x]
    y_centered = [v - mean_y for v in y]
    sx = math.fsum(v * v for v in x_centered)
    sy = math.fsum(v * v for v in y_centered)
    if sx <= 0 or sy <= 0:
        raise PairedWindBlocked("zero observed variation invalidates Pearson statistic")
    pearson = math.fsum(p * q for p, q in zip(x_centered, y_centered)) / math.sqrt(sx * sy)
    threshold_counts = []
    for threshold in THRESHOLDS_MPS:
        count_a = sum(v >= threshold for v in x)
        count_b = sum(v >= threshold for v in y)
        both = sum(p >= threshold and q >= threshold for p, q in zip(x, y))
        threshold_counts.append({
            "threshold_mps": threshold,
            "station00003_observation_count": count_a,
            "station00348_observation_count": count_b,
            "simultaneous_10min_observation_count": both,
        })
    # No "effective independent N": storms create temporal dependence.
    return {
        "paired_10min_samples": n,
        "pairing": "EXACT_SAME_UTC_10MIN_TIMESTAMP_ZERO_LAG",
        "first_station_qn_distribution": first["shared_qn_counts"],
        "second_station_qn_distribution": second["shared_qn_counts"],
        "pearson_r_zero_lag_unadjusted": round(pearson, 6),
        "original_station00003_mean_mps": round(mean_x, 5),
        "original_station00348_mean_mps": round(mean_y, 5),
        "cooccurrence_counts_by_gust_threshold": threshold_counts,
        "serial_dependence_adjusted": False,
        "meteorological_event_dependence_derived": False,
        "spatial_wind_field_derived": False,
        "statistical_significance_inferred": False,
    }


def compare(first_path: Path, second_path: Path, *,
            first_digest: str = FIRST_SHA, second_digest: str = SECOND_SHA,
            first_count: int = FIRST_ROWS,
            second_count: int = SECOND_ROWS) -> dict:
    a = _extract(Path(first_path), station="00003", filename=FIRST_FILE,
                 digest=first_digest, expected_full_count=first_count)
    b = _extract(Path(second_path), station="00348", filename=SECOND_FILE,
                 digest=second_digest, expected_full_count=second_count)
    return {
        "profile": "opencatastrophe-dwd-two-original-station-fx10-paired-utc-v0",
        "source_00003_sha256": a["source_sha256"],
        "source_00348_sha256": b["source_sha256"],
        "original_source_hashes_pinned": (first_digest == FIRST_SHA and second_digest == SECOND_SHA),
        "common_start_utc": START.isoformat() + "Z",
        "common_end_utc": END.isoformat() + "Z",
        **_paired_stats(a, b),
        "raw_observation_rows_emitted_or_persisted": False,
        "instrument_join_proven": False,
        "hazard_model_calibrated": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-zip", type=Path, required=True)
    parser.add_argument("--second-zip", type=Path, required=True)
    opts = parser.parse_args(argv)
    try:
        result = compare(opts.first_zip, opts.second_zip)
    except PairedWindBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
