# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the exact ESRM20 Greece exposure wrapper."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import acquire_efehr_greece_exposure_profile as worker
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-exposure-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-greece-exposure-profile-result-v1"
ACTION = "esrm20_greece_exposure_wrapper_profile"
CONTROL_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 24000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "receipt_sha256",
    "requester",
}


class GreeceExposureProfileActionError(RuntimeError):
    """Fail-closed trusted Greece exposure profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise GreeceExposureProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise GreeceExposureProfileActionError(f"non-finite JSON constant: {value}")


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise GreeceExposureProfileActionError("text is not UTF-8 encodable") from exc


def _identity() -> dict[str, Any]:
    return {
        "project_id": worker._CANONICAL_PROJECT_ID,
        "project_path": worker._CANONICAL_PROJECT_PATH,
        "release": worker._CANONICAL_RELEASE,
        "commit_sha": worker._CANONICAL_COMMIT_SHA,
        "consumer_event": worker._CANONICAL_CONSUMER_EVENT,
        "repository_path": worker._CANONICAL_REPOSITORY_PATH,
        "receipt_issue": worker._CANONICAL_RECEIPT_ISSUE,
        "receipt_comment_id": worker._CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_execution_sha": worker._CANONICAL_RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": worker._CANONICAL_RECEIPT_RETRIEVED_AT,
        "byte_count": worker._CANONICAL_BYTE_COUNT,
        "sha256": worker._CANONICAL_SHA256,
    }


def _require_canonical_authority() -> None:
    worker._require_profile_contract()
    identity = _identity()
    expected = {
        "project_id": 269,
        "project_path": "efehr/esrm20",
        "release": "v1.0",
        "commit_sha": "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        "consumer_event": "Greece_07-9-1999",
        "repository_path": "Exposure/OQ_Exposure_Input_Greece.xml",
        "receipt_issue": 285,
        "receipt_comment_id": 5_388_640_521,
        "receipt_execution_sha": "9bf3fee5d80431dfa873ee5ae03e07891e6f154a",
        "receipt_retrieved_at": "2026-08-23T21:47:08Z",
        "byte_count": 697,
        "sha256": "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556",
    }
    if identity != expected:
        raise GreeceExposureProfileActionError("canonical Greece exposure identity drifted")
    if worker._CANONICAL_SOURCE_ISSUE != CONTROL_ISSUE:
        raise GreeceExposureProfileActionError("canonical source issue drifted")
    if worker._CANONICAL_DATASET_ID != "efehr.esrm20.risk-inputs.v1.0":
        raise GreeceExposureProfileActionError("canonical dataset id drifted")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    _require_canonical_authority()
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise GreeceExposureProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceExposureProfileActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise GreeceExposureProfileActionError("invalid Greece exposure request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureProfileActionError("Greece exposure request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except GreeceExposureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureProfileActionError("invalid Greece exposure request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceExposureProfileActionError("Greece exposure request fields drifted")
    exact = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": ACTION,
        "issue": CONTROL_ISSUE,
        "target_sha": execution_sha,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "receipt_sha256": worker._CANONICAL_SHA256,
    }
    for field, expected in exact.items():
        if type(request.get(field)) is not type(expected) or request.get(field) != expected:
            raise GreeceExposureProfileActionError(
                f"Greece exposure request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise GreeceExposureProfileActionError("invalid requester identity")
    return request


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "exposure_identity": _identity(),
        "external_bytes_persisted": False,
        "referenced_dependency_bytes_receipted": False,
        "referenced_dependency_content_profiled": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_evidence(evidence: object) -> dict[str, Any]:
    try:
        validated = worker._validate_profile_result(evidence)
    except worker.GreeceExposureContractError as exc:
        raise GreeceExposureProfileActionError(
            "Greece exposure evidence contract drifted"
        ) from exc
    if validated.get("content_profile", {}).get("source_declarations_profiled") is not True:
        raise GreeceExposureProfileActionError(
            "Greece exposure evidence did not profile source declarations"
        )
    return validated


def _validate_terminal_result(
    result: object, *, execution_sha: str
) -> dict[str, Any]:
    _require_canonical_authority()
    base = _base_result(execution_sha=execution_sha)
    fields = set(base) | {
        "status",
        "failure_class",
        "evidence",
        "provider_file_bytes_read",
        "source_declarations_profiled",
    }
    if type(result) is not dict or set(result) != fields:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure result fields drifted"
        )
    for field, expected in base.items():
        if type(result.get(field)) is not type(expected) or result.get(field) != expected:
            raise GreeceExposureProfileActionError(
                f"trusted Greece exposure result drifted at {field}"
            )

    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    if _utf8_size(RESULT_MARKER + "\n" + encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise GreeceExposureProfileActionError("trusted Greece exposure result exceeds terminal bound")

    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("provider_file_bytes_read") is not True
            or result.get("source_declarations_profiled") is not True
        ):
            raise GreeceExposureProfileActionError("Greece exposure PASS state drifted")
        _validate_evidence(result.get("evidence"))
        return result

    if status == "blocked":
        failure = result.get("failure_class")
        if (
            failure not in {"acquisition_failure", "profile_failure"}
            or result.get("evidence") is not None
            or result.get("source_declarations_profiled") is not False
        ):
            raise GreeceExposureProfileActionError(
                "Greece exposure BLOCKED state drifted"
            )
        if (
            failure == "acquisition_failure"
            and result.get("provider_file_bytes_read") is not None
        ):
            raise GreeceExposureProfileActionError(
                "Greece exposure acquisition failure overclaims byte-read state"
            )
        if (
            failure == "profile_failure"
            and result.get("provider_file_bytes_read") is not True
        ):
            raise GreeceExposureProfileActionError(
                "Greece exposure profile failure lost byte-read state"
            )
        return result

    raise GreeceExposureProfileActionError(
        "trusted Greece exposure result is not terminal"
    )


def _parse_terminal(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if (
        _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES
        or body.count(RESULT_MARKER) != 1
    ):
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure result marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure result envelope is malformed"
        )
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except GreeceExposureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure result JSON is malformed"
        ) from exc
    if type(result) is not dict:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure result is not an object"
        )
    result_sha = result.get("execution_sha")
    if type(result_sha) is not str or _SHA_RE.fullmatch(result_sha) is None:
        raise GreeceExposureProfileActionError(
            "trusted Greece exposure result SHA is invalid"
        )
    _validate_terminal_result(result, execution_sha=result_sha)
    return result_sha == execution_sha


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None
) -> bool:
    kwargs: dict[str, Any] = {
        "issue": CONTROL_ISSUE,
        "max_pages": MAX_LEDGER_PAGES,
    }
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceExposureProfileActionError(
            "Greece exposure result ledger is incomplete"
        ) from exc

    match_seen = False
    for comment in comments:
        if type(comment) is not dict:
            raise GreeceExposureProfileActionError(
                "Greece exposure ledger contains non-object comment"
            )
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login == TRUSTED_RESULT_LOGIN:
            match_seen = (
                _parse_terminal(comment.get("body"), execution_sha=execution_sha)
                or match_seen
            )
    return match_seen


def _run(
    *, execution_sha: str, acquirer: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        evidence = acquirer()
    except worker.GreeceExposureAcquisitionError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "evidence": None,
                "provider_file_bytes_read": None,
                "source_declarations_profiled": False,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except worker.GreeceExposureContentError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "profile_failure",
                "evidence": None,
                "provider_file_bytes_read": True,
                "source_declarations_profiled": False,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)

    evidence = _validate_evidence(evidence)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "evidence": evidence,
            "provider_file_bytes_read": True,
            "source_declarations_profiled": True,
        }
    )
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run(*, execution_sha: str) -> dict[str, Any]:
    return _run(
        execution_sha=execution_sha,
        acquirer=worker.acquire_and_profile_greece_exposure,
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
        body, expected_issue=args.expected_issue, execution_sha=args.execution_sha
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")

    result = run(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
