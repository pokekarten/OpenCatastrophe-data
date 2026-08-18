# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for three source-derived ESRM20 EBRISK risk INIs."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from scripts.acquire_efehr_esrm20_ebrisk_config_receipts import (
        COMMIT_SHA,
        DATASET_ID,
        GROUP1_OPERATION_ID,
        GROUP1_REPOSITORY_PATH,
        GROUP2_OPERATION_ID,
        GROUP2_REPOSITORY_PATH,
        ICELAND_OPERATION_ID,
        ICELAND_REPOSITORY_PATH,
        MAX_CONFIG_BYTES,
        PROJECT_ID,
        PROJECT_PATH,
        acquire_ebrisk_group1_candidate_receipt,
        acquire_ebrisk_group2_candidate_receipt,
        acquire_ebrisk_iceland_candidate_receipt,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from acquire_efehr_esrm20_ebrisk_config_receipts import (
        COMMIT_SHA,
        DATASET_ID,
        GROUP1_OPERATION_ID,
        GROUP1_REPOSITORY_PATH,
        GROUP2_OPERATION_ID,
        GROUP2_REPOSITORY_PATH,
        ICELAND_OPERATION_ID,
        ICELAND_REPOSITORY_PATH,
        MAX_CONFIG_BYTES,
        PROJECT_ID,
        PROJECT_PATH,
        acquire_ebrisk_group1_candidate_receipt,
        acquire_ebrisk_group2_candidate_receipt,
        acquire_ebrisk_iceland_candidate_receipt,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-ebrisk-risk-config-receipts-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-ebrisk-risk-config-receipts-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-ebrisk-risk-config-receipts-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-ebrisk-risk-config-receipts-result-v1"
ACTION = "esrm20_ebrisk_risk_config_receipts"
CONTROL_ISSUE = 281
SOURCE_SCIENCE_ISSUE = 281
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = frozenset(
    {
        "schema_version",
        "action",
        "issue",
        "target_sha",
        "dataset_id",
        "requester",
    }
)
_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "action",
        "source_issue",
        "source_science_issue",
        "dataset_id",
        "target_sha",
        "execution_sha",
        "provider_identity",
        "historical_group_assignment_verified",
        "config_content_interpreted",
        "dependency_closure_verified",
        "runtime_compatibility_verified",
        "model_use_authorized",
        "external_bytes_persisted",
        "publication_authorized",
        "status",
        "failure_class",
        "receipts",
    }
)
_RECEIPT_ROW_FIELDS = frozenset(
    {
        "repository_path",
        "operation_id",
        "retrieved_at",
        "byte_count",
        "sha256",
        "content_type",
        "etag",
    }
)
_RECEIPT_TARGETS = (
    (
        GROUP1_REPOSITORY_PATH,
        GROUP1_OPERATION_ID,
        acquire_ebrisk_group1_candidate_receipt,
    ),
    (
        GROUP2_REPOSITORY_PATH,
        GROUP2_OPERATION_ID,
        acquire_ebrisk_group2_candidate_receipt,
    ),
    (
        ICELAND_REPOSITORY_PATH,
        ICELAND_OPERATION_ID,
        acquire_ebrisk_iceland_candidate_receipt,
    ),
)

_CANONICAL_RECEIPT_TARGETS = _RECEIPT_TARGETS
_CANONICAL_FETCH_REPOSITORY_COMMENTS = fetch_repository_comments
_CANONICAL_FIXED_AUTHORITY = (
    REQUEST_MARKER,
    RESULT_MARKER,
    REQUEST_SCHEMA_VERSION,
    RESULT_SCHEMA_VERSION,
    ACTION,
    CONTROL_ISSUE,
    SOURCE_SCIENCE_ISSUE,
    TRUSTED_RESULT_LOGIN,
    MAX_LEDGER_PAGES,
    DATASET_ID,
    PROJECT_ID,
    PROJECT_PATH,
    COMMIT_SHA,
    MAX_CONFIG_BYTES,
    GROUP1_REPOSITORY_PATH,
    GROUP1_OPERATION_ID,
    GROUP2_REPOSITORY_PATH,
    GROUP2_OPERATION_ID,
    ICELAND_REPOSITORY_PATH,
    ICELAND_OPERATION_ID,
)


class EbriskRiskConfigReceiptsActionError(RuntimeError):
    """Fail-closed EBRISK risk-config receipt action error."""


