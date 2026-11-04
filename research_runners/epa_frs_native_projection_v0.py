#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded native-format US EPA FRS_FACILITIES.csv *slice* -> FRS projection.

Publisher original ZIP/file receipts must be verified separately. No HTTP
requests, provider archive downloads, exposure estimation or approved data writes.
Original source data and local projections remain OUTSIDE the public Git repo.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re

MAX_BYTES = 2_000_000
MAX_ROWS = 10_000
REQUIRED = ("REGISTRY_ID", "LATITUDE_MEASURE", "LONGITUDE_MEASURE")
OUTPUT = ("frs_id", "country_code", "latitude", "longitude")
HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,35}\Z")
RELEASE = re.compile(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}\Z")


class FRSProjectionBlocked(ValueError):
    """Original file identity, input semantics or output boundary unresolved."""


def _release(value: str) -> str:
    if not isinstance(value, str) or not RELEASE.fullmatch(value):
        raise FRSProjectionBlocked("fixed FRS YYYY-MM-DD release required")
    try:
        y, m, d = (int(x) for x in value.split("-"))
        day = date(y, m, d)
    except ValueError as exc:
        raise FRSProjectionBlocked("invalid FRS release date") from exc
    if not date(2020, 1, 1) <= day <= date.today():
        raise FRSProjectionBlocked("future or out-of-scope FRS vintage")
    return value


def _coord(value: str, axis: str) -> str:
    if value == "":
        return ""
    if len(value) > 30 or not re.fullmatch(r"[+-]?[0-9]{1,3}(?:\.[0-9]{1,15})?", value):
        raise FRSProjectionBlocked(axis + ": unrecognized source coordinate representation")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise FRSProjectionBlocked(axis + ": invalid decimal") from exc
    low, high = (-90, 90) if axis == "latitude" else (-180, 180)
    if not low <= number <= high:
        raise FRSProjectionBlocked(axis + ": outside geographic coordinate range")
    return value


def project_native_frs(original: bytes, expected_sha256: str, *,
                       release_date: str, coordinates_approved: bool = False) -> tuple[bytes, dict]:
    """Project caller-provided native-format CSV slice; not original provider proof.

    Coordinates are intentionally suppressed by default. Permit passing them
    through only after an upstream review establishes geographic reference
    system, source coordinate quality and policy for the exact release.
    """
    _release(release_date)
    if not isinstance(coordinates_approved, bool):
        raise FRSProjectionBlocked("coordinate approval must be an explicit boolean")
    if not isinstance(expected_sha256, str) or not HEX_SHA.fullmatch(expected_sha256):
        raise FRSProjectionBlocked("expected native-slice lowercase SHA-256")
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise FRSProjectionBlocked("native-format CSV slice empty or over bounded limit")
    actual = hashlib.sha256(original).hexdigest()
    if actual != expected_sha256:
        raise FRSProjectionBlocked("supplied CSV slice SHA-256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(original.decode("utf-8-sig"), newline=""), strict=True)
        headers = tuple(reader.fieldnames or ())
        if len(headers) != len(set(headers)) or not all(x in headers for x in REQUIRED):
            raise FRSProjectionBlocked("native-format FRS_FACILITIES columns missing or repeated")
        rows = []
        seen = set()
        missing_coordinates = 0
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise FRSProjectionBlocked("bounded FRS row limit exceeded")
            if None in row or any(v is None or v != v.strip() for v in row.values()):
                raise FRSProjectionBlocked("malformed FRS CSV row or whitespace")
            key = row["REGISTRY_ID"]
            if not SOURCE_ID.fullmatch(key):
                raise FRSProjectionBlocked("invalid FRS original registry ID")
            if key in seen:
                raise FRSProjectionBlocked("duplicate native FRS registry ID in bounded subset")
            seen.add(key)
            lat = _coord(row["LATITUDE_MEASURE"], "latitude")
            lon = _coord(row["LONGITUDE_MEASURE"], "longitude")
            if bool(lat) != bool(lon):
                raise FRSProjectionBlocked("partial FRS coordinates must be reviewed")
            if not lat:
                missing_coordinates += 1
            if not coordinates_approved:
                lat = lon = ""
            rows.append({"frs_id": key, "country_code": "US", "latitude": lat, "longitude": lon})
    except (UnicodeError, csv.Error) as exc:
        raise FRSProjectionBlocked("malformed UTF-8 FRS CSV") from exc
    if not rows:
        raise FRSProjectionBlocked("native subset has no records")
    rows.sort(key=lambda x: x["frs_id"])
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, OUTPUT, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    projection = stream.getvalue().encode("utf-8")
    return projection, {
        "state": "RESEARCH_PROJECTION_ONLY",
        "native_product": "EPA_ECHO_FRS_FACILITIES_CSV",
        "source_vintage": release_date,
        "source_native_csv_slice_sha256": actual,
        "normalized_projection_sha256": hashlib.sha256(projection).hexdigest(),
        "rows": len(rows),
        "native_rows_without_both_coordinates": missing_coordinates,
        "projected_coordinates_suppressed": not coordinates_approved,
        "country_code_assigned_from_product_scope": "US",
        "projection_preserves_source_ids": True,
        "publisher_original_file_bytes_authenticated": False,
        "native_csv_slice_is_publisher_original": False,
        "source_rights_or_model_admission_granted": False,
        "insured_asset_or_tiv_inferred": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-facilities-slice-csv", type=Path, required=True)
    ap.add_argument("--native-slice-sha256", required=True)
    ap.add_argument("--release-date", required=True)
    ap.add_argument("--output", type=Path, required=True)
    # Deliberately no CLI switch to override coordinate suppression;
    # that gate requires a separately reviewed/native-to-WGS84 transform.
    args = ap.parse_args(argv)
    try:
        if (args.native_facilities_slice_csv.is_symlink() or not args.native_facilities_slice_csv.is_file() or
                args.native_facilities_slice_csv.stat().st_size > MAX_BYTES):
            raise FRSProjectionBlocked("expected bounded local native-format CSV slice")
        out = args.output.expanduser().absolute()
        repository = Path(__file__).resolve().parents[1]
        if out == repository or repository in out.parents or out.is_symlink():
            raise FRSProjectionBlocked("output must remain outside public repository")
        projection, report = project_native_frs(
            args.native_facilities_slice_csv.read_bytes(), args.native_slice_sha256,
            release_date=args.release_date)
        # Exclusive create refuses overwrites and directories, and never prints source IDs.
        with out.open("xb") as handle:
            handle.write(projection)
    except (OSError, FRSProjectionBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
