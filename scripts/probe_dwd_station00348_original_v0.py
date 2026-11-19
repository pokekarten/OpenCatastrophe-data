#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""First independent DWD 10-minute extreme-wind station pilot beyond station 00003.

Only exact original public filenames for station 00348, verified against official
DWD historical and meta_data directory listings. No arbitrary URL input,
no raw data publication, no database mutations and no CAT model input admission.
The first live receipt establishes source-byte SHA identities; those must be
pinned by a separate deliberate review before any expanded source admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

from scripts.dwd_metadata_temporal_evidence import _read_bounded_regular_snapshot
from scripts.dwd_original_metadata_shapes_v0 import _table_shape

STATION = "00348"
WIND_FILE = "10minutenwerte_extrema_wind_00348_20100101_20110901_hist.zip"
METADATA_FILE = "Meta_Daten_zehn_min_fx_00348.zip"
STATION_GEO = "Metadaten_Geographie_00348.txt"
START_LABEL = date(2010, 1, 1)
END_LABEL = date(2011, 9, 1)
WIND_COLUMNS = ("STATIONS_ID", "MESS_DATUM", "QN", "FX_10", "FNX_10", "FMX_10", "DX_10")
GEO_COLUMNS = ("Stations_id", "Stationshoehe", "Geogr.Breite",
               "Geogr.Laenge", "von_datum", "bis_datum", "Stationsname")
MAX_WIND_ZIP = 8 * 1024 * 1024
MAX_METADATA_ZIP = 1024 * 1024
MAX_WIND_EXPANDED = 50 * 1024 * 1024
MAX_METADATA_EXPANDED = 5 * 1024 * 1024
MAX_WIND_ROWS = 180_000
MAX_MEMBER_BYTES = 50 * 1024 * 1024
MAX_LINE_BYTES = 4096
MAX_MEMBERS = 40
# Independently established by official original DWD live-source receipt
# GitHub Actions run 41322132794 (2026-11-01). Any future provider revision
# must be a new explicit review, never silently accepted as equivalent bytes.
PINNED_WIND_SHA256 = "9a854b621298ed0374677ce36796da2b4e628d45529c815351c8b988e62aaf0c"
PINNED_METADATA_SHA256 = "041501a00b62502e961f612b43a0b28ce78a8c634d318ed595cc1f5a923cfb02"
COMMON_START = date(2010, 1, 1)
COMMON_END = date(2011, 3, 31)



class SecondStationBlocked(ValueError):
    """Original station pilot source failed validation; do not promote data."""


def _snapshot(path: Path, expected_name: str, max_bytes: int) -> bytes:
    if path.name != expected_name or path.is_symlink() or not path.is_file():
        raise SecondStationBlocked("only exact regular DWD station00348 original filenames are allowed")
    try:
        size = path.stat().st_size
        if not 0 < size <= max_bytes:
            raise SecondStationBlocked("original source exceeds fixed size limit")
        return _read_bounded_regular_snapshot(path, size)
    except OSError as exc:
        raise SecondStationBlocked("original source failed secure bounded snapshot") from exc
    except ValueError as exc:
        raise SecondStationBlocked("original source changed after secure reopen") from exc


