#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Versioned Eurostat GISCO NUTS 2024 *attribute ID* audit for HANZE v3.

Only verifies existence, country, year and hierarchy of individual region IDs.
The official GISCO NUTS_AT_2024.csv contains NO geometries. It cannot show
where a flood occurred, prove that two events are identical, or allocate
national exposure, insured TIV or actual flood loss to a building.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import re

if __package__:
    from .historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS, inspect_hanze_v302
else:
    from historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS, inspect_hanze_v302

GISCO_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/csv/NUTS_AT_2024.csv"
GISCO_GEOMETRY_REFERENCE = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_03M_2024_4326_LEVL_3.geojson"
)
GISCO_HEADER = (
    "CNTR_CODE", "NUTS_ID", "NAME_LATN", "NUTS_NAME", "MOUNT_TYPE",
    "URBN_TYPE", "COAST_TYPE",
)
REGION = re.compile(r"[A-Z]{2}[A-Z0-9]{0,3}\Z")
COUNTRY = re.compile(r"[A-Z]{2}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_BYTES = 4_000_000


class NUTS2024AuditError(ValueError):
    """Fail closed on original geometry catalogue or source-join ambiguity."""


def nuts2024_index(blob: bytes, *, expected_sha256: str | None = None) -> tuple[dict, dict]:
    """Parse real official attribute CSV. Index is in-memory only; no raw output."""
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise NUTS2024AuditError("GISCO NUTS 2024 original CSV byte size invalid")
    sha = hashlib.sha256(blob).hexdigest()
    if expected_sha256 is not None and (
        type(expected_sha256) is not str or not SHA.fullmatch(expected_sha256)
        or expected_sha256 != sha
    ):
        raise NUTS2024AuditError("GISCO original source SHA256 mismatch")
    try:
        body = blob.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(body, newline=""), strict=True)
        if reader.fieldnames != list(GISCO_HEADER):
            raise NUTS2024AuditError("unexpected official NUTS_AT_2024.csv header")
        mapping = {}
        countries = set()
        per_level = Counter()
        for row in reader:
            if None in row or any(item is None for item in row.values()):
                raise NUTS2024AuditError("GISCO original row column count mismatch")
            code, country = row["NUTS_ID"], row["CNTR_CODE"]
            if (type(code) is not str or not REGION.fullmatch(code)
                    or type(country) is not str or not COUNTRY.fullmatch(country)
                    or not code.startswith(country)):
                raise NUTS2024AuditError("noncanonical GISCO NUTS country or identifier")
            if code in mapping:
                raise NUTS2024AuditError("duplicate official NUTS2024 identifier")
            mapping[code] = country
            countries.add(country)
            per_level[len(code) - 2] += 1
            if len(mapping) > 20000:
                raise NUTS2024AuditError("unexpected official NUTS row count")
    except (UnicodeError, csv.Error) as exc:
        raise NUTS2024AuditError("invalid original GISCO CSV") from exc
    if not mapping:
        raise NUTS2024AuditError("empty official NUTS dataset")
    return mapping, {
        "source_url": GISCO_URL,
        "source_sha256": sha,
        "byte_length": len(blob),
        "official_attribute_rows": len(mapping),
        "official_country_code_count": len(countries),
        "official_rows_by_nuts_level": {str(i): per_level.get(i, 0) for i in range(4)},
        "original_file_sha256_pinned": expected_sha256 is not None,
        "original_geometry_downloaded": False,
        "model_input_admitted": False,
    }


