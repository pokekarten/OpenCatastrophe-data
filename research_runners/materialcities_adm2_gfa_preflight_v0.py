#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded offline metadata/science preflight for original MaterialCities ADM2 GFA.

The source publisher's 2026.9 ADM2 CSV has *no* separate 'GFA' total.
Its 15 GFA_<function>_<structure> columns are the only published area
components. Their sum is not an independent ground-truth area check.

A region with GID_2 == '0' is not uniquely geocoded. Real GID_2 values
also have collisions in the source; neither case may silently become a
synthetic building roster. All findings remain non-admission research.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

SOURCE_ID = "leiden.materialcities.global-floor-material-stock.2026-9"
SOURCE_URL = "https://zenodo.org/records/22306604"
ARCHIVE_NAME = "MaterialCities_adm_gfa_csv.zip"
ADM2_MEMBER = "MaterialCities_adm_gfa_ADM2.csv"
PUBLISHER_MD5 = "098f04f9b204d3102165ba4b3e2b8520"
ORIGINAL_SHA256 = "ca7e01d65b9ac366c67505e2af0e6fdf2d746f2a65a231e3af4d3dc9c1a23a38"
MAX_ARCHIVE_BYTES = 12_000_000
MAX_EXPANDED_BYTES = 120_000_000
MAX_ROWS = 500_000
FUNCTIONS = ("NR", "RS", "RM")
STRUCTURES = ("C", "M", "S", "T", "U")
GFA_FIELDS = tuple(f"GFA_{function}_{structure}" for function in FUNCTIONS for structure in STRUCTURES)
GID_PATTERN = re.compile(r"(?:[A-Z]{3}|Z\d{2})\.\d+\.\d+_\d+\Z")
COUNTRY_PATTERN = re.compile(r"[A-Z]{3}\Z")
SOURCE_COUNTRY_PATTERN = re.compile(r"(?:[A-Z]{3}|Z\d{2})\Z")


class MaterialCitiesPreflightError(ValueError):
    """Source integrity, source-shape or numeric evidence is not verifiable."""


def _number(value: str | None, field: str) -> float:
    if value is None or not value.strip():
        raise MaterialCitiesPreflightError(f"missing regional value: {field}")
    try:
        x = float(value)
    except ValueError as exc:
        raise MaterialCitiesPreflightError(f"invalid regional number in {field}") from exc
    if not math.isfinite(x) or x < 0:
        raise MaterialCitiesPreflightError(f"negative/nonfinite regional number in {field}")
    return x


def _adm2_member(archive: zipfile.ZipFile) -> zipfile.ZipInfo:
    entries = archive.infolist()
    if not entries or len(entries) > 32:
        raise MaterialCitiesPreflightError("empty or unbounded ZIP inventory")
    if sum(info.file_size for info in entries) > MAX_EXPANDED_BYTES:
        raise MaterialCitiesPreflightError("expanded ZIP exceeds source review cap")
    seen = set()
    target = None
    for info in entries:
        name = info.filename
        if (not name or name.startswith("/") or "\\" in name or ".." in PurePosixPath(name).parts
                or name in seen or info.flag_bits & 1):
            raise MaterialCitiesPreflightError("unsafe ZIP member identity")
        seen.add(name)
        if info.is_dir():
            continue
        if (info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or info.file_size > MAX_EXPANDED_BYTES):
            raise MaterialCitiesPreflightError("unsupported or oversized ZIP member")
        if name == ADM2_MEMBER:
            target = info
    if target is None:
        raise MaterialCitiesPreflightError("original ADM2 CSV member absent")
    return target


