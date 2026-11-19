# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""USGS WESM work-unit quality semantics: offline, fail-closed, non-admission.

Official Work Unit Extent Spatial Metadata (WESM) status categories belong to
the original source work unit, not necessarily to an individual S1M tile/pixel.
This classifier NEVER establishes provider-original WESM bytes, a spatial join,
GEOID18, per-cell source quality, or model fitness. No external requests.
"""
from __future__ import annotations

import re
from typing import Mapping

CATEGORIES = {
    "lpc_category": frozenset((
        "Expected to meet", "Under review", "Meets",
        "Meets with variance", "Does not meet", "Not applicable",
    )),
    "sourcedem_category": frozenset((
        "Expected to meet", "Under review", "Meets",
        "Meets with variance", "Does not meet",
    )),
    "seamless_category": frozenset((
        "Pending publication", "Under review", "Meets",
        "Meets with variance", "Does not meet",
    )),
}
SEAMLESS_REASONS = {
    "Pending publication": frozenset({"Awaiting final absolute vertical accuracy assessment"}),
    "Under review": frozenset({"Pending LPC/source DEM review"}),
    "Meets": frozenset({"Meets 3DEP seamless requirements"}),
    "Meets with variance": frozenset({"LPC meets v.1.0 or earlier draft specification"}),
    "Does not meet": frozenset((
        "LPC does not meet", "Source DEM resolution too coarse", "Source DEM not available",
    )),
}
FIELD_NAMES = frozenset((
    "workunit_id", "project_id", "lpc_category",
    "sourcedem_category", "seamless_category", "seamless_reason",
))
# The WESM archive is refreshed frequently; a matched status cannot be assumed
# stable or linked to a particular TIFF without actual spatial-source evidence.
QUALITY_CLASS = {
    "Pending publication": "pending_final_vertical_accuracy_not_approved",
    "Under review": "source_lineage_under_review_not_approved",
    "Meets": "workunit_reports_meets_not_tile_verified",
    "Meets with variance": "source_variance_requires_independent_review",
    "Does not meet": "source_workunit_fails_3dep_requirements",
}


class Blocked(ValueError):
    """Unsupported, ambiguous or contradictory USGS WESM work-unit metadata."""


def _identity(value: object, name: str) -> str:
    if type(value) is not str or not 1 <= len(value.strip()) <= 128:
        raise Blocked(name + " missing or unbounded")
    # A work-unit identifier is not an arbitrary path, URL, SQL fragment or
    # coordinate. It must be a stable opaque identifier extracted by a trusted
    # caller from an authentic provider table/GeoPackage.
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]{0,127}", value):
        raise Blocked(name + " is an unsafe source identifier")
    if value.strip() != value:
        raise Blocked(name + " contains ambiguous outer whitespace")
    return value


def classify_wesm_seamless_workunit(row: object) -> dict[str, object]:
    """Screen one caller-extracted WESM record, preserving missing source proof.

    WESM is work-unit-level source/quality context, not the per-cell spatial
    lineage GeoPackage for a particular S1M tile. A source status of 'Meets'
    does NOT itself authorise hydrological or actuarial use.
    """
    if not isinstance(row, Mapping) or type(row) is not dict:
        raise Blocked("WESM row must be an ordinary source-field mapping")
    for field in FIELD_NAMES:
        if field not in row:
            raise Blocked("source WESM field missing: " + field)
    workunit_id = _identity(row["workunit_id"], "workunit_id")
    project_id = _identity(row["project_id"], "project_id")
    for field, accepted in CATEGORIES.items():
        value = row[field]
        if type(value) is not str or value not in accepted:
            raise Blocked("WESM product category not valid for " + field)
    category = row["seamless_category"]
    reason = row["seamless_reason"]
    if type(reason) is not str or reason not in SEAMLESS_REASONS[category]:
        raise Blocked("source seamless reason does not match official category")
    lpc = row["lpc_category"]
    source_dem = row["sourcedem_category"]
    if category == "Pending publication" and (
        lpc != "Expected to meet" or source_dem != "Expected to meet"
    ):
        raise Blocked("WESM pending publication requires both upstream expected-to-meet")
    if category in {"Meets", "Meets with variance"} and (
        lpc in {"Does not meet", "Expected to meet", "Under review", "Not applicable"}
        or source_dem in {"Does not meet", "Expected to meet", "Under review"}
    ):
        raise Blocked("contradictory upstream source status cannot prove seamless quality")
    if category == "Meets" and (
        lpc == "Meets with variance" or source_dem == "Meets with variance"
    ):
        raise Blocked("source variance must not be silently promoted into meets")
    return {
        "classification": QUALITY_CLASS[category],
        "workunit_id": workunit_id,
        "project_id": project_id,
        "official_wesm_seamless_category": category,
        "official_wesm_seamless_reason": reason,
        "status_reports_meets": category == "Meets",
        "variance_or_failure_present": category in {"Meets with variance", "Does not meet"},
        "source_is_workunit_not_s1m_pixel": True,
        "provider_original_csv_full_hash_verified": False,
        "provider_original_geopackage_full_hash_verified": False,
        "workunit_geometry_intersection_with_exact_s1m_tile_verified": False,
        "tile_specific_lidar_vintage_and_void_fill_verified": False,
        "original_vertical_accuracy_independently_assessed": False,
        "cat_model_input_approved": False,
    }
