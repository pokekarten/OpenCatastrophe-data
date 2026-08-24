# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the exact ESRM20 Greece exposure-wrapper profile."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.acquire_efehr_greece_exposure_profile import (
        GreeceExposureAcquisitionError,
        GreeceExposureContentError,
        GreeceExposureContractError,
        _validate_profile_result,
        acquire_and_profile_greece_exposure,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_greece_exposure_profile import (
        GreeceExposureAcquisitionError,
        GreeceExposureContentError,
        GreeceExposureContractError,
        _validate_profile_result,
        acquire_and_profile_greece_exposure,
    )


REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-exposure-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-greece-exposure-profile-result-v1"
ACTION = "esrm20_greece_exposure_wrapper_profile"
CONTROL_ISSUE = 285
SOURCE_ISSUE = 285
RECEIPT_ISSUE = 285
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE = "v1.0"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
CONSUMER_EVENT = "Greece_07-9-1999"
REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Greece.xml"
RECEIPT_COMMENT_ID = 5_388_640_521
RECEIPT_EXECUTION_SHA = "9bf3fee5d80431dfa873ee5ae03e07891e6f154a"
RECEIPT_RETRIEVED_AT = "2026-08-23T21:47:08Z"
EXPECTED_BYTE_COUNT = 697
EXPECTED_SHA256 = "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}


class GreeceExposureProfileActionError(RuntimeError):
    """Fail-closed trusted Greece exposure-profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise GreeceExposureProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise GreeceExposureProfileActionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise GreeceExposureProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise GreeceExposureProfileActionError(
            "invalid Greece exposure-profile request marker"
        )
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile request envelope is not canonical"
        )
    try:
        request = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceExposureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureProfileActionError(
            "invalid Greece exposure-profile request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile request fields drifted"
        )
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", CONTROL_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureProfileActionError(
                f"Greece exposure-profile request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise GreeceExposureProfileActionError("invalid requester identity")
    return request


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "exposure_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "release": RELEASE,
            "commit_sha": COMMIT_SHA,
            "consumer_event": CONSUMER_EVENT,
            "repository_path": REPOSITORY_PATH,
            "receipt_comment_id": RECEIPT_COMMENT_ID,
            "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
            "receipt_retrieved_at": RECEIPT_RETRIEVED_AT,
            "byte_count": EXPECTED_BYTE_COUNT,
            "sha256": EXPECTED_SHA256,
        },
        "referenced_dependency_bytes_receipted": False,
        "referenced_dependency_content_profiled": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile_payload(payload: object) -> dict[str, Any]:
    try:
        return _validate_profile_result(payload)
    except GreeceExposureContractError as exc:
        raise GreeceExposureProfileActionError(
            "Greece exposure-profile payload violates reviewed worker contract"
        ) from exc


def _validate_terminal_result(
    result: object, *, execution_sha: str
) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {"status", "failure_class", "profile"}
    if type(result) is not dict or set(result) != expected_fields:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result fields drifted"
        )
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureProfileActionError(
                f"trusted Greece exposure-profile result drifted at {field}"
            )
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise GreeceExposureProfileActionError(
                "Greece exposure-profile PASS cannot carry failure_class"
            )
        _validate_profile_payload(result.get("profile"))
        return result
    if status == "blocked":
        if (
            result.get("failure_class")
            not in {"acquisition_failure", "profile_failure"}
            or result.get("profile") is not None
        ):
            raise GreeceExposureProfileActionError(
                "blocked Greece exposure-profile result is not safely bounded"
            )
        return result
    raise GreeceExposureProfileActionError(
        "trusted Greece exposure-profile result has non-terminal status"
    )


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    if body.count(RESULT_MARKER) != 1:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result envelope is malformed"
        )
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceExposureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result JSON is malformed"
        ) from exc
    if type(result) is not dict:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result fields drifted"
        )
    observed_execution_sha = result.get("execution_sha")
    if (
        type(observed_execution_sha) is not str
        or not _SHA_RE.fullmatch(observed_execution_sha)
    ):
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure-profile result execution SHA is invalid"
        )
    _validate_terminal_result(result, execution_sha=observed_execution_sha)
    return observed_execution_sha == execution_sha


def _run_greece_exposure_profile(
    *,
    execution_sha: str,
    acquirer: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise GreeceExposureProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquirer()
    except GreeceExposureAcquisitionError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "profile": None,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except GreeceExposureContentError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "profile_failure",
                "profile": None,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)
    payload = _validate_profile_payload(payload)
    result.update({"status": "pass", "failure_class": None, "profile": payload})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_greece_exposure_profile(*, execution_sha: str) -> dict[str, Any]:
    return _run_greece_exposure_profile(
        execution_sha=execution_sha,
        acquirer=acquire_and_profile_greece_exposure,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")
    result = run_greece_exposure_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
