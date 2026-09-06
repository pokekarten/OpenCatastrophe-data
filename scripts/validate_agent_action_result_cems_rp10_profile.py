# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate durable Agent Action results for the trusted CEMS RP10 profile."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_europe_rp10_receipt as _cems
    from scripts import agent_action_protocol_cems_rp10_profile as _protocol
    from scripts import validate_agent_action_result_cems_rp10 as _legacy
    from scripts.validate_agent_action_request_cems_rp10_profile import (
        CEMS_RP10_PROFILE_ACTION,
        CEMS_RP10_PROFILE_DATASET_ID,
        CEMS_RP10_PROFILE_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_rp10_receipt as _cems
    import agent_action_protocol_cems_rp10_profile as _protocol
    import validate_agent_action_result_cems_rp10 as _legacy
    from validate_agent_action_request_cems_rp10_profile import (
        CEMS_RP10_PROFILE_ACTION,
        CEMS_RP10_PROFILE_DATASET_ID,
        CEMS_RP10_PROFILE_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_RP10_PROFILE_ACTION}
_CEMS_PROFILE_FIELD = "cems_europe_rp10_profile"
_CEMS_PROFILE_EVIDENCE_FIELDS = _legacy._CEMS_EVIDENCE_FIELDS - {_legacy._CEMS_FIELD} | {
    _CEMS_PROFILE_FIELD
}
_ACCEPTED_BYTE_COUNT = 272_286_610
_ACCEPTED_SHA256 = "15f86b86c228a065250b05488548d7386ac8e33cec4cba6da93f712f7500f45b"
_PROFILE_SCHEMA_VERSION = "oc-cems-rp10-geotiff-profile-receipt-v1"
_GEOTIFF_SCHEMA_VERSION = "oc-cems-rp10-geotiff-profile-v1"
_MAX_BANDS = 64
_MAX_CRS_TEXT = 65_536
_MAX_TEXT = 256
_UNIT_TAG_KEYS = frozenset({"UNIT", "UNITS", "UNITTYPE", "UNIT_TYPE"})
_PROFILE_RECEIPT_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "profile_issue", "release",
    "filename", "requested_url", "final_url", "retrieved_at", "http_status",
    "media_type", "content_length_header", "receipt_byte_count", "receipt_sha256",
    "geotiff_profile", "external_bytes_persisted", "benchmark_use_authorized",
    "publication_authorized", "model_use_authorized",
}
_GEOTIFF_PROFILE_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "profile_issue", "release",
    "filename", "source_url", "receipt_byte_count", "receipt_sha256",
    "receipt_identity_verified", "driver", "band_count", "dtypes", "width", "height",
    "crs", "transform_gdal", "resolution", "bounds", "nodatavals", "scales",
    "offsets", "descriptions", "band_units", "band_unit_tags", "unit_metadata_present",
    "reader", "raster_values_inspected", "geotiff_metadata_verified",
    "benchmark_use_authorized", "publication_authorized", "model_use_authorized",
}


