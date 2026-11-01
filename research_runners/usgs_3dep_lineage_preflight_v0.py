# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline metadata-only USGS 3DEP S1M/LPC alignment and shared-lineage gate.

No DEM, LiDAR, source URLs, tiles, customer information, or scientific model
inputs are downloaded, copied, geocoded or published by this module.
Matching reference labels are *necessary*, not sufficient, for numeric height
comparison. LiDAR source overlap is never an independent observation.
"""

from __future__ import annotations

from datetime import date
import re
from typing import Any

S1M_ID = "usgs.3dep.seamless-1m-dem"
LPC_ID = "usgs.3dep.lidar-point-cloud"
REQUIRED = frozenset({
    "dataset_id", "asset_id", "sha256", "byte_count", "data_type",
    "horizontal_crs", "vertical_datum", "vertical_realization", "geoid_model",
    "elevation_unit", "source_vintage_start", "source_vintage_end",
    "source_lidar_workunit_ids",
})
S1M_TYPE = "bare_earth_dem"
LPC_TYPE = "classified_lidar_point_cloud"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
CRS = re.compile(r"^EPSG:[1-9][0-9]{3,5}$")
REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,79}$")


class MetadataError(ValueError):
    """Stop on unknown/missing reference and source provenance evidence."""


def _day(value: Any, label: str) -> date:
    if type(value) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise MetadataError(f"{label} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise MetadataError(f"{label} is not a valid calendar date") from exc


def _asset(value: Any, expected_id: str, data_type: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != REQUIRED:
        raise MetadataError("unreviewed or missing 3DEP receipt fields")
    if value["dataset_id"] != expected_id or value["data_type"] != data_type:
        raise MetadataError("wrong 3DEP source dataset or product type")
    if type(value["asset_id"]) is not str or not SAFE_ID.fullmatch(value["asset_id"]):
        raise MetadataError("asset_id must be a bounded source-native label, not a URL/path")
    digest = value["sha256"]
    if type(digest) is not str or not HASH.fullmatch(digest) or digest == "0" * 64:
        raise MetadataError("sha256 must identify non-empty original artifact bytes")
    if type(value["byte_count"]) is not int or not 0 < value["byte_count"] <= 100_000_000_000:
        raise MetadataError("byte_count must be positive and bounded")
    horizontal = value["horizontal_crs"]
    if type(horizontal) is not str or not CRS.fullmatch(horizontal):
        raise MetadataError("horizontal_crs must be an explicitly named EPSG CRS")
    for field in ("vertical_datum", "vertical_realization", "geoid_model"):
        label = value[field]
        if type(label) is not str or not REF.fullmatch(label) or label.casefold() in {"unknown", "none", "na", "unspecified"}:
            raise MetadataError(f"{field} must be explicit and source-verified")
    if value["elevation_unit"] != "metre":
        raise MetadataError("elevation_unit must be declared as metre; no silent conversions")
    first = _day(value["source_vintage_start"], "source_vintage_start")
    last = _day(value["source_vintage_end"], "source_vintage_end")
    if first > last:
        raise MetadataError("source vintage interval is inverted")
    units = value["source_lidar_workunit_ids"]
    if (type(units) is not list or not 1 <= len(units) <= 100
            or any(type(x) is not str or not SAFE_ID.fullmatch(x) for x in units)
            or len(set(units)) != len(units)):
        raise MetadataError("source_lidar_workunit_ids must be unique, bounded provider IDs")
    return value


def preflight(payload: Any) -> dict[str, Any]:
    """Validate explicit metadata and return no asset IDs or source coordinates.

    Same label/realization/geoid is necessary but no proof of vertical accuracy,
    same-footprint overlap, common survey epoch or scientific model eligibility.
    A shared original LiDAR work unit makes DEM/LPC evidence correlated.
    """
    if type(payload) is not dict or set(payload) != {"s1m", "lidar"}:
        raise MetadataError("expected only s1m and lidar metadata receipts")
    dem = _asset(payload["s1m"], S1M_ID, S1M_TYPE)
    lidar = _asset(payload["lidar"], LPC_ID, LPC_TYPE)
    for field in ("horizontal_crs", "vertical_datum", "vertical_realization", "geoid_model"):
        if dem[field] != lidar[field]:
            raise MetadataError(f"{field} differs; audited coordinate transformation required")
    common = set(dem["source_lidar_workunit_ids"]) & set(lidar["source_lidar_workunit_ids"])
    lineage = "shared_lidar_workunit" if common else "not_proven_independent"
    # Not a numerical height join: spatial overlap, age and local source
    # quality remain outside this strictly metadata-only contract.
    return {
        "profile": "usgs_3dep_s1m_lidar_metadata_preflight_v0",
        "input_artifact_count": 2,
        "artifact_original_byte_hashes_recorded": True,
        "horizontal_and_vertical_metadata_exact_match": True,
        "upstream_relationship": lineage,
        "shared_lidar_workunit_count": len(common),
        "scientific_independence_proven": False,
        "spatial_alignment_proven": False,
        "numeric_height_comparison_permitted": False,
        "model_input_admitted": False,
        "source_data_redistribution_permitted": False,
        "scope": "metadata_only_research",
    }


if __name__ == "__main__":
    raise SystemExit("Call preflight() on synthetic or separately reviewed local metadata")