def _require_production_authority() -> None:
    if _RECEIPT_TARGETS is not _CANONICAL_RECEIPT_TARGETS:
        raise EbriskRiskConfigReceiptsActionError(
            "frozen EBRISK action worker targets drifted"
        )
    if fetch_repository_comments is not _CANONICAL_FETCH_REPOSITORY_COMMENTS:
        raise EbriskRiskConfigReceiptsActionError(
            "frozen EBRISK action ledger fetcher drifted"
        )
    observed = (
        REQUEST_MARKER,
        RESULT_MARKER,
        REQUEST_SCHEMA_VERSION,
        RESULT_SCHEMA_VERSION,
        ACTION,
        CONTROL_ISSUE,
        SOURCE_SCIENCE_ISSUE,
        TRUSTED_RESULT_LOGIN,
        MAX_LEDGER_PAGES,
        DATASET_ID,
        PROJECT_ID,
        PROJECT_PATH,
        COMMIT_SHA,
        MAX_CONFIG_BYTES,
        GROUP1_REPOSITORY_PATH,
        GROUP1_OPERATION_ID,
        GROUP2_REPOSITORY_PATH,
        GROUP2_OPERATION_ID,
        ICELAND_REPOSITORY_PATH,
        ICELAND_OPERATION_ID,
    )
    if observed != _CANONICAL_FIXED_AUTHORITY:
        raise EbriskRiskConfigReceiptsActionError(
            "frozen EBRISK action fixed authority drifted"
        )


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise EbriskRiskConfigReceiptsActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise EbriskRiskConfigReceiptsActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise EbriskRiskConfigReceiptsActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskRiskConfigReceiptsActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise EbriskRiskConfigReceiptsActionError("invalid EBRISK receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskRiskConfigReceiptsActionError("EBRISK receipt request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except EbriskRiskConfigReceiptsActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskRiskConfigReceiptsActionError("invalid EBRISK receipt request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise EbriskRiskConfigReceiptsActionError("EBRISK receipt request fields drifted")
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
            raise EbriskRiskConfigReceiptsActionError(
                f"EBRISK receipt request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise EbriskRiskConfigReceiptsActionError("invalid requester identity")
    return request


def _validate_receipt(
    receipt: object, *, repository_path: str, operation_id: str
) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise EbriskRiskConfigReceiptsActionError("worker returned a non-object receipt")
    exact = (
        ("schema_version", "oc-efehr-trusted-acquisition-v1"),
        ("operation_id", operation_id),
        ("source_issue", SOURCE_SCIENCE_ISSUE),
        ("dataset_id", DATASET_ID),
        ("provider_host", "gitlab.seismo.ethz.ch"),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("repository_path", repository_path),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    )
    for field, expected in exact:
        observed = receipt.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskRiskConfigReceiptsActionError(
                f"EBRISK receipt drifted at {field}"
            )
    byte_count = receipt.get("byte_count")
    if (
        type(byte_count) is not int
        or isinstance(byte_count, bool)
        or byte_count <= 0
        or byte_count > MAX_CONFIG_BYTES
    ):
        raise EbriskRiskConfigReceiptsActionError("EBRISK receipt byte count is invalid")
    digest = receipt.get("sha256")
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise EbriskRiskConfigReceiptsActionError("EBRISK receipt SHA-256 is invalid")
    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not (1 <= len(retrieved_at) <= 64):
        raise EbriskRiskConfigReceiptsActionError(
            "EBRISK receipt retrieval time is invalid"
        )
    return receipt


def _bounded_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "retrieved_at": receipt["retrieved_at"],
        "byte_count": receipt["byte_count"],
        "sha256": receipt["sha256"],
        "content_type": receipt.get("content_type"),
        "etag": receipt.get("etag"),
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
        },
        "historical_group_assignment_verified": False,
        "config_content_interpreted": False,
        "dependency_closure_verified": False,
        "runtime_compatibility_verified": False,
        "model_use_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _validate_receipt_row(row: object, *, path: str, operation_id: str) -> None:
    if type(row) is not dict or set(row) != _RECEIPT_ROW_FIELDS:
        raise EbriskRiskConfigReceiptsActionError(
            "bounded EBRISK receipt row fields drifted"
        )
    if row.get("repository_path") != path or row.get("operation_id") != operation_id:
        raise EbriskRiskConfigReceiptsActionError(
            "bounded EBRISK receipt row identity drifted"
        )
    byte_count = row.get("byte_count")
    digest = row.get("sha256")
    retrieved_at = row.get("retrieved_at")
    content_type = row.get("content_type")
    etag = row.get("etag")
    if (
        type(byte_count) is not int
        or isinstance(byte_count, bool)
        or byte_count <= 0
        or byte_count > MAX_CONFIG_BYTES
        or type(digest) is not str
        or _DIGEST_RE.fullmatch(digest) is None
        or type(retrieved_at) is not str
        or not (1 <= len(retrieved_at) <= 64)
        or not (
            content_type is None
            or (type(content_type) is str and len(content_type) <= 256)
        )
        or not (etag is None or (type(etag) is str and len(etag) <= 512))
    ):
        raise EbriskRiskConfigReceiptsActionError("bounded EBRISK receipt row is invalid")


def _validated_terminal_result_sha(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise EbriskRiskConfigReceiptsActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskRiskConfigReceiptsActionError("trusted result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except EbriskRiskConfigReceiptsActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskRiskConfigReceiptsActionError("trusted result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise EbriskRiskConfigReceiptsActionError("trusted result fields drifted")
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if (
        type(target_sha) is not str
        or type(execution_sha) is not str
        or _SHA_RE.fullmatch(target_sha) is None
        or _SHA_RE.fullmatch(execution_sha) is None
        or target_sha != execution_sha
    ):
        raise EbriskRiskConfigReceiptsActionError("trusted result SHA identity drifted")
    own_sha = execution_sha
    for field, expected in _base_result(execution_sha=own_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskRiskConfigReceiptsActionError(f"trusted result drifted at {field}")
    if result.get("status") == "pass":
        rows = result.get("receipts")
        if type(rows) is not list or len(rows) != len(_CANONICAL_RECEIPT_TARGETS):
            raise EbriskRiskConfigReceiptsActionError(
                "trusted PASS must contain three receipts"
            )
        for row, (path, operation_id, _worker) in zip(
            rows, _CANONICAL_RECEIPT_TARGETS
        ):
            _validate_receipt_row(row, path=path, operation_id=operation_id)
        if result.get("failure_class") is not None:
            raise EbriskRiskConfigReceiptsActionError(
                "trusted PASS failure class is not null"
            )
        return own_sha
    if result.get("status") == "blocked":
        if (
            result.get("failure_class") != "acquisition_failure"
            or result.get("receipts") is not None
        ):
            raise EbriskRiskConfigReceiptsActionError(
                "trusted blocked result is not atomic"
            )
        return own_sha
    raise EbriskRiskConfigReceiptsActionError("trusted result has non-terminal status")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    _require_production_authority()
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskRiskConfigReceiptsActionError("invalid execution SHA")
    own_sha = _validated_terminal_result_sha(body)
    return own_sha is not None and own_sha == execution_sha


def _has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    fetcher: Callable[..., list[dict[str, Any]]],
    max_pages: int,
) -> bool:
    try:
        comments = fetcher(
            repository,
            token,
            issue=CONTROL_ISSUE,
            max_pages=max_pages,
        )
    except LedgerError as exc:
        raise EbriskRiskConfigReceiptsActionError("result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(
            comment.get("body"), execution_sha=execution_sha
        ):
            return True
    return False


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    _require_production_authority()
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskRiskConfigReceiptsActionError("invalid execution SHA")
    return _has_terminal_result(
        repository=repository,
        token=token,
        execution_sha=execution_sha,
        fetcher=_CANONICAL_FETCH_REPOSITORY_COMMENTS,
        max_pages=MAX_LEDGER_PAGES,
    )


def _run_one(
    worker: Callable[[], dict[str, Any]], *, repository_path: str, operation_id: str
) -> dict[str, Any]:
    return _validate_receipt(
        worker(), repository_path=repository_path, operation_id=operation_id
    )


def _run_receipts(
    *,
    execution_sha: str,
    targets: tuple[tuple[str, str, Callable[[], dict[str, Any]]], ...],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskRiskConfigReceiptsActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    receipts: list[dict[str, Any]] = []
    try:
        for repository_path, operation_id, worker in targets:
            receipt = _run_one(
                worker, repository_path=repository_path, operation_id=operation_id
            )
            receipts.append(
                {
                    "repository_path": repository_path,
                    "operation_id": operation_id,
                    **_bounded_receipt(receipt),
                }
            )
    except (EfehrAcquisitionError, EbriskRiskConfigReceiptsActionError):
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipts": None,
            }
        )
        return result
    result.update({"status": "pass", "failure_class": None, "receipts": receipts})
    return result


def run_receipts(*, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()
    return _run_receipts(
        execution_sha=execution_sha,
        targets=_CANONICAL_RECEIPT_TARGETS,
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
        raise EbriskRiskConfigReceiptsActionError("--output is required for execution")
    result = run_receipts(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
