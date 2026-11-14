#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only offline EPA FRS 'EIA-860' ORIS plant identity linkage.

Caller-projected EIA annual plant IDs are NOT the raw EIA workbook.
EPA native-format CSV slices are NOT authenticated publisher originals.
This audit does not create a GEM asset link or insurer portfolio allocation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re

MAX_BYTES = 2_000_000
MAX_ROWS = 10_000
FRS_HEADERS = ("REGISTRY_ID", "PGM_SYS_ACRNM", "PGM_SYS_ID")
EIA_HEADERS = ("plant_id_eia",)
HEX = re.compile(r"[0-9a-f]{64}\Z")
FRS_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,35}\Z")
CLEAN = re.compile(r"[ -~]{1,90}\Z")


class EIAFRSBridgeBlocked(ValueError):
    """No evidence-based source identity join is possible."""


def _read(blob: bytes, sha: str, fields: tuple[str, ...], name: str) -> list[dict]:
    if not isinstance(sha, str) or not HEX.fullmatch(sha):
        raise EIAFRSBridgeBlocked(name + ": valid lowercase SHA-256 required")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise EIAFRSBridgeBlocked(name + ": invalid bounded byte slice")
    if hashlib.sha256(blob).hexdigest() != sha:
        raise EIAFRSBridgeBlocked(name + ": supplied slice SHA-256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig"), newline=""), strict=True)
        headers = tuple(reader.fieldnames or ())
        if len(headers) != len(set(headers)) or not all(x in headers for x in fields):
            raise EIAFRSBridgeBlocked(name + ": missing or duplicate columns")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise EIAFRSBridgeBlocked(name + ": row count exceeds bounded limit")
            if None in row or any(v is None or v != v.strip() for v in row.values()):
                raise EIAFRSBridgeBlocked(name + ": malformed row")
            rows.append(row)
        if not rows:
            raise EIAFRSBridgeBlocked(name + ": at least one row required")
        return rows
    except (csv.Error, UnicodeError) as exc:
        raise EIAFRSBridgeBlocked(name + ": invalid CSV") from exc


def _plant_id(raw: str) -> str:
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9]{1,6}", raw) or int(raw) < 1:
        raise EIAFRSBridgeBlocked("invalid EIA plant/ORIS numeric ID")
    # EIA reference codes and EPA EIA-860 programme IDs may pad leading zeros.
    return str(int(raw))


def _asof(release: str) -> str:
    if not isinstance(release, str) or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", release):
        raise EIAFRSBridgeBlocked("explicit FRS YYYY-MM-DD release required")
    try:
        y, m, d = (int(v) for v in release.split("-"))
        day = date(y, m, d)
    except ValueError as exc:
        raise EIAFRSBridgeBlocked("FRS invalid calendar release date") from exc
    if not date(2020, 1, 1) <= day <= date.today():
        raise EIAFRSBridgeBlocked("FRS unsupported or future release date")
    return release


def audit_eia_frs(frs_blob: bytes, frs_sha: str, eia_blob: bytes, eia_sha: str,
                  *, frs_release: str, eia_reporting_year: int) -> dict:
    _asof(frs_release)
    if type(eia_reporting_year) is not int or eia_reporting_year != 2025:
        raise EIAFRSBridgeBlocked("pin EIA annual reporting year 2025 for this pilot")
    frs = _read(frs_blob, frs_sha, FRS_HEADERS, "EPA FRS program links")
    eia = _read(eia_blob, eia_sha, EIA_HEADERS, "EIA annual plant projection")
    ids = set()
    for row in eia:
        p = _plant_id(row["plant_id_eia"])
        if p in ids:
            raise EIAFRSBridgeBlocked("duplicate EIA plant identity after zero-padding normalization")
        ids.add(p)
    by_plant: dict[str, set[str]] = defaultdict(set)
    by_frs: dict[str, set[str]] = defaultdict(set)
    other_programs = 0
    repeated_original_link = 0
    known = set()
    for row in frs:
        fid, program, pid = row["REGISTRY_ID"], row["PGM_SYS_ACRNM"], row["PGM_SYS_ID"]
        if not FRS_ID.fullmatch(fid) or not CLEAN.fullmatch(program) or not CLEAN.fullmatch(pid):
            raise EIAFRSBridgeBlocked("invalid original EPA programme or FRS ID")
        if program != "EIA-860":
            other_programs += 1
            continue
        p = _plant_id(pid)
        if (fid, p) in known:
            repeated_original_link += 1
        known.add((fid, p))
        by_plant[p].add(fid)
        by_frs[fid].add(p)
    # Never index a defaultdict during classification: doing so would create
    # empty entries for missing EIA IDs and falsify the missing/extra counts.
    unique = multi = missing = 0
    for p in ids:
        frs_ids = by_plant.get(p)
        if not frs_ids:
            missing += 1
        elif len(frs_ids) != 1 or len(by_frs[next(iter(frs_ids))]) != 1:
            multi += 1
        else:
            unique += 1
    extra = sum(1 for p in by_plant if p not in ids)
    if unique + multi + missing != len(ids):
        raise EIAFRSBridgeBlocked("EIA plant-row conservation failed")
    return {
        "audit": "epa-frs-eia860-oris-crosswalk-v0",
        "frs_release": frs_release, "eia_reporting_year": eia_reporting_year,
        "frs_program_links_slice_sha256": frs_sha,
        "eia_normalized_plant_projection_sha256": eia_sha,
        "eia_plant_rows": len(eia), "frs_program_link_rows": len(frs),
        "non_eia860_program_rows": other_programs,
        "unique_eia_plant_to_frs_research_candidates": unique,
        "eia_plants_with_cardinality_conflict": multi,
        "eia_plants_not_in_supplied_frs_slice": missing,
        "frs_eia860_plant_ids_outside_eia_projection": extra,
        "repeated_identical_eia860_program_links": repeated_original_link,
        "plant_rows_conserved": True,
        "state": "REVIEW_IDENTITY_CARDINALITY_OR_SCOPE" if multi or extra else (
            "RESEARCH_ORIS_ID_CANDIDATES_ONLY" if unique else "NO_EIA860_ID_CANDIDATES"),
        "eia_to_gem_asset_ids_confirmed": False,
        "frs_to_eia_original_provider_files_authenticated": False,
        "plant_id_is_generator_or_building_id": False,
        "facility_ownership_or_insurance_inferred": False,
        "source_rights_or_model_admission_granted": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frs-program-links-slice", type=Path, required=True)
    ap.add_argument("--frs-sha256", required=True)
    ap.add_argument("--frs-release", required=True)
    ap.add_argument("--eia-plant-projection", type=Path, required=True)
    ap.add_argument("--eia-sha256", required=True)
    ap.add_argument("--eia-reporting-year", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        files = (args.frs_program_links_slice, args.eia_plant_projection)
        if any(f.is_symlink() or not f.is_file() or f.stat().st_size > MAX_BYTES for f in files):
            raise EIAFRSBridgeBlocked("expected two bounded regular local source slices")
        result = audit_eia_frs(
            files[0].read_bytes(), args.frs_sha256, files[1].read_bytes(), args.eia_sha256,
            frs_release=args.frs_release, eia_reporting_year=args.eia_reporting_year)
    except (OSError, EIAFRSBridgeBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["state"] == "REVIEW_IDENTITY_CARDINALITY_OR_SCOPE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
