# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main bounded IMT-name profile for the exact ESRM20 Group2 root."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import acquire_esrm20_event_hazard_dependencies as _acquisition
from scripts import verify_esrm20_event_hazard_dependencies as _bridge
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-group2-imt-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-group2-imt-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-event-hazard-group2-imt-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-event-hazard-group2-imt-profile-result-v1"
ACTION = "esrm20_event_hazard_group2_imt_profile"
CONTROL_ISSUE = 281
DATASET_ID = _bridge.DATASET_ID
GROUP = 2
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
_CANONICAL_ACQUIRER = _acquisition.acquire_event_hazard_group2_imt_profile


class Group2ImtProfileActionError(RuntimeError):
    """Fail-closed trusted Group2 IMT profile error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Group2ImtProfileActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise Group2ImtProfileActionError(f"non-finite JSON constant: {value}")


def _require_contract() -> None:
    spec = _bridge._root_spec(GROUP)
    exact = (
        (_bridge.SOURCE_ISSUE, CONTROL_ISSUE, "source issue"),
        (_bridge.DATASET_ID, DATASET_ID, "dataset"),
        (spec.repository_path, "Configuration_files/config_event_hazard_Group2.ini", "path"),
        (spec.byte_count, 1673, "byte count"),
        (spec.sha256, "eb74edd2168bad20c23d4b0e1a99f5ed97ef28606a9ebfef6b8c8191d35dd34c", "SHA-256"),
        (spec.receipt_comment_id, 5301299581, "receipt comment"),
        (_bridge.IMT_PROFILE_SCHEMA_VERSION, "oc-esrm20-event-hazard-imt-profile-v1", "profile schema"),
        (_bridge.OPENQUAKE_COMMIT, "9f044c93d72846421a8faa90ebf0a6afacdf3c20", "OpenQuake commit"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Group2ImtProfileActionError(f"trusted Group2 IMT {label} drifted")
    if _acquisition.acquire_event_hazard_group2_imt_profile is not _CANONICAL_ACQUIRER:
        raise Group2ImtProfileActionError("trusted Group2 IMT acquirer identity drifted")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_contract()
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Group2ImtProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group2ImtProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Group2ImtProfileActionError("invalid Group2 IMT request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Group2ImtProfileActionError("Group2 IMT request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Group2ImtProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Group2ImtProfileActionError("invalid Group2 IMT request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Group2ImtProfileActionError("Group2 IMT request fields drifted")
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
            raise Group2ImtProfileActionError(f"Group2 IMT request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Group2ImtProfileActionError("invalid requester identity")
    return request


def _validate_profile(profile: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "source_issue",
        "control_issue",
        "dataset_id",
        "project_id",
        "project_path",
        "commit_sha",
        "group",
        "operation_id",
        "repository_path",
        "byte_count",
        "sha256",
        "receipt_comment_id",
        "imt_option",
        "imt_names",
        "imt_count",
        "levels_returned",
        "raw_config_returned",
        "component_semantics_verified",
        "unit_semantics_verified",
        "hazard_vulnerability_imt_compatibility_verified",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(profile) is not dict or set(profile) != fields:
        raise Group2ImtProfileActionError("Group2 IMT profile fields drifted")
    spec = _bridge._root_spec(GROUP)
    exact = {
        "schema_version": _bridge.IMT_PROFILE_SCHEMA_VERSION,
        "source_issue": CONTROL_ISSUE,
        "control_issue": _bridge.CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": _bridge.PROJECT_ID,
        "project_path": _bridge.PROJECT_PATH,
        "commit_sha": _bridge.COMMIT_SHA,
        "group": GROUP,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": spec.byte_count,
        "sha256": spec.sha256,
        "receipt_comment_id": spec.receipt_comment_id,
        "levels_returned": False,
        "raw_config_returned": False,
        "component_semantics_verified": False,
        "unit_semantics_verified": False,
        "hazard_vulnerability_imt_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        observed = profile.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Group2ImtProfileActionError(f"Group2 IMT profile drifted at {field}")
    option = profile.get("imt_option")
    if option not in _bridge.IMT_OPTIONS:
        raise Group2ImtProfileActionError("Group2 IMT option is not canonical")
    names = profile.get("imt_names")
    if type(names) is not list or not names:
        raise Group2ImtProfileActionError("Group2 IMT names are not canonical")
    try:
        canonical = _bridge._canonicalize_imt_names(names)
    except _bridge.VerifiedEventHazardConfigError as exc:
        raise Group2ImtProfileActionError("Group2 IMT name is invalid") from exc
    if names != canonical:
        raise Group2ImtProfileActionError("Group2 IMT names are not OpenQuake-canonical")
    imt_count = profile.get("imt_count")
    if type(imt_count) is not int or imt_count != len(names):
        raise Group2ImtProfileActionError("Group2 IMT count drifted")
    return profile


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_bytes_persisted": False,
        "component_semantics_verified": False,
        "unit_semantics_verified": False,
        "hazard_vulnerability_imt_compatibility_verified": False,
        "numerical_hazard_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    if type(result) is not dict or set(result) != set(base) | {"status", "failure_class", "profile"}:
        raise Group2ImtProfileActionError("trusted Group2 IMT result fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Group2ImtProfileActionError(f"trusted Group2 IMT result drifted at {field}")
    if result.get("status") == "pass":
        if result.get("failure_class") is not None:
            raise Group2ImtProfileActionError("Group2 IMT PASS cannot carry failure_class")
        _validate_profile(result.get("profile"))
        return result
    if result.get("status") == "blocked":
        if result.get("failure_class") != "profile_failure" or result.get("profile") is not None:
            raise Group2ImtProfileActionError("blocked Group2 IMT result is not safely bounded")
        return result
    raise Group2ImtProfileActionError("trusted Group2 IMT result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise Group2ImtProfileActionError("trusted Group2 IMT result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Group2ImtProfileActionError("trusted Group2 IMT result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Group2ImtProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Group2ImtProfileActionError("trusted Group2 IMT result JSON is malformed") from exc
    if type(result) is not dict:
        raise Group2ImtProfileActionError("trusted Group2 IMT result is not an object")
    candidate = result.get("execution_sha")
    target = result.get("target_sha")
    if (
        type(candidate) is not str
        or _SHA_RE.fullmatch(candidate) is None
        or type(target) is not str
        or target != candidate
    ):
        raise Group2ImtProfileActionError("trusted Group2 IMT historical SHA identity is inconsistent")
    _validate_terminal_result(result, execution_sha=candidate)
    return candidate == execution_sha


def has_terminal_imt_profile_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group2ImtProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Group2ImtProfileActionError("Group2 IMT result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise Group2ImtProfileActionError("Group2 IMT ledger contains a non-object comment")
        user = comment.get("user")
        if type(user) is dict and user.get("login") == TRUSTED_RESULT_LOGIN:
            if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
                return True
    return False


def _run_profile(
    *, execution_sha: str, acquirer: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        profile = acquirer()
        profile = _validate_profile(profile)
    except (_acquisition.EventHazardDependencyAcquisitionError, Group2ImtProfileActionError):
        result.update({"status": "blocked", "failure_class": "profile_failure", "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    result.update({"status": "pass", "failure_class": None, "profile": profile})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    _require_contract()
    return _run_profile(execution_sha=execution_sha, acquirer=_CANONICAL_ACQUIRER)


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
    result = run_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
