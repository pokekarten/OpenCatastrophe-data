#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, aggregate-only FRS facility × native FRS_NAICS_CODES.csv audit.

A legal/native-format research slice is NOT an authenticated EPA original file.
NAICS codes are facility classification candidates, NOT insured occupancy/TIV.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

try:
    from .epa_frs_native_projection_v0 import _release, MAX_BYTES, MAX_ROWS
except ImportError:  # Direct script invocation from repository root.
    from epa_frs_native_projection_v0 import _release, MAX_BYTES, MAX_ROWS

PROJECTION_HEADERS = ("frs_id", "country_code", "latitude", "longitude")
NAICS_HEADERS = ("REGISTRY_ID", "PGM_SYS_ACRNM", "PGM_SYS_ID", "NAICS_CODE")
HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,99}\Z")
PROGRAM_FIELD = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,89}\Z")


class NAICSAuditBlocked(ValueError):
    """Cannot safely interpret NAICS source slice as one per insured asset."""


def _csv(blob: bytes, sha: str, required: tuple[str, ...], label: str) -> list[dict]:
    if not isinstance(sha, str) or not HEX_SHA.fullmatch(sha):
        raise NAICSAuditBlocked(label + ": expected lowercase SHA-256")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise NAICSAuditBlocked(label + ": invalid bounded source slice")
    if hashlib.sha256(blob).hexdigest() != sha:
        raise NAICSAuditBlocked(label + ": supplied slice SHA-256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig"), newline=""), strict=True)
        cols = tuple(reader.fieldnames or ())
        if len(cols) != len(set(cols)) or not all(c in cols for c in required):
            raise NAICSAuditBlocked(label + ": missing or repeated required columns")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise NAICSAuditBlocked(label + ": too many rows")
            if None in row or any(v is None or v != v.strip() for v in row.values()):
                raise NAICSAuditBlocked(label + ": malformed row")
            rows.append(row)
        if not rows:
            raise NAICSAuditBlocked(label + ": expected rows")
        return rows
    except (csv.Error, UnicodeError) as exc:
        raise NAICSAuditBlocked(label + ": invalid CSV") from exc


def audit_frs_naics(frs_blob: bytes, frs_sha: str, naics_blob: bytes, naics_sha: str,
                   *, frs_vintage: str, naics_vintage: str) -> dict:
    _release(frs_vintage)
    _release(naics_vintage)
    # Never use facility/NAICS values as one-to-one portfolio records.
    facilities = _csv(frs_blob, frs_sha, PROJECTION_HEADERS, "FRS projection")
    codes = _csv(naics_blob, naics_sha, NAICS_HEADERS, "native FRS NAICS slice")
    known_ids = set()
    for row in facilities:
        key = row["frs_id"]
        if not SAFE_ID.fullmatch(key) or row["country_code"] != "US":
            raise NAICSAuditBlocked("invalid FRS projection scope or identifier")
        if key in known_ids:
            raise NAICSAuditBlocked("duplicate FRS projection ID")
        known_ids.add(key)
    naics_for_facility: dict[str, set[str]] = defaultdict(set)
    seen_native = set()
    out_of_scope_rows = 0
    repeated_codes_across_programs = 0
    for row in codes:
        key, code = row["REGISTRY_ID"], row["NAICS_CODE"]
        if not SAFE_ID.fullmatch(key) or not re.fullmatch(r"[0-9]{6}", code):
            raise NAICSAuditBlocked("invalid original FRS identifier or six-digit NAICS code")
        program = row["PGM_SYS_ACRNM"]
        system = row["PGM_SYS_ID"]
        if not PROGRAM_FIELD.fullmatch(program) or not PROGRAM_FIELD.fullmatch(system):
            raise NAICSAuditBlocked("invalid FRS program identity")
        triple = (program, system, key, code)
        if triple in seen_native:
            raise NAICSAuditBlocked("duplicated native FRS-NAICS program-code relationship")
        seen_native.add(triple)
        if key not in known_ids:
            out_of_scope_rows += 1
            continue
        if code in naics_for_facility[key]:
            repeated_codes_across_programs += 1
        naics_for_facility[key].add(code)
    covered = len(naics_for_facility)
    multicoded = sum(1 for codeset in naics_for_facility.values() if len(codeset) > 1)
    # NAICS 2-digit sector summaries count each *facility at most once per sector*;
    # never sum across sectors as physical facility or insured value counts.
    sectors = Counter()
    for codeset in naics_for_facility.values():
        for prefix in {code[:2] for code in codeset}:
            sectors[prefix] += 1
    return {
        "audit": "epa-frs-native-naics-multiplicity-v0",
        "frs_vintage": frs_vintage, "naics_vintage": naics_vintage,
        "frs_projection_sha256": frs_sha, "naics_native_slice_sha256": naics_sha,
        "frs_facilities": len(facilities), "native_naics_rows": len(codes),
        "frs_facilities_with_at_least_one_naics": covered,
        "frs_facilities_with_no_naics_in_selected_slice": len(facilities) - covered,
        "facilities_with_multiple_distinct_naics": multicoded,
        "naics_rows_for_facilities_outside_selected_perimeter": out_of_scope_rows,
        "repeated_same_code_across_distinct_programs": repeated_codes_across_programs,
        "facility_sector_memberships_by_naics2": dict(sorted(sectors.items())),
        "state": "REVIEW_MULTIPLE_OCCUPANCIES" if multicoded or out_of_scope_rows else "RESEARCH_CLASSIFICATIONS_ONLY",
        "sector_memberships_are_additive_exposure_counts": False,
        "native_slice_proves_epa_original_byte_identity": False,
        "naics_is_insurance_line_or_tiv": False,
        "source_rights_or_model_admission_granted": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("frs", "naics"):
        ap.add_argument("--"+name+"-csv", type=Path, required=True)
        ap.add_argument("--"+name+"-sha256", required=True)
        ap.add_argument("--"+name+"-vintage", required=True)
    args = ap.parse_args(argv)
    try:
        blobs = []
        for name in ("frs", "naics"):
            f = getattr(args, name+"_csv")
            if f.is_symlink() or not f.is_file() or f.stat().st_size > MAX_BYTES:
                raise NAICSAuditBlocked("expected bounded regular CSV outside Git")
            blobs.extend((f.read_bytes(), getattr(args, name+"_sha256")))
        result = audit_frs_naics(*blobs, frs_vintage=args.frs_vintage,
                                 naics_vintage=args.naics_vintage)
    except (OSError, NAICSAuditBlocked, ValueError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["state"] == "REVIEW_MULTIPLE_OCCUPANCIES" else 0


if __name__ == "__main__":
    raise SystemExit(main())
