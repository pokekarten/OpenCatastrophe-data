# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for receipt-bound EBRISK first-order dependency profiles."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import acquire_esrm20_ebrisk_risk_config_dependencies as worker
from scripts import openquake_config_dependencies as oqdeps
from scripts import verify_esrm20_ebrisk_risk_config_dependencies as bridge
from scripts.acquire_efehr_gitlab_receipt import utc_now
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-ebrisk-risk-config-dependency-profiles-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-ebrisk-risk-config-dependency-profiles-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-ebrisk-risk-config-dependency-profiles-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-ebrisk-risk-config-dependency-profiles-result-v1"
ACTION = "esrm20_ebrisk_risk_config_dependency_profiles"
CONTROL_ISSUE = 281
DATASET_ID = bridge.DATASET_ID
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_DEPENDENCIES = 128
MAX_TEXT_UTF8_BYTES = 2048
MAX_RESULT_UTF8_BYTES = 96_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_UTC_SECOND_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUEST_FIELDS = {
    "schema_version", "action", "issue", "target_sha", "dataset_id", "requester"
}
_PROFILE_FIELDS = {
    "schema_version", "source_issue", "dataset_id", "project_id", "project_path",
    "commit_sha", "candidate_key", "operation_id", "repository_path", "byte_count",
    "sha256", "receipt_comment_id", "parser", "dependencies", "raw_config_returned",
    "historical_group_assignment_verified", "dependency_inventory_authorized",
    "runtime_compatibility_verified", "external_bytes_persisted", "publication_authorized",
    "model_use_authorized", "profiled_at"
}
_DEPENDENCY_FIELDS = {"section", "option", "raw_path", "resolved_path"}
_RESULT_FIELDS = {
    "schema_version", "action", "source_issue", "dataset_id", "target_sha",
    "execution_sha", "status", "failure_class", "profiles", "raw_config_returned",
    "historical_group_assignment_verified", "dependency_inventory_authorized",
    "runtime_compatibility_verified", "external_bytes_persisted", "publication_authorized",
    "model_use_authorized"
}

_ACQUIRERS = (
    worker.acquire_group1_dependencies,
    worker.acquire_group2_dependencies,
    worker.acquire_iceland_dependencies,
)
_CANONICAL_ACQUIRERS = _ACQUIRERS
_CANONICAL_WORKER_REQUIRE_PRODUCTION_IDENTITY = worker._require_production_identity
_CANONICAL_FETCH_COMMENTS = fetch_repository_comments
_CANONICAL_NORMALIZE_REFERENCE = oqdeps.normalize_repository_reference
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_CONFIG_SPECS = bridge.CONFIG_SPECS
_CANONICAL_FIXED_AUTHORITY = (
    REQUEST_MARKER,
    RESULT_MARKER,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_VERSION,
    ACTION,
    CONTROL_ISSUE,
    DATASET_ID,
    TRUSTED_RESULT_LOGIN,
    MAX_LEDGER_PAGES,
    MAX_DEPENDENCIES,
    MAX_TEXT_UTF8_BYTES,
    MAX_RESULT_UTF8_BYTES,
    bridge.SCHEMA_VERSION,
    bridge.SOURCE_ISSUE,
    bridge.DATASET_ID,
    bridge.PROJECT_ID,
    bridge.PROJECT_PATH,
    bridge.COMMIT_SHA,
    bridge.RECEIPT_COMMENT_ID,
    bridge.PARSER_ID,
    tuple(
        (spec.key, spec.operation_id, spec.repository_path, spec.byte_count, spec.sha256)
        for spec in bridge.CONFIG_SPECS
    ),
)


