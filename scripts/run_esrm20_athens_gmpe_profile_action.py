# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main action for the exact Athens ESRM20 v1.0 GMPE logic tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Any

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _declared_length,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
)
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
from scripts import profile_esrm20_scenario_v10_greece_gmpe_logic_tree as profiler

REQUEST_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-result-v1"
ACTION = "esrm20_athens_gmpe_logic_tree_structure_profile"
CONTROL_ISSUE = 669
SOURCE_ISSUE = 285
CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE = "v1.0"
COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
EVENT_ID = "Greece_07-9-1999"
REPOSITORY_PATH = "ruptures/ground-motion-models/gmpe_logic_tree_5br_shallow_default.xml"
EXPECTED_BYTE_COUNT = 6_490
EXPECTED_SHA256 = "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_FILE_BYTES = 64 * 1024

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_PROFILER = profiler.profile_fixed_greece_gmpe_logic_tree


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
    if expected_issue != CONTROL_ISSUE:
        raise AthensGmpeProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise AthensGmpeProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise AthensGmpeProfileActionError("invalid request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileActionError("request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except AthensGmpeProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensGmpeProfileActionError("invalid request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise AthensGmpeProfileActionError("request fields drifted")
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
            raise AthensGmpeProfileActionError(f"request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or not _SAFE_REQUESTER_RE.fullmatch(requester):
        raise AthensGmpeProfileActionError("invalid requester identity")
    return request


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "content_issue": SOURCE_ISSUE,
        "consumer_issue": CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "artifact_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "release": RELEASE,
            "commit_sha": COMMIT_SHA,
            "event_id": EVENT_ID,
            "repository_path": REPOSITORY_PATH,
            "byte_count": EXPECTED_BYTE_COUNT,
            "sha256": EXPECTED_SHA256,
        },
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False,
        "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _raw_file_url() -> str:
    path = urllib.parse.quote(REPOSITORY_PATH, safe="")
    ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/{path}/raw?ref={ref}"


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED or time.monotonic is not _CANONICAL_MONOTONIC:
        raise AthensGmpeProfileActionError("production transport identity drifted")
    if profiler.profile_fixed_greece_gmpe_logic_tree is not _CANONICAL_PROFILER:
        raise AthensGmpeProfileActionError("merged profiler identity drifted")
    if profiler.EXPECTED_BYTE_COUNT != EXPECTED_BYTE_COUNT or profiler.EXPECTED_SHA256 != EXPECTED_SHA256:
        raise AthensGmpeProfileActionError("merged profiler byte authority drifted")


def _acquire_and_profile() -> dict[str, object]:
    _require_production_identity()
    deadline = time.monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        response = _open_fixed(_raw_file_url(), timeout=_remaining(deadline))
        _validate_exact_response(response)
        declared = _declared_length(response)
        if declared is not None and declared != EXPECTED_BYTE_COUNT:
            raise AthensGmpeProfileActionError("declared byte count drifted")
        raw = _read_bounded(response, max_bytes=MAX_FILE_BYTES, deadline=deadline)
    except (EfehrAcquisitionError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AthensGmpeProfileActionError("acquisition_failure") from exc
    if len(raw) != EXPECTED_BYTE_COUNT or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise AthensGmpeProfileActionError("byte_identity_mismatch")
    try:
        return profiler.profile_fixed_greece_gmpe_logic_tree(raw)
    except profiler.GmpeLogicTreeProfileError as exc:
        raise AthensGmpeProfileActionError("profile_failure") from exc


def _validate_profile(profile: object) -> dict[str, object]:
    if type(profile) is not dict:
        raise AthensGmpeProfileActionError("profile is not an object")
    exact_false = (
        "raw_model_values_returned",
        "gmpe_semantics_verified",
        "gmpe_applicability_verified",
        "numerical_equivalence_verified",
        "scenario_selection_authorized",
        "independent_validation_established",
        "publication_authorized",
        "model_use_authorized",
    )
    if profile.get("schema_version") != "oc-esrm20-scenario-v10-greece-gmpe-logic-tree-profile-v1":
        raise AthensGmpeProfileActionError("profile schema drifted")
    if profile.get("byte_count") != EXPECTED_BYTE_COUNT or profile.get("sha256") != EXPECTED_SHA256:
        raise AthensGmpeProfileActionError("profile identity drifted")
    for field in exact_false:
        if profile.get(field) is not False:
            raise AthensGmpeProfileActionError(f"profile authority widened at {field}")
    return profile


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {"status", "failure_class", "profile"}
    if type(result) is not dict or set(result) != expected_fields:
        raise AthensGmpeProfileActionError("terminal fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileActionError(f"terminal drifted at {field}")
    if result.get("status") == "pass":
        if result.get("failure_class") is not None:
            raise AthensGmpeProfileActionError("PASS carries failure class")
        _validate_profile(result.get("profile"))
        if result.get("provider_file_bytes_read") is not True:
            raise AthensGmpeProfileActionError("PASS lacks provider byte-read evidence")
        return result
    if result.get("status") == "blocked":
        if result.get("failure_class") not in {"acquisition_failure", "byte_identity_mismatch", "profile_failure"} or result.get("profile") is not None:
            raise AthensGmpeProfileActionError("BLOCKED result is not bounded")
        return result
    raise AthensGmpeProfileActionError("non-terminal status")


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        profile = _acquire_and_profile()
    except AthensGmpeProfileActionError as exc:
        failure = str(exc)
        if failure not in {"acquisition_failure", "byte_identity_mismatch", "profile_failure"}:
            raise
        result.update({"status": "blocked", "failure_class": failure, "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    result.update({"provider_file_bytes_read": True, "status": "pass", "failure_class": None, "profile": profile})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise AthensGmpeProfileActionError("terminal marker malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileActionError("terminal envelope malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensGmpeProfileActionError("terminal JSON malformed") from exc
    result_sha = result.get("execution_sha") if type(result) is dict else None
    if type(result_sha) is not str or not _SHA_RE.fullmatch(result_sha):
        raise AthensGmpeProfileActionError("terminal execution SHA invalid")
    _validate_terminal_result(result, execution_sha=result_sha)
    return result_sha == execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str, max_pages: int = 20) -> bool:
    try:
        comments = fetch_repository_comments(repository, token, issue=CONTROL_ISSUE, max_pages=max_pages)
    except LedgerError as exc:
        raise AthensGmpeProfileActionError("result ledger incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise AthensGmpeProfileActionError("ledger comment is not object")
        user = comment.get("user")
        if type(user) is dict and user.get("login") == TRUSTED_RESULT_LOGIN:
            if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
                return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(os.environ.get(args.comment_body_env), expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required")
    result = run_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
