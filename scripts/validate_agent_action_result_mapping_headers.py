# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed durable validation for exact ESRM20 mapping-header evidence."""

from __future__ import annotations

import hashlib
from typing import Any, Sequence

try:
    from scripts import acquire_efehr_esrm20_mapping_headers as worker
    from scripts import validate_agent_action_result_mapping as legacy
    from scripts.validate_agent_action_request import (
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_HEADERS_ACTION,
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_HEADERS_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import acquire_efehr_esrm20_mapping_headers as worker
    import validate_agent_action_result_mapping as legacy
    from validate_agent_action_request import (
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_HEADERS_ACTION,
        ESRM20_EXPOSURE_VULNERABILITY_MAPPING_HEADERS_ISSUE,
    )

ResultError = legacy.ResultError

RECEIPT_FIELD = "esrm20_exposure_vulnerability_mapping_headers"
EVIDENCE_FIELDS = legacy.REQUEST_EVIDENCE_FIELDS | {RECEIPT_FIELD}
RECEIPT_FIELDS = {
    "schema_version",
    "operation_id",
    "control_issue",
    "source_issue",
    "dataset_id",
    "provider_host",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "receipt_comment_id",
    "receipt_run_id",
    "receipt_execution_sha",
    "header_source_commit",
    "header_path",
    "header_function",
    "header_git_blob_sha1",
    "retrieved_at",
    "disclosure",
    "raw_bytes_returned",
    "external_bytes_persisted",
    "derived_bytes_persisted",
    "publication_authorized",
    "mapping_interpretation_authorized",
    "taxonomy_join_authorized",
    "vulnerability_selection_authorized",
    "model_use_authorized",
}
DISCLOSURE_FIELDS = {
    "schema_version",
    "decision_issue",
    "source_issue",
    "profile_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "receipt_comment_id",
    "receipt_run_id",
    "receipt_execution_sha",
    "byte_count",
    "sha256",
    "column_count",
    "ordered_header_sha256",
    "headers",
    "disclosure_scope",
    "header_strings_returned",
    "cell_values_returned",
    "raw_rows_returned",
    "normalization_applied",
    "mapping_interpretation_authorized",
    "taxonomy_join_authorized",
    "vulnerability_selection_authorized",
    "external_bytes_persisted",
    "derived_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}


def _length_prefixed_sha256(values: Sequence[str]) -> str:
    digest = hashlib.sha256()
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _bounded_header(value: Any, field: str) -> str:
    if type(value) is not str or not (1 <= len(value) <= 512):
        raise ResultError(f"{field} must be bounded non-empty text")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ResultError(f"{field} contains control characters")
    return value


def _validate_disclosure(disclosure: Any) -> dict[str, Any]:
    prefix = f"{RECEIPT_FIELD}.disclosure"
    if type(disclosure) is not dict or set(disclosure) != DISCLOSURE_FIELDS:
        raise ResultError(f"{prefix} fields drifted")

    exact_values = {
        "schema_version": "oc-esrm20-mapping-header-disclosure-v1",
        "decision_issue": worker.CONTROL_ISSUE,
        "source_issue": worker.SOURCE_ISSUE,
        "profile_issue": 404,
        "dataset_id": worker.DATASET_ID,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": worker.REPOSITORY_PATH,
        "receipt_comment_id": worker.RECEIPT_COMMENT_ID,
        "receipt_run_id": worker.RECEIPT_RUN_ID,
        "receipt_execution_sha": worker.RECEIPT_EXECUTION_SHA,
        "byte_count": worker.EXPECTED_BYTE_COUNT,
        "sha256": worker.EXPECTED_SHA256,
        "disclosure_scope": "exact_header_strings_only",
        "header_strings_returned": True,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(disclosure[field]) is not type(expected) or disclosure[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen disclosure contract")

    count = disclosure["column_count"]
    if type(count) is not int or isinstance(count, bool) or count <= 0 or count > 4096:
        raise ResultError(f"{prefix}.column_count must be a positive bounded non-bool integer")
    headers = disclosure["headers"]
    if type(headers) is not list or len(headers) != count:
        raise ResultError(f"{prefix}.headers must match column_count")
    canonical_headers = [
        _bounded_header(value, f"{prefix}.headers[{index}]")
        for index, value in enumerate(headers)
    ]
    if len(set(canonical_headers)) != len(canonical_headers):
        raise ResultError(f"{prefix}.headers must be ordered unique literals")
    fingerprint = disclosure["ordered_header_sha256"]
    if type(fingerprint) is not str or not legacy.DIGEST_RE.fullmatch(fingerprint):
        raise ResultError(f"{prefix}.ordered_header_sha256 must be lowercase SHA-256")
    if _length_prefixed_sha256(canonical_headers) != fingerprint:
        raise ResultError(f"{prefix}.ordered_header_sha256 does not bind the exact ordered headers")
    return disclosure


def validate_esrm20_mapping_headers(receipt: Any) -> dict[str, Any]:
    """Validate one exact, bounded, header-only acquisition receipt."""

    prefix = RECEIPT_FIELD
    if type(receipt) is not dict or set(receipt) != RECEIPT_FIELDS:
        raise ResultError(f"{prefix} fields drifted")
    exact_values = {
        "schema_version": worker.SCHEMA_VERSION,
        "operation_id": worker.OPERATION_ID,
        "control_issue": worker.CONTROL_ISSUE,
        "source_issue": worker.SOURCE_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": worker.REPOSITORY_PATH,
        "receipt_comment_id": worker.RECEIPT_COMMENT_ID,
        "receipt_run_id": worker.RECEIPT_RUN_ID,
        "receipt_execution_sha": worker.RECEIPT_EXECUTION_SHA,
        "header_source_commit": worker.HEADER_SOURCE_COMMIT,
        "header_path": worker.HEADER_PATH,
        "header_function": worker.HEADER_FUNCTION,
        "header_git_blob_sha1": worker.HEADER_GIT_BLOB_SHA1,
        "raw_bytes_returned": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen acquisition contract")
    legacy._utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    _validate_disclosure(receipt["disclosure"])
    return receipt


def validate_mapping_headers_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the closed Agent Action wrapper around mapping-header evidence."""

    if type(result) is not dict or set(result) != legacy.REQUIRED_FIELDS:
        raise ResultError("mapping-header result fields drifted")
    if result["schema_version"] != legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not legacy.DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not legacy.REPOSITORY_RE.fullmatch(result["repository"]):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != ESRM20_EXPOSURE_VULNERABILITY_MAPPING_HEADERS_ACTION:
        raise ResultError("unsupported mapping-header action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive non-bool integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not legacy.GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("mapping-header network result requires target_sha == execution_sha")
    if result["source_issue"] != ESRM20_EXPOSURE_VULNERABILITY_MAPPING_HEADERS_ISSUE:
        raise ResultError("mapping-header result is outside issue 410")
    if result["dataset_id"] != worker.DATASET_ID:
        raise ResultError("mapping-header result is outside the frozen ESRM20 risk-input dataset")
    try:
        expected_semantic_id = legacy.semantic_request_id_from_result(result)
    except legacy.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if result["semantic_request_id"] != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = legacy._utc_second(result["started_at"], "started_at")
    finished = legacy._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase, status = result["phase"], result["status"]
    if type(phase) is not str or phase not in legacy.ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    if type(status) is not str or status not in legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id, failure_class = result["duplicate_result_comment_id"], result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or isinstance(duplicate_id, bool) or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive non-bool integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        evidence = legacy._validate_request_evidence(result["evidence"])
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
        raise ResultError("mapping-header network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != EVIDENCE_FIELDS:
        raise ResultError("mapping-header evidence fields drifted")
    for field in legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True or evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False or duplicate_id is not None:
        raise ResultError("mapping-header acquisition requires validated complete non-reused ledger state")
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful mapping-header acquisition cannot carry failure_class")
        receipt = validate_esrm20_mapping_headers(evidence[RECEIPT_FIELD])
        retrieved = legacy._utc_second(receipt["retrieved_at"], f"{RECEIPT_FIELD}.retrieved_at")
        if retrieved < started or retrieved > finished:
            raise ResultError(f"{RECEIPT_FIELD}.retrieved_at must fall within action start/finish bounds")
    elif status == "blocked":
        if failure_class != legacy.ACQUISITION_FAILURE_CLASS or evidence[RECEIPT_FIELD] is not None:
            raise ResultError("blocked mapping-header acquisition state is invalid")
    else:
        raise ResultError("duplicate mapping-header network result must remain request_validation")
    return result
