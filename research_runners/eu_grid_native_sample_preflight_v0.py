#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline-only original-source QA for 3 EU hazard/exposure leads.

Eurostat Census Grid 2021 V3: validated prefix with disclosure sentinels.
JRC GHS-AGE R2025A V1-0: exact embedded colour/age class legend.
DWD RADKLIM RW2017.002: reject known-bad 2021 original NetCDF archive.

Never fetch provider data, emit cell/geometry/claims records, or admit to CAT.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile, BadZipFile

CSV_FIELDS = (
    "GRD_ID,T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,"
    "SAME,CHG_IN,CHG_OUT,LAND_SURFACE,POPULATED,CNTR_ID"
).split(",")
STAT_FIELDS = CSV_FIELDS[1:14]
MISSING = {-8888: "confidentiality", -9999: "other_missing"}
GRID_RE = re.compile(r"CRS3035RES1000mN\d+E\d+")
COUNTRY_RE = re.compile(r"[A-Z]{2}(?:-[A-Z]{2})*")
UNALLOCATED_RE = re.compile(r"[A-Z]{2}_unallocated")
MAX_CENSUS_PREFIX_BYTES = 1_048_576
MAX_CENSUS_ROWS = 10000

GHSL_MEMBER = ("GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0.csv")
GHSL_EXPECTED_CRC = 0xabea4f34
GHSL_EXPECTED_BYTES = 209
GHSL_ROWS = [
    (0, 0, "not built-up"),
    (1, 1980, "< 1980"),
    (2, 1990, "1980 - 1990"),
    (3, 2000, "1990 - 2000"),
    (4, 2010, "2000 - 2010"),
    (5, 2020, "2010 - 2020"),
]
MAX_GHSL_ZIP_BYTES = 32_000_000
DWD_BASE = ("https://opendata.dwd.de/climate_environment/CDC/"
            "grids_germany/hourly/radolan/reproc/2017_002/netCDF/")


class SourceGateError(ValueError):
    pass


