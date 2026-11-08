#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, non-admission review of the original MaterialCities 2026.9 ADM GFA ZIP.

Only source-provided regional aggregate floor area is inspected. No building
locations, insurance exposures, sums insured or model-ready values are inferred.
The original provider ZIP belongs outside Git; this tool never downloads data.
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
import zipfile

SOURCE_ID = "leiden.materialcities.global-floor-material-stock.2026-9"
SOURCE_URL = "https://zenodo.org/records/22306604"
ARCHIVE_NAME = "MaterialCities_adm_gfa_csv.zip"
PUBLISHER_MD5 = "098f04f9b204d3102165ba4b3e2b8520"
MAX_ARCHIVE_BYTES = 12_000_000
MAX_EXPANDED_BYTES = 120_000_000
MAX_ROWS = 500_000
STRUCTURES = ("C", "M", "T", "S", "U")
FUNCTIONS = ("NR", "RS", "RM")
GFA_FIELDS = tuple(f"GFA_{function}_{structure}" for function in FUNCTIONS for structure in STRUCTURES)
ADM2_KEYS = ("GID_2", "ADM2_GID")
COUNTRY_KEYS = ("GID_0", "ADM0_GID", "ADM0_ISO", "ISO_0")


class MaterialCitiesPreflightError(ValueError):
    """The original archive or a proposed scientific interpretation is unsafe."""


def _number(value: str | None, field: str) -> float:
    if value is None or not value.strip():
        raise MaterialCitiesPreflightError(f"missing regional value: {field}")
    try:
        number = float(value)
    except ValueError as exc:
        raise MaterialCitiesPreflightError(f"invalid numeric regional value: {field}") from exc
    if not math.isfinite(number) or number < 0:
        raise MaterialCitiesPreflightError(f"negative or nonfinite regional value: {field}")
    return number


def _members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = archive.infolist()
    if not entries or len(entries) > 32:
        raise MaterialCitiesPreflightError("empty or unbounded archive inventory")
    if sum(x.file_size for x in entries) > MAX_EXPANDED_BYTES:
        raise MaterialCitiesPreflightError("unbounded expanded archive size")
    seen: set[str] = set()
    out = []
    for info in entries:
        name = info.filename
        parts = PurePosixPath(name).parts
        if (not name or name.startswith("/") or "\\" in name or
                ".." in parts or name in seen or info.flag_bits & 1):
            raise MaterialCitiesPreflightError("unsafe ZIP member identity")
        seen.add(name)
        if info.is_dir():
            continue
        if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise MaterialCitiesPreflightError("unsupported ZIP compression")
        if info.file_size > MAX_EXPANDED_BYTES:
            raise MaterialCitiesPreflightError("oversized ZIP member")
        if name.lower().endswith(".csv"):
            out.append(info)
    if not out or len(out) > 20:
        raise MaterialCitiesPreflightError("no bounded CSV member inventory")
    return out


