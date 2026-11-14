# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Historical Hurricane Michael source-vintage and independence gate.

Research only: source *metadata* (never FGDL owner/address/parcel rows, FEMA
individual assessment geometry, source imagery, or model exposures). A parcel
polygon is not a building outline. Distinct publishers and two visual layers
in one FEMA map do not prove independent damage labels.
"""

from __future__ import annotations

from datetime import date
from typing import Any

EVENT_DAY = date(2018, 10, 10)
SUPPORTED = frozenset((
    "florida.fgdl.parcels-2017",
    "florida.fgdl.parcels-2018",
    "noaa.ngs.hurricane-michael-2018-emergency-imagery",
    "nicb.gic.hurricane-michael-2018-imagery",
    "us.fema.historical-geospatial-damage-assessments",
))
EXPECTED_ROLE = {
    "florida.fgdl.parcels-2017": "parcel_polygon",
    "florida.fgdl.parcels-2018": "parcel_polygon",
    "noaa.ngs.hurricane-michael-2018-emergency-imagery": "post_event_imagery",
    "nicb.gic.hurricane-michael-2018-imagery": "post_event_imagery",
    "us.fema.historical-geospatial-damage-assessments": "remote_sensing_assessment",
}
MAX_SOURCES = 5


class MichaelSourceVintageError(ValueError):
    """Reject inconsistent vintage claims or attempted admission of raw data."""


def _date(value: Any, field: str) -> date | None:
    if value is None:
        return None
    if type(value) is not str or len(value) != 10:
        raise MichaelSourceVintageError(f"{field} requires YYYY-MM-DD or null")
    try:
        d = date.fromisoformat(value)
    except ValueError as exc:
        raise MichaelSourceVintageError(f"{field} is not a Gregorian date") from exc
    if d.isoformat() != value or d.year not in range(2000, 2030):
        raise MichaelSourceVintageError(f"{field} must be a bounded full ISO date")
    return d


def assess_source_metadata(source: Any) -> dict[str, Any]:
    """Strict one-source semantic gate, with no parcel/point/imagery payload.

    Source date ranges denote *provider-described dataset content*, not a
    proof that each feature existed at that date; archival parcel files can
    include updated attributes after the meteorological event.
    """
    expected = {
        "source_id", "role", "content_start", "content_end",
        "publication_date", "actual_file_bytes_verified",
        "building_footprint_version_verified", "fema_image_lineage_verified",
        "dataset_access_and_license_verified",
    }
    if type(source) is not dict or set(source) != expected:
        raise MichaelSourceVintageError("only exact metadata fields are accepted")
    sid = source["source_id"]
    if type(sid) is not str or sid not in SUPPORTED:
        raise MichaelSourceVintageError("unreviewed source identity")
    role = source["role"]
    if role != EXPECTED_ROLE[sid]:
        raise MichaelSourceVintageError("source cannot be relabeled as observed building geometry")
    for field in ("actual_file_bytes_verified", "building_footprint_version_verified",
                  "fema_image_lineage_verified", "dataset_access_and_license_verified"):
        if type(source[field]) is not bool:
            raise MichaelSourceVintageError("source evidence status must be boolean")
    start = _date(source["content_start"], "content_start")
    end = _date(source["content_end"], "content_end")
    published = _date(source["publication_date"], "publication_date")
    if (start is None) != (end is None) or (start and end and start > end):
        raise MichaelSourceVintageError("inconsistent content acquisition interval")
    if role == "parcel_polygon" and (start is None or published is None):
        raise MichaelSourceVintageError("parcel vintage requires dated content and publication")
    if role == "post_event_imagery" and start is not None and start <= EVENT_DAY:
        raise MichaelSourceVintageError("known post-event image vintage must begin after event")
    if role == "remote_sensing_assessment" and (
        start is not None or end is not None
    ):
        raise MichaelSourceVintageError("FEMA damage IMG_DATE is unknown, not event day")
    if source["building_footprint_version_verified"]:
        raise MichaelSourceVintageError("none of these source families proves 2018 roof-footprint identity")
    if source["fema_image_lineage_verified"]:
        raise MichaelSourceVintageError("exact FEMA original classification image is unverified")
    # Even a caller's asserted boolean cannot convert *parcel* polygons to
    # roof polygons; identity/geometry requires a separately scoped product.
    temporal = (
        "pre_event_content_interval" if end is not None and end < EVENT_DAY
        else "post_event_content_interval" if start is not None and start > EVENT_DAY
        else "content_interval_crosses_event" if start is not None
        else "image_acquisition_date_unverified" if role == "post_event_imagery"
        else "imagery_date_missing_in_public_fema_cohort"
    )
    is_pre_event_candidate = role == "parcel_polygon" and temporal == "pre_event_content_interval"
    may_use_as_independent_label = False
    return {
        "profile": "florida_michael_2018_source_vintage_and_lineage_v0",
        "source_id": sid,
        "source_role": role,
        "frozen_event_day": EVENT_DAY.isoformat(),
        "provider_content_start": start.isoformat() if start else None,
        "provider_content_end": end.isoformat() if end else None,
        "provider_publication_date": published.isoformat() if published else None,
        "temporal_relation_to_event": temporal,
        "pre_event_parcel_context_candidate": is_pre_event_candidate,
        "pre_event_building_footprint_proven": False,
        "parcel_polygon_is_building_footprint": False,
        "fema_assessment_original_image_proven": False,
        "independent_image_label_validation_proven": may_use_as_independent_label,
        "original_data_bytes_acquired_by_gate": False,
        "personal_address_or_owner_information_processed": False,
        "model_input_admitted": False,
    }


def reconcile_source_family(records: Any) -> dict[str, Any]:
    """Compare the explicit exact-five metadata profiles, not source rows."""
    if type(records) is not list or not 1 <= len(records) <= MAX_SOURCES:
        raise MichaelSourceVintageError("exact bounded metadata records required")
    entries = [assess_source_metadata(record) for record in records]
    by_id = {e["source_id"]: e for e in entries}
    if len(by_id) != len(entries):
        raise MichaelSourceVintageError("duplicate source identities in the family")
    # No automatic claim that FEMA's independent image has been located.
    missing_fema_original_image = (
        "us.fema.historical-geospatial-damage-assessments" in by_id
        and not by_id["us.fema.historical-geospatial-damage-assessments"][
            "fema_assessment_original_image_proven"
        ]
    )
    return {
        "profile": "florida_michael_2018_source_lineage_family_v0",
        "metadata_records_reconciled": len(entries),
        "pre_event_parcel_candidate_source_ids": sorted([
            x["source_id"] for x in entries
            if x["pre_event_parcel_context_candidate"]
        ]),
        "event_crossing_parcel_source_ids": sorted([
            x["source_id"] for x in entries
            if x["source_role"] == "parcel_polygon"
            and x["temporal_relation_to_event"] == "content_interval_crosses_event"
        ]),
        "fema_original_image_identity_missing": missing_fema_original_image,
        "two_organizations_make_label_independence_proven": False,
        "parcels_can_be_autojoined_to_roof_or_fema_points": False,
        "building_damage_training_labels_admitted": False,
        "model_input_admitted": False,
    }
