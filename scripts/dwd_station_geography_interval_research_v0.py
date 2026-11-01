#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Provisional interval *overlap audit*, not a geographic CAT exposure join.

The DWD original station-00003 metadata SHA and the exact geography column
schema were confirmed via #960. This module examines the six provider-native
geographic history rows in-memory and checks candidate date coverage against
the 2010-2011 frozen gust measurement period. Inclusive endpoint interpretation
is only an explicit research ASSUMPTION. No source coordinates are printed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from scripts import dwd_metadata_temporal_evidence as evidence
from scripts.dwd_original_metadata_shapes_v0 import _table_shape, MetadataShapeBlocked

GEO_MEMBER = "Metadaten_Geographie_00003.txt"
COLUMNS = (
    "Stations_id", "Stationshoehe", "Geogr.Breite", "Geogr.Laenge",
    "von_datum", "bis_datum", "Stationsname",
)
START = date(2010, 1, 1)
END = date(2011, 3, 31)
MAX_SOURCE_ROWS = 256


class GeographyBlocked(ValueError):
    """Exact original source or historical metadata geography is not trustworthy."""


def _date_label(value: str) -> date:
    value = value.strip()
    if not re.fullmatch(r"[0-9]{8}", value):
        raise GeographyBlocked("unreviewed station validity date representation")
    try:
        return date.fromisoformat(value[:4] + "-" + value[4:6] + "-" + value[6:])
    except ValueError as exc:
        raise GeographyBlocked("invalid calendar value in original history") from exc


def _decimal(value: str, lo: str, hi: str, field: str) -> Decimal:
    try:
        result = Decimal(value.strip())
    except InvalidOperation as exc:
        raise GeographyBlocked(f"{field}: nonnumeric provider geography") from exc
    if not result.is_finite() or not Decimal(lo) <= result <= Decimal(hi):
        raise GeographyBlocked(f"{field}: invalid or out-of-domain geography")
    return result


def _parse_geography(raw: bytes) -> list[tuple[date, date, tuple[Decimal, Decimal, Decimal]]]:
    try:
        shape = _table_shape(raw)
    except MetadataShapeBlocked as exc:
        raise GeographyBlocked("original geography member size or encoding invalid") from exc
    if (not shape["header_recognized"]
            or shape["shape_status"] != "syntactically_consistent_unreviewed_columns"
            or shape["delimiter"] != "semicolon"
            or tuple(shape["columns"]) != COLUMNS):
        raise GeographyBlocked("actual source geography schema drifted from observed #960")
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";", strict=True)
        segments = []
        for row in reader:
            if len(segments) >= MAX_SOURCE_ROWS:
                raise GeographyBlocked("too many source geography history rows")
            if row["Stations_id"].strip().zfill(5) != evidence.EXPECTED_STATION_ID:
                raise GeographyBlocked("original history contains a different station")
            begin = _date_label(row["von_datum"])
            end = _date_label(row["bis_datum"])
            if begin > end:
                raise GeographyBlocked("provider geography interval inverted")
            height = _decimal(row["Stationshoehe"], "-500", "9000", "station_height")
            lat = _decimal(row["Geogr.Breite"], "-90", "90", "latitude")
            lon = _decimal(row["Geogr.Laenge"], "-180", "180", "longitude")
            segments.append((begin, end, (lat, lon, height)))
    except (UnicodeError, csv.Error, KeyError, TypeError) as exc:
        raise GeographyBlocked("original geography rows cannot be read safely") from exc
    if not segments:
        raise GeographyBlocked("original geography has no provider history rows")
    return segments


def _day_audit(segments):
    unique, missing, ambiguous = 0, 0, 0
    by_month = {}
    day = START
    while day <= END:
        candidates = [s for s, e, _pos in segments if s <= day <= e]
        month = day.strftime("%Y-%m")
        x = by_month.setdefault(month, {"candidate_unique_days": 0,
                                        "zero_candidate_days": 0,
                                        "multiple_candidate_days": 0})
        if len(candidates) == 1:
            unique += 1
            x["candidate_unique_days"] += 1
        elif not candidates:
            missing += 1
            x["zero_candidate_days"] += 1
        else:
            ambiguous += 1
            x["multiple_candidate_days"] += 1
        day += timedelta(days=1)
    return {
        "provisional_inclusive_candidate_unique_days": unique,
        "provisional_inclusive_zero_candidate_days": missing,
        "provisional_inclusive_multiple_candidate_days": ambiguous,
        "coverage_by_month": dict(sorted(by_month.items())),
    }


def analyze(path: Path, *, expected_sha256: str = evidence.EXPECTED_METADATA_SHA256) -> dict:
    try:
        receipt = evidence._collect(Path(path), expected_sha256,
                                    evidence.EXPECTED_STATION_ID)
        original = evidence._read_bounded_regular_snapshot(
            Path(path), receipt["metadata_asset"]["byte_size"])
    except (OSError, evidence.TemporalEvidenceError) as exc:
        raise GeographyBlocked("frozen provider metadata original did not pass exact-source gates") from exc
    if hashlib.sha256(original).hexdigest() != expected_sha256:
        raise GeographyBlocked("source bytes changed after original inspection")
    members = receipt["required_family_members"]["geography"]
    if len(members) != 1 or members[0]["path"] != GEO_MEMBER:
        raise GeographyBlocked("provider geography member set is not the observed exact original")
    try:
        with zipfile.ZipFile(io.BytesIO(original), "r") as z:
            raw = z.read(GEO_MEMBER)
    except (KeyError, OSError, zipfile.BadZipFile) as exc:
        raise GeographyBlocked("missing source geography member") from exc
    if hashlib.sha256(raw).hexdigest() != members[0]["sha256"]:
        raise GeographyBlocked("provider geography member SHA mismatch")
    try:
        segments = _parse_geography(raw)
    except MetadataShapeBlocked as exc:
        raise GeographyBlocked("provider geography schema unsupported") from exc
    result = _day_audit(segments)
    known_positions = len({(a, b, c) for _start, _end, (a, b, c) in segments})
    return {
        "profile": "opencatastrophe-dwd-00003-provisional-geographic-timeline-v0",
        "original_metadata_zip_sha256": expected_sha256,
        "geography_member_sha256": members[0]["sha256"],
        "pinned_measurement_zip_sha256": evidence.MEASUREMENT_SHA256,
        "original_geography_history_rows": len(segments),
        "distinct_original_geographic_positions": known_positions,
        "measurement_window": {"start": START.isoformat(), "end": END.isoformat()},
        **result,
        "interval_endpoint_interpretation": "PROVISIONAL_INCLUSIVE_RESEARCH_ONLY",
        "station_coordinates_persisted": False,
        "station_coordinates_emitted": False,
        "instrument_and_measurement_coherence_proven": False,
        "production_geographic_join_approved": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = analyze(args.source_zip)
    except GeographyBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
