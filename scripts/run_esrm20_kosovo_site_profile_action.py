# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the exact ESRM20 Kosovo site structure profile."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.acquire_efehr_kosovo_site_profile import (
        SiteProfileAcquisitionError,
        SiteProfileContentError,
        SiteProfileContractError,
        _validate_profile_result,
        acquire_and_profile_kosovo_site,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_kosovo_site_profile import (
        SiteProfileAcquisitionError,
        SiteProfileContentError,
        SiteProfileContractError,
        _validate_profile_result,
        acquire_and_profile_kosovo_site,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments


REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-site-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-site-profile-result-v1"
ACTION = "esrm20_kosovo_site_model_structure_profile"
CONTROL_ISSUE = 459
SOURCE_ISSUE = 291
SOURCE_SCIENCE_ISSUE = 284
RECEIPT_ISSUE = 342
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
WORKER_OPERATION_ID = "esrm20-kosovo-site-model-v1"
RECEIPT_COMMENT_ID = 5308044390
EXPECTED_BYTE_COUNT = 5_891
EXPECTED_SHA256 = "746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd"
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


class SiteProfileActionError(RuntimeError):
    """Fail-closed trusted site-profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise SiteProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise SiteProfileActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise SiteProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteProfileActionError("invalid site-profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteProfileActionError("site-profile request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteProfileActionError("invalid site-profile request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteProfileActionError("site-profile request fields drifted")
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
            raise SiteProfileActionError(f"site-profile request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise SiteProfileActionError("invalid requester identity")
    return request


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "content_issue": SOURCE_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "site_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
            "worker_operation_id": WORKER_OPERATION_ID,
            "receipt_comment_id": RECEIPT_COMMENT_ID,
            "byte_count": EXPECTED_BYTE_COUNT,
            "sha256": EXPECTED_SHA256,
        },
        "crs_coordinate_semantics_verified": False,
        "site_parameter_units_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile_payload(payload: object) -> dict[str, Any]:
    try:
        return _validate_profile_result(payload)
    except SiteProfileContractError as exc:
        raise SiteProfileActionError("site-profile payload violates reviewed worker contract") from exc


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {"status", "failure_class", "profile"}
    if type(result) is not dict or set(result) != expected_fields:
        raise SiteProfileActionError("trusted site-profile result fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteProfileActionError(f"trusted site-profile result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise SiteProfileActionError("site-profile PASS cannot carry failure_class")
        _validate_profile_payload(result.get("profile"))
        return result
    if status == "blocked":
        if (
            result.get("failure_class") not in {"acquisition_failure", "profile_failure"}
            or result.get("profile") is not None
        ):
            raise SiteProfileActionError("blocked site-profile result is not safely bounded")
        return result
    raise SiteProfileActionError("trusted site-profile result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteProfileActionError("invalid execution SHA")
    if body.count(RESULT_MARKER) != 1:
        raise SiteProfileActionError("trusted site-profile result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteProfileActionError("trusted site-profile result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteProfileActionError("trusted site-profile result JSON is malformed") from exc
    if type(result) is not dict:
        raise SiteProfileActionError("trusted site-profile result fields drifted")
    result_execution_sha = result.get("execution_sha")
    if type(result_execution_sha) is not str or not _SHA_RE.fullmatch(result_execution_sha):
        raise SiteProfileActionError("trusted site-profile result execution SHA is invalid")
    _validate_terminal_result(result, execution_sha=result_execution_sha)
    return result_execution_sha == execution_sha


def has_terminal_site_profile_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fail closed unless the complete bounded Issue #459 ledger is known."""

    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SiteProfileActionError("site-profile result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteProfileActionError("site-profile ledger contains a non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def _run_site_profile(
    *,
    execution_sha: str,
    acquirer: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquirer()
    except SiteProfileAcquisitionError:
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except SiteProfileContentError:
        result.update({"status": "blocked", "failure_class": "profile_failure", "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    payload = _validate_profile_payload(payload)
    result.update({"status": "pass", "failure_class": None, "profile": payload})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_site_profile(*, execution_sha: str) -> dict[str, Any]:
    return _run_site_profile(
        execution_sha=execution_sha,
        acquirer=acquire_and_profile_kosovo_site,
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
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")
    result = run_site_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
