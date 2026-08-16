# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the two source-derived ESRM20 hazard logic trees."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from scripts.acquire_efehr_esrm20_event_hazard_receipts import (
        COMMIT_SHA,
        DATASET_ID,
        GSIM_LOGIC_TREE_OPERATION_ID,
        GSIM_LOGIC_TREE_REPOSITORY_PATH,
        PROJECT_ID,
        SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
        SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
        acquire_event_hazard_gsim_logic_tree_receipt,
        acquire_event_hazard_source_model_logic_tree_receipt,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from acquire_efehr_esrm20_event_hazard_receipts import (
        COMMIT_SHA,
        DATASET_ID,
        GSIM_LOGIC_TREE_OPERATION_ID,
        GSIM_LOGIC_TREE_REPOSITORY_PATH,
        PROJECT_ID,
        SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
        SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
        acquire_event_hazard_gsim_logic_tree_receipt,
        acquire_event_hazard_source_model_logic_tree_receipt,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-hazard-logic-tree-receipts-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-hazard-logic-tree-receipts-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-hazard-logic-tree-receipts-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-hazard-logic-tree-receipts-result-v1"
ACTION = "esrm20_hazard_logic_tree_receipts"
CONTROL_ISSUE = 476
SOURCE_SCIENCE_ISSUE = 281
PROJECT_PATH = "efehr/esrm20"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}


class HazardLogicTreeReceiptsActionError(RuntimeError):
    """Fail-closed hazard receipt action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise HazardLogicTreeReceiptsActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise HazardLogicTreeReceiptsActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise HazardLogicTreeReceiptsActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardLogicTreeReceiptsActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise HazardLogicTreeReceiptsActionError("invalid hazard receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise HazardLogicTreeReceiptsActionError("hazard receipt request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except HazardLogicTreeReceiptsActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HazardLogicTreeReceiptsActionError("invalid hazard receipt request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise HazardLogicTreeReceiptsActionError("hazard receipt request fields drifted")
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
            raise HazardLogicTreeReceiptsActionError(f"hazard receipt request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise HazardLogicTreeReceiptsActionError("invalid requester identity")
    return request


def _validate_receipt(
    receipt: object, *, repository_path: str, operation_id: str
) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise HazardLogicTreeReceiptsActionError("worker returned a non-object receipt")
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
            raise HazardLogicTreeReceiptsActionError(f"hazard receipt drifted at {field}")
    byte_count = receipt.get("byte_count")
    if type(byte_count) is not int or isinstance(byte_count, bool) or byte_count <= 0:
        raise HazardLogicTreeReceiptsActionError("hazard receipt byte count is invalid")
    digest = receipt.get("sha256")
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise HazardLogicTreeReceiptsActionError("hazard receipt SHA-256 is invalid")
    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not retrieved_at:
        raise HazardLogicTreeReceiptsActionError("hazard receipt retrieval time is invalid")
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
        "dependency_content_interpreted": False,
        "transitive_dependency_closure_verified": False,
        "runtime_compatibility_verified": False,
        "model_use_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _validate_receipt_row(row: object, *, path: str, operation_id: str) -> None:
    if type(row) is not dict or set(row) != {
        "repository_path",
        "operation_id",
        "retrieved_at",
        "byte_count",
        "sha256",
        "content_type",
        "etag",
    }:
        raise HazardLogicTreeReceiptsActionError("bounded hazard receipt row fields drifted")
    if row.get("repository_path") != path or row.get("operation_id") != operation_id:
        raise HazardLogicTreeReceiptsActionError("bounded hazard receipt row identity drifted")
    byte_count = row.get("byte_count")
    digest = row.get("sha256")
    if (
        type(byte_count) is not int
        or isinstance(byte_count, bool)
        or byte_count <= 0
        or type(digest) is not str
        or _DIGEST_RE.fullmatch(digest) is None
    ):
        raise HazardLogicTreeReceiptsActionError("bounded hazard receipt row is invalid")


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise HazardLogicTreeReceiptsActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise HazardLogicTreeReceiptsActionError("trusted result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except HazardLogicTreeReceiptsActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HazardLogicTreeReceiptsActionError("trusted result JSON is malformed") from exc
    if type(result) is not dict:
        raise HazardLogicTreeReceiptsActionError("trusted result is not an object")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise HazardLogicTreeReceiptsActionError(f"trusted result drifted at {field}")
    if result.get("status") == "pass":
        rows = result.get("receipts")
        if type(rows) is not list or len(rows) != 2:
            raise HazardLogicTreeReceiptsActionError("trusted PASS must contain two receipts")
        expected = (
            (GSIM_LOGIC_TREE_REPOSITORY_PATH, GSIM_LOGIC_TREE_OPERATION_ID),
            (SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH, SOURCE_MODEL_LOGIC_TREE_OPERATION_ID),
        )
        for row, (path, operation_id) in zip(rows, expected):
            _validate_receipt_row(row, path=path, operation_id=operation_id)
        return True
    if result.get("status") == "blocked":
        if result.get("failure_class") != "acquisition_failure" or result.get("receipts") is not None:
            raise HazardLogicTreeReceiptsActionError("trusted blocked result is not atomic")
        return True
    raise HazardLogicTreeReceiptsActionError("trusted result has non-terminal status")


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardLogicTreeReceiptsActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise HazardLogicTreeReceiptsActionError("result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def run_receipts(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardLogicTreeReceiptsActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        gsim = _validate_receipt(
            acquire_event_hazard_gsim_logic_tree_receipt(),
            repository_path=GSIM_LOGIC_TREE_REPOSITORY_PATH,
            operation_id=GSIM_LOGIC_TREE_OPERATION_ID,
        )
        source = _validate_receipt(
            acquire_event_hazard_source_model_logic_tree_receipt(),
            repository_path=SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
            operation_id=SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
        )
    except (EfehrAcquisitionError, HazardLogicTreeReceiptsActionError):
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "receipts": None})
        return result
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "receipts": [
                {
                    "repository_path": GSIM_LOGIC_TREE_REPOSITORY_PATH,
                    "operation_id": GSIM_LOGIC_TREE_OPERATION_ID,
                    **_bounded_receipt(gsim),
                },
                {
                    "repository_path": SOURCE_MODEL_LOGIC_TREE_REPOSITORY_PATH,
                    "operation_id": SOURCE_MODEL_LOGIC_TREE_OPERATION_ID,
                    **_bounded_receipt(source),
                },
            ],
        }
    )
    return result


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
        raise HazardLogicTreeReceiptsActionError("--output is required for execution")
    result = run_receipts(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