def audit_hanze_candidate_region_codes(
    hanze_blob: bytes, expected_hanze_sha256: str, overlap: dict,
    gisco_blob: bytes, *, expected_gisco_sha256: str | None = None
) -> dict:
    """Match only unambiguous one-code HANZE candidates to official 2024 ID table."""
    if (type(overlap) is not dict
            or overlap.get("evidence_class") != "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY"
            or overlap.get("model_input_admitted") is not False
            or overlap.get("common_event_identity_proven") is not False
            or overlap.get("geographic_footprint_aligned") is not False
            or overlap.get("input_sha256", {}).get("hanze_csv") != expected_hanze_sha256):
        raise NUTS2024AuditError("invalid upstream HANZE candidate evidence")
    profile = inspect_hanze_v302(hanze_blob, expected_hanze_sha256)
    if profile.get("source_admitted") is not False:
        raise NUTS2024AuditError("HANZE original was unexpectedly admitted")
    index, gisco = nuts2024_index(gisco_blob, expected_sha256=expected_gisco_sha256)
    try:
        reader = csv.DictReader(io.StringIO(hanze_blob.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != list(HANZE_COLUMNS):
            raise NUTS2024AuditError("HANZE original CSV header drift")
        hanze_rows = {}
        for row in reader:
            eid = row["id"]
            if eid in hanze_rows:
                raise NUTS2024AuditError("duplicate HANZE original event id")
            hanze_rows[eid] = row
    except (UnicodeError, csv.Error) as exc:
        raise NUTS2024AuditError("HANZE source CSV malformed") from exc
    counts = Counter()
    seen = set()
    unique_hanze = set()
    for pair in overlap.get("candidate_pairs", []):
        if (type(pair) is not dict
                or pair.get("relationship") != "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY"
                or pair.get("same_event_confirmed") is not False
                or pair.get("losses_joined") is not False):
            raise NUTS2024AuditError("candidate no longer an unconfirmed source-time overlap")
        did, hid = pair.get("dfo_event_id"), pair.get("hanze_event_id")
        if type(did) is not str or type(hid) is not str or (did, hid) in seen:
            raise NUTS2024AuditError("duplicate or invalid pair identity")
        seen.add((did, hid))
        unique_hanze.add(hid)
        row = hanze_rows.get(hid)
        if row is None or row["country_code"] != pair.get("country_iso2_from_supplied_crosswalk"):
            raise NUTS2024AuditError("HANZE code/country does not match candidate original")
        counts["candidate_pairs"] += 1
        code = row["admin_unit_code"].strip()
        nomenclature = row["admin_unit_nomenclature"].strip()
        level = row["admin_unit_level"].strip()
        year = row["admin_unit_year"].strip()
        if not code:
            counts["missing_region_code"] += 1
            continue
        if nomenclature not in ("NUTS", "NUTS 2024"):
            counts["unsupported_or_non_nuts_nomenclature"] += 1
            continue
        if year != "2024":
            counts["unsupported_region_vintage"] += 1
            continue
        if not REGION.fullmatch(code):
            counts["multi_region_or_noncanonical_code_manual_review"] += 1
            continue
        if level not in ("0", "1", "2", "3") or int(level) != len(code) - 2:
            counts["missing_or_mismatched_nuts_level"] += 1
            continue
        country = index.get(code)
        if country is None:
            counts["canonical_hanze_code_absent_from_gisco"] += 1
        elif country != row["country_code"]:
            counts["official_country_disagrees_with_hanze"] += 1
        else:
            counts["exact_official_country_level_vintage_code_matches"] += 1
    if counts["candidate_pairs"] != overlap.get("candidate_pair_count"):
        raise NUTS2024AuditError("pair count mismatch")
    return {
        "evidence_stage": "EXACT_GISCO_NUTS_2024_REGION_ID_LOOKUP_ONLY",
        "hanze_sha256": expected_hanze_sha256,
        "gisco_original_source": gisco,
        "geojson_geometry_reference_unverified": GISCO_GEOMETRY_REFERENCE,
        "candidate_pair_count": counts["candidate_pairs"],
        "distinct_hanze_events_in_pairs": len(unique_hanze),
        "candidate_code_status_counts": {
            key: counts[key] for key in (
                "exact_official_country_level_vintage_code_matches",
                "missing_region_code",
                "unsupported_or_non_nuts_nomenclature",
                "unsupported_region_vintage",
                "multi_region_or_noncanonical_code_manual_review",
                "missing_or_mismatched_nuts_level",
                "canonical_hanze_code_absent_from_gisco",
                "official_country_disagrees_with_hanze",
            )
        },
        "historical_2024_nuts_code_existence_confirmed": counts["exact_official_country_level_vintage_code_matches"] > 0,
        "verified_geographic_point_or_polygon_overlay": False,
        "dfo_flood_extent_geolocated": False,
        "same_flood_event_identity_confirmed": False,
        "source_or_region_values_exported": False,
        "insured_loss_or_tiv_estimated": False,
        "third_party_rights_review_complete": False,
        "model_source_admitted": False,
    }
