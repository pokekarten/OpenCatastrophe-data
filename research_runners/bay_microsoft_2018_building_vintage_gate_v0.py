# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bay County footprint service vs exact 2018 Microsoft source-vintage gate.

Strict public service metadata and aggregate counts only. No building
polygon, feature ID, address, roof attribute value or owner row is ever
retrieved. In particular, a 2018 *publication* does not establish exact
underlying image or building capture time. Never cast live 2026 Bay County
footprints as pre-Hurricane-Michael 2018 geometry.
"""

from __future__ import annotations

from typing import Any

BAY_SERVICE = (
    "https://gis.baycountyfl.gov/arcgis/rest/services/"
    "Hosted/FC_BuildingFootprints/FeatureServer/22"
)
BAY_ITEM = "6b68c1a8d4354fc3b6f38cf41f46b754"
MS_REPO = "Microsoft/USBuildingFootprints"
MS_COMMIT = "c9fb49b5f7475102b2923ae2c7fc455412c7f0e8"
MS_SOURCE_ZIP = "https://usbuildingdata.blob.core.windows.net/usbuildings-v1-1/Florida.zip"
MS_FLORIDA_DECLARED = 6_903_772
HURRICANE_DAY = "2018-10-10"


class BuildingVintageGateError(ValueError):
    """A source does not meet bounded, exact proof of its vintage."""


def bay_original_count_plan() -> dict[str, dict[str, str]]:
    """All queries aggregate only; never export building geometries."""
    wheres = {
        "total": "1=1",
        "lastupdate_null": "lastupdate IS NULL",
        "lastupdate_nonnull": "lastupdate IS NOT NULL",
        "lastupdate_before_event": "lastupdate < timestamp '2018-10-10 00:00:00'",
        "create_date_before_event": "create_date < timestamp '2018-10-10 00:00:00'",
    }
    return {
        k: {"where": v, "returnCountOnly": "true",
            "returnGeometry": "false", "f": "json"}
        for k, v in wheres.items()
    }


def _count(value: Any) -> int:
    if type(value) is not dict or set(value) != {"count"}:
        raise BuildingVintageGateError("source returns count-only, never features")
    n = value["count"]
    if type(n) is not int or not 0 <= n <= 1_000_000:
        raise BuildingVintageGateError("Bay County count exceeds fixed guardrails")
    return n


def audit_bay_current_footprints(meta: Any, replies: Any) -> dict[str, Any]:
    """Validate a strict projection of service schema and five provider counts.

    Caller must authenticate original service URL separately; this pure
    validation cannot itself prove provider response authenticity.
    """
    keys = {"serviceItemId", "name", "geometryType", "spatialReferenceLatestWkid",
            "isDataVersioned", "supportsHistoricMoment", "fields"}
    if type(meta) is not dict or set(meta) != keys:
        raise BuildingVintageGateError("unreviewed Bay County layer projection")
    if (meta["serviceItemId"] != BAY_ITEM
        or meta["name"] != "Building Footprints"
        or meta["geometryType"] != "esriGeometryPolygon"
        or meta["spatialReferenceLatestWkid"] != 2238
        or meta["isDataVersioned"] is not False
        or meta["supportsHistoricMoment"] is not False):
        raise BuildingVintageGateError("exact county footprint identity or history capability changed")
    fields = meta["fields"]
    if (type(fields) is not list or
        any(type(f) is not str for f in fields)
        or len(set(fields)) != len(fields)
        or not {"objectid", "lastupdate", "create_date", "roof_type",
                "bldgheight", "numstories"}.issubset(set(fields))):
        raise BuildingVintageGateError("required original roof/height/time schema absent")
    if type(replies) is not dict or set(replies) != set(bay_original_count_plan()):
        raise BuildingVintageGateError("all count-only time controls required")
    counts = {k: _count(v) for k, v in replies.items()}
    total = counts["total"]
    if (total == 0 or counts["lastupdate_null"] + counts["lastupdate_nonnull"] != total
        or counts["lastupdate_before_event"] > counts["lastupdate_nonnull"]
        or counts["create_date_before_event"] > total):
        raise BuildingVintageGateError("source feature time-count conservation failed")
    return {
        "profile": "bay_county_live_building_footprints_temporal_gate_v0",
        "source_layer_item": BAY_ITEM,
        "current_source_building_polygon_feature_count": total,
        "lastupdate_null_count": counts["lastupdate_null"],
        "lastupdate_nonnull_count": counts["lastupdate_nonnull"],
        "lastupdate_before_hurricane_count": counts["lastupdate_before_event"],
        "create_date_before_hurricane_count": counts["create_date_before_event"],
        "supports_historicMoment": False,
        "has_versioned_data": False,
        "feature_updated_before_event_proves_historical_shape": False,
        "precise_source_imagery_acquisition_vintage_proven": False,
        "pre_2018_geojson_building_snapshot_available": False,
        "individual_roof_geometry_processed": False,
        "model_input_admitted": False,
    }


def audit_microsoft_2018_original_readme(meta: Any) -> dict[str, Any]:
    """Conservatively audit a repository pinned as-of 2018-10-09.

    No assumption that the 2018 original Azure V1.1 link still serves the
    same original bytes. Licenses in README and LICENSE conflicted in
    that historic commit; do not silently select either for commercial use.
    """
    keys = {
        "github_repository", "pinned_commit", "commit_date",
        "florida_original_release_url", "florida_readme_building_count",
        "readme_license", "license_file",
        "original_zip_header_bytes_verified",
        "original_zip_whole_sha256_verified",
        "image_capture_vintage_per_building_verified",
    }
    if type(meta) is not dict or set(meta) != keys:
        raise BuildingVintageGateError("incomplete pre-event Microsoft GitHub receipt")
    if (meta["github_repository"] != MS_REPO or meta["pinned_commit"] != MS_COMMIT
        or meta["commit_date"] != "2018-10-09"
        or meta["florida_original_release_url"] != MS_SOURCE_ZIP
        or type(meta["florida_readme_building_count"]) is not int
        or meta["florida_readme_building_count"] != MS_FLORIDA_DECLARED
        or meta["readme_license"] != "ODbL-1.0"
        or meta["license_file"] != "CC-BY-4.0"
        or any(meta[k] is not False for k in (
            "original_zip_header_bytes_verified",
            "original_zip_whole_sha256_verified",
            "image_capture_vintage_per_building_verified",
        ))):
        raise BuildingVintageGateError("unreviewed bytes, licence or event-era publication")
    return {
        "profile": "microsoft_usbuildings_2018_repo_pinned_fl_v1_1_v0",
        "exact_original_commit": MS_COMMIT,
        "repo_publication_before_hurricane": True,
        "florida_readme_nominal_footprint_count": MS_FLORIDA_DECLARED,
        "original_archive_byte_identity_verified": False,
        "historic_readme_and_license_file_disagree": True,
        "exact_building_imagery_date_verified": False,
        "source_file_sha256_verified": False,
        "commercial_redistribution_rights_approved": False,
        "can_train_2018_damage_from_this_without_other_checks": False,
        "model_input_admitted": False,
    }
