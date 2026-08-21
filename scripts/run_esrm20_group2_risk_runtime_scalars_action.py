# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for exact Group2 risk-runtime scalar evidence."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import acquire_esrm20_ebrisk_risk_config_dependencies as worker
from scripts import project_esrm20_group2_risk_runtime_scalars as projector
from scripts import run_esrm20_group1_risk_runtime_scalars_action as shared_action
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-group2-risk-runtime-scalars-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-group2-risk-runtime-scalars-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-group2-risk-runtime-scalars-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-group2-risk-runtime-scalars-result-v1"
ACTION = "esrm20_group2_risk_runtime_scalars"
CONTROL_ISSUE = 287
DATASET_ID = projector.DATASET_ID
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = shared_action.MAX_LEDGER_PAGES
MAX_REQUEST_UTF8_BYTES = shared_action.MAX_REQUEST_UTF8_BYTES
MAX_TERMINAL_UTF8_BYTES = shared_action.MAX_TERMINAL_UTF8_BYTES

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "evidence",
    "raw_config_returned",
    "historical_group_assignment_verified",
    "runtime_compatibility_verified",
    "numerical_loss_reproduction_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_EVIDENCE_FIELDS = {
    "schema_version",
    "control_issue",
    "source_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "candidate_key",
    "repository_path",
    "byte_count",
    "sha256",
    "receipt_comment_id",
    "openquake_reference",
    "runtime_scalars",
    "raw_config_returned",
    "historical_group_assignment_verified",
    "runtime_compatibility_verified",
    "numerical_loss_reproduction_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_OPENQUAKE_FIELDS = {"repository", "tag", "commit_sha"}

Group2RuntimeScalarsActionError = shared_action.Group1RuntimeScalarsActionError

_CANONICAL_FETCH_COMMENTS = fetch_repository_comments
_CANONICAL_SHARED_ACTION_AUTHORITY = shared_action._require_production_authority  # noqa: SLF001
_CANONICAL_STRICT_LOADS = shared_action._strict_loads  # noqa: SLF001
_CANONICAL_UTF8_SIZE = shared_action._utf8_size  # noqa: SLF001
_CANONICAL_VALIDATE_RUNTIME_SCALARS = shared_action._validate_runtime_scalars  # noqa: SLF001
_CANONICAL_ACQUIRE_PAYLOAD = worker._CANONICAL_ACQUIRE_EXACT_PAYLOAD  # noqa: SLF001
_CANONICAL_OPEN_FIXED = worker._CANONICAL_OPEN_FIXED  # noqa: SLF001
_CANONICAL_MONOTONIC = worker._CANONICAL_MONOTONIC  # noqa: SLF001
_CANONICAL_REQUIRE_WORKER_IDENTITY = worker._require_production_identity  # noqa: SLF001
_CANONICAL_PROJECT = projector.project_group2_risk_runtime_scalars
_CANONICAL_GROUP2_SPEC = projector.GROUP2_SPEC
_CANONICAL_SHARED_RUNTIME_PROJECT = projector.project_runtime_scalars_from_verified_text
_CANONICAL_FIXED_AUTHORITY = (
    projector.SCHEMA_VERSION,
    projector.CONTROL_ISSUE,
    projector.SOURCE_ISSUE,
    projector.DATASET_ID,
    projector.PROJECT_ID,
    projector.PROJECT_PATH,
    projector.COMMIT_SHA,
    projector.GROUP2_KEY,
    projector.GROUP2_SPEC.repository_path,
    projector.GROUP2_SPEC.byte_count,
    projector.GROUP2_SPEC.sha256,
    projector.OPENQUAKE_REPOSITORY,
    projector.OPENQUAKE_TAG,
    projector.OPENQUAKE_COMMIT,
)


