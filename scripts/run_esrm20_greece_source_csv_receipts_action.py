# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the three frozen Greece source CSV receipts."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_esrm20_greece_source_csv_receipts import (
    COMMIT_SHA,
    DATASET_ID,
    PROJECT_ID,
    PROJECT_PATH,
    RELEASE_TAG,
    TARGETS,
    GreeceSourceCsvReceiptsError,
    acquire_receipts,
    validate_receipts,
)
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-source-csv-receipts-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-source-csv-receipts-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-source-csv-receipts-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-greece-source-csv-receipts-result-v1"
ACTION = "esrm20_greece_source_csv_receipts"
CONTROL_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_TERMINAL_UTF8_BYTES = 55_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_FALSE_FIELDS = (
    "provider_file_content_profiled",
    "source_runtime_lineage_verified",
    "replacement_cost_semantics_verified",
    "taxonomy_semantics_verified",
    "crs_semantics_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)


class GreeceSourceCsvReceiptsActionError(RuntimeError):
    """Fail-closed trusted action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GreeceSourceCsvReceiptsActionError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise GreeceSourceCsvReceiptsActionError(f"non-finite JSON constant: {value}")


def _load_json(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except GreeceSourceCsvReceiptsActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceSourceCsvReceiptsActionError(f"invalid {label} JSON") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise GreeceSourceCsvReceiptsActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceSourceCsvReceiptsActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise GreeceSourceCsvReceiptsActionError("invalid Greece receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceSourceCsvReceiptsActionError("Greece receipt request envelope is not canonical")
    request = _load_json(after.strip(), label="Greece receipt request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceSourceCsvReceiptsActionError("Greece receipt request fields drifted")
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
            raise GreeceSourceCsvReceiptsActionError(f"Greece receipt request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _SAFE_REQUESTER_RE.fullmatch(requester) is None:
        raise GreeceSourceCsvReceiptsActionError("invalid requester identity")
    return request


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
    }
    result.update({field: False for field in _FALSE_FIELDS})
    return result


def _validate_terminal_receipts(receipts: object) -> list[dict[str, Any]]:
    try:
        validated = validate_receipts(receipts)
    except GreeceSourceCsvReceiptsError as exc:
        raise GreeceSourceCsvReceiptsActionError("trusted Greece receipt bundle drifted") from exc
    if len(validated) != 3:
        raise GreeceSourceCsvReceiptsActionError("trusted Greece receipt cardinality drifted")
    for receipt, target in zip(validated, TARGETS, strict=True):
        path, blob_sha1, tree_bytes = target
        if receipt["repository_path"] != path or receipt["git_blob_sha1"] != blob_sha1:
            raise GreeceSourceCsvReceiptsActionError("trusted Greece receipt target identity drifted")
        if type(receipt["byte_count"]) is not int or receipt["byte_count"] != tree_bytes:
            raise GreeceSourceCsvReceiptsActionError("trusted Greece receipt byte count drifted")
        if type(receipt["sha256"]) is not str or _DIGEST_RE.fullmatch(receipt["sha256"]) is None:
            raise GreeceSourceCsvReceiptsActionError("trusted Greece receipt digest drifted")
    return validated


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise GreeceSourceCsvReceiptsActionError("trusted Greece result is not UTF-8 encodable") from exc
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise GreeceSourceCsvReceiptsActionError("trusted Greece result exceeds byte bound")
    if body.count(RESULT_MARKER) != 1:
        raise GreeceSourceCsvReceiptsActionError("trusted Greece result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceSourceCsvReceiptsActionError("trusted Greece result envelope is malformed")
    result = _load_json(after.strip(), label="trusted Greece result")
    if type(result) is not dict:
        raise GreeceSourceCsvReceiptsActionError("trusted Greece result is not an object")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", CONTROL_ISSUE),
        ("parent_consumer_issue", PARENT_CONSUMER_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("execution_sha", execution_sha),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("release_tag", RELEASE_TAG),
        ("commit_sha", COMMIT_SHA),
    ) + tuple((field, False) for field in _FALSE_FIELDS)
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceSourceCsvReceiptsActionError(f"trusted Greece result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        _validate_terminal_receipts(result.get("receipts"))
        return True
    if status == "blocked":
        if result.get("failure_class") != "acquisition_failure" or result.get("receipts") is not None:
            raise GreeceSourceCsvReceiptsActionError("trusted Greece blocked result is not safely bounded")
        return True
    raise GreeceSourceCsvReceiptsActionError("trusted Greece result has non-terminal status")


def has_terminal_result(*, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceSourceCsvReceiptsActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceSourceCsvReceiptsActionError("Greece receipt result ledger is incomplete") from exc
    match_seen = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            match_seen = True
    return match_seen


def run_receipts(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceSourceCsvReceiptsActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        receipts = _validate_terminal_receipts(acquire_receipts())
    except (EfehrAcquisitionError, GreeceSourceCsvReceiptsError, GreeceSourceCsvReceiptsActionError):
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "receipts": None})
        return result
    result.update({"status": "pass", "failure_class": None, "receipts": receipts})
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
        parser.error("--output is required for execution")
    result = run_receipts(execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
