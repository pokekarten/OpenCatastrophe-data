#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only coverage of original geographic and source-reference fields.

These are *field-availability* checks for the existing DFO/HANZE candidate
pairs; country text and HANZE administrative codes are NOT verified spatial
overlap, flood footprints, precise coordinates or observed insured assets.
No raw provider rows, original event identifiers or regional identifiers are
written to the result. All provider bytes must match the pinned SHA256.
"""
from __future__ import annotations

import csv
import hashlib
import io

if __package__:
    from .historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS, inspect_hanze_v302
else:
    from historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS, inspect_hanze_v302


class GeographicCoverageError(ValueError):
    """Missing, inconsistent or incorrectly staged source evidence."""


FIELDS = (
    "admin_unit_nomenclature",
    "admin_unit_level",
    "admin_unit_year",
    "admin_unit_code",
    "event_source",
    "sources_author_year",
    "sources_impact_information",
    "hips_label",
    "hips_identifier",
    "hips_version",
    "area_affected",
)
REQUIRED_OVERLAP_STAGE = "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY"
REQUIRED_DFO_STAGE = "REPORTED_HISTORICAL_FLOOD_EVENTS_NO_DEPTH_NO_INSURED_LOSS"


def _populated(value: str) -> bool:
    if type(value) is not str:
        raise GeographicCoverageError("original provider field must be text")
    return bool(value.strip())


def survey_geographic_source_coverage(overlap: dict, dfo_preflight: dict,
                                      hanze_csv: bytes, expected_hanze_sha256: str) -> dict:
    """Report counts ONLY, never spatial correspondences or source row content."""
    if not isinstance(overlap, dict) or not isinstance(dfo_preflight, dict):
        raise GeographicCoverageError("missing version-pinned upstream preflight")
    if (overlap.get("evidence_class") != REQUIRED_OVERLAP_STAGE
            or dfo_preflight.get("evidence_class") != REQUIRED_DFO_STAGE
            or overlap.get("common_event_identity_proven") is not False
            or overlap.get("geographic_footprint_aligned") is not False
            or overlap.get("economic_or_insured_loss_joined") is not False
            or overlap.get("model_input_admitted") is not False
            or dfo_preflight.get("model_source_admission_approved") is not False):
        raise GeographicCoverageError("upstream candidate/rights/science stage invalid")
    if type(hanze_csv) is not bytes or len(hanze_csv) == 0:
        raise GeographicCoverageError("HANZE original bytes required")
    if (overlap.get("input_sha256", {}).get("hanze_csv") != expected_hanze_sha256
            or overlap.get("input_sha256", {}).get("dfo_csv") != dfo_preflight.get("source_csv_sha256")):
        raise GeographicCoverageError("source identity differs from validated candidate matcher")
    # Existing scientific preflight is the one authoritative parser for HANZE.
    profile = inspect_hanze_v302(hanze_csv, expected_hanze_sha256)
    if profile.get("source_admitted") is not False or profile.get("provider_rows_exported") is not False:
        raise GeographicCoverageError("HANZE original source has invalid admission flags")
    candidate_pairs = overlap.get("candidate_pairs")
    dfo_events = dfo_preflight.get("events")
    if not isinstance(candidate_pairs, list) or not isinstance(dfo_events, list):
        raise GeographicCoverageError("missing provider event lists")
    if len(candidate_pairs) != overlap.get("candidate_pair_count"):
        raise GeographicCoverageError("candidate list/profile size mismatch")
    dfo_index = {}
    for row in dfo_events:
        if not isinstance(row, dict) or type(row.get("dfo_event_id")) is not str:
            raise GeographicCoverageError("invalid DFO row identity")
        key = row["dfo_event_id"]
        if key in dfo_index:
            raise GeographicCoverageError("duplicate DFO record")
        dfo_index[key] = row
    if len(dfo_index) != dfo_preflight.get("reported_event_count"):
        raise GeographicCoverageError("DFO row count changed")
    try:
        reader = csv.DictReader(io.StringIO(hanze_csv.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != list(HANZE_COLUMNS):
            raise GeographicCoverageError("HANZE columns do not match source preflight")
        hanze_index = {}
        for row in reader:
            key = row["id"]
            if key in hanze_index:
                raise GeographicCoverageError("duplicate HANZE identity")
            hanze_index[key] = row
    except (UnicodeError, csv.Error) as exc:
        raise GeographicCoverageError("HANZE original CSV invalid") from exc
    if len(hanze_index) != profile.get("event_count"):
        raise GeographicCoverageError("HANZE row count changed")
    counts = {key: 0 for key in FIELDS}
    dfo_country_present = 0
    dfo_glide_id_present = 0
    pair_count = 0
    unique_dfo = set()
    unique_hanze = set()
    seen_pairs = set()
    for pair in candidate_pairs:
        if not isinstance(pair, dict) or pair.get("relationship") != "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY":
            raise GeographicCoverageError("candidate is not unconfirmed country/time overlap")
        if (pair.get("same_event_confirmed") is not False
                or pair.get("losses_joined") is not False):
            raise GeographicCoverageError("candidate falsely claims identity or losses")
        did, hid = pair.get("dfo_event_id"), pair.get("hanze_event_id")
        if type(did) is not str or type(hid) is not str or did not in dfo_index or hid not in hanze_index:
            raise GeographicCoverageError("candidate ID missing in original source")
        if (did, hid) in seen_pairs:
            raise GeographicCoverageError("duplicate candidate pair")
        seen_pairs.add((did, hid))
        unique_dfo.add(did)
        unique_hanze.add(hid)
        dr, hr = dfo_index[did], hanze_index[hid]
        if dr["country_text_unparsed"] != pair.get("dfo_country_original"):
            raise GeographicCoverageError("DFO candidate country changed")
        if hr["country_code"] != pair.get("country_iso2_from_supplied_crosswalk"):
            raise GeographicCoverageError("HANZE candidate country changed")
        pair_count += 1
        dfo_country_present += int(_populated(dr["country_text_unparsed"]))
        dfo_glide_id_present += int(_populated(dr["glide_id_unverified"] or ""))
        for key in FIELDS:
            counts[key] += int(_populated(hr[key]))
    return {
        "evidence_stage": "SOURCE_FIELD_AVAILABILITY_NOT_GEOGRAPHIC_MATCHING",
        "candidate_pair_count": pair_count,
        "distinct_dfo_records_in_pairs": len(unique_dfo),
        "distinct_hanze_records_in_pairs": len(unique_hanze),
        "dfo_country_label_present_pairs": dfo_country_present,
        "dfo_glide_identifier_present_pairs": dfo_glide_id_present,
        "hanze_nonempty_original_field_pair_counts": counts,
        "hanze_admin_codes_are_recorded_regions_not_flood_polygons": True,
        "dfo_record_has_no_geocoded_location_in_pinned_csv": True,
        "dfo_country_is_not_a_geographic_footprint": True,
        "hanze_admin_code_vintage_and_level_not_semantically_resolved": True,
        "hips_and_glide_identifiers_have_no_approved_crosswalk": True,
        "hanze_original_source_bibliography_not_independently_verified": True,
        "provider_field_values_or_event_ids_emitted": False,
        "same_flood_event_identity_confirmed": False,
        "region_geometry_intersection_verified": False,
        "hydrologic_event_causality_verified": False,
        "third_party_rights_review_complete": False,
        "observed_insured_loss_computed": False,
        "model_input_admitted": False,
    }
