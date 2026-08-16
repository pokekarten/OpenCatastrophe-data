# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed Agent Action result validation with bounded mapping/child extensions.

All pre-existing actions delegate byte-for-byte to the reviewed taxonomy-aware
validator layer. This layer handles the frozen ESRM20 mapping byte receipt and
the fixed ESHM20 source-model child receipt set. Neither action widens scientific,
publication, dependency-closure, or model-use authority.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts import acquire_efehr_esrm20_mapping_receipt as _mapping
    from scripts import acquire_eshm20_source_model_child_receipts as _children
    from scripts import validate_agent_action_result_taxonomy as _legacy
    from scripts.efehr_gitlab_receipt import (
        PROJECTS,
        PROVIDER_HOST,
        SCHEMA_VERSION as EFEHR_RECEIPT_SCHEMA_VERSION,
        raw_file_api_url,
        validate_target,
    )
    from scripts.validate_agent_action_request import (
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ACTION,
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ISSUE,
        EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ACTION,
        EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import acquire_efehr_esrm20_mapping_receipt as _mapping
    import acquire_eshm20_source_model_child_receipts as _children
    import validate_agent_action_result_taxonomy as _legacy
    from efehr_gitlab_receipt import (
        PROJECTS,
        PROVIDER_HOST,
        SCHEMA_VERSION as EFEHR_RECEIPT_SCHEMA_VERSION,
        raw_file_api_url,
        validate_target,
    )
    from validate_agent_action_request import (
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ACTION,
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ISSUE,
        EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ACTION,
        EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_strict_json = _legacy._strict_json
_utc_second = _legacy._utc_second
_validate_request_evidence = _legacy._validate_request_evidence
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {
    ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ACTION,
    EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ACTION,
}

_MAPPING_RECEIPT_FIELD = "esrm20_exposure_vulnerability_mapping_receipt"
_MAPPING_EVIDENCE_FIELDS = _legacy.REQUEST_EVIDENCE_FIELDS | {_MAPPING_RECEIPT_FIELD}
_MAPPING_RECEIPT_FIELDS = {
    "schema_version", "operation_id", "source_issue", "dataset_id", "provider_host",
    "project_id", "project_path", "commit_sha", "repository_path", "requested_url",
    "final_url", "retrieved_at", "byte_count", "sha256", "content_type", "etag",
    "external_bytes_persisted", "publication_authorized",
}

_CHILD_RECEIPT_FIELD = "efehr_eshm20_source_model_child_receipts"
_CHILD_EVIDENCE_FIELDS = _legacy.REQUEST_EVIDENCE_FIELDS | {_CHILD_RECEIPT_FIELD}
_CHILD_SET_FIELDS = {
    "schema_version", "operation_id", "control_issue", "source_issue", "dataset_id",
    "provider_host", "project_id", "project_path", "commit_sha",
    "parent_request_comment_id", "parent_result_comment_id", "parent_run_id",
    "parent_execution_sha", "parent_semantic_request_id", "parent_source_tree_byte_count",
    "parent_source_tree_sha256", "child_count", "child_paths_sha256", "retrieved_at",
    "receipts", "dependency_inventory_authorized", "dependency_receipt_authorized",
    "external_bytes_persisted", "publication_authorized", "model_use_authorized",
}
_CHILD_RECEIPT_FIELDS = {
    "schema_version", "source_issue", "dataset_id", "provider_host", "project_id",
    "project_path", "commit_sha", "repository_path", "requested_url", "final_url",
    "retrieved_at", "byte_count", "sha256", "content_type", "etag",
    "external_bytes_persisted", "publication_authorized", "parent_result_comment_id",
}


def _bounded_nullable_header(value: Any, field: str) -> None:
    if value is None:
        return
    if type(value) is not str or len(value) > 512:
        raise ResultError(f"{field} must be null or bounded text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ResultError(f"{field} contains control characters")


def validate_esrm20_exposure_vulnerability_mapping_receipt(receipt: Any) -> dict[str, Any]:
    prefix = _MAPPING_RECEIPT_FIELD
    if type(receipt) is not dict or set(receipt) != _MAPPING_RECEIPT_FIELDS:
        missing = sorted(_MAPPING_RECEIPT_FIELDS - set(receipt)) if type(receipt) is dict else sorted(_MAPPING_RECEIPT_FIELDS)
        unexpected = sorted(set(receipt) - _MAPPING_RECEIPT_FIELDS) if type(receipt) is dict else []
        raise ResultError(f"{prefix} fields mismatch; missing={missing}, unexpected={unexpected}")

    target = validate_target(
        source_issue=_mapping.SOURCE_ISSUE,
        dataset_id=_mapping.DATASET_ID,
        project_id=_mapping.PROJECT_ID,
        commit_sha=_mapping.COMMIT_SHA,
        repository_path=_mapping.REPOSITORY_PATH,
    )
    expected_url = raw_file_api_url(target)
    exact_values = {
        "schema_version": _mapping.SCHEMA_VERSION,
        "operation_id": _mapping.OPERATION_ID,
        "source_issue": _mapping.SOURCE_ISSUE,
        "dataset_id": _mapping.DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": _mapping.PROJECT_ID,
        "project_path": PROJECTS[_mapping.PROJECT_ID]["project_path"],
        "commit_sha": _mapping.COMMIT_SHA,
        "repository_path": _mapping.REPOSITORY_PATH,
        "requested_url": expected_url,
        "final_url": expected_url,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen mapping byte-receipt contract")

    _legacy._utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    byte_count = receipt["byte_count"]
    if type(byte_count) is not int or not (1 <= byte_count <= _mapping.MAX_FILE_BYTES):
        raise ResultError(f"{prefix}.byte_count is outside bounded policy")
    sha256 = receipt["sha256"]
    if type(sha256) is not str or not _legacy.DIGEST_RE.fullmatch(sha256):
        raise ResultError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")
    _bounded_nullable_header(receipt["content_type"], f"{prefix}.content_type")
    _bounded_nullable_header(receipt["etag"], f"{prefix}.etag")
    return receipt


def validate_efehr_eshm20_source_model_child_receipts(receipt: Any) -> dict[str, Any]:
    prefix = _CHILD_RECEIPT_FIELD
    if type(receipt) is not dict or set(receipt) != _CHILD_SET_FIELDS:
        missing = sorted(_CHILD_SET_FIELDS - set(receipt)) if type(receipt) is dict else sorted(_CHILD_SET_FIELDS)
        unexpected = sorted(set(receipt) - _CHILD_SET_FIELDS) if type(receipt) is dict else []
        raise ResultError(f"{prefix} fields mismatch; missing={missing}, unexpected={unexpected}")

    exact_values = {
        "schema_version": _children.SCHEMA_VERSION,
        "operation_id": _children.OPERATION_ID,
        "control_issue": _children.CONTROL_ISSUE,
        "source_issue": _children.SOURCE_ISSUE,
        "dataset_id": _children.DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": _children.PROJECT_ID,
        "project_path": _children.PROJECT_PATH,
        "commit_sha": _children.COMMIT_SHA,
        "parent_request_comment_id": _children.PARENT_REQUEST_COMMENT_ID,
        "parent_result_comment_id": _children.PARENT_RESULT_COMMENT_ID,
        "parent_run_id": _children.PARENT_RUN_ID,
        "parent_execution_sha": _children.PARENT_EXECUTION_SHA,
        "parent_semantic_request_id": _children.PARENT_SEMANTIC_REQUEST_ID,
        "parent_source_tree_byte_count": _children.PARENT_SOURCE_TREE_BYTE_COUNT,
        "parent_source_tree_sha256": _children.PARENT_SOURCE_TREE_SHA256,
        "child_count": _children.EXPECTED_CHILD_COUNT,
        "child_paths_sha256": _children.EXPECTED_PATHS_SHA256,
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the fixed 51-child contract")

    final_retrieved = _legacy._utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    receipts = receipt["receipts"]
    if type(receipts) is not list or len(receipts) != _children.EXPECTED_CHILD_COUNT:
        raise ResultError(f"{prefix}.receipts must contain exactly {_children.EXPECTED_CHILD_COUNT} items")

    expected_paths = tuple(spec.repository_path for spec in _children.CHILDREN)
    observed_paths: list[str] = []
    last_retrieved = None
    for index, item in enumerate(receipts):
        label = f"{prefix}.receipts[{index}]"
        if type(item) is not dict or set(item) != _CHILD_RECEIPT_FIELDS:
            raise ResultError(f"{label} fields drifted")
        expected_path = expected_paths[index]
        target = validate_target(
            source_issue=_children.SOURCE_ISSUE,
            dataset_id=_children.DATASET_ID,
            project_id=_children.PROJECT_ID,
            commit_sha=_children.COMMIT_SHA,
            repository_path=expected_path,
        )
        expected_url = raw_file_api_url(target)
        child_exact = {
            "schema_version": EFEHR_RECEIPT_SCHEMA_VERSION,
            "source_issue": _children.SOURCE_ISSUE,
            "dataset_id": _children.DATASET_ID,
            "provider_host": PROVIDER_HOST,
            "project_id": _children.PROJECT_ID,
            "project_path": _children.PROJECT_PATH,
            "commit_sha": _children.COMMIT_SHA,
            "repository_path": expected_path,
            "requested_url": expected_url,
            "final_url": expected_url,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "parent_result_comment_id": _children.PARENT_RESULT_COMMENT_ID,
        }
        for field, expected in child_exact.items():
            if type(item[field]) is not type(expected) or item[field] != expected:
                raise ResultError(f"{label}.{field} does not match the fixed child receipt contract")
        observed_paths.append(item["repository_path"])
        byte_count = item["byte_count"]
        if type(byte_count) is not int or not (1 <= byte_count <= _children.MAX_ARTIFACT_BYTES):
            raise ResultError(f"{label}.byte_count is outside bounded policy")
        sha256 = item["sha256"]
        if type(sha256) is not str or not _legacy.DIGEST_RE.fullmatch(sha256):
            raise ResultError(f"{label}.sha256 must be a lowercase SHA-256 digest")
        _bounded_nullable_header(item["content_type"], f"{label}.content_type")
        _bounded_nullable_header(item["etag"], f"{label}.etag")
        last_retrieved = _legacy._utc_second(item["retrieved_at"], f"{label}.retrieved_at")

    if tuple(observed_paths) != expected_paths or len(set(observed_paths)) != _children.EXPECTED_CHILD_COUNT:
        raise ResultError(f"{prefix}.receipts paths are not the canonical unique 51-child order")
    if last_retrieved is None or final_retrieved != last_retrieved:
        raise ResultError(f"{prefix}.retrieved_at must equal the final child receipt timestamp")
    return receipt


def _validate_mapping_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict:
        raise ResultError("result must be a JSON object")
    keys = set(result)
    if keys != _legacy.REQUIRED_FIELDS:
        raise ResultError(
            f"result fields mismatch; missing={sorted(_legacy.REQUIRED_FIELDS - keys)}, "
            f"unexpected={sorted(keys - _legacy.REQUIRED_FIELDS)}"
        )
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not _legacy.DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not _legacy.REPOSITORY_RE.fullmatch(result["repository"]):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ACTION:
        raise ResultError("unsupported ESRM20 mapping receipt action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not _legacy.GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    dataset_id = result["dataset_id"]
    if type(dataset_id) is not str or not (1 <= len(dataset_id) <= 160) or not _legacy.SAFE_ID_RE.fullmatch(dataset_id):
        raise ResultError("dataset_id is not a safe bounded identifier")
    try:
        expected_semantic_id = _legacy.semantic_request_id_from_result(result)
    except _legacy.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if result["semantic_request_id"] != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound repository/action/dataset/target/execution fields")

    started = _legacy._utc_second(result["started_at"], "started_at")
    finished = _legacy._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase = result["phase"]
    if type(phase) is not str or phase not in _legacy.ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    status = result["status"]
    if type(status) is not str or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if type(result["external_bytes_persisted"]) is not bool or result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false in result v1")
    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or a positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if result["source_issue"] != ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ISSUE:
        raise ResultError("mapping receipt result is outside frozen control issue 340")
    if result["dataset_id"] != _mapping.DATASET_ID:
        raise ResultError("mapping receipt result is outside the frozen ESRM20 risk-input dataset")

    if phase == "request_validation":
        evidence = _legacy._validate_request_evidence(result["evidence"])
        if status == "pass":
            if duplicate_id is not None or failure_class is not None:
                raise ResultError("pass result cannot carry duplicate/failure state")
            if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
                raise ResultError("pass result requires complete ledger scan and no prior reuse")
        elif status == "duplicate":
            if duplicate_id is None or failure_class != "duplicate_request":
                raise ResultError("duplicate result requires prior result comment identity")
            if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not True:
                raise ResultError("duplicate result requires complete ledger scan and prior reuse")
        else:
            if duplicate_id is not None or failure_class != "ledger_incomplete":
                raise ResultError("blocked request-validation result must identify ledger_incomplete")
            if evidence["ledger_scan_complete"] is not False or evidence["prior_result_reused"] is not False:
                raise ResultError("blocked request-validation result requires incomplete ledger and no prior reuse")
        return result

    if phase != "acquisition_receipt":
        raise ResultError("mapping network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _MAPPING_EVIDENCE_FIELDS:
        raise ResultError("evidence must be a closed ESRM20 mapping receipt evidence object")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True:
        raise ResultError("result v1 requires request_validated=true")
    if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
        raise ResultError("acquisition_receipt phase requires complete ledger scan and no prior reuse")
    if duplicate_id is not None:
        raise ResultError("acquisition_receipt phase cannot carry duplicate_result_comment_id")

    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful acquisition_receipt cannot carry failure_class")
        receipt = validate_esrm20_exposure_vulnerability_mapping_receipt(evidence[_MAPPING_RECEIPT_FIELD])
        retrieved = _legacy._utc_second(receipt["retrieved_at"], f"{_MAPPING_RECEIPT_FIELD}.retrieved_at")
        if retrieved < started or retrieved > finished:
            raise ResultError(f"{_MAPPING_RECEIPT_FIELD}.retrieved_at must fall within action start/finish bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked acquisition_receipt must identify acquisition_failed")
        if evidence[_MAPPING_RECEIPT_FIELD] is not None:
            raise ResultError("blocked acquisition_receipt cannot carry a receipt")
    else:
        raise ResultError("duplicate network acquisition must remain in request_validation phase")
    return result


def _validate_child_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("source-model child result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not _legacy.DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not _legacy.REPOSITORY_RE.fullmatch(result["repository"]):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ACTION:
        raise ResultError("unsupported source-model child receipt action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not _legacy.GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("source-model child network result requires target_sha == execution_sha")
    if result["source_issue"] != EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ISSUE:
        raise ResultError("source-model child result is outside frozen control issue 414")
    if result["dataset_id"] != _children.DATASET_ID:
        raise ResultError("source-model child result is outside the frozen ESHM20 dataset")
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
        raise ResultError("source-model child network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _CHILD_EVIDENCE_FIELDS:
        raise ResultError("source-model child evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True or evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False or duplicate_id is not None:
        raise ResultError("source-model child acquisition requires validated complete non-reused ledger state")
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful source-model child acquisition cannot carry failure_class")
        receipt = validate_efehr_eshm20_source_model_child_receipts(evidence[_CHILD_RECEIPT_FIELD])
        retrieved = _legacy._utc_second(receipt["retrieved_at"], f"{_CHILD_RECEIPT_FIELD}.retrieved_at")
        if retrieved < started or retrieved > finished:
            raise ResultError(f"{_CHILD_RECEIPT_FIELD}.retrieved_at must fall within action start/finish bounds")
        for index, item in enumerate(receipt["receipts"]):
            child_retrieved = _legacy._utc_second(item["retrieved_at"], f"{_CHILD_RECEIPT_FIELD}.receipts[{index}].retrieved_at")
            if child_retrieved < started or child_retrieved > finished:
                raise ResultError("child receipt timestamp must fall within action start/finish bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS or evidence[_CHILD_RECEIPT_FIELD] is not None:
            raise ResultError("blocked source-model child acquisition state is invalid")
    else:
        raise ResultError("duplicate source-model child network result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == ESRM20_EXPOSURE_VULNERABILITY_MAPPING_RECEIPT_ACTION:
        return _validate_mapping_result(result)
    if type(result) is dict and result.get("action") == EFEHR_ESHM20_SOURCE_MODEL_CHILD_RECEIPTS_ACTION:
        return _validate_child_result(result)
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
