# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate durable Agent Action results for CEMS companion-mask profiles."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_europe_mask_profiles as _worker
    from scripts import acquire_cems_europe_mask_receipts as _masks
    from scripts import agent_action_protocol_cems_mask_profiles as _protocol
    from scripts import profile_cems_europe_mask_geotiffs as _profile
    from scripts import validate_agent_action_result_cems_masks as _legacy
    from scripts import validate_agent_action_result_cems_rp10 as _rp10_receipt_result
    from scripts import validate_agent_action_result_cems_rp10_profile as _rp10_result
    from scripts.validate_agent_action_request_cems_mask_profiles import (
        CEMS_MASK_PROFILES_ACTION,
        CEMS_MASK_PROFILES_DATASET_ID,
        CEMS_MASK_PROFILES_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover
    import acquire_cems_europe_mask_profiles as _worker
    import acquire_cems_europe_mask_receipts as _masks
    import agent_action_protocol_cems_mask_profiles as _protocol
    import profile_cems_europe_mask_geotiffs as _profile
    import validate_agent_action_result_cems_masks as _legacy
    import validate_agent_action_result_cems_rp10 as _rp10_receipt_result
    import validate_agent_action_result_cems_rp10_profile as _rp10_result
    from validate_agent_action_request_cems_mask_profiles import (
        CEMS_MASK_PROFILES_ACTION,
        CEMS_MASK_PROFILES_DATASET_ID,
        CEMS_MASK_PROFILES_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_MASK_PROFILES_ACTION}
_CEMS_MASK_PROFILES_FIELD = "cems_europe_mask_profiles"
_CEMS_MASK_PROFILES_EVIDENCE_FIELDS = _legacy._CEMS_MASK_EVIDENCE_FIELDS - {
    _legacy._CEMS_MASK_FIELD
} | {_CEMS_MASK_PROFILES_FIELD}
_AGGREGATE_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "profile_issue", "release",
    "rp10_profile_receipt", "mask_profile_receipts", "comparisons",
    "external_bytes_persisted", "mask_values_inspected", "mask_value_semantics_verified",
    "benchmark_use_authorized", "publication_authorized", "model_use_authorized",
}
_PROFILE_RECEIPT_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "profile_issue", "release",
    "mask_kind", "filename", "requested_url", "final_url", "retrieved_at", "http_status",
    "media_type", "content_length_header", "receipt_byte_count", "receipt_sha256",
    "geotiff_profile", "external_bytes_persisted", "mask_values_inspected",
    "mask_value_semantics_verified", "benchmark_use_authorized", "publication_authorized",
    "model_use_authorized",
}
_GEOTIFF_PROFILE_FIELDS = _rp10_result._GEOTIFF_PROFILE_FIELDS | {
    "mask_kind", "mask_values_inspected"
}
_COMPARISON_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "profile_issue", "mask_kind",
    "mask_filename", "rp10_filename", "grid_field_equal", "grid_metadata_equal",
    "container_field_equal", "container_metadata_equal", "mask_values_inspected",
    "mask_value_semantics_verified", "benchmark_use_authorized", "publication_authorized",
    "model_use_authorized",
}


