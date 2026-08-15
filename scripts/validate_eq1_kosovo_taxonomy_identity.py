# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed bridge validation for the Kosovo taxonomy identity handoff.

The bridge accepts only a *whole* canonically validated Agent Action result and
then reduces its already-validated identity receipt to the path-free metadata
needed by later EQ1 compatibility work.  A naked #368 worker-shaped receipt is
never sufficient authority: its frozen values are intentionally public and can
be reconstructed without a trusted-main execution.

This module does not inspect GitHub comment authorship or fetch the trusted
result ledger.  Canonical result validation therefore proves contract/identity
consistency only; callers must separately establish that the durable result was
loaded from the trusted repository ledger before treating the returned
projection as execution provenance.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from scripts import acquire_efehr_kosovo_taxonomy as worker
from scripts import extract_efehr_kosovo_taxonomy as taxonomy
from scripts import profile_efehr_kosovo_exposure as exposure
from scripts import validate_agent_action_result as action_result


_ACTION = "efehr_kosovo_taxonomy_identity"
_ACTION_ISSUE = 363
_REPOSITORY = "pokekarten/OpenCatastrophe-data"
_RECEIPT_FIELD = "efehr_kosovo_taxonomy_identity"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_EXPECTED_RECEIPT_FIELDS = {
    "schema_version",
    "operation_id",
    "control_issue",
    "worker_identity",
    "retrieved_at",
    "source_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "receipt_comment_id",
    "receipt_execution_sha",
    "source_byte_count",
    "source_sha256",
    "taxonomy_field",
    "taxonomy_count",
    "taxonomy_artifact_representation",
    "taxonomy_artifact_byte_count",
    "taxonomy_artifact_sha256",
    "taxonomy_values_returned",
    "normalization_applied",
    "raw_rows_returned",
    "external_bytes_persisted",
    "derived_artifact_persisted",
    "publication_authorized",
}

_EXPECTED_EVIDENCE_FIELDS = {
    "request_validated",
    "ledger_scan_complete",
    "prior_result_reused",
    _RECEIPT_FIELD,
}

_FALSE_CEILINGS = (
    "taxonomy_values_returned",
    "normalization_applied",
    "raw_rows_returned",
    "external_bytes_persisted",
    "derived_artifact_persisted",
    "publication_authorized",
)


class Eq1TaxonomyIdentityError(ValueError):
    """Raised when the public taxonomy identity handoff is unsafe or ambiguous."""