def _bounded_text(value: Any, *, field: str, limit: int, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if type(value) is not str or len(value) > limit:
        raise ResultError(f"{field} is outside bounded profile contract")
    return value


def _profile_number(value: Any, *, field: str, nullable: bool = False) -> Any:
    if value is None and nullable:
        return None
    if type(value) is bool:
        raise ResultError(f"{field} is not bounded numeric metadata")
    if type(value) is int:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ResultError(f"{field} contains non-finite float metadata")
        return value
    if value in {"NaN", "Infinity", "-Infinity"}:
        return value
    raise ResultError(f"{field} is not bounded numeric metadata")


def _numeric_list(value: Any, *, field: str, length: int, nullable: bool = False) -> list[Any]:
    if type(value) is not list or len(value) != length:
        raise ResultError(f"{field} shape drifted")
    for item in value:
        _profile_number(item, field=field, nullable=nullable)
    return value


def validate_cems_rp10_profile_receipt(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _PROFILE_RECEIPT_FIELDS:
        raise ResultError("CEMS RP10 profile receipt fields drifted")
    exact_outer = {
        "schema_version": _PROFILE_SCHEMA_VERSION,
        "dataset_id": CEMS_RP10_PROFILE_DATASET_ID,
        "source_issue": _cems.SOURCE_ISSUE,
        "profile_issue": CEMS_RP10_PROFILE_ISSUE,
        "release": _cems.RELEASE,
        "filename": _cems.FILENAME,
        "requested_url": _cems.SOURCE_URL,
        "final_url": _cems.SOURCE_URL,
        "http_status": 200,
        "receipt_byte_count": _ACCEPTED_BYTE_COUNT,
        "receipt_sha256": _ACCEPTED_SHA256,
        "external_bytes_persisted": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_outer.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS RP10 profile receipt {field} drifted from frozen authority")
    _base._utc_second(receipt["retrieved_at"], f"{_CEMS_PROFILE_FIELD}.retrieved_at")
    if receipt["media_type"] not in _cems.ALLOWED_MEDIA_TYPES:
        raise ResultError("CEMS RP10 profile media_type is outside fixed contract")
    declared = receipt["content_length_header"]
    if declared is not None and (type(declared) is not int or declared != _ACCEPTED_BYTE_COUNT):
        raise ResultError("CEMS RP10 profile Content-Length does not match accepted receipt")

    profile = receipt["geotiff_profile"]
    if type(profile) is not dict or set(profile) != _GEOTIFF_PROFILE_FIELDS:
        raise ResultError("CEMS RP10 GeoTIFF profile fields drifted")
    exact_profile = {
        "schema_version": _GEOTIFF_SCHEMA_VERSION,
        "dataset_id": CEMS_RP10_PROFILE_DATASET_ID,
        "source_issue": _cems.SOURCE_ISSUE,
        "profile_issue": CEMS_RP10_PROFILE_ISSUE,
        "release": _cems.RELEASE,
        "filename": _cems.FILENAME,
        "source_url": _cems.SOURCE_URL,
        "receipt_byte_count": _ACCEPTED_BYTE_COUNT,
        "receipt_sha256": _ACCEPTED_SHA256,
        "receipt_identity_verified": True,
        "driver": "GTiff",
        "raster_values_inspected": False,
        "geotiff_metadata_verified": True,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_profile.items():
        if type(profile[field]) is not type(expected) or profile[field] != expected:
            raise ResultError(f"CEMS RP10 GeoTIFF profile {field} drifted from frozen authority")

    band_count = profile["band_count"]
    if type(band_count) is not int or isinstance(band_count, bool) or not (1 <= band_count <= _MAX_BANDS):
        raise ResultError("CEMS RP10 GeoTIFF band_count is outside bounded contract")
    for field in ("width", "height"):
        value = profile[field]
        if type(value) is not int or isinstance(value, bool) or value < 1:
            raise ResultError(f"CEMS RP10 GeoTIFF {field} is invalid")
    dtypes = profile["dtypes"]
    if type(dtypes) is not list or len(dtypes) != band_count:
        raise ResultError("CEMS RP10 GeoTIFF dtypes shape drifted")
    for value in dtypes:
        _bounded_text(value, field="dtype", limit=_MAX_TEXT)

    crs = profile["crs"]
    if type(crs) is not dict or set(crs) != {"string", "epsg", "wkt"}:
        raise ResultError("CEMS RP10 GeoTIFF CRS shape drifted")
    _bounded_text(crs["string"], field="CRS string", limit=_MAX_CRS_TEXT, nullable=True)
    _bounded_text(crs["wkt"], field="CRS WKT", limit=_MAX_CRS_TEXT, nullable=True)
    epsg = crs["epsg"]
    if epsg is not None and (type(epsg) is not int or isinstance(epsg, bool) or epsg < 1):
        raise ResultError("CEMS RP10 GeoTIFF CRS EPSG is invalid")

    _numeric_list(profile["transform_gdal"], field="transform_gdal", length=6)
    _numeric_list(profile["resolution"], field="resolution", length=2)
    _numeric_list(profile["bounds"], field="bounds", length=4)
    for field in ("nodatavals", "scales", "offsets"):
        _numeric_list(profile[field], field=field, length=band_count, nullable=True)
    for field in ("descriptions", "band_units"):
        values = profile[field]
        if type(values) is not list or len(values) != band_count:
            raise ResultError(f"CEMS RP10 GeoTIFF {field} shape drifted")
        for value in values:
            _bounded_text(value, field=field, limit=_MAX_TEXT, nullable=True)

    tags = profile["band_unit_tags"]
    if type(tags) is not list or len(tags) != band_count:
        raise ResultError("CEMS RP10 GeoTIFF unit tag shape drifted")
    for band_tags in tags:
        if type(band_tags) is not dict:
            raise ResultError("CEMS RP10 GeoTIFF unit tags must be objects")
        for key, value in band_tags.items():
            if type(key) is not str or key.upper() not in _UNIT_TAG_KEYS:
                raise ResultError("CEMS RP10 GeoTIFF unit tag key escaped allowlist")
            _bounded_text(key, field="unit tag key", limit=_MAX_TEXT)
            _bounded_text(value, field="unit tag value", limit=_MAX_TEXT)
    if type(profile["unit_metadata_present"]) is not bool:
        raise ResultError("CEMS RP10 GeoTIFF unit_metadata_present must be boolean")

    reader = profile["reader"]
    if type(reader) is not dict or set(reader) != {"name", "version", "gdal_version", "proj_version"}:
        raise ResultError("CEMS RP10 GeoTIFF reader shape drifted")
    if reader["name"] != "rasterio":
        raise ResultError("CEMS RP10 GeoTIFF reader is not rasterio")
    _bounded_text(reader["version"], field="reader version", limit=_MAX_TEXT)
    _bounded_text(reader["gdal_version"], field="GDAL version", limit=_MAX_TEXT, nullable=True)
    _bounded_text(reader["proj_version"], field="PROJ version", limit=_MAX_TEXT, nullable=True)
    return receipt


def _validate_profile_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("CEMS RP10 profile result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _legacy.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _legacy.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_RP10_PROFILE_ACTION:
        raise ResultError("unsupported CEMS RP10 profile action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _legacy.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("CEMS RP10 profile requires target_sha == execution_sha")
    if result["source_issue"] != CEMS_RP10_PROFILE_ISSUE:
        raise ResultError("CEMS RP10 profile result is outside control issue 802")
    if result["dataset_id"] != CEMS_RP10_PROFILE_DATASET_ID:
        raise ResultError("CEMS RP10 profile result is outside frozen dataset")
    try:
        expected_semantic_id = _protocol.semantic_request_id_from_result(result)
    except _protocol.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if semantic_id != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = _base._utc_second(result["started_at"], "started_at")
    finished = _base._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase, status = result["phase"], result["status"]
    if phase not in _legacy.ALLOWED_PHASES or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported CEMS RP10 profile result state")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id, failure_class = result["duplicate_result_comment_id"], result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        return _legacy._validate_request_validation_state(
            result, status=status, duplicate_id=duplicate_id, failure_class=failure_class
        )
    if phase != "acquisition_receipt":
        raise ResultError("CEMS RP10 profile network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _CEMS_PROFILE_EVIDENCE_FIELDS:
        raise ResultError("CEMS RP10 profile evidence fields drifted")
    for field in _legacy._legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError("CEMS RP10 profile requires complete non-reused ledger state")

    profile_receipt = evidence[_CEMS_PROFILE_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful CEMS RP10 profile cannot carry failure_class")
        profile_receipt = validate_cems_rp10_profile_receipt(profile_receipt)
        retrieved = _base._utc_second(
            profile_receipt["retrieved_at"], f"{_CEMS_PROFILE_FIELD}.retrieved_at"
        )
        if retrieved < started or retrieved > finished:
            raise ResultError("CEMS RP10 profile retrieved_at must fall within action bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS RP10 profile failure class is invalid")
        if profile_receipt is not None:
            raise ResultError("blocked CEMS RP10 profile cannot publish profile evidence")
    else:
        raise ResultError("duplicate CEMS RP10 profile must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == CEMS_RP10_PROFILE_ACTION:
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
