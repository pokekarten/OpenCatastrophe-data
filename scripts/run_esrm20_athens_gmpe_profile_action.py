# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the exact Athens ESRM20 v1.0 GMPE tree."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts.acquire_efehr_esrm20_athens_gmpe_profile import (
    AthensGmpeProfileAcquisitionError,
    AthensGmpeProfileContentError,
    AthensGmpeProfileContractError,
    COMMIT_SHA,
    DATASET_ID,
    EVENT_ID,
    EXPECTED_BYTE_COUNT,
    EXPECTED_SHA256,
    GIT_BLOB_SHA1,
    PROJECT_ID,
    PROJECT_PATH,
    RECEIPT_COMMENT_ID,
    RECEIPT_EXECUTION_SHA,
    RECEIPT_ISSUE,
    RECEIPT_RETRIEVED_AT,
    RELEASE_TAG,
    REPOSITORY_PATH,
    SOURCE_ISSUE,
    _validate_profile_payload,
    acquire_and_profile_athens_gmpe,
)
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-result-v1"
ACTION = "esrm20_athens_gmpe_logic_tree_structure_profile"
CONTROL_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}


class AthensGmpeProfileActionError(RuntimeError):
    """Fail-closed trusted Athens GMPE profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise AthensGmpeProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise AthensGmpeProfileActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise AthensGmpeProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise AthensGmpeProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise AthensGmpeProfileActionError("invalid Athens GMPE request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileActionError("Athens GMPE request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except AthensGmpeProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensGmpeProfileActionError("invalid Athens GMPE request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise AthensGmpeProfileActionError("Athens GMPE request fields drifted")
    exact = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": ACTION,
        "issue": CONTROL_ISSUE,
        "target_sha": execution_sha,
        "dataset_id": DATASET_ID,
    }
    for field, expected in exact.items():
        if type(request.get(field)) is not type(expected) or request.get(field) != expected:
            raise AthensGmpeProfileActionError(f"Athens GMPE request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or not _SAFE_REQUESTER_RE.fullmatch(requester):
        raise AthensGmpeProfileActionError("invalid requester identity")
    return request


def _identity() -> dict[str, Any]:
    return {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "event_id": EVENT_ID,
        "repository_path": REPOSITORY_PATH,
        "git_blob_sha1": GIT_BLOB_SHA1,
        "receipt_issue": RECEIPT_ISSUE,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": RECEIPT_RETRIEVED_AT,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "content_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "gmpe_identity": _identity(),
        "external_bytes_persisted": False,
        "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False,
        "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_evidence(evidence: object) -> dict[str, Any]:
    fields = {
        "schema_version", "source_issue", "receipt_issue", "dataset_id", "project_id",
        "project_path", "release_tag", "commit_sha", "event_id", "repository_path",
        "git_blob_sha1", "receipt_comment_id", "receipt_execution_sha", "receipt_retrieved_at",
        "byte_count", "sha256", "profile", "provider_file_bytes_read",
        "external_bytes_persisted", "publication_authorized", "model_use_authorized",
    }
    if type(evidence) is not dict or set(evidence) != fields:
        raise AthensGmpeProfileActionError("Athens GMPE evidence fields drifted")
    exact = {
        "schema_version": "oc-esrm20-athens-gmpe-profile-evidence-v1",
        "source_issue": SOURCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        **_identity(),
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    exact.pop("receipt_issue", None)
    exact.pop("receipt_comment_id", None)
    exact.pop("receipt_execution_sha", None)
    exact.pop("receipt_retrieved_at", None)
    for field, expected in exact.items():
        if field == "profile":
            continue
        if type(evidence.get(field)) is not type(expected) or evidence.get(field) != expected:
            raise AthensGmpeProfileActionError(f"Athens GMPE evidence drifted at {field}")
    if evidence.get("receipt_issue") != RECEIPT_ISSUE:
        raise AthensGmpeProfileActionError("Athens GMPE receipt issue drifted")
    if evidence.get("receipt_comment_id") != RECEIPT_COMMENT_ID:
        raise AthensGmpeProfileActionError("Athens GMPE receipt comment drifted")
    if evidence.get("receipt_execution_sha") != RECEIPT_EXECUTION_SHA:
        raise AthensGmpeProfileActionError("Athens GMPE receipt execution drifted")
    if evidence.get("receipt_retrieved_at") != RECEIPT_RETRIEVED_AT:
        raise AthensGmpeProfileActionError("Athens GMPE receipt retrieval drifted")
    try:
        _validate_profile_payload(evidence.get("profile"))
    except AthensGmpeProfileContractError as exc:
        raise AthensGmpeProfileActionError("Athens GMPE profile payload drifted") from exc
    return evidence


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    fields = set(base) | {"status", "failure_class", "evidence", "provider_file_bytes_read"}
    if type(result) is not dict or set(result) != fields:
        raise AthensGmpeProfileActionError("trusted Athens GMPE result fields drifted")
    for field, expected in base.items():
        if type(result.get(field)) is not type(expected) or result.get(field) != expected:
            raise AthensGmpeProfileActionError(f"trusted Athens GMPE result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None or result.get("provider_file_bytes_read") is not True:
            raise AthensGmpeProfileActionError("Athens GMPE PASS state drifted")
        _validate_evidence(result.get("evidence"))
        return result
    if status == "blocked":
        failure = result.get("failure_class")
        if failure not in {"acquisition_failure", "profile_failure"} or result.get("evidence") is not None:
            raise AthensGmpeProfileActionError("Athens GMPE BLOCKED state drifted")
        if failure == "acquisition_failure" and result.get("provider_file_bytes_read") is not None:
            raise AthensGmpeProfileActionError("Athens GMPE acquisition failure overclaims byte-read state")
        if failure == "profile_failure" and result.get("provider_file_bytes_read") is not True:
            raise AthensGmpeProfileActionError("Athens GMPE profile failure lost byte-read state")
        return result
    raise AthensGmpeProfileActionError("trusted Athens GMPE result is not terminal")


def _parse_terminal(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise AthensGmpeProfileActionError("trusted Athens GMPE result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileActionError("trusted Athens GMPE result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except AthensGmpeProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensGmpeProfileActionError("trusted Athens GMPE result JSON is malformed") from exc
    if type(result) is not dict:
        raise AthensGmpeProfileActionError("trusted Athens GMPE result is not an object")
    result_sha = result.get("execution_sha")
    if type(result_sha) is not str or not _SHA_RE.fullmatch(result_sha):
        raise AthensGmpeProfileActionError("trusted Athens GMPE result SHA is invalid")
    _validate_terminal_result(result, execution_sha=result_sha)
    return result_sha == execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str, opener: Any | None = None) -> bool:
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": 20}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise AthensGmpeProfileActionError("Athens GMPE result ledger is incomplete") from exc
    match_seen = False
    for comment in comments:
        if type(comment) is not dict:
            raise AthensGmpeProfileActionError("Athens GMPE ledger contains non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login == TRUSTED_RESULT_LOGIN:
            match_seen = _parse_terminal(comment.get("body"), execution_sha=execution_sha) or match_seen
    return match_seen


def _run(*, execution_sha: str, acquirer: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        evidence = acquirer()
    except AthensGmpeProfileAcquisitionError:
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "evidence": None, "provider_file_bytes_read": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except AthensGmpeProfileContentError:
        result.update({"status": "blocked", "failure_class": "profile_failure", "evidence": None, "provider_file_bytes_read": True})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    evidence = _validate_evidence(evidence)
    result.update({"status": "pass", "failure_class": None, "evidence": evidence, "provider_file_bytes_read": True})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run(*, execution_sha: str) -> dict[str, Any]:
    return _run(execution_sha=execution_sha, acquirer=acquire_and_profile_athens_gmpe)


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
    result = run(execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