def _require_exact(value: Any, expected: Any, field: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise Eq1TaxonomyIdentityError(f"{field} does not match the frozen public authority")


def _require_sha256(value: Any, field: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise Eq1TaxonomyIdentityError(f"{field} must be a lowercase SHA-256")
    return value


def _require_utc_second(value: Any) -> str:
    if type(value) is not str or _UTC_RE.fullmatch(value) is None:
        raise Eq1TaxonomyIdentityError("retrieved_at must be canonical second-precision UTC")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise Eq1TaxonomyIdentityError("retrieved_at is not a valid UTC timestamp") from exc
    return value


def _validate_identity_receipt(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise Eq1TaxonomyIdentityError("taxonomy identity receipt must be an object")
    if set(receipt) != _EXPECTED_RECEIPT_FIELDS:
        raise Eq1TaxonomyIdentityError("taxonomy identity receipt fields drifted")

    exact = {
        "schema_version": worker.SCHEMA_VERSION,
        "operation_id": worker.OPERATION_ID,
        "control_issue": worker.CONTROL_ISSUE,
        "worker_identity": worker.WORKER_IDENTITY,
        "source_issue": exposure.SOURCE_ISSUE,
        "dataset_id": exposure.DATASET_ID,
        "project_id": exposure.PROJECT_ID,
        "project_path": exposure.PROJECT_PATH,
        "commit_sha": exposure.COMMIT_SHA,
        "repository_path": exposure.REPOSITORY_PATH,
        "receipt_comment_id": exposure.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": exposure.RECEIPT_EXECUTION_SHA,
        "source_byte_count": exposure.EXPECTED_BYTE_COUNT,
        "source_sha256": exposure.EXPECTED_SHA256,
        "taxonomy_field": taxonomy.TAXONOMY_FIELD,
        "taxonomy_count": taxonomy.EXPECTED_DISTINCT_COUNT,
        "taxonomy_artifact_representation": worker.ARTIFACT_REPRESENTATION,
        "taxonomy_artifact_sha256": taxonomy.EXPECTED_VALUE_SET_SHA256,
    }
    for field, expected in exact.items():
        _require_exact(receipt[field], expected, field)

    _require_utc_second(receipt["retrieved_at"])
    _require_sha256(receipt["source_sha256"], "source_sha256")
    _require_sha256(receipt["taxonomy_artifact_sha256"], "taxonomy_artifact_sha256")

    artifact_byte_count = receipt["taxonomy_artifact_byte_count"]
    minimum = taxonomy.EXPECTED_DISTINCT_COUNT * 9
    if (
        type(artifact_byte_count) is not int
        or artifact_byte_count < minimum
        or artifact_byte_count > exposure.EXPECTED_BYTE_COUNT
    ):
        raise Eq1TaxonomyIdentityError(
            "taxonomy_artifact_byte_count is outside the bounded canonical range"
        )

    for field in _FALSE_CEILINGS:
        if receipt[field] is not False:
            raise Eq1TaxonomyIdentityError(f"{field} widened the public authority ceiling")

    return receipt


def validate_eq1_kosovo_taxonomy_identity(payload: Any) -> dict[str, object]:
    """Validate a durable #363 result before reducing its identity metadata.

    The canonical Agent Action validator is intentionally invoked first.  This
    function then independently rebinds the exact EQ1 handoff envelope and the
    #368 receipt before returning a reduced projection.  The projection is not a
    model-input admission, mapping result, vulnerability selection, or proof of
    trusted GitHub-comment authorship.
    """

    try:
        validated = action_result.validate_result(payload)
    except action_result.ResultError as exc:
        raise Eq1TaxonomyIdentityError(
            "durable Agent Action result failed canonical validation"
        ) from exc

    if type(validated) is not dict:
        raise Eq1TaxonomyIdentityError("canonical Agent Action result must be an object")

    top_level_exact = {
        "schema_version": "oc-action-result-v1",
        "repository": _REPOSITORY,
        "action": _ACTION,
        "source_issue": _ACTION_ISSUE,
        "dataset_id": exposure.DATASET_ID,
        "phase": "acquisition_receipt",
        "status": "pass",
        "external_bytes_persisted": False,
        "duplicate_result_comment_id": None,
        "failure_class": None,
    }
    for field, expected in top_level_exact.items():
        if field not in validated:
            raise Eq1TaxonomyIdentityError(f"durable result is missing {field}")
        _require_exact(validated[field], expected, f"result.{field}")

    target_sha = validated.get("target_sha")
    execution_sha = validated.get("execution_sha")
    if type(target_sha) is not str or type(execution_sha) is not str or target_sha != execution_sha:
        raise Eq1TaxonomyIdentityError(
            "result.target_sha must equal result.execution_sha for trusted-main execution"
        )

    evidence = validated.get("evidence")
    if type(evidence) is not dict or set(evidence) != _EXPECTED_EVIDENCE_FIELDS:
        raise Eq1TaxonomyIdentityError("durable result evidence fields drifted")
    for field, expected in (
        ("request_validated", True),
        ("ledger_scan_complete", True),
        ("prior_result_reused", False),
    ):
        _require_exact(evidence[field], expected, f"result.evidence.{field}")

    receipt = _validate_identity_receipt(evidence[_RECEIPT_FIELD])

    semantic_request_id = validated.get("semantic_request_id")
    _require_sha256(semantic_request_id, "result.semantic_request_id")
    source_comment_id = validated.get("source_comment_id")
    run_id = validated.get("run_id")
    for field, value in (("source_comment_id", source_comment_id), ("run_id", run_id)):
        if type(value) is not int or value < 1:
            raise Eq1TaxonomyIdentityError(f"result.{field} must be a positive integer")

    return {
        "schema_version": "eq1-kosovo-taxonomy-identity-bridge-v1",
        "source_action": _ACTION,
        "source_issue": _ACTION_ISSUE,
        "source_semantic_request_id": semantic_request_id,
        "source_comment_id": source_comment_id,
        "source_execution_sha": execution_sha,
        "source_run_id": run_id,
        "dataset_id": receipt["dataset_id"],
        "source_commit_sha": receipt["commit_sha"],
        "source_sha256": receipt["source_sha256"],
        "taxonomy_field": receipt["taxonomy_field"],
        "taxonomy_count": receipt["taxonomy_count"],
        "taxonomy_artifact_representation": receipt["taxonomy_artifact_representation"],
        "taxonomy_artifact_byte_count": receipt["taxonomy_artifact_byte_count"],
        "taxonomy_artifact_sha256": receipt["taxonomy_artifact_sha256"],
        "source_receipt_comment_id": receipt["receipt_comment_id"],
        "source_receipt_execution_sha": receipt["receipt_execution_sha"],
        "ledger_authorship_verification": "external_required",
    }