def _require_production_authority() -> None:
    if fetch_repository_comments is not _CANONICAL_FETCH_COMMENTS:
        raise Group2RuntimeScalarsActionError("trusted Group2 ledger authority drifted")
    if shared_action._require_production_authority is not _CANONICAL_SHARED_ACTION_AUTHORITY:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("shared runtime scalar authority drifted")
    if shared_action._strict_loads is not _CANONICAL_STRICT_LOADS:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("shared strict JSON authority drifted")
    if shared_action._utf8_size is not _CANONICAL_UTF8_SIZE:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("shared UTF-8 bound authority drifted")
    if shared_action._validate_runtime_scalars is not _CANONICAL_VALIDATE_RUNTIME_SCALARS:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("shared runtime validation authority drifted")
    try:
        _CANONICAL_SHARED_ACTION_AUTHORITY()
    except shared_action.Group1RuntimeScalarsActionError as exc:
        raise Group2RuntimeScalarsActionError(
            "shared runtime scalar authority failed"
        ) from exc
    if worker._CANONICAL_ACQUIRE_EXACT_PAYLOAD is not _CANONICAL_ACQUIRE_PAYLOAD:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError(
            "trusted Group2 byte acquisition authority drifted"
        )
    if worker._CANONICAL_OPEN_FIXED is not _CANONICAL_OPEN_FIXED:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("trusted Group2 transport authority drifted")
    if worker._CANONICAL_MONOTONIC is not _CANONICAL_MONOTONIC:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("trusted Group2 clock authority drifted")
    if worker._require_production_identity is not _CANONICAL_REQUIRE_WORKER_IDENTITY:  # noqa: SLF001
        raise Group2RuntimeScalarsActionError("trusted Group2 worker identity gate drifted")
    if projector.project_group2_risk_runtime_scalars is not _CANONICAL_PROJECT:
        raise Group2RuntimeScalarsActionError("trusted Group2 projector authority drifted")
    if projector.GROUP2_SPEC is not _CANONICAL_GROUP2_SPEC:
        raise Group2RuntimeScalarsActionError("trusted Group2 config spec object drifted")
    if (
        projector.project_runtime_scalars_from_verified_text
        is not _CANONICAL_SHARED_RUNTIME_PROJECT
        or projector.project_runtime_scalars_from_verified_text
        is not projector.shared_runtime.project_runtime_scalars_from_verified_text
    ):
        raise Group2RuntimeScalarsActionError("trusted shared scalar parser drifted")
    observed = (
        projector.SCHEMA_VERSION,
        projector.CONTROL_ISSUE,
        projector.SOURCE_ISSUE,
        projector.DATASET_ID,
        projector.PROJECT_ID,
        projector.PROJECT_PATH,
        projector.COMMIT_SHA,
        projector.GROUP2_KEY,
        projector.GROUP2_SPEC.repository_path,
        projector.GROUP2_SPEC.byte_count,
        projector.GROUP2_SPEC.sha256,
        projector.OPENQUAKE_REPOSITORY,
        projector.OPENQUAKE_TAG,
        projector.OPENQUAKE_COMMIT,
    )
    if observed != _CANONICAL_FIXED_AUTHORITY:
        raise Group2RuntimeScalarsActionError("trusted Group2 fixed authority drifted")
    try:
        _CANONICAL_REQUIRE_WORKER_IDENTITY()
    except worker.EbriskDependencyAcquisitionError as exc:
        raise Group2RuntimeScalarsActionError("trusted Group2 worker authority failed") from exc


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    _require_production_authority()
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Group2RuntimeScalarsActionError("wrong Group2 scalar issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group2RuntimeScalarsActionError("invalid execution SHA")
    if type(body) is not str:
        raise Group2RuntimeScalarsActionError("Group2 scalar request is not text")
    if _CANONICAL_UTF8_SIZE(body, label="Group2 scalar request") > MAX_REQUEST_UTF8_BYTES:
        raise Group2RuntimeScalarsActionError("Group2 scalar request exceeds limit")
    if body.count(REQUEST_MARKER) != 1:
        raise Group2RuntimeScalarsActionError("invalid Group2 scalar request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Group2RuntimeScalarsActionError(
            "Group2 scalar request envelope is not canonical"
        )
    request = _CANONICAL_STRICT_LOADS(after.strip(), label="Group2 scalar request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Group2RuntimeScalarsActionError("Group2 scalar request fields drifted")
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
            raise Group2RuntimeScalarsActionError(
                f"Group2 scalar request {field} drifted"
            )
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Group2RuntimeScalarsActionError("invalid requester identity")
    return request


def validate_evidence(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _EVIDENCE_FIELDS:
        raise Group2RuntimeScalarsActionError("Group2 scalar evidence fields drifted")
    exact = (
        ("schema_version", _CANONICAL_FIXED_AUTHORITY[0]),
        ("control_issue", _CANONICAL_FIXED_AUTHORITY[1]),
        ("source_issue", _CANONICAL_FIXED_AUTHORITY[2]),
        ("dataset_id", _CANONICAL_FIXED_AUTHORITY[3]),
        ("project_id", _CANONICAL_FIXED_AUTHORITY[4]),
        ("project_path", _CANONICAL_FIXED_AUTHORITY[5]),
        ("commit_sha", _CANONICAL_FIXED_AUTHORITY[6]),
        ("candidate_key", _CANONICAL_FIXED_AUTHORITY[7]),
        ("repository_path", _CANONICAL_FIXED_AUTHORITY[8]),
        ("byte_count", _CANONICAL_FIXED_AUTHORITY[9]),
        ("sha256", _CANONICAL_FIXED_AUTHORITY[10]),
        ("receipt_comment_id", projector.risk_config.RECEIPT_COMMENT_ID),
        ("raw_config_returned", False),
        ("historical_group_assignment_verified", False),
        ("runtime_compatibility_verified", False),
        ("numerical_loss_reproduction_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Group2RuntimeScalarsActionError(
                f"Group2 scalar evidence drifted at {field}"
            )
    if _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise Group2RuntimeScalarsActionError("Group2 scalar evidence SHA-256 is invalid")
    oq = value.get("openquake_reference")
    if type(oq) is not dict or set(oq) != _OPENQUAKE_FIELDS:
        raise Group2RuntimeScalarsActionError("OpenQuake reference shape drifted")
    expected_oq = {
        "repository": _CANONICAL_FIXED_AUTHORITY[11],
        "tag": _CANONICAL_FIXED_AUTHORITY[12],
        "commit_sha": _CANONICAL_FIXED_AUTHORITY[13],
    }
    if oq != expected_oq:
        raise Group2RuntimeScalarsActionError("OpenQuake reference drifted")
    _CANONICAL_VALIDATE_RUNTIME_SCALARS(value.get("runtime_scalars"))
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
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_terminal_result(
    result: object, *, execution_sha: str
) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise Group2RuntimeScalarsActionError(
            "trusted Group2 scalar result fields drifted"
        )
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Group2RuntimeScalarsActionError(
                f"trusted Group2 scalar result drifted at {field}"
            )
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise Group2RuntimeScalarsActionError("PASS result carries failure_class")
        validate_evidence(result.get("evidence"))
        return result
    if status == "blocked":
        if (
            result.get("failure_class") != "projection_failure"
            or result.get("evidence") is not None
        ):
            raise Group2RuntimeScalarsActionError(
                "blocked result widened or leaked evidence"
            )
        return result
    raise Group2RuntimeScalarsActionError(
        "trusted Group2 scalar result has non-terminal status"
    )


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _CANONICAL_UTF8_SIZE(body, label="Group2 scalar result") > MAX_TERMINAL_UTF8_BYTES:
        raise Group2RuntimeScalarsActionError("trusted Group2 scalar result exceeds limit")
    if body.count(RESULT_MARKER) != 1:
        raise Group2RuntimeScalarsActionError(
            "trusted Group2 scalar result marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Group2RuntimeScalarsActionError(
            "trusted Group2 scalar result envelope is malformed"
        )
    result = _CANONICAL_STRICT_LOADS(after.strip(), label="Group2 scalar result")
    execution_sha = result.get("execution_sha") if type(result) is dict else None
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group2RuntimeScalarsActionError(
            "trusted Group2 scalar result SHA is invalid"
        )
    validate_terminal_result(result, execution_sha=execution_sha)
    return execution_sha


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = MAX_LEDGER_PAGES,
) -> bool:
    _require_production_authority()
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group2RuntimeScalarsActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Group2RuntimeScalarsActionError("Group2 scalar ledger is incomplete") from exc
    found = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        terminal_sha = parse_terminal_result(comment.get("body"))
        if terminal_sha == execution_sha:
            found = True
    return found


def _execute_with(
    *,
    execution_sha: str,
    acquire_payload: Callable[[], bytes],
    project: Callable[[bytes], dict[str, Any]],
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquire_payload()
        if type(payload) is not bytes:
            raise Group2RuntimeScalarsActionError(
                "trusted Group2 acquisition returned non-bytes"
            )
        evidence = validate_evidence(project(payload))
    except (
        worker.EbriskDependencyAcquisitionError,
        projector.RiskRuntimeScalarError,
        Group2RuntimeScalarsActionError,
    ):
        result.update(
            {"status": "blocked", "failure_class": "projection_failure", "evidence": None}
        )
        return result
    result.update({"status": "pass", "failure_class": None, "evidence": evidence})
    validate_terminal_result(result, execution_sha=execution_sha)
    return result


def run_projection(*, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()

    def acquire() -> bytes:
        return _CANONICAL_ACQUIRE_PAYLOAD(
            "group2", opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC
        )

    return _execute_with(
        execution_sha=execution_sha,
        acquire_payload=acquire,
        project=_CANONICAL_PROJECT,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True, type=int)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        if args.output is not None:
            parser.error("--output is not valid with --validate-request-only")
        return 0
    if args.output is None:
        parser.error("--output is required unless --validate-request-only is used")
    result = run_projection(execution_sha=args.execution_sha)
    args.output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