def inspect_archive(blob: bytes, *, expected_md5: str = PUBLISHER_MD5,
                    expected_sha256: str = ORIGINAL_SHA256, country: str | None = None) -> dict:
    """Inspect original or synthetic exact-checksum ZIP; never authorize model use."""
    if not isinstance(blob, bytes) or not 0 < len(blob) <= MAX_ARCHIVE_BYTES:
        raise MaterialCitiesPreflightError("source ZIP missing or exceeds byte cap")
    if (not re.fullmatch(r"[a-f0-9]{32}", expected_md5)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)):
        raise MaterialCitiesPreflightError("invalid pinned original source digests")
    if country is not None and not COUNTRY_PATTERN.fullmatch(country):
        raise MaterialCitiesPreflightError("country must be uppercase ISO3")
    actual_md5 = hashlib.md5(blob).hexdigest()  # nosec: compare publisher fingerprint only
    actual_sha256 = hashlib.sha256(blob).hexdigest()
    if actual_md5 != expected_md5 or actual_sha256 != expected_sha256:
        raise MaterialCitiesPreflightError("original source digest mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            info = _adm2_member(archive)
            with archive.open(info) as binary:
                with io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
                    reader = csv.DictReader(stream)
                    header = reader.fieldnames
                    if (not header or len(header) != len(set(header)) or
                            not {"GID_0", "GID_2", *GFA_FIELDS}.issubset(header)):
                        raise MaterialCitiesPreflightError("unexpected original ADM2 CSV schema")
                    if "GFA" in header:
                        raise MaterialCitiesPreflightError("unreviewed source: total GFA column appeared")
                    row_count = 0
                    selected_count = 0
                    unidentified_count = 0
                    non_iso_country_count = 0
                    collision_count = 0
                    collided_ids = set()
                    seen_region_ids = set()
                    component_totals = {field: 0.0 for field in GFA_FIELDS}
                    source_row_total = 0.0
                    keyed_row_total = 0.0
                    for row in reader:
                        row_count += 1
                        if row_count > MAX_ROWS or None in row:
                            raise MaterialCitiesPreflightError("malformed or unbounded original CSV")
                        row_country = (row.get("GID_0") or "").strip()
                        if not SOURCE_COUNTRY_PATTERN.fullmatch(row_country):
                            raise MaterialCitiesPreflightError("missing/invalid original country code")
                        if country is not None and row_country != country:
                            continue
                        selected_count += 1
                        if not COUNTRY_PATTERN.fullmatch(row_country):
                            non_iso_country_count += 1
                        try:
                            components = [_number(row.get(field), field) for field in GFA_FIELDS]
                            total = math.fsum(components)
                        except OverflowError as exc:
                            raise MaterialCitiesPreflightError("unrepresentable regional area") from exc
                        if not math.isfinite(total):
                            raise MaterialCitiesPreflightError("nonfinite regional component sum")
                        source_row_total += total
                        for field, value in zip(GFA_FIELDS, components):
                            component_totals[field] += value
                        gid = (row.get("GID_2") or "").strip()
                        if not GID_PATTERN.fullmatch(gid) or not gid.startswith(row_country + "."):
                            unidentified_count += 1
                            continue
                        keyed_row_total += total
                        if gid in seen_region_ids:
                            collision_count += 1
                            collided_ids.add(gid)
                        seen_region_ids.add(gid)
    except (zipfile.BadZipFile, UnicodeError, csv.Error, OSError, RuntimeError) as exc:
        raise MaterialCitiesPreflightError("unreadable original ZIP or CSV") from exc
    if selected_count == 0:
        raise MaterialCitiesPreflightError("no ADM2 records in the selected source scope")
    # These sums are research diagnostics over raw rows, not unique building
    # assets, independent area controls or insurer-account model input.
    return {
        "source_candidate_id": SOURCE_ID,
        "publisher_record": SOURCE_URL,
        "original_archive": ARCHIVE_NAME,
        "original_member": ADM2_MEMBER,
        "publisher_md5": actual_md5,
        "archive_sha256": actual_sha256,
        "original_archive_bytes": len(blob),
        "country_filter": country,
        "csv_rows_scanned": row_count,
        "source_adm2_rows_selected": selected_count,
        "source_rows_without_unique_adm2_key": unidentified_count,
        "non_iso_source_country_rows": non_iso_country_count,
        "duplicate_key_occurrences": collision_count,
        "distinct_collided_region_keys": len(collided_ids),
        "distinct_valid_adm2_keys": len(seen_region_ids),
        "complete_unique_region_keyset": unidentified_count == 0 and collision_count == 0,
        "source_row_gross_floor_area_m2": source_row_total,
        "keyed_row_gross_floor_area_m2": keyed_row_total,
        "source_row_gfa_components_m2": component_totals,
        "independent_gfa_total_in_original_source": False,
        "rights_reviewed": False,
        "commercial_use_cleared": False,
        "scientific_model_admitted": False,
        "actual_insured_sites_proven": False,
        "insurer_tiv_inferred": False,
        "research_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Original ZIP outside Git")
    parser.add_argument("--country", help="Optional GADM country code, e.g. DEU")
    parser.add_argument("--out", type=Path, required=True, help="Non-public research JSON receipt")
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise MaterialCitiesPreflightError("refuse to overwrite existing receipt")
        report = inspect_archive(args.archive.read_bytes(), country=args.country)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, MaterialCitiesPreflightError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print("RESEARCH ONLY:", report["source_adm2_rows_selected"],
          "source rows; unique geography:", report["complete_unique_region_keyset"],
          "; NO MODEL ADMISSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
