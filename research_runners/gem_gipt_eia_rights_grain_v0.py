#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic/local GEM GIPT 2026-09 unit/phase and source-rights preflight.

Input is a manually prepared *projection*, NOT the native GEM workbook.
No publisher dataset is downloaded. Even an EIA-860 external-ID claim is
only a research clue, never validated GEM↔EIA identity or insurance exposure.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import re

MAX_BYTES = 1_500_000
MAX_ROWS = 10_000
HEADERS = ("gem_unit_phase_id", "gem_location_id", "country_area",
           "other_ids_unit_phase")
HEXDIGEST = re.compile(r"[0-9a-f]{64}\Z")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}\Z")
EIA_TOKEN = re.compile(r"(?<![A-Za-z0-9])EIA[ -]860\s*:\s*0*([1-9][0-9]{0,5})(?![0-9])", re.I)
TZ_TOKEN = re.compile(r"(?:\bTZ\s*ID\b|\bTransitionZero\b)", re.I)
# FRS original JSON city proof / EIA 2025 original ZIP proof (#1259, #1291):
DE_EPA_EIA_CODES = frozenset((
    "599", "7318", "57337", "57349", "67391", "10030", "63700",
    "591", "593", "7153", "59922", "597", "61934", "67572", "58110",
))


class GIPTBlocked(ValueError):
    """No legally or scientifically supportable GIPT source assertion."""


def _read_projected_csv(blob: bytes, expected_sha: str) -> list[dict]:
    if not isinstance(expected_sha, str) or not HEXDIGEST.fullmatch(expected_sha):
        raise GIPTBlocked("required lowercase projection SHA-256")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise GIPTBlocked("bounded local projection required")
    if sha256(blob).hexdigest() != expected_sha:
        raise GIPTBlocked("caller-supplied projection hash mismatch")
    try:
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig"), newline=""), strict=True)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or tuple(fields) != HEADERS:
            raise GIPTBlocked("exact normalized projection column order/headers required")
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise GIPTBlocked("bounded GIPT record limit exceeded")
            if None in row or any(v is None or v != v.strip() or len(v) > 1200
                                  for v in row.values()):
                raise GIPTBlocked("malformed or oversized projection field")
            rows.append(row)
    except (csv.Error, UnicodeError) as exc:
        raise GIPTBlocked("invalid UTF-8/CSV projection") from exc
    if not rows:
        raise GIPTBlocked("zero projection rows")
    return rows


