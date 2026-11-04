#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Audit exact, already-fetched EPA FRS JSON API response *bytes* offline.

Only three fixed public EIA-860 Delaware research queries are in scope.
No live network, raw-source-file persistence, inferred EIA-2025/GEM membership,
insurer assignment, loss or CAT data admission. A body digest is not a ZIP receipt.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re

ROOT_URL = "https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities"
COHORTS = {
    city: (ROOT_URL + "?pgm_sys_acrnm=EIA-860&state_abbr=DE&city_name=" +
           city + "&output=JSON&program_output=yes")
    for city in ("DOVER", "NEWARK", "WILMINGTON")
}
SHA = re.compile(r"[0-9a-f]{64}\Z")
FRS_ID = re.compile(r"[0-9]{10,16}\Z")
EIA_PLANT_ID = re.compile(r"[0-9]{1,6}\Z")
MAX_BYTES = 64_000
MAX_FACILITIES = 30
MAX_PROGRAMS = 150


class FRSOriginalReceiptBlocked(ValueError):
    """Source response identity or bounded official FRS semantics not verified."""


def _no_duplicate_pairs(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise FRSOriginalReceiptBlocked("duplicate original FRS JSON key")
        seen[key] = value
    return seen


def _plant(raw):
    if type(raw) is not str or not EIA_PLANT_ID.fullmatch(raw) or int(raw) == 0:
        raise FRSOriginalReceiptBlocked("invalid numeric original EIA-860 plant code")
    return str(int(raw))


def inspect_original_response(original: bytes, expected_sha256: str, *,
                              cohort: str, observed_date: str) -> dict:
    """Return only counts and byte receipt, never actual site records or coordinates."""
    if cohort not in COHORTS:
        raise FRSOriginalReceiptBlocked("cohort must be one of three fixed DE city queries")
    if type(observed_date) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", observed_date):
        raise FRSOriginalReceiptBlocked("explicit observation calendar day required")
    try:
        day = date.fromisoformat(observed_date)
    except ValueError as exc:
        raise FRSOriginalReceiptBlocked("invalid observed calendar day") from exc
    if not date(2026, 11, 4) <= day <= date.today():
        raise FRSOriginalReceiptBlocked("out-of-period or future observation date")
    if type(original) is not bytes or not 0 < len(original) <= MAX_BYTES:
        raise FRSOriginalReceiptBlocked("empty or oversized original API body")
    if type(expected_sha256) is not str or not SHA.fullmatch(expected_sha256):
        raise FRSOriginalReceiptBlocked("expected exact lowercase body SHA-256")
    actual = hashlib.sha256(original).hexdigest()
    if actual != expected_sha256:
        raise FRSOriginalReceiptBlocked("original HTTP body SHA-256 mismatch")
    try:
        obj = json.loads(original.decode("utf-8-sig"),
                         object_pairs_hook=_no_duplicate_pairs,
                         parse_constant=lambda x: (_ for _ in ()).throw(
                             FRSOriginalReceiptBlocked("non-finite JSON constant")))
    except (ValueError, UnicodeError, TypeError) as exc:
        raise FRSOriginalReceiptBlocked("malformed original FRS JSON response") from exc
    records = obj.get("Results", {}).get("FRSFacility") if isinstance(obj, dict) else None
    if not isinstance(records, list) or not 0 < len(records) <= MAX_FACILITIES:
        raise FRSOriginalReceiptBlocked("no bounded FRSFacility list")
    seen_frs = set()
    by_plant = Counter()
    eia_edges = 0
    multi_frs = 0
    no_eia = 0
    other_programs = 0
    for facility in records:
        if not isinstance(facility, dict):
            raise FRSOriginalReceiptBlocked("invalid FRS facility object")
        fid = facility.get("RegistryId")
        if type(fid) is not str or not FRS_ID.fullmatch(fid) or fid in seen_frs:
            raise FRSOriginalReceiptBlocked("invalid or duplicate FRS RegistryId")
        seen_frs.add(fid)
        if (facility.get("StateAbbr") != "DE" or
                str(facility.get("CityName", "")).upper() != cohort):
            raise FRSOriginalReceiptBlocked("provider facility outside exact city/state query")
        programs = facility.get("ProgramFacilities")
        if not isinstance(programs, list) or len(programs) > MAX_PROGRAMS:
            raise FRSOriginalReceiptBlocked("missing or excessive programme links")
        matches = set()
        for row in programs:
            if not isinstance(row, dict):
                raise FRSOriginalReceiptBlocked("invalid programme link object")
            acronym = row.get("ProgramSystemAcronym")
            pid = row.get("ProgramSystemId")
            if type(acronym) is not str or type(pid) is not str:
                raise FRSOriginalReceiptBlocked("missing FRS programme identity fields")
            if acronym == "EIA-860":
                p = _plant(pid)
                if p in matches:
                    raise FRSOriginalReceiptBlocked("duplicate FRS-EIA programme link")
                matches.add(p)
            else:
                other_programs += 1
        if not matches:
            no_eia += 1
        if len(matches) > 1:
            multi_frs += 1
        for p in matches:
            by_plant[p] += 1
            eia_edges += 1
    multiple_frs_per_plant = sum(count > 1 for count in by_plant.values())
    return {
        "audit": "epa-frs-eia860-original-json-city-v0",
        "cohort": cohort,
        "api_url": COHORTS[cohort],
        "observed_date": observed_date,
        "source_response_body_sha256": actual,
        "source_response_body_bytes": len(original),
        "frs_facility_rows": len(records),
        "frs_facilities_without_eia860_link": no_eia,
        "eia860_program_link_rows": eia_edges,
        "distinct_eia860_plant_ids": len(by_plant),
        "frs_facilities_with_multiple_plant_ids": multi_frs,
        "eia860_plant_ids_with_multiple_frs_records": multiple_frs_per_plant,
        "other_program_link_rows": other_programs,
        "state": ("REVIEW_CARDINALITY" if multi_frs or multiple_frs_per_plant or no_eia
                  else "RESEARCH_SOURCE_IDS_ONLY"),
        "source_http_headers_and_transport_independently_verified": False,
        "provider_original_full_frs_zip_authenticated": False,
        "eia_annual_2025_membership_verified": False,
        "gem_asset_identity_confirmed": False,
        "frs_name_or_coordinate_proves_powerplant_location": False,
        "corporate_ownership_or_insurance_inferred": False,
        "source_rights_or_model_admission_granted": False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-response", type=Path, required=True)
    ap.add_argument("--response-sha256", required=True)
    ap.add_argument("--cohort", choices=sorted(COHORTS), required=True)
    ap.add_argument("--observed-date", required=True)
    args = ap.parse_args(argv)
    try:
        p = args.original_response
        if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
            raise FRSOriginalReceiptBlocked("require bounded, regular local original response")
        report = inspect_original_response(p.read_bytes(), args.response_sha256,
                                           cohort=args.cohort, observed_date=args.observed_date)
    except (OSError, FRSOriginalReceiptBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["state"] == "REVIEW_CARDINALITY" else 0


if __name__ == "__main__":
    raise SystemExit(main())