class EbriskDependencyProfilesActionError(RuntimeError):
    """Fail-closed trusted-main EBRISK dependency-profile error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EbriskDependencyProfilesActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise EbriskDependencyProfilesActionError(f"non-finite JSON constant: {value}")


def _canonical_utc(value: object, *, field: str) -> str:
    if type(value) is not str or _UTC_SECOND_RE.fullmatch(value) is None:
        raise EbriskDependencyProfilesActionError(f"{field} must be canonical UTC seconds")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise EbriskDependencyProfilesActionError(f"{field} is not a valid UTC timestamp") from exc
    return value


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise EbriskDependencyProfilesActionError(f"{field} must be a non-empty trimmed string")
    if len(value.encode("utf-8")) > MAX_TEXT_UTF8_BYTES:
        raise EbriskDependencyProfilesActionError(f"{field} exceeds bounded text policy")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise EbriskDependencyProfilesActionError(f"{field} contains control characters")
    return value


def _require_production_authority() -> None:
    if _ACQUIRERS is not _CANONICAL_ACQUIRERS:
        raise EbriskDependencyProfilesActionError("trusted EBRISK acquirer tuple drifted")
    if (
        worker.acquire_group1_dependencies is not _CANONICAL_ACQUIRERS[0]
        or worker.acquire_group2_dependencies is not _CANONICAL_ACQUIRERS[1]
        or worker.acquire_iceland_dependencies is not _CANONICAL_ACQUIRERS[2]
        or worker._require_production_identity is not _CANONICAL_WORKER_REQUIRE_PRODUCTION_IDENTITY
        or oqdeps.normalize_repository_reference is not _CANONICAL_NORMALIZE_REFERENCE
        or fetch_repository_comments is not _CANONICAL_FETCH_COMMENTS
        or utc_now is not _CANONICAL_UTC_NOW
    ):
        raise EbriskDependencyProfilesActionError("trusted EBRISK dependency authority drifted")
    if bridge.CONFIG_SPECS is not _CANONICAL_CONFIG_SPECS:
        raise EbriskDependencyProfilesActionError("frozen EBRISK candidate specs drifted")
    observed = (
        REQUEST_MARKER,
        RESULT_MARKER,
        REQUEST_SCHEMA_VERSION,
        RESULT_SCHEMA_VERSION,
        ACTION,
        CONTROL_ISSUE,
        DATASET_ID,
        TRUSTED_RESULT_LOGIN,
        MAX_LEDGER_PAGES,
        MAX_DEPENDENCIES,
        MAX_TEXT_UTF8_BYTES,
        MAX_RESULT_UTF8_BYTES,
        bridge.SCHEMA_VERSION,
        bridge.SOURCE_ISSUE,
        bridge.DATASET_ID,
        bridge.PROJECT_ID,
        bridge.PROJECT_PATH,
        bridge.COMMIT_SHA,
        bridge.RECEIPT_COMMENT_ID,
        bridge.PARSER_ID,
        tuple(
            (spec.key, spec.operation_id, spec.repository_path, spec.byte_count, spec.sha256)
            for spec in bridge.CONFIG_SPECS
        ),
    )
    if observed != _CANONICAL_FIXED_AUTHORITY:
        raise EbriskDependencyProfilesActionError("frozen EBRISK dependency fixed authority drifted")
    try:
        _CANONICAL_WORKER_REQUIRE_PRODUCTION_IDENTITY()
    except worker.EbriskDependencyAcquisitionError as exc:
        raise EbriskDependencyProfilesActionError(
            "trusted EBRISK inner production authority drifted"
        ) from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise EbriskDependencyProfilesActionError("wrong EBRISK dependency issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskDependencyProfilesActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise EbriskDependencyProfilesActionError("invalid EBRISK dependency request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskDependencyProfilesActionError("request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EbriskDependencyProfilesActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskDependencyProfilesActionError("invalid request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise EbriskDependencyProfilesActionError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION), ("action", ACTION),
        ("issue", CONTROL_ISSUE), ("target_sha", execution_sha), ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskDependencyProfilesActionError(f"request {field} drifted")
    requester = request.get("requester")
    if type(requester) is not str or requester != requester.strip() or _SAFE_REQUESTER_RE.fullmatch(requester) is None:
        raise EbriskDependencyProfilesActionError("requester identity is invalid")
    return request


def _validate_dependency(value: object, *, config_path: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != _DEPENDENCY_FIELDS:
        raise EbriskDependencyProfilesActionError("dependency row shape drifted")
    row = {
        field: _bounded_text(value.get(field), field=f"dependency {field}")
        for field in ("section", "option", "raw_path", "resolved_path")
    }
    try:
        expected = _CANONICAL_NORMALIZE_REFERENCE(config_path, row["raw_path"])
    except oqdeps.OpenQuakeConfigError as exc:
        raise EbriskDependencyProfilesActionError("dependency path fails reviewed normalization") from exc
    if row["resolved_path"] != expected:
        raise EbriskDependencyProfilesActionError("dependency resolved path drifted")
    return row


def validate_profile(value: object, *, spec: bridge.ConfigSpec) -> dict[str, Any]:
    _require_production_authority()
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise EbriskDependencyProfilesActionError("dependency profile fields drifted")
    exact = (
        ("schema_version", _CANONICAL_FIXED_AUTHORITY[12]),
        ("source_issue", _CANONICAL_FIXED_AUTHORITY[13]),
        ("dataset_id", DATASET_ID),
        ("project_id", _CANONICAL_FIXED_AUTHORITY[15]),
        ("project_path", _CANONICAL_FIXED_AUTHORITY[16]),
        ("commit_sha", _CANONICAL_FIXED_AUTHORITY[17]),
        ("candidate_key", spec.key), ("operation_id", spec.operation_id),
        ("repository_path", spec.repository_path), ("byte_count", spec.byte_count),
        ("sha256", spec.sha256),
        ("receipt_comment_id", _CANONICAL_FIXED_AUTHORITY[18]),
        ("parser", _CANONICAL_FIXED_AUTHORITY[19]),
        ("raw_config_returned", False),
        ("historical_group_assignment_verified", False), ("dependency_inventory_authorized", False),
        ("runtime_compatibility_verified", False), ("external_bytes_persisted", False),
        ("publication_authorized", False), ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskDependencyProfilesActionError(f"dependency profile drifted at {field}")
    if _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise EbriskDependencyProfilesActionError("dependency profile SHA-256 is invalid")
    _canonical_utc(value.get("profiled_at"), field="profiled_at")
    raw_dependencies = value.get("dependencies")
    if type(raw_dependencies) is not list or len(raw_dependencies) > MAX_DEPENDENCIES:
        raise EbriskDependencyProfilesActionError("dependency list exceeds bounded policy")
    dependencies = [_validate_dependency(row, config_path=spec.repository_path) for row in raw_dependencies]
    identities = [(row["section"], row["option"], row["resolved_path"]) for row in dependencies]
    if len(identities) != len(set(identities)):
        raise EbriskDependencyProfilesActionError("dependency profile contains duplicates")
    if dependencies != sorted(dependencies, key=lambda row: (row["resolved_path"], row["section"], row["option"], row["raw_path"])):
        raise EbriskDependencyProfilesActionError("dependency profile ordering drifted")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "dependency_inventory_authorized": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise EbriskDependencyProfilesActionError("trusted result fields drifted")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskDependencyProfilesActionError(f"trusted result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise EbriskDependencyProfilesActionError("PASS result carries failure_class")
        profiles = result.get("profiles")
        if type(profiles) is not list or len(profiles) != len(_CANONICAL_CONFIG_SPECS):
            raise EbriskDependencyProfilesActionError("PASS result must carry exactly three profiles")
        for profile, spec in zip(profiles, _CANONICAL_CONFIG_SPECS, strict=True):
            validate_profile(profile, spec=spec)
        return result
    if status == "blocked":
        if result.get("failure_class") != "profile_failure" or result.get("profiles") is not None:
            raise EbriskDependencyProfilesActionError("blocked result widened or leaked evidence")
        return result
    if status == "duplicate":
        if result.get("failure_class") is not None or result.get("profiles") is not None:
            raise EbriskDependencyProfilesActionError("duplicate result must not carry evidence")
        return result
    raise EbriskDependencyProfilesActionError("trusted result has non-terminal status")


def _parse_terminal_body(body: object) -> tuple[str, dict[str, Any]] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise EbriskDependencyProfilesActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskDependencyProfilesActionError("trusted result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EbriskDependencyProfilesActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskDependencyProfilesActionError("trusted result JSON is malformed") from exc
    if type(result) is not dict:
        raise EbriskDependencyProfilesActionError("trusted result is not an object")
    execution_sha = result.get("execution_sha")
    target_sha = result.get("target_sha")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None or target_sha != execution_sha:
        raise EbriskDependencyProfilesActionError("trusted result SHA identity is inconsistent")
    validate_terminal_result(result, execution_sha=execution_sha)
    return execution_sha, result


def _has_terminal_result(
    *, repository: str, token: str, execution_sha: str, fetch_comments: Callable[..., list[dict[str, Any]]]
) -> bool:
    try:
        comments = fetch_comments(repository, token, issue=CONTROL_ISSUE, max_pages=MAX_LEDGER_PAGES)
    except LedgerError as exc:
        raise EbriskDependencyProfilesActionError("result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise EbriskDependencyProfilesActionError("result ledger contains non-object")
        user = comment.get("user")
        if type(user) is not dict or user.get("login") != TRUSTED_RESULT_LOGIN:
            continue
        parsed = _parse_terminal_body(comment.get("body"))
        if parsed is not None and parsed[0] == execution_sha:
            return True
    return False


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    _require_production_authority()
    return _has_terminal_result(
        repository=repository,
        token=token,
        execution_sha=execution_sha,
        fetch_comments=_CANONICAL_FETCH_COMMENTS,
    )


def _execute_profiles(
    *, repository: str, token: str, execution_sha: str,
    acquirers: tuple[Callable[[], dict[str, Any]], ...],
    now: Callable[[], str],
    fetch_comments: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    if _has_terminal_result(
        repository=repository,
        token=token,
        execution_sha=execution_sha,
        fetch_comments=fetch_comments,
    ):
        return {**_base_result(execution_sha=execution_sha), "status": "duplicate", "failure_class": None, "profiles": None}
    if type(acquirers) is not tuple or len(acquirers) != len(_CANONICAL_CONFIG_SPECS):
        raise EbriskDependencyProfilesActionError("exactly three EBRISK acquirers are required")
    profiles: list[dict[str, Any]] = []
    try:
        for acquirer, spec in zip(acquirers, _CANONICAL_CONFIG_SPECS, strict=True):
            profile = dict(acquirer())
            profile["profiled_at"] = now()
            validate_profile(profile, spec=spec)
            profiles.append(profile)
    except (worker.EbriskDependencyAcquisitionError, EbriskDependencyProfilesActionError):
        return {**_base_result(execution_sha=execution_sha), "status": "blocked", "failure_class": "profile_failure", "profiles": None}
    result = {**_base_result(execution_sha=execution_sha), "status": "pass", "failure_class": None, "profiles": profiles}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise EbriskDependencyProfilesActionError("dependency result exceeds publication limit")
    return validate_terminal_result(result, execution_sha=execution_sha)


def execute_profiles(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    """Execute only the code-owned canonical workers and clocks on trusted main."""

    _require_production_authority()
    return _execute_profiles(
        repository=repository,
        token=token,
        execution_sha=execution_sha,
        acquirers=_CANONICAL_ACQUIRERS,
        now=_CANONICAL_UTC_NOW,
        fetch_comments=_CANONICAL_FETCH_COMMENTS,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--token-env")
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)
    validate_request(os.environ.get(args.comment_body_env), expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error("--repository, --token-env and --output are required for execution")
    token = os.environ.get(args.token_env)
    if not token:
        raise EbriskDependencyProfilesActionError("GitHub ledger token is absent")
    result = execute_profiles(repository=args.repository, token=token, execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
