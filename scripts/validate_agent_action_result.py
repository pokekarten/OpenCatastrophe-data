# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed Agent Action result validation with bounded #397 source-model wiring.

All pre-existing actions delegate to the reviewed mapping-aware validator layer,
which in turn owns delegation to the canonical taxonomy-aware validator layer.
This layer handles only the ESHM20 source-model dependency action without
widening any pre-existing closed result contract.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts import validate_agent_action_result_mapping as _legacy
    from scripts import acquire_eshm20_source_model_dependencies as _source_model
    from scripts.validate_agent_action_request import (
        EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ACTION,
        EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import validate_agent_action_result_mapping as _legacy
    import acquire_eshm20_source_model_dependencies as _source_model
    from validate_agent_action_request import (
        EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ACTION,
        EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ISSUE,
    )

# Preserve the historical public validator surface for existing imports/tests.
for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_strict_json = _legacy._strict_json
_utc_second = _legacy._utc_second
_validate_request_evidence = _legacy._validate_request_evidence
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {
    EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ACTION,
}


_SOURCE_MODEL_FIELD = "efehr_eshm20_source_model_dependencies"
_SOURCE_MODEL_EVIDENCE_FIELDS = _legacy.REQUEST_EVIDENCE_FIELDS | {_SOURCE_MODEL_FIELD}
_SOURCE_MODEL_RECEIPT_FIELDS = {
    "schema_version", "source_issue", "control_issue", "dataset_id", "project_id",
    "project_path", "commit_sha", "repository_path", "byte_count", "sha256", "parser",
    "inventory_receipt_comment_id", "root_dependency_result_comment_id",
    "root_dependency_section", "root_dependency_option", "first_order_receipt_request_comment_id",
    "first_order_receipt_run_id", "first_order_receipt_execution_sha", "dependencies",
    "dependency_inventory_authorized", "dependency_receipt_authorized",
    "external_bytes_persisted", "publication_authorized", "model_use_authorized",
}
_SOURCE_MODEL_MAX_ORIGINS = 512


def _source_text(value: Any, field: str) -> str:
    if type(value) is not str or not value or value != value.strip() or len(value) > 512:
        raise ResultError(f"{field} must be bounded already-trimmed text")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ResultError(f"{field} contains control characters")
    return value


def validate_efehr_eshm20_source_model_dependencies(receipt: Any) -> dict[str, Any]:
    prefix = _SOURCE_MODEL_FIELD
    if type(receipt) is not dict or set(receipt) != _SOURCE_MODEL_RECEIPT_FIELDS:
        raise ResultError(f"{prefix} fields drifted")
    exact_values = {
        "schema_version": _source_model._CANONICAL_SCHEMA_VERSION,
        "source_issue": _source_model._CANONICAL_SOURCE_ISSUE,
        "control_issue": _source_model._CANONICAL_CONTROL_ISSUE,
        "dataset_id": _source_model._CANONICAL_DATASET_ID,
        "project_id": _source_model._CANONICAL_PROJECT_ID,
        "project_path": _source_model._CANONICAL_PROJECT_PATH,
        "commit_sha": _source_model._CANONICAL_COMMIT_SHA,
        "repository_path": _source_model._CANONICAL_REPOSITORY_PATH,
        "byte_count": _source_model._CANONICAL_EXPECTED_BYTE_COUNT,
        "sha256": _source_model._CANONICAL_EXPECTED_SHA256,
        "parser": _source_model._CANONICAL_PARSER_ID,
        "inventory_receipt_comment_id": _source_model._CANONICAL_INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": _source_model._CANONICAL_ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": _source_model._CANONICAL_SOURCE_SPEC.parent_section,
        "root_dependency_option": _source_model._CANONICAL_SOURCE_SPEC.parent_option,
        "first_order_receipt_request_comment_id": _source_model._CANONICAL_FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_run_id": _source_model._CANONICAL_FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": _source_model._CANONICAL_FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the hardened source-model contract")
    dependencies = receipt["dependencies"]
    if type(dependencies) is not list or not (1 <= len(dependencies) <= 62):
        raise ResultError(f"{prefix}.dependencies must contain 1..62 derived paths")
    seen: set[str] = set()
    order: list[tuple[str, tuple[tuple[str, str], ...]]] = []
    for index, dependency in enumerate(dependencies):
        label = f"{prefix}.dependencies[{index}]"
        if type(dependency) is not dict or set(dependency) != {"resolved_path", "origins", "is_hdf5_companion"}:
            raise ResultError(f"{label} fields drifted")
        path = _source_text(dependency["resolved_path"], f"{label}.resolved_path")
        if path not in _source_model._CANONICAL_INVENTORY or path in seen:
            raise ResultError(f"{label}.resolved_path is duplicate or outside the frozen inventory")
        seen.add(path)
        if dependency["is_hdf5_companion"] is not False:
            raise ResultError(f"{label}.is_hdf5_companion must remain false")
        origins = dependency["origins"]
        if type(origins) is not list or not (1 <= len(origins) <= _SOURCE_MODEL_MAX_ORIGINS):
            raise ResultError(
                f"{label}.origins must contain 1..{_SOURCE_MODEL_MAX_ORIGINS} canonical origins"
            )
        origin_keys: list[tuple[str, str]] = []
        for origin_index, origin in enumerate(origins):
            origin_label = f"{label}.origins[{origin_index}]"
            if type(origin) is not dict or set(origin) != {"uncertainty_type", "branch_id"}:
                raise ResultError(f"{origin_label} fields drifted")
            uncertainty_type = origin["uncertainty_type"]
            if type(uncertainty_type) is not str or uncertainty_type not in {"sourceModel", "extendModel"}:
                raise ResultError(f"{origin_label}.uncertainty_type widened source semantics")
            branch_id = _source_text(origin["branch_id"], f"{origin_label}.branch_id")
            origin_keys.append((uncertainty_type, branch_id))
        if origin_keys != sorted(origin_keys) or len(origin_keys) != len(set(origin_keys)):
            raise ResultError(f"{label}.origins are not canonical and unique")
        order.append((path, tuple(origin_keys)))
    if order != sorted(order):
        raise ResultError(f"{prefix}.dependencies are not in canonical order")
    return receipt


def _validate_source_model_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("source-model result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not _legacy.DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not _legacy.REPOSITORY_RE.fullmatch(result["repository"]):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ACTION:
        raise ResultError("unsupported source-model action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not _legacy.GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("source-model network result requires target_sha == execution_sha")
    if result["source_issue"] != EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ISSUE:
        raise ResultError("source-model result is outside issue 397")
    if result["dataset_id"] != _source_model._CANONICAL_DATASET_ID:
        raise ResultError("source-model result is outside the frozen ESHM20 dataset")
    try:
        expected_semantic_id = _legacy.semantic_request_id_from_result(result)
    except _legacy.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if result["semantic_request_id"] != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound result fields")
    started = _legacy._utc_second(result["started_at"], "started_at")
    finished = _legacy._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase, status = result["phase"], result["status"]
    if type(phase) is not str or phase not in _legacy.ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    if type(status) is not str or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id, failure_class = result["duplicate_result_comment_id"], result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")
    if phase == "request_validation":
        evidence = _legacy._validate_request_evidence(result["evidence"])
        if status == "pass":
            if duplicate_id is not None or failure_class is not None or evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
                raise ResultError("pass request-validation state is invalid")
        elif status == "duplicate":
            if duplicate_id is None or failure_class != "duplicate_request" or evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not True:
                raise ResultError("duplicate request-validation state is invalid")
        else:
            if duplicate_id is not None or failure_class != "ledger_incomplete" or evidence["ledger_scan_complete"] is not False or evidence["prior_result_reused"] is not False:
                raise ResultError("blocked request-validation state is invalid")
        return result
    if phase != "acquisition_receipt":
        raise ResultError("source-model network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _SOURCE_MODEL_EVIDENCE_FIELDS:
        raise ResultError("source-model evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True or evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False or duplicate_id is not None:
        raise ResultError("source-model acquisition requires validated complete non-reused ledger state")
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful source-model acquisition cannot carry failure_class")
        validate_efehr_eshm20_source_model_dependencies(evidence[_SOURCE_MODEL_FIELD])
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS or evidence[_SOURCE_MODEL_FIELD] is not None:
            raise ResultError("blocked source-model acquisition state is invalid")
    else:
        raise ResultError("duplicate source-model network result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == EFEHR_ESHM20_SOURCE_MODEL_DEPENDENCIES_ACTION:
        return _validate_source_model_result(result)
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
        result = validate_result(_strict_json(os.environ[args.result_env]))
    except ResultError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