def review_gipt_projection(blob: bytes, projection_sha: str, *,
                           native_original_sha: str | None,
                           release: str = "2026-09") -> dict:
    """Aggregate-only candidate counts and license/grain contradiction signals."""
    if release != "2026-09":
        raise GIPTBlocked("this contract is only for September 2026 GIPT")
    if native_original_sha is not None and (
            type(native_original_sha) is not str or
            not HEXDIGEST.fullmatch(native_original_sha)):
        raise GIPTBlocked("unknown original workbook SHA-256 syntax")
    rows = _read_projected_csv(blob, projection_sha)
    seen_units = set()
    location_rights: dict[str, set[str]] = defaultdict(set)
    eia_locations: dict[str, set[str]] = defaultdict(set)
    tz_rows = matched_rows = multi_eia_rows = non_us_claims = 0
    idless_rows = missing_location_rows = 0
    for row in rows:
        unit, location = row["gem_unit_phase_id"], row["gem_location_id"]
        country, other = row["country_area"], row["other_ids_unit_phase"]
        if not SAFE_ID.fullmatch(unit) or unit in seen_units:
            raise GIPTBlocked("invalid or repeated GEM unit/phase ID")
        seen_units.add(unit)
        if not location:
            missing_location_rows += 1
            # Missing GIPT location prevents site identity assertion.
            loc = "__NO_LOCATION__" + unit
        elif not SAFE_ID.fullmatch(location):
            raise GIPTBlocked("invalid GEM location identifier")
        else:
            loc = location
        if not country or len(country) > 90 or any(ord(c) < 32 for c in country):
            raise GIPTBlocked("invalid country/area")
        is_tz = bool(TZ_TOKEN.search(other))
        if is_tz:
            tz_rows += 1
        location_rights[loc].add("TZ_NONCOMMERCIAL" if is_tz else "DEFAULT_REVIEW_ONLY")
        # No extrapolation from names, geolocation, ORIS aliases or corporate owners.
        ids = {str(int(x)) for x in EIA_TOKEN.findall(other)}
        if not ids:
            idless_rows += 1
            continue
        if len(ids) > 1:
            multi_eia_rows += 1
        if country != "United States":
            non_us_claims += 1
            continue
        matched_rows += 1
        if location:
            for plant in ids:
                if plant in DE_EPA_EIA_CODES:
                    eia_locations[plant].add(location)
    cohort_with_location = len(eia_locations)
    eia_multiple_locations = sum(len(places) > 1 for places in eia_locations.values())
    de_without_candidate = len(DE_EPA_EIA_CODES) - cohort_with_location
    mixed = sum(len(rights) > 1 for rights in location_rights.values())
    quarantined_locations = {
        place for place, rights in location_rights.items()
        if "TZ_NONCOMMERCIAL" in rights
    }
    # Report only *reviewable* non-TZ claims when no units at the location
    # carry the non-commercial marker. Never call even those rights-approved.
    eia_with_non_tz_location_only = sum(
        all(place not in quarantined_locations for place in locations)
        for locations in eia_locations.values()
    )
    eia_with_any_tz_location = sum(
        any(place in quarantined_locations for place in locations)
        for locations in eia_locations.values()
    )
    if cohort_with_location + de_without_candidate != len(DE_EPA_EIA_CODES):
        raise GIPTBlocked("Delaware cohort conservation failure")
    if tz_rows:
        state = "REVIEW_TZ_NONCOMMERCIAL_AND_IDENTITY"
    elif multi_eia_rows or eia_multiple_locations or mixed:
        state = "REVIEW_CARDINALITY"
    elif cohort_with_location:
        state = "PUBLISHER_ID_CLAIMS_ONLY"
    else:
        state = "NO_EIA_860_PUBLISHER_CROSS_IDS_IN_THIS_SLICE"
    return {
        "profile": "gem-gipt-2026-09-unit-rights-eia-claim-v0",
        "release": release,
        "normalized_projection_sha256": projection_sha,
        "original_workbook_sha256_claim": native_original_sha,
        "original_workbook_bytes_independently_authenticated": False,
        "original_publisher_download_consent_and_terms_verified": False,
        "rows": len(rows),
        "distinct_unit_phase_ids": len(seen_units),
        "location_id_groups_including_missing_sentinels": len(location_rights),
        "rows_missing_gem_location_id": missing_location_rows,
        "rows_with_transitionzero_id": tz_rows,
        "locations_containing_both_tz_and_non_tz_units": mixed,
        "gem_locations_with_any_tz_unit": len(quarantined_locations),
        "eia_de_claims_at_any_tz_quarantined_location": eia_with_any_tz_location,
        "eia_de_claims_only_at_non_tz_locations_still_rights_unverified": eia_with_non_tz_location_only,
        "rows_with_no_explicit_eia860_token": idless_rows,
        "rows_with_multiple_eia860_tokens": multi_eia_rows,
        "rows_with_eia_claim_in_non_us_country_area": non_us_claims,
        "us_rows_with_eia860_publisher_claim": matched_rows,
        "epa_delaware_2025_eia_plant_ids": len(DE_EPA_EIA_CODES),
        "epa_delaware_ids_with_any_gem_location_claim": cohort_with_location,
        "epa_delaware_ids_without_gem_location_claim_in_slice": de_without_candidate,
        "epa_delaware_ids_claimed_by_multiple_gem_locations": eia_multiple_locations,
        "gem_unit_row_count_is_unique_physical_assets": False,
        "non_tz_marker_proves_unrestricted_commercial_rights": False,
        "transitionzero_marked_rows_permitted_for_commercial_use": False,
        "eia860_external_id_text_proves_cross_provider_plant_identity": False,
        "epa_gem_site_or_owner_identity_confirmed": False,
        "gem_entity_parent_equals_insurance_group": False,
        "insurer_tiv_or_cat_exposure_inferred": False,
        "source_rights_or_model_admission_granted": False,
        "state": state,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projected-csv", type=Path, required=True)
    p.add_argument("--projection-sha256", required=True)
    p.add_argument("--native-workbook-sha256")
    p.add_argument("--release", default="2026-09")
    args = p.parse_args(argv)
    try:
        path = args.projected_csv
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise GIPTBlocked("expected bounded local projected CSV; do not store source in Git")
        result = review_gipt_projection(
            path.read_bytes(), args.projection_sha256,
            native_original_sha=args.native_workbook_sha256, release=args.release)
    except (OSError, GIPTBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["state"] in (
        "REVIEW_TZ_NONCOMMERCIAL_AND_IDENTITY", "REVIEW_CARDINALITY") else 0


if __name__ == "__main__":
    raise SystemExit(main())