def _sha_matches(raw: bytes, expected: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise SourceGateError("original SHA-256 required (64 lowercase hex)")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise SourceGateError("source SHA-256 mismatch")
    return digest


def parse_census_prefix(raw: bytes, expected_sha256: str) -> dict:
    """Validate CSV *prefix* from exact 2021 V3 source, not complete coverage."""
    if not raw or len(raw) > MAX_CENSUS_PREFIX_BYTES or not raw.endswith(b"\n"):
        raise SourceGateError("CSV must be nonempty bounded complete lines")
    sha = _sha_matches(raw, expected_sha256)
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise SourceGateError("source not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(source, newline=""), strict=True)
    if reader.fieldnames != CSV_FIELDS:
        raise SourceGateError("wrong 2021 V3 CSV header or column order")
    summary = {
        "row_count": 0, "known_total_population_sum": 0,
        "nonzero_total_cells": 0, "zero_total_cells": 0,
        "missing_population_cells": 0, "missing_by_reason": {
            "confidentiality": 0, "other_missing": 0},
        "mf_total_mismatches": 0, "populated_flag_1": 0,
        "unallocated_rows": 0, "multicountry_cells": 0,
    }
    for row in reader:
        if summary["row_count"] >= MAX_CENSUS_ROWS:
            raise SourceGateError("source row limit exceeded")
        if None in row or any(v is None for v in row.values()):
            raise SourceGateError("unexpected or missing source CSV columns")
        grid = row["GRD_ID"]
        unallocated = bool(UNALLOCATED_RE.fullmatch(grid))
        if not unallocated and not GRID_RE.fullmatch(grid):
            raise SourceGateError("invalid EPSG3035 grid identifier")
        if not COUNTRY_RE.fullmatch(row["CNTR_ID"]):
            raise SourceGateError("invalid original country code(s)")
        summary["unallocated_rows"] += int(unallocated)
        summary["multicountry_cells"] += int("-" in row["CNTR_ID"])
        parsed = {}
        for field in STAT_FIELDS:
            value = row[field]
            if not re.fullmatch(r"-?\d+", value):
                raise SourceGateError("invalid statistical integer " + field)
            value = int(value)
            if value < 0 and value not in MISSING:
                raise SourceGateError("negative total is not a valid population/sentinel")
            parsed[field] = value
        try:
            land = Decimal(row["LAND_SURFACE"])
        except InvalidOperation as exc:
            raise SourceGateError("invalid LAND_SURFACE") from exc
        if not land.is_finite() or (
            land not in (Decimal(-8888), Decimal(-9999))
            and not Decimal(0) <= land <= Decimal(1)
        ):
            raise SourceGateError("land surface cannot exceed one square km")
        if row["POPULATED"] not in ("0", "1", "-8888", "-9999"):
            raise SourceGateError("invalid populated flag")
        summary["populated_flag_1"] += int(row["POPULATED"] == "1")
        total = parsed["T"]
        if total < 0:
            summary["missing_population_cells"] += 1
            summary["missing_by_reason"][MISSING[total]] += 1
        else:
            summary["known_total_population_sum"] += total
            summary["nonzero_total_cells"] += int(total > 0)
            summary["zero_total_cells"] += int(total == 0)
            if parsed["M"] >= 0 and parsed["F"] >= 0:
                summary["mf_total_mismatches"] += int(parsed["M"] + parsed["F"] != total)
        summary["row_count"] += 1
    if not summary["row_count"]:
        raise SourceGateError("empty source prefix")
    return {
        "source_id": "eurostat.gisco.census-population-grid.2021",
        "product_version": "Eurostat_Census-GRID_2021_V3",
        "evidence_kind": "bounded_original_csv_prefix",
        "prefix_sha256": sha,
        "source_bytes": len(raw),
        "summary": summary,
        "crs": "EPSG:3035",
        "grid_resolution_metres": 1000,
        "first_rows_are_not_representative": True,
        "source_is_incomplete": True,
        "source_cells_or_geometries_exported": False,
        "model_input_approved": False,
    }


def parse_ghsl_legend(raw: bytes, expected_sha256: str) -> dict:
    """Parse exactly the tiny original JRC 209-byte class legend, no raster."""
    if not isinstance(raw, bytes) or len(raw) != GHSL_EXPECTED_BYTES:
        raise SourceGateError("wrong JRC 1-km legend byte length")
    sha = _sha_matches(raw, expected_sha256)
    try:
        rows = list(csv.DictReader(io.StringIO(raw.decode("ascii"), newline="")))
    except (UnicodeError, csv.Error) as exc:
        raise SourceGateError("invalid original JRC legend CSV") from exc
    if not rows or list(rows[0]) != ["gridcode", "epoch_num", "epoch_txt", "R", "G", "B"]:
        raise SourceGateError("wrong JRC class schema")
    if len(rows) != len(GHSL_ROWS):
        raise SourceGateError("unexpected class count")
    for row, expected in zip(rows, GHSL_ROWS):
        try:
            triple = (int(row["gridcode"]), int(row["epoch_num"]), row["epoch_txt"])
            rgb = [int(row[x]) for x in ("R", "G", "B")]
        except (ValueError, TypeError, KeyError) as exc:
            raise SourceGateError("invalid class or colour") from exc
        if triple != expected or any(not 0 <= x <= 255 for x in rgb):
            raise SourceGateError("JRC age-class semantics drift")
    return {
        "source_id": "ec-jrc.ghsl.ghs-age.r2025a",
        "product_version": "GHS_AGE_1980102020_GLOBE_R2025A_54009_1000_V1_0",
        "source_legend_bytes": len(raw),
        "source_legend_sha256": sha,
        "class_codes": [x[0] for x in GHSL_ROWS],
        "epoch_labels": [x[2] for x in GHSL_ROWS],
        "raster_pixel_count_verified": False,
        "individual_building_construction_year_known": False,
        "model_input_approved": False,
    }


def verify_ghsl_zip(raw_zip: bytes, expected_sha256: str) -> dict:
    if not raw_zip or len(raw_zip) > MAX_GHSL_ZIP_BYTES:
        raise SourceGateError("unsafe GHSL archive size")
    digest = _sha_matches(raw_zip, expected_sha256)
    try:
        with ZipFile(io.BytesIO(raw_zip)) as arc:
            member = arc.getinfo(GHSL_MEMBER)
            if (member.file_size != GHSL_EXPECTED_BYTES
                or member.CRC != GHSL_EXPECTED_CRC
                or member.compress_type != 8):
                raise SourceGateError("GHSL legend ZIP metadata mismatch")
            legend = arc.read(member)
    except (BadZipFile, KeyError, OSError) as exc:
        raise SourceGateError("bad JRC original ZIP or missing class member") from exc
    result = parse_ghsl_legend(legend, hashlib.sha256(legend).hexdigest())
    result["full_archive_sha256"] = digest
    result["zip_member_crc_verified"] = True
    return result


def classify_dwd_radklim_2021_archive(url: str) -> dict:
    """No content fetch: file version/official supplement gate only."""
    if not isinstance(url, str) or not url.startswith(DWD_BASE):
        raise SourceGateError("not the reviewed original DWD CDC source")
    rejected = DWD_BASE + "2021/RW2017.002_2021_netcdf.tar.gz"
    corrected = DWD_BASE + "supplement/RW2017.002_2021_netcdf_supplement.tar.gz"
    if url == rejected:
        raise SourceGateError("DWD warns original 2021 NetCDF is incorrect")
    if url != corrected:
        raise SourceGateError("unreviewed archive/version: exact 2021 supplement required")
    return {
        "source_id": "dwd.radklim.rw.v2017.002",
        "source_archive_version": "RW2017.002_2021_netcdf_supplement",
        "expected_annual_year": 2021,
        "source_correction_warning_reviewed": True,
        "corrected_archive_bytes_validated": False,
        "netcdf_raster_scientifically_approved": False,
        "model_input_approved": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("eurostat-prefix","ghsl-legend","ghsl-zip","dwd-2021-url"),
                        required=True)
    parser.add_argument("--path", type=Path)
    parser.add_argument("--sha256")
    parser.add_argument("--dwd-url")
    args = parser.parse_args(argv)
    try:
        if args.mode == "dwd-2021-url":
            if args.path or args.sha256 or not args.dwd_url:
                raise SourceGateError("DWD gate accepts exact URL only")
            receipt = classify_dwd_radklim_2021_archive(args.dwd_url)
        else:
            if (not args.path or args.path.is_symlink()
                or not args.path.is_file() or not args.sha256):
                raise SourceGateError("offline existing file and external SHA required")
            limit = MAX_GHSL_ZIP_BYTES if args.mode == "ghsl-zip" else MAX_CENSUS_PREFIX_BYTES
            if args.path.stat().st_size > limit:
                raise SourceGateError("file too large")
            raw = args.path.read_bytes()
            if args.mode == "eurostat-prefix":
                receipt = parse_census_prefix(raw, args.sha256)
            elif args.mode == "ghsl-legend":
                receipt = parse_ghsl_legend(raw, args.sha256)
            else:
                receipt = verify_ghsl_zip(raw, args.sha256)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (SourceGateError, OSError) as exc:
        print(json.dumps({"status":"BLOCKED", "reason":str(exc),
                          "model_input_approved":False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
