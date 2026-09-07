# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile the exact CEMS companion-mask GeoTIFFs and compare metadata to RP10.

The two public mask identities are frozen to trusted-main Issue #809 receipts.
This module reuses the reviewed Issue #802 metadata extractor and never reads
raster values. Metadata equality is reported separately for grid and container
fields and must not be interpreted as mask-value semantics or model authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from scripts import profile_cems_europe_rp10_geotiff as _rp10
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_cems_europe_rp10_geotiff as _rp10

SOURCE_ISSUE = 809
PROFILE_ISSUE = 816
DATASET_ID = _rp10.DATASET_ID
RELEASE = _rp10.RELEASE
BASE_URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/"
PROFILE_SCHEMA_VERSION = "oc-cems-mask-geotiff-profile-v1"
COMPARISON_SCHEMA_VERSION = "oc-cems-mask-rp10-metadata-comparison-v1"

MASK_RECEIPTS: dict[str, dict[str, Any]] = {
    "permanent_water": {
        "filename": "Europe_permanent_water_bodies.tif",
        "byte_count": 112_287_284,
        "sha256": "5e14f13fb202263a8407026aa60e7c455db7976284217e5da09ea49c13112eee",
    },
    "spurious_depth": {
        "filename": "Europe_spurious_depth_areas.tif",
        "byte_count": 74_730_820,
        "sha256": "6b609153e28b7e634159525cf7cc9089242a8e17de2578f162d51a0e80d2e7c8",
    },
}

_GRID_FIELDS = (
    "width",
    "height",
    "crs",
    "transform_gdal",
    "resolution",
    "bounds",
)
_CONTAINER_FIELDS = (
    "driver",
    "band_count",
    "dtypes",
    "nodatavals",
    "scales",
    "offsets",
)


class CemsMaskGeoTiffProfileError(RuntimeError):
    """Raised when a frozen mask identity or metadata comparison is invalid."""


def _receipt(mask_kind: str) -> dict[str, Any]:
    if type(mask_kind) is not str or mask_kind not in MASK_RECEIPTS:
        raise CemsMaskGeoTiffProfileError("mask kind is outside the frozen #809 receipt set")
    return MASK_RECEIPTS[mask_kind]


def profile_cems_mask_geotiff(path: str | Path, *, mask_kind: str) -> dict[str, Any]:
    """Profile only one exact companion-mask object accepted by trusted-main #809."""
    receipt = _receipt(mask_kind)
    filename = receipt["filename"]
    try:
        profile = _rp10._profile_bound_geotiff(
            path,
            expected_byte_count=receipt["byte_count"],
            expected_sha256=receipt["sha256"],
            schema_version=PROFILE_SCHEMA_VERSION,
            dataset_id=DATASET_ID,
            source_issue=SOURCE_ISSUE,
            profile_issue=PROFILE_ISSUE,
            release=RELEASE,
            filename=filename,
            source_url=BASE_URL + filename,
        )
    except _rp10.CemsRp10GeoTiffProfileError as exc:
        raise CemsMaskGeoTiffProfileError(str(exc)) from exc

    profile["mask_kind"] = mask_kind
    profile["mask_values_inspected"] = False
    return profile


def _require_verified_profile(profile: Any, *, label: str) -> dict[str, Any]:
    if type(profile) is not dict:
        raise CemsMaskGeoTiffProfileError(f"{label} profile must be an object")
    required_true = ("receipt_identity_verified", "geotiff_metadata_verified")
    for field in required_true:
        if profile.get(field) is not True:
            raise CemsMaskGeoTiffProfileError(f"{label} profile {field} is not verified")
    if profile.get("raster_values_inspected") is not False:
        raise CemsMaskGeoTiffProfileError(f"{label} profile inspected raster values")
    for field in ("benchmark_use_authorized", "publication_authorized", "model_use_authorized"):
        if profile.get(field) is not False:
            raise CemsMaskGeoTiffProfileError(f"{label} profile authority ceiling drifted")
    for field in _GRID_FIELDS + _CONTAINER_FIELDS:
        if field not in profile:
            raise CemsMaskGeoTiffProfileError(f"{label} profile is missing {field}")
    return profile


def compare_mask_profile_to_rp10(
    mask_profile: dict[str, Any],
    rp10_profile: dict[str, Any],
) -> dict[str, Any]:
    """Compare observed structural metadata without inferring mask semantics."""
    mask_profile = _require_verified_profile(mask_profile, label="mask")
    rp10_profile = _require_verified_profile(rp10_profile, label="RP10")

    if mask_profile.get("dataset_id") != DATASET_ID or rp10_profile.get("dataset_id") != DATASET_ID:
        raise CemsMaskGeoTiffProfileError("profile dataset identity drifted from frozen CEMS dataset")
    if mask_profile.get("source_issue") != SOURCE_ISSUE:
        raise CemsMaskGeoTiffProfileError("mask profile is not bound to Issue #809")
    if mask_profile.get("profile_issue") != PROFILE_ISSUE:
        raise CemsMaskGeoTiffProfileError("mask profile is not bound to Issue #816")
    mask_kind = mask_profile.get("mask_kind")
    receipt = _receipt(mask_kind)
    if mask_profile.get("filename") != receipt["filename"]:
        raise CemsMaskGeoTiffProfileError("mask profile filename drifted from #809 receipt")
    if mask_profile.get("receipt_byte_count") != receipt["byte_count"]:
        raise CemsMaskGeoTiffProfileError("mask profile byte count drifted from #809 receipt")
    if mask_profile.get("receipt_sha256") != receipt["sha256"]:
        raise CemsMaskGeoTiffProfileError("mask profile SHA-256 drifted from #809 receipt")
    if mask_profile.get("mask_values_inspected") is not False:
        raise CemsMaskGeoTiffProfileError("mask value semantics escaped metadata-only boundary")

    grid_equal = {
        field: mask_profile[field] == rp10_profile[field]
        for field in _GRID_FIELDS
    }
    container_equal = {
        field: mask_profile[field] == rp10_profile[field]
        for field in _CONTAINER_FIELDS
    }
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "source_issue": SOURCE_ISSUE,
        "profile_issue": PROFILE_ISSUE,
        "mask_kind": mask_kind,
        "mask_filename": mask_profile["filename"],
        "rp10_filename": rp10_profile.get("filename"),
        "grid_field_equal": grid_equal,
        "grid_metadata_equal": all(grid_equal.values()),
        "container_field_equal": container_equal,
        "container_metadata_equal": all(container_equal.values()),
        "mask_values_inspected": False,
        "mask_value_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