def _validate_profile_metadata(profile: dict[str, Any]) -> None:
    band_count = profile["band_count"]
    if type(band_count) is not int or isinstance(band_count, bool) or not (
        1 <= band_count <= _rp10_result._MAX_BANDS
    ):
        raise ResultError("CEMS mask GeoTIFF band_count is outside bounded contract")
    for field in ("width", "height"):
        value = profile[field]
        if type(value) is not int or isinstance(value, bool) or value < 1:
            raise ResultError(f"CEMS mask GeoTIFF {field} is invalid")
    dtypes = profile["dtypes"]
    if type(dtypes) is not list or len(dtypes) != band_count:
        raise ResultError("CEMS mask GeoTIFF dtypes shape drifted")
    for value in dtypes:
        _rp10_result._bounded_text(value, field="dtype", limit=_rp10_result._MAX_TEXT)

    crs = profile["crs"]
    if type(crs) is not dict or set(crs) != {"string", "epsg", "wkt"}:
        raise ResultError("CEMS mask GeoTIFF CRS shape drifted")
    _rp10_result._bounded_text(
        crs["string"], field="CRS string", limit=_rp10_result._MAX_CRS_TEXT, nullable=True
    )
    _rp10_result._bounded_text(
        crs["wkt"], field="CRS WKT", limit=_rp10_result._MAX_CRS_TEXT, nullable=True
    )
    epsg = crs["epsg"]
    if epsg is not None and (type(epsg) is not int or isinstance(epsg, bool) or epsg < 1):
        raise ResultError("CEMS mask GeoTIFF CRS EPSG is invalid")

    _rp10_result._numeric_list(profile["transform_gdal"], field="transform_gdal", length=6)
    _rp10_result._numeric_list(profile["resolution"], field="resolution", length=2)
    _rp10_result._numeric_list(profile["bounds"], field="bounds", length=4)
    for field in ("nodatavals", "scales", "offsets"):
        _rp10_result._numeric_list(
            profile[field], field=field, length=band_count, nullable=True
        )
    for field in ("descriptions", "band_units"):
        values = profile[field]
        if type(values) is not list or len(values) != band_count:
            raise ResultError(f"CEMS mask GeoTIFF {field} shape drifted")
        for value in values:
            _rp10_result._bounded_text(
                value, field=field, limit=_rp10_result._MAX_TEXT, nullable=True
            )

    tags = profile["band_unit_tags"]
    if type(tags) is not list or len(tags) != band_count:
        raise ResultError("CEMS mask GeoTIFF unit tag shape drifted")
    for band_tags in tags:
        if type(band_tags) is not dict:
            raise ResultError("CEMS mask GeoTIFF unit tags must be objects")
        for key, value in band_tags.items():
            if type(key) is not str or key.upper() not in _rp10_result._UNIT_TAG_KEYS:
                raise ResultError("CEMS mask GeoTIFF unit tag key escaped allowlist")
            _rp10_result._bounded_text(key, field="unit tag key", limit=_rp10_result._MAX_TEXT)
            _rp10_result._bounded_text(value, field="unit tag value", limit=_rp10_result._MAX_TEXT)
    if type(profile["unit_metadata_present"]) is not bool:
        raise ResultError("CEMS mask GeoTIFF unit_metadata_present must be boolean")

    reader = profile["reader"]
    if type(reader) is not dict or set(reader) != {
        "name", "version", "gdal_version", "proj_version"
    }:
        raise ResultError("CEMS mask GeoTIFF reader shape drifted")
    if reader["name"] != "rasterio":
        raise ResultError("CEMS mask GeoTIFF reader is not rasterio")
    _rp10_result._bounded_text(reader["version"], field="reader version", limit=_rp10_result._MAX_TEXT)
    _rp10_result._bounded_text(
        reader["gdal_version"], field="GDAL version", limit=_rp10_result._MAX_TEXT, nullable=True
    )
    _rp10_result._bounded_text(
        reader["proj_version"], field="PROJ version", limit=_rp10_result._MAX_TEXT, nullable=True
    )