def inspect_archive(blob: bytes, *, expected_md5: str = PUBLISHER_MD5,
                    country: str | None = None) -> dict:
    """Validate pinned ZIP bytes and report aggregates; never grant admission."""
    if (not isinstance(blob, bytes) or not 0 < len(blob) <= MAX_ARCHIVE_BYTES):
        raise MaterialCitiesPreflightError("original ZIP missing or over archive byte limit")
    if not re.fullmatch(r"[0-9a-f]{32}", expected_md5):
        raise MaterialCitiesPreflightError("invalid pinned provider MD5")
    if country is not None and not re.fullmatch(r"[A-Z]{3}", country):
        raise MaterialCitiesPreflightError("country must be an uppercase ISO3 code")
    md5 = hashlib.md5(blob).hexdigest()  # nosec: source-published integrity fingerprint
    if md5 != expected_md5:
        raise MaterialCitiesPreflightError("original publisher MD5 mismatch")
    sha256 = hashlib.sha256(blob).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            members = _members(archive)
            csv_files = []
            total_rows = 0
            selected_rows = 0
            mismatches = 0
            seen_regions: set[str] = set()
            # Bounded-memory accumulation; do not retain external source rows.
            totals = {field: 0.0 for field in GFA_FIELDS}
            gfa_sum = 0.0
            for info in members:
                with archive.open(info) as binary:
                    with io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
                        reader = csv.DictReader(stream)
                        header = reader.fieldnames
                        if not header or len(header) != len(set(header)):
                            raise MaterialCitiesPreflightError("invalid or duplicate CSV headers")
                        if "GFA" not in header:
                            continue
                        region_key = next((x for x in ADM2_KEYS if x in header), None)
                        if region_key is None:
                            continue  # ADM0/ADM1 CSVs are not ADM2 evidence.
                        absent = [x for x in GFA_FIELDS if x not in header]
                        if absent:
                            raise MaterialCitiesPreflightError("missing expected GFA function/type fields")
                        country_key = next((x for x in COUNTRY_KEYS if x in header), None)
                        if country is not None and country_key is None:
                            raise MaterialCitiesPreflightError("cannot verify requested country filter")
                        file_regions = 0
                        for row in reader:
                            total_rows += 1
                            if total_rows > MAX_ROWS or None in row:
                                raise MaterialCitiesPreflightError("unbounded or malformed original CSV")
                            region = (row.get(region_key) or "").strip()
                            if not region:
                                continue
                            if country is not None and (row.get(country_key) or "").strip() != country:
                                continue
                            if region in seen_regions:
                                raise MaterialCitiesPreflightError("duplicate ADM2 source region")
                            seen_regions.add(region)
                            total = _number(row.get("GFA"), "GFA")
                            components = [_number(row.get(field), field) for field in GFA_FIELDS]
                            component_sum = math.fsum(components)
                            if not math.isclose(total, component_sum, rel_tol=0.0001, abs_tol=1.0):
                                mismatches += 1
                            gfa_sum += total
                            for field, value in zip(GFA_FIELDS, components):
                                totals[field] += value
                            selected_rows += 1
                            file_regions += 1
                        csv_files.append({"member": info.filename, "adm2_rows": file_regions})
    except (zipfile.BadZipFile, UnicodeError, csv.Error, OSError, RuntimeError) as exc:
        raise MaterialCitiesPreflightError("unreadable original ZIP or CSV") from exc
    if selected_rows == 0:
        raise MaterialCitiesPreflightError("no ADM2 records meet the source scope")
    breakdown = totals
    return {
        "source_candidate_id": SOURCE_ID,
        "publisher_record": SOURCE_URL,
        "archive_filename": ARCHIVE_NAME,
        "publisher_md5": md5,
        "archive_sha256": sha256,
        "country_filter": country,
        "csv_members_used": csv_files,
        "rows_inspected": total_rows,
        "adm2_regions": selected_rows,
        "gross_floor_area_m2": gfa_sum,
        "gfa_function_structure_m2": breakdown,
        "regional_component_mismatch_count": mismatches,
        "research_only": True,
        "source_rights_reviewed": False,
        "scientific_fitness_reviewed": False,
        "site_geolocation_verified": False,
        "insured_portfolio_inferred": False,
        "insured_tiv_inferred": False,
        "model_input_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="Original MaterialCities 2026.9 ADM GFA ZIP, outside Git")
    parser.add_argument("--country", help="Optional GADM country ISO3, e.g. DEU")
    parser.add_argument("--out", type=Path, required=True, help="Local JSON research receipt")
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise MaterialCitiesPreflightError("refuse to overwrite existing research receipt")
        blob = args.archive.read_bytes()
        report = inspect_archive(blob, country=args.country)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, MaterialCitiesPreflightError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(f"RESEARCH ONLY: {report['adm2_regions']} ADM2 records reviewed; NO MODEL ADMISSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