def _zip_open(raw: bytes, *, max_expanded: int):
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw), "r")
        items = archive.infolist()
        if not 1 <= len(items) <= MAX_MEMBERS:
            raise SecondStationBlocked("invalid original ZIP member count")
        total = 0
        seen = set()
        for item in items:
            path = PurePosixPath(item.filename)
            if (not item.filename or item.filename.startswith("/")
                    or "\\" in item.filename or ".." in path.parts
                    or item.filename in seen or len(item.filename) > 256):
                raise SecondStationBlocked("unsafe or duplicated original ZIP member")
            seen.add(item.filename)
            mode = (item.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise SecondStationBlocked("original ZIP special-file member forbidden")
            if item.flag_bits & 1 or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise SecondStationBlocked("unreviewed ZIP member encryption/compression")
            if item.file_size > MAX_MEMBER_BYTES:
                raise SecondStationBlocked("oversized expanded original ZIP member")
            total += item.file_size
        if total > max_expanded:
            raise SecondStationBlocked("original ZIP expansion exceeds fixed limit")
        return archive
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise SecondStationBlocked("original source is not a safely readable ZIP") from exc


def _date(raw: str) -> date:
    if not re.fullmatch(r"[0-9]{8}", raw):
        raise SecondStationBlocked("original date is not exact YYYYMMDD")
    try:
        return date.fromisoformat(raw[:4] + "-" + raw[4:6] + "-" + raw[6:])
    except ValueError as exc:
        raise SecondStationBlocked("invalid original calendar date") from exc


def _decimal(value: str, lower: int, upper: int) -> Decimal:
    try:
        n = Decimal(value.strip())
    except InvalidOperation as exc:
        raise SecondStationBlocked("original geography numeric is malformed") from exc
    if not n.is_finite() or not lower <= n <= upper:
        raise SecondStationBlocked("original geography numeric outside bounds")
    return n


def _wind_stats(raw: bytes) -> dict:
    with _zip_open(raw, max_expanded=MAX_WIND_EXPANDED) as z:
        # DWD original ZIP internal product names may vary by station/era.
        # Identify the single product by its actual verified native header,
        # NOT by copying station-00003's internal product filename.
        matches = []
        for info in z.infolist():
            if info.is_dir() or not info.filename.endswith(".txt"):
                continue
            try:
                with z.open(info) as probe:
                    header_sample = probe.readline(MAX_LINE_BYTES + 1)
                if len(header_sample) > MAX_LINE_BYTES:
                    raise SecondStationBlocked("oversized original product candidate header")
                fields = [x.strip().strip('"') for x in
                          header_sample.decode("utf-8-sig").strip().split(";")]
            except (UnicodeDecodeError, RuntimeError, zipfile.BadZipFile) as exc:
                raise SecondStationBlocked("unreviewed original TXT header encoding or ZIP CRC") from exc
            if len(fields) == len(set(fields)) and set(WIND_COLUMNS).issubset(fields):
                matches.append(info)
        if len(matches) != 1:
            raise SecondStationBlocked(
                "must identify exactly one original wind product by required field header"
            )
        member = matches[0]
        embedded_ids = re.findall(r"(?<![0-9])[0-9]{5}(?![0-9])",
                                  PurePosixPath(member.filename).name)
        if embedded_ids and set(embedded_ids) != {STATION}:
            raise SecondStationBlocked("original DWD product member filename station mismatch")
        try:
            with z.open(member) as reader:
                header_raw = reader.readline(MAX_LINE_BYTES + 1)
                if len(header_raw) > MAX_LINE_BYTES:
                    raise SecondStationBlocked("oversized DWD product header")
                headers = [x.strip().strip('"') for x in header_raw.decode("utf-8-sig").strip().split(";")]
                if len(set(headers)) != len(headers) or not set(WIND_COLUMNS).issubset(headers):
                    raise SecondStationBlocked("DWD product header differs from known extreme-wind original")
                indexes = {c: headers.index(c) for c in WIND_COLUMNS}
                row_count = 0
                missing_fx = 0
                qn = Counter()
                maximum_gust = None
                first = last = None
                missing_slots = 0
                common_count = 0
                common_missing = 0
                common_max = None
                common_qn = Counter()
                for line in reader:
                    if not line.strip():
                        continue
                    if len(line) > MAX_LINE_BYTES:
                        raise SecondStationBlocked("oversized DWD wind observation line")
                    fields = [x.strip().strip('"') for x in line.decode("utf-8").rstrip("\r\n").split(";")]
                    if len(fields) != len(headers):
                        raise SecondStationBlocked("original DWD product row field-count drift")
                    if fields[indexes["STATIONS_ID"]].zfill(5) != STATION:
                        raise SecondStationBlocked("original source station identity drifted")
                    stamp = fields[indexes["MESS_DATUM"]]
                    if not re.fullmatch(r"[0-9]{12}", stamp):
                        raise SecondStationBlocked("invalid DWD 10-minute timestamp syntax")
                    try:
                        observation = datetime.strptime(stamp, "%Y%m%d%H%M")
                    except ValueError as exc:
                        raise SecondStationBlocked("invalid DWD timestamp calendar value") from exc
                    if not START_LABEL <= observation.date() <= END_LABEL:
                        raise SecondStationBlocked("DWD observation outside exact original archive filename bounds")
                    if observation.minute % 10:
                        raise SecondStationBlocked("DWD product timestamp not on 10-minute cadence")
                    if last is not None:
                        gap = int((observation - last).total_seconds())
                        if gap < 600 or gap % 600:
                            raise SecondStationBlocked("duplicate, out-of-order or off-grid timestamps")
                        missing_slots += gap // 600 - 1
                    if first is None:
                        first = observation
                    last = observation
                    quality = fields[indexes["QN"]]
                    if not re.fullmatch(r"-?[0-9]+", quality):
                        raise SecondStationBlocked("invalid source quality-level label")
                    qn[quality] += 1
                    try:
                        gust = Decimal(fields[indexes["FX_10"]])
                    except InvalidOperation as exc:
                        raise SecondStationBlocked("invalid DWD gust source number") from exc
                    if not gust.is_finite() or (gust < 0 and gust != Decimal(-999)):
                        raise SecondStationBlocked("nonfinite or unreviewed negative wind gust")
                    if gust == Decimal(-999):
                        missing_fx += 1
                    elif maximum_gust is None or gust > maximum_gust:
                        maximum_gust = gust
                    # Shared exact calendar window of frozen station 00003.
                    # Aggregate only; never infer a meteorological correlation.
                    if COMMON_START <= observation.date() <= COMMON_END:
                        common_count += 1
                        common_qn[quality] += 1
                        if gust == Decimal(-999):
                            common_missing += 1
                        elif common_max is None or gust > common_max:
                            common_max = gust
                    row_count += 1
                    if row_count > MAX_WIND_ROWS:
                        raise SecondStationBlocked("original wind archive exceeds pilot row bound")
                if row_count == 0 or first is None or last is None:
                    raise SecondStationBlocked("original DWD wind product is empty")
            # CRC/read all remaining exact-source members; no member released.
            for info in z.infolist():
                if info.filename == member.filename or info.is_dir():
                    continue
                with z.open(info) as handle:
                    while handle.read(65_536):
                        pass
        except (OSError, UnicodeDecodeError, RuntimeError, zipfile.BadZipFile) as exc:
            raise SecondStationBlocked("DWD wind product decompression or text decode failed") from exc
        member_sha256 = hashlib.sha256(z.read(member)).hexdigest()
    return {
        "observation_rows": row_count,
        "first_observation_utc": first.strftime("%Y-%m-%dT%H:%MZ"),
        "last_observation_utc": last.strftime("%Y-%m-%dT%H:%MZ"),
        "fx_10_missing_sentinel_rows": missing_fx,
        "fx_10_nonmissing_rows": row_count - missing_fx,
        "fx_10_max_mps": str(maximum_gust) if maximum_gust is not None else None,
        "quality_level_distribution": dict(sorted(qn.items())),
        "missing_10minute_slots_between_first_and_last": missing_slots,
        "product_member_sha256": member_sha256,
        "product_member": PurePosixPath(member.filename).name,
        "common_calendar_window_with_station00003": {
            "start_utc_date": COMMON_START.isoformat(),
            "end_utc_date": COMMON_END.isoformat(),
            "original_10min_observations": common_count,
            "fx_10_missing_sentinel_rows": common_missing,
            "fx_10_nonmissing_rows": common_count - common_missing,
            "max_fx_10_mps": str(common_max) if common_max is not None else None,
            "quality_level_distribution": dict(sorted(common_qn.items())),
            "measurement_series_directly_correlated": False,
        },
    }


def _geography_stats(raw: bytes, start: date, end: date) -> dict:
    with _zip_open(raw, max_expanded=MAX_METADATA_EXPANDED) as z:
        names = {item.filename for item in z.infolist()}
        if STATION_GEO not in names:
            raise SecondStationBlocked("second-station original metadata geography member absent")
        # A second independent station may have different metadata members; do
        # not claim exact file-family parity with station 00003.
        if not any(x.startswith("Metadaten_Geraete_") for x in names):
            raise SecondStationBlocked("second-station source lacks device metadata family")
        if not any(x.startswith("Metadaten_Parameter_") for x in names):
            raise SecondStationBlocked("second-station source lacks parameter metadata family")
        try:
            member = z.read(STATION_GEO)
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            raise SecondStationBlocked("original station geography ZIP CRC invalid") from exc
        if len(member) > 512_000:
            raise SecondStationBlocked("original geography TXT too large for research pilot")
        shape = _table_shape(member)
        if (tuple(shape.get("columns", [])) != GEO_COLUMNS
                or shape.get("shape_status") != "syntactically_consistent_unreviewed_columns"):
            raise SecondStationBlocked("new station original geography schema needs review")
        rows = member.decode("utf-8-sig").splitlines()
        history = []
        for line in rows[1:]:
            if not line.strip():
                continue
            fields = line.split(";")
            if len(fields) != len(GEO_COLUMNS):
                raise SecondStationBlocked("new station geography source row shape drift")
            if fields[0].strip().zfill(5) != STATION:
                raise SecondStationBlocked("new station geography ID mismatch")
            height = _decimal(fields[1], -500, 9000)
            lat = _decimal(fields[2], -90, 90)
            lon = _decimal(fields[3], -180, 180)
            begins, ends = _date(fields[4].strip()), _date(fields[5].strip())
            if begins > ends:
                raise SecondStationBlocked("inverted original geography timeline")
            history.append((begins, ends, lat, lon, height))
            if len(history) > 64:
                raise SecondStationBlocked("unreviewed geography history cardinality")
        if not history:
            raise SecondStationBlocked("original station geography history empty")
        for info in z.infolist():
            if info.filename == STATION_GEO or info.is_dir():
                continue
            with z.open(info) as handle:
                while handle.read(65_536):
                    pass
    unique = absent = multiple = 0
    current = start
    while current <= end:
        match = sum(b <= current <= e for b, e, _lat, _lon, _h in history)
        if match == 1:
            unique += 1
        elif match == 0:
            absent += 1
        else:
            multiple += 1
        current += timedelta(days=1)
    return {
        "history_rows": len(history),
        "distinct_original_position_height_tuples": len({
            (lat, lon, h) for _b, _e, lat, lon, h in history
        }),
        "provisional_inclusive_unique_geography_days": unique,
        "provisional_inclusive_missing_geography_days": absent,
        "provisional_inclusive_overlapping_geography_days": multiple,
        "geography_member_sha256": hashlib.sha256(member).hexdigest(),
        "source_geographic_coordinates_emitted": False,
    }


def inspect(wind_path: Path, metadata_path: Path, *,
            expected_wind_sha256: str | None = None,
            expected_metadata_sha256: str | None = None) -> dict:
    wind = _snapshot(Path(wind_path), WIND_FILE, MAX_WIND_ZIP)
    meta = _snapshot(Path(metadata_path), METADATA_FILE, MAX_METADATA_ZIP)
    wind_sha = hashlib.sha256(wind).hexdigest()
    meta_sha = hashlib.sha256(meta).hexdigest()
    if expected_wind_sha256 is not None and expected_wind_sha256 != wind_sha:
        raise SecondStationBlocked("original wind ZIP SHA drifted from preapproved expectation")
    if expected_metadata_sha256 is not None and expected_metadata_sha256 != meta_sha:
        raise SecondStationBlocked("original metadata ZIP SHA drifted from preapproved expectation")
    wind_evidence = _wind_stats(wind)
    first = datetime.strptime(wind_evidence["first_observation_utc"], "%Y-%m-%dT%H:%MZ").date()
    last = datetime.strptime(wind_evidence["last_observation_utc"], "%Y-%m-%dT%H:%MZ").date()
    geography = _geography_stats(meta, first, last)
    return {
        "profile": "opencatastrophe-dwd-second-original-station-00348-research-v0",
        "station_id": STATION,
        "first_station_00003_independent": True,
        "wind_original_filename": WIND_FILE,
        "metadata_original_filename": METADATA_FILE,
        "wind_original_sha256": wind_sha,
        "metadata_original_sha256": meta_sha,
        "wind_original_bytes": len(wind),
        "metadata_original_bytes": len(meta),
        "original_source_hashes_approved_for_next_runs":
            expected_wind_sha256 == PINNED_WIND_SHA256
            and expected_metadata_sha256 == PINNED_METADATA_SHA256,
        "measurement": wind_evidence,
        "geography": geography,
        "source_archive_label_dates": {
            "start": START_LABEL.isoformat(), "end": END_LABEL.isoformat(),
        },
        "historical_geography_endpoint_interpretation": "PROVISIONAL_INCLUSIVE",
        "measurement_sensor_join_proven": False,
        "external_original_bytes_persisted": False,
        "model_input_approved": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wind-zip", type=Path, required=True)
    p.add_argument("--metadata-zip", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        receipt = inspect(args.wind_zip, args.metadata_zip,
                          expected_wind_sha256=PINNED_WIND_SHA256,
                          expected_metadata_sha256=PINNED_METADATA_SHA256)
    except (SecondStationBlocked, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