def _validate_mask_profile_receipt(
    receipt: Any, *, kind: str, filename: str
) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _PROFILE_RECEIPT_FIELDS:
        raise ResultError("CEMS mask profile receipt fields drifted")
    accepted = _profile.MASK_RECEIPTS[kind]
    url = _profile.BASE_URL + filename
    exact = {
        "schema_version": _worker.PROFILE_RECEIPT_SCHEMA_VERSION,
        "dataset_id": CEMS_MASK_PROFILES_DATASET_ID,
        "source_issue": _worker.SOURCE_ISSUE,
        "profile_issue": CEMS_MASK_PROFILES_ISSUE,
        "release": _masks.RELEASE,
        "mask_kind": kind,
        "filename": filename,
        "requested_url": url,
        "final_url": url,
        "http_status": 200,
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "external_bytes_persisted": False,
        "mask_values_inspected": False,
        "mask_value_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS mask profile receipt {field} drifted from frozen authority")
    _base._utc_second(receipt["retrieved_at"], f"{_CEMS_MASK_PROFILES_FIELD}.{kind}.retrieved_at")
    media = receipt["media_type"]
    if type(media) is not str or media not in _masks._base.ALLOWED_MEDIA_TYPES:
        raise ResultError("CEMS mask profile media_type is outside fixed contract")
    declared = receipt["content_length_header"]
    if declared is not None and (
        type(declared) is not int
        or isinstance(declared, bool)
        or declared != accepted["byte_count"]
    ):
        raise ResultError("CEMS mask profile Content-Length does not match accepted receipt")

    profile = receipt["geotiff_profile"]
    if type(profile) is not dict or set(profile) != _GEOTIFF_PROFILE_FIELDS:
        raise ResultError("CEMS mask GeoTIFF profile fields drifted")
    profile_exact = {
        "schema_version": _profile.PROFILE_SCHEMA_VERSION,
        "dataset_id": CEMS_MASK_PROFILES_DATASET_ID,
        "source_issue": _worker.SOURCE_ISSUE,
        "profile_issue": CEMS_MASK_PROFILES_ISSUE,
        "release": _masks.RELEASE,
        "filename": filename,
        "source_url": url,
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "receipt_identity_verified": True,
        "driver": "GTiff",
        "mask_kind": kind,
        "raster_values_inspected": False,
        "mask_values_inspected": False,
        "geotiff_metadata_verified": True,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in profile_exact.items():
        if type(profile[field]) is not type(expected) or profile[field] != expected:
            raise ResultError(f"CEMS mask GeoTIFF profile {field} drifted from frozen authority")
    _validate_profile_metadata(profile)
    return receipt


def _validate_comparison(
    comparison: Any,
    mask_profile: dict[str, Any],
    rp10_profile: dict[str, Any],
) -> dict[str, Any]:
    if type(comparison) is not dict or set(comparison) != _COMPARISON_FIELDS:
        raise ResultError("CEMS mask/RP10 comparison fields drifted")
    try:
        expected = _profile.compare_mask_profile_to_rp10(mask_profile, rp10_profile)
    except _profile.CemsMaskGeoTiffProfileError as exc:
        raise ResultError(f"CEMS mask/RP10 comparison input is invalid: {exc}") from exc
    if comparison != expected:
        raise ResultError("CEMS mask/RP10 comparison does not match validated profiles")
    return comparison


def validate_cems_mask_profiles(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _AGGREGATE_FIELDS:
        raise ResultError("CEMS mask profile aggregate fields drifted")
    exact = {
        "schema_version": _worker.SCHEMA_VERSION,
        "dataset_id": CEMS_MASK_PROFILES_DATASET_ID,
        "source_issue": _worker.SOURCE_ISSUE,
        "profile_issue": CEMS_MASK_PROFILES_ISSUE,
        "release": _masks.RELEASE,
        "external_bytes_persisted": False,
        "mask_values_inspected": False,
        "mask_value_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS mask profile aggregate {field} drifted from frozen authority")

    rp10_receipt = _rp10_result.validate_cems_rp10_profile_receipt(
        receipt["rp10_profile_receipt"]
    )
    rp10_profile = rp10_receipt["geotiff_profile"]
    profiles = receipt["mask_profile_receipts"]
    comparisons = receipt["comparisons"]
    if type(profiles) is not list or len(profiles) != len(_masks.ASSETS):
        raise ResultError("CEMS mask profile receipt count drifted")
    if type(comparisons) is not list or len(comparisons) != len(_masks.ASSETS):
        raise ResultError("CEMS mask/RP10 comparison count drifted")
    for profile_receipt, comparison, (kind, filename) in zip(
        profiles, comparisons, _masks.ASSETS, strict=True
    ):
        validated = _validate_mask_profile_receipt(
            profile_receipt, kind=kind, filename=filename
        )
        _validate_comparison(
            comparison,
            validated["geotiff_profile"],
            rp10_profile,
        )
    return receipt


def _validate_profile_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("CEMS mask profile result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _legacy.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _legacy.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_MASK_PROFILES_ACTION:
        raise ResultError("unsupported CEMS mask profile action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _legacy.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("CEMS mask profile network result requires target_sha == execution_sha")
    if result["source_issue"] != CEMS_MASK_PROFILES_ISSUE:
        raise ResultError("CEMS mask profile result is outside control issue 816")
    if result["dataset_id"] != CEMS_MASK_PROFILES_DATASET_ID:
        raise ResultError("CEMS mask profile result is outside frozen dataset")
    try:
        expected_id = _protocol.semantic_request_id_from_result(result)
    except _protocol.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if semantic_id != expected_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = _base._utc_second(result["started_at"], "started_at")
    finished = _base._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase, status = result["phase"], result["status"]
    if phase not in _legacy.ALLOWED_PHASES or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported CEMS mask profile result state")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id, failure_class = result["duplicate_result_comment_id"], result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        return _rp10_receipt_result._validate_request_validation_state(
            result,
            status=status,
            duplicate_id=duplicate_id,
            failure_class=failure_class,
        )
    if phase != "acquisition_receipt":
        raise ResultError("CEMS mask profile network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _CEMS_MASK_PROFILES_EVIDENCE_FIELDS:
        raise ResultError("CEMS mask profile evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError("CEMS mask profile acquisition requires complete non-reused ledger state")

    aggregate = evidence[_CEMS_MASK_PROFILES_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful CEMS mask profile acquisition cannot carry failure_class")
        aggregate = validate_cems_mask_profiles(aggregate)
        retrieved_times = [
            item["retrieved_at"] for item in aggregate["mask_profile_receipts"]
        ] + [aggregate["rp10_profile_receipt"]["retrieved_at"]]
        for value in retrieved_times:
            retrieved = _base._utc_second(value, f"{_CEMS_MASK_PROFILES_FIELD}.retrieved_at")
            if retrieved < started or retrieved > finished:
                raise ResultError("CEMS profile retrieved_at must fall within action bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS mask profile failure class is invalid")
        if aggregate is not None:
            raise ResultError("blocked CEMS mask profile acquisition cannot publish profiles")
    else:
        raise ResultError("duplicate CEMS mask profile result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == CEMS_MASK_PROFILES_ACTION:
        return _validate_profile_result(result)
    return _legacy.validate_result(result)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.result_env not in os.environ:
        print("BLOCKED: result environment variable is absent", file=sys.stderr)
        return 2
    try:
        result = validate_result(_base._strict_json(os.environ[args.result_env]))
    except ResultError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
