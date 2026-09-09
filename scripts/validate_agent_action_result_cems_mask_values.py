# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate durable Agent Action results for CEMS companion-mask value inventories."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_europe_mask_receipts as _masks
    from scripts import acquire_cems_europe_mask_value_inventories as _worker
    from scripts import agent_action_protocol_cems_mask_values as _protocol
    from scripts import profile_cems_europe_mask_geotiffs as _metadata
    from scripts import profile_cems_europe_mask_values as _values
    from scripts import validate_agent_action_result_cems_mask_profiles as _legacy
    from scripts import validate_agent_action_result_cems_rp10 as _rp10_receipt_result
    from scripts.validate_agent_action_request_cems_mask_values import (
        CEMS_MASK_VALUE_INVENTORIES_ACTION,
        CEMS_MASK_VALUE_INVENTORIES_DATASET_ID,
        CEMS_MASK_VALUE_INVENTORIES_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover
    import acquire_cems_europe_mask_receipts as _masks
    import acquire_cems_europe_mask_value_inventories as _worker
    import agent_action_protocol_cems_mask_values as _protocol
    import profile_cems_europe_mask_geotiffs as _metadata
    import profile_cems_europe_mask_values as _values
    import validate_agent_action_result_cems_mask_profiles as _legacy
    import validate_agent_action_result_cems_rp10 as _rp10_receipt_result
    from validate_agent_action_request_cems_mask_values import (
        CEMS_MASK_VALUE_INVENTORIES_ACTION,
        CEMS_MASK_VALUE_INVENTORIES_DATASET_ID,
        CEMS_MASK_VALUE_INVENTORIES_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_MASK_VALUE_INVENTORIES_ACTION}
_CEMS_MASK_VALUE_INVENTORIES_FIELD = "cems_europe_mask_value_inventories"
_CEMS_MASK_VALUE_INVENTORIES_EVIDENCE_FIELDS = (
    _legacy._CEMS_MASK_PROFILES_EVIDENCE_FIELDS
    - {_legacy._CEMS_MASK_PROFILES_FIELD}
    | {_CEMS_MASK_VALUE_INVENTORIES_FIELD}
)

_AGGREGATE_FIELDS = {
    "schema_version",
    "dataset_id",
    "source_issue",
    "profile_issue",
    "release",
    "mask_value_inventory_receipts",
    "external_bytes_persisted",
    "mask_values_inspected",
    "mask_value_semantics_verified",
    "per_cell_scientific_correctness_verified",
    "benchmark_use_authorized",
    "publication_authorized",
    "model_use_authorized",
}
_INVENTORY_RECEIPT_FIELDS = {
    "schema_version",
    "dataset_id",
    "source_issue",
    "profile_issue",
    "release",
    "mask_kind",
    "filename",
    "requested_url",
    "final_url",
    "retrieved_at",
    "http_status",
    "media_type",
    "content_length_header",
    "receipt_byte_count",
    "receipt_sha256",
    "value_inventory",
    "external_bytes_persisted",
    "mask_values_inspected",
    "mask_value_semantics_verified",
    "per_cell_scientific_correctness_verified",
    "benchmark_use_authorized",
    "publication_authorized",
    "model_use_authorized",
}
_VALUE_RESULT_FIELDS = {
    "schema_version",
    "dataset_id",
    "release",
    "source_issue",
    "profile_issue",
    "mask_kind",
    "filename",
    "receipt_byte_count",
    "receipt_sha256",
    "receipt_identity_verified",
    "grid",
    "inventory",
    "mask_values_inspected",
    "mask_value_semantics_verified",
    "per_cell_scientific_correctness_verified",
    "benchmark_use_authorized",
    "model_use_authorized",
    "publication_authorized",
    "external_bytes_persisted",
    "result_sha256",
}
_GRID_FIELDS = {
    "width",
    "height",
    "crs",
    "transform_gdal",
    "resolution",
    "bounds",
    "band_count",
    "dtype",
}
_INVENTORY_FIELDS = {
    "total_cells",
    "block_count",
    "nodata_value",
    "nodata_count",
    "nan_non_nodata_count",
    "positive_infinity_count",
    "negative_infinity_count",
    "finite_count",
    "zero_count",
    "nonzero_count",
    "finite_min",
    "finite_max",
    "cardinality_cap",
    "cardinality_cap_exceeded",
    "finite_unique_value_count",
    "finite_value_counts",
    "encoding_observation",
    "inventory_sha256",
}

_EXPECTED_GRID = {
    "width": 110162,
    "height": 51992,
    "crs": "EPSG:4326",
    "transform_gdal": [
        -24.54208333,
        0.0008333333333333334,
        0.0,
        71.13375,
        0.0,
        -0.0008333333333333334,
    ],
    "resolution": [0.0008333333333333334, 0.0008333333333333334],
    "bounds": [
        -24.54208333,
        27.80708333333334,
        67.25958333666668,
        71.13375,
    ],
    "band_count": 1,
    "dtype": "float64",
}
_EXPECTED_TOTAL_CELLS = _EXPECTED_GRID["width"] * _EXPECTED_GRID["height"]


def _nonnegative_int(value: Any, field: str) -> int:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise ResultError(f"{field} must be a non-negative integer")
    return value


def _finite_number_or_none(value: Any, field: str) -> int | float | None:
    if value is None:
        return None
    if type(value) not in (int, float) or isinstance(value, bool):
        raise ResultError(f"{field} must be finite numeric metadata or null")
    if not math.isfinite(float(value)):
        raise ResultError(f"{field} must be finite numeric metadata or null")
    return value


def _sha256_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_inventory(inventory: Any) -> dict[str, Any]:
    if type(inventory) is not dict or set(inventory) != _INVENTORY_FIELDS:
        raise ResultError("CEMS mask value inventory fields drifted")

    supplied_digest = inventory["inventory_sha256"]
    if type(supplied_digest) is not str or not _legacy.DIGEST_RE.fullmatch(
        supplied_digest
    ):
        raise ResultError("CEMS mask value inventory digest is invalid")
    digest_payload = dict(inventory)
    del digest_payload["inventory_sha256"]
    if supplied_digest != _sha256_digest(digest_payload):
        raise ResultError("CEMS mask value inventory digest does not match payload")

    total_cells = _nonnegative_int(inventory["total_cells"], "inventory.total_cells")
    if total_cells != _EXPECTED_TOTAL_CELLS:
        raise ResultError("CEMS mask value inventory total cell count drifted")
    block_count = _nonnegative_int(inventory["block_count"], "inventory.block_count")
    if not (1 <= block_count <= total_cells):
        raise ResultError("CEMS mask value inventory block_count is invalid")
    if inventory["nodata_value"] != -9999:
        raise ResultError("CEMS mask value inventory nodata value drifted")

    count_fields = (
        "nodata_count",
        "nan_non_nodata_count",
        "positive_infinity_count",
        "negative_infinity_count",
        "finite_count",
        "zero_count",
        "nonzero_count",
    )
    counts = {
        field: _nonnegative_int(inventory[field], f"inventory.{field}")
        for field in count_fields
    }
    accounted = (
        counts["nodata_count"]
        + counts["nan_non_nodata_count"]
        + counts["positive_infinity_count"]
        + counts["negative_infinity_count"]
        + counts["finite_count"]
    )
    if accounted != total_cells:
        raise ResultError("CEMS mask value inventory cell accounting is incomplete")
    if counts["zero_count"] + counts["nonzero_count"] != counts["finite_count"]:
        raise ResultError("CEMS mask value inventory finite zero accounting drifted")

    finite_min = _finite_number_or_none(inventory["finite_min"], "inventory.finite_min")
    finite_max = _finite_number_or_none(inventory["finite_max"], "inventory.finite_max")
    if counts["finite_count"] == 0:
        if finite_min is not None or finite_max is not None:
            raise ResultError("empty finite inventory cannot publish min/max")
    else:
        if finite_min is None or finite_max is None or float(finite_min) > float(finite_max):
            raise ResultError("finite inventory min/max is invalid")

    if inventory["cardinality_cap"] != _values.CARDINALITY_CAP:
        raise ResultError("CEMS mask value inventory cardinality cap drifted")
    if type(inventory["cardinality_cap_exceeded"]) is not bool:
        raise ResultError("CEMS mask value inventory cardinality flag must be boolean")

    cap_exceeded = inventory["cardinality_cap_exceeded"]
    unique_count = inventory["finite_unique_value_count"]
    value_counts = inventory["finite_value_counts"]
    observation = inventory["encoding_observation"]

    if cap_exceeded:
        if unique_count is not None or value_counts is not None:
            raise ResultError("capped CEMS mask value inventory leaked an exact catalogue")
        if observation != "cardinality_cap_exceeded":
            raise ResultError("capped CEMS mask value inventory observation drifted")
        return inventory

    if type(unique_count) is not int or isinstance(unique_count, bool) or not (
        0 <= unique_count <= _values.CARDINALITY_CAP
    ):
        raise ResultError("CEMS mask finite unique-value count is invalid")
    if type(value_counts) is not list or len(value_counts) != unique_count:
        raise ResultError("CEMS mask finite value catalogue shape drifted")

    catalogue_values: list[float] = []
    catalogue_total = 0
    catalogue_zero = 0
    seen: set[float] = set()
    for item in value_counts:
        if type(item) is not dict or set(item) != {"value", "count"}:
            raise ResultError("CEMS mask finite value-count entry shape drifted")
        value = item["value"]
        if type(value) not in (int, float) or isinstance(value, bool):
            raise ResultError("CEMS mask finite catalogue value is not numeric")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ResultError("CEMS mask finite catalogue contains non-finite value")
        if numeric in seen:
            raise ResultError("CEMS mask finite catalogue contains duplicate value")
        seen.add(numeric)
        catalogue_values.append(numeric)
        item_count = _nonnegative_int(item["count"], "inventory.finite_value_counts.count")
        if item_count < 1:
            raise ResultError("CEMS mask finite value catalogue count must be positive")
        catalogue_total += item_count
        if numeric == 0.0:
            catalogue_zero += item_count

    if catalogue_values != sorted(catalogue_values):
        raise ResultError("CEMS mask finite value catalogue is not sorted")
    if catalogue_total != counts["finite_count"]:
        raise ResultError("CEMS mask finite value catalogue does not reconcile")
    if catalogue_zero != counts["zero_count"]:
        raise ResultError("CEMS mask finite zero catalogue does not reconcile")

    if counts["finite_count"] == 0:
        expected_observation = "no_finite_non_nodata_values"
        if unique_count != 0:
            raise ResultError("empty finite inventory cannot publish unique values")
    elif unique_count == 1:
        expected_observation = "single_finite_value_candidate_support"
    elif unique_count >= 2:
        expected_observation = "multiple_finite_values_mapping_unresolved"
    else:
        raise ResultError("non-empty finite inventory lacks value catalogue")

    if observation != expected_observation:
        raise ResultError("CEMS mask value encoding observation drifted")

    if counts["finite_count"] > 0:
        if float(finite_min) != catalogue_values[0] or float(finite_max) != catalogue_values[-1]:
            raise ResultError("CEMS mask finite min/max does not match exact catalogue")
    return inventory


def _validate_value_result(
    value_result: Any, *, kind: str, filename: str
) -> dict[str, Any]:
    if type(value_result) is not dict or set(value_result) != _VALUE_RESULT_FIELDS:
        raise ResultError("CEMS mask value-profile result fields drifted")

    supplied_digest = value_result["result_sha256"]
    if type(supplied_digest) is not str or not _legacy.DIGEST_RE.fullmatch(
        supplied_digest
    ):
        raise ResultError("CEMS mask value-profile result digest is invalid")
    digest_payload = dict(value_result)
    del digest_payload["result_sha256"]
    if supplied_digest != _sha256_digest(digest_payload):
        raise ResultError("CEMS mask value-profile result digest does not match payload")

    accepted = _metadata.MASK_RECEIPTS[kind]
    exact = {
        "schema_version": _values.SCHEMA_VERSION,
        "dataset_id": CEMS_MASK_VALUE_INVENTORIES_DATASET_ID,
        "release": _metadata.RELEASE,
        "source_issue": _worker.SOURCE_ISSUE,
        "profile_issue": CEMS_MASK_VALUE_INVENTORIES_ISSUE,
        "mask_kind": kind,
        "filename": filename,
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "receipt_identity_verified": True,
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "model_use_authorized": False,
        "publication_authorized": False,
        "external_bytes_persisted": False,
    }
    for field, expected in exact.items():
        if type(value_result[field]) is not type(expected) or value_result[field] != expected:
            raise ResultError(
                f"CEMS mask value-profile {field} drifted from frozen authority"
            )

    grid = value_result["grid"]
    if type(grid) is not dict or set(grid) != _GRID_FIELDS:
        raise ResultError("CEMS mask value-profile grid fields drifted")
    if grid != _EXPECTED_GRID:
        raise ResultError("CEMS mask value-profile grid drifted from accepted #816 evidence")

    _validate_inventory(value_result["inventory"])
    return value_result


def _validate_inventory_receipt(
    receipt: Any, *, kind: str, filename: str
) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _INVENTORY_RECEIPT_FIELDS:
        raise ResultError("CEMS mask value-inventory receipt fields drifted")

    accepted = _metadata.MASK_RECEIPTS[kind]
    url = _metadata.BASE_URL + filename
    exact = {
        "schema_version": _worker.INVENTORY_RECEIPT_SCHEMA_VERSION,
        "dataset_id": CEMS_MASK_VALUE_INVENTORIES_DATASET_ID,
        "source_issue": _worker.SOURCE_ISSUE,
        "profile_issue": CEMS_MASK_VALUE_INVENTORIES_ISSUE,
        "release": _masks.RELEASE,
        "mask_kind": kind,
        "filename": filename,
        "requested_url": url,
        "final_url": url,
        "http_status": 200,
        "receipt_byte_count": accepted["byte_count"],
        "receipt_sha256": accepted["sha256"],
        "external_bytes_persisted": False,
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(
                f"CEMS mask value-inventory receipt {field} drifted from frozen authority"
            )

    _base._utc_second(
        receipt["retrieved_at"],
        f"{_CEMS_MASK_VALUE_INVENTORIES_FIELD}.{kind}.retrieved_at",
    )
    media = receipt["media_type"]
    if type(media) is not str or media not in _masks._base.ALLOWED_MEDIA_TYPES:
        raise ResultError("CEMS mask value-inventory media_type is outside fixed contract")
    declared = receipt["content_length_header"]
    if declared is not None and (
        type(declared) is not int
        or isinstance(declared, bool)
        or declared != accepted["byte_count"]
    ):
        raise ResultError(
            "CEMS mask value-inventory Content-Length does not match accepted receipt"
        )

    _validate_value_result(
        receipt["value_inventory"],
        kind=kind,
        filename=filename,
    )
    return receipt


def validate_cems_mask_value_inventories(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _AGGREGATE_FIELDS:
        raise ResultError("CEMS mask value-inventory aggregate fields drifted")

    exact = {
        "schema_version": _worker.SCHEMA_VERSION,
        "dataset_id": CEMS_MASK_VALUE_INVENTORIES_DATASET_ID,
        "source_issue": _worker.SOURCE_ISSUE,
        "profile_issue": CEMS_MASK_VALUE_INVENTORIES_ISSUE,
        "release": _masks.RELEASE,
        "external_bytes_persisted": False,
        "mask_values_inspected": True,
        "mask_value_semantics_verified": False,
        "per_cell_scientific_correctness_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(
                f"CEMS mask value-inventory aggregate {field} drifted from frozen authority"
            )

    receipts = receipt["mask_value_inventory_receipts"]
    if type(receipts) is not list or len(receipts) != len(_masks.ASSETS):
        raise ResultError("CEMS mask value-inventory receipt count drifted")

    for inventory_receipt, (kind, filename) in zip(
        receipts, _masks.ASSETS, strict=True
    ):
        _validate_inventory_receipt(
            inventory_receipt,
            kind=kind,
            filename=filename,
        )
    return receipt


def _validate_value_inventory_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("CEMS mask value-inventory result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")

    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _legacy.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _legacy.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_MASK_VALUE_INVENTORIES_ACTION:
        raise ResultError("unsupported CEMS mask value-inventory action")

    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _legacy.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError(
            "CEMS mask value-inventory network result requires target_sha == execution_sha"
        )
    if result["source_issue"] != CEMS_MASK_VALUE_INVENTORIES_ISSUE:
        raise ResultError("CEMS mask value-inventory result is outside control issue 823")
    if result["dataset_id"] != CEMS_MASK_VALUE_INVENTORIES_DATASET_ID:
        raise ResultError("CEMS mask value-inventory result is outside frozen dataset")

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
        raise ResultError("unsupported CEMS mask value-inventory result state")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")

    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (
        type(duplicate_id) is not int or isinstance(duplicate_id, bool) or duplicate_id < 1
    ):
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
        raise ResultError(
            "CEMS mask value-inventory network result requires acquisition_receipt phase"
        )

    evidence = result["evidence"]
    if (
        type(evidence) is not dict
        or set(evidence) != _CEMS_MASK_VALUE_INVENTORIES_EVIDENCE_FIELDS
    ):
        raise ResultError("CEMS mask value-inventory evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError(
            "CEMS mask value-inventory acquisition requires complete non-reused ledger state"
        )

    aggregate = evidence[_CEMS_MASK_VALUE_INVENTORIES_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError(
                "successful CEMS mask value-inventory acquisition cannot carry failure_class"
            )
        aggregate = validate_cems_mask_value_inventories(aggregate)
        for item in aggregate["mask_value_inventory_receipts"]:
            retrieved = _base._utc_second(
                item["retrieved_at"],
                f"{_CEMS_MASK_VALUE_INVENTORIES_FIELD}.retrieved_at",
            )
            if retrieved < started or retrieved > finished:
                raise ResultError(
                    "CEMS mask value-inventory retrieved_at must fall within action bounds"
                )
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS mask value-inventory failure class is invalid")
        if aggregate is not None:
            raise ResultError(
                "blocked CEMS mask value-inventory acquisition cannot publish inventories"
            )
    else:
        raise ResultError(
            "duplicate CEMS mask value-inventory result must remain request_validation"
        )
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if (
        type(result) is dict
        and result.get("action") == CEMS_MASK_VALUE_INVENTORIES_ACTION
    ):
        return _validate_value_inventory_result(result)
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
