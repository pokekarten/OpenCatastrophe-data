# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the frozen project-278 site manual receipt.

A PASS proves byte identity only. PDF interpretation, CRS/datum/EPSG semantics,
historical generator invocation, missingness, site compatibility, publication,
and model-use authority remain separate fail-closed gates under #291/#287.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_project278_manual_receipt import acquire_project278_manual_receipt
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-project278-manual-receipt-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-project278-manual-receipt-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-project278-manual-receipt-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-project278-manual-receipt-result-v1"
ACTION = "esrm20_project278_manual_receipt"
CONTROL_ISSUE = 291
DATASET_ID = "efehr.esrm20.sitemodel-source"
PROJECT_ID = 278
PROJECT_PATH = "efehr/esrm20_sitemodel"
COMMIT_SHA = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
REPOSITORY_PATH = "ExposureReadme.pdf"
WORKER_OPERATION_ID = "esrm20-project278-exposure-manual-receipt-v1"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_TERMINAL_UTF8_BYTES = 55_000

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
_AUTHORITY_FALSE_FIELDS = (
    "pdf_content_interpreted",
    "crs_coordinate_semantics_verified",
    "generator_invocation_verified",
    "missingness_semantics_verified",
    "site_model_compatibility_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)
_MANUAL_IDENTITY_EXACT = (
    ("project_id", PROJECT_ID),
    ("project_path", PROJECT_PATH),
    ("commit_sha", COMMIT_SHA),
    ("repository_path", REPOSITORY_PATH),
    ("worker_operation_id", WORKER_OPERATION_ID),
)
_MANUAL_IDENTITY_FIELDS = frozenset(field for field, _ in _MANUAL_IDENTITY_EXACT)


class Project278ManualReceiptActionError(RuntimeError):
    """Fail-closed trusted action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise Project278ManualReceiptActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise Project278ManualReceiptActionError(f"non-finite JSON constant: {value}")


def _load_json(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Project278ManualReceiptActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Project278ManualReceiptActionError(f"invalid {label} JSON") from exc


def _validate_manual_identity(identity: object) -> dict[str, Any]:
    if type(identity) is not dict or set(identity) != _MANUAL_IDENTITY_FIELDS:
        raise Project278ManualReceiptActionError("trusted manual result identity fields drifted")
    for field, expected in _MANUAL_IDENTITY_EXACT:
        observed = identity.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Project278ManualReceiptActionError(
                f"trusted manual result identity drifted at {field}"
            )
    return identity


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Project278ManualReceiptActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise Project278ManualReceiptActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Project278ManualReceiptActionError("invalid manual receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Project278ManualReceiptActionError("manual receipt request envelope is not canonical")
    request = _load_json(after.strip(), label="manual receipt request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Project278ManualReceiptActionError("manual receipt request fields drifted")
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
            raise Project278ManualReceiptActionError(f"manual receipt request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or not _SAFE_REQUESTER_RE.fullmatch(requester):
        raise Project278ManualReceiptActionError("invalid requester identity")
    return request


def _validate_receipt(receipt: object) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise Project278ManualReceiptActionError("manual worker returned a non-object receipt")
    exact = (
        ("schema_version", "oc-efehr-trusted-acquisition-v1"),
        ("operation_id", WORKER_OPERATION_ID),
        ("source_issue", CONTROL_ISSUE),
        ("dataset_id", DATASET_ID),
        ("provider_host", "gitlab.seismo.ethz.ch"),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("repository_path", REPOSITORY_PATH),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    )
    for field, expected in exact:
        observed = receipt.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Project278ManualReceiptActionError(f"manual receipt identity drifted at {field}")
    byte_count = receipt.get("byte_count")
    if type(byte_count) is not int or byte_count <= 0:
        raise Project278ManualReceiptActionError("manual receipt byte count is invalid")
    digest = receipt.get("sha256")
    if type(digest) is not str or not _DIGEST_RE.fullmatch(digest):
        raise Project278ManualReceiptActionError("manual receipt SHA-256 is invalid")
    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not retrieved_at:
        raise Project278ManualReceiptActionError("manual receipt retrieval time is invalid")
    for field, value in receipt.items():
        if field.endswith("_authorized") or field.endswith("_persisted"):
            if value is not False:
                raise Project278ManualReceiptActionError(f"manual receipt widened authority at {field}")
    return receipt


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "manual_identity": dict(_MANUAL_IDENTITY_EXACT),
    }
    result.update({field: False for field in _AUTHORITY_FALSE_FIELDS})
    return result


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise Project278ManualReceiptActionError("trusted manual result is not UTF-8 encodable") from exc
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise Project278ManualReceiptActionError("trusted manual result exceeds byte bound")
    if body.count(RESULT_MARKER) != 1:
        raise Project278ManualReceiptActionError("trusted manual result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Project278ManualReceiptActionError("trusted manual result envelope is malformed")
    result = _load_json(after.strip(), label="trusted manual result")
    if type(result) is not dict:
        raise Project278ManualReceiptActionError("trusted manual result is not an object")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", CONTROL_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("execution_sha", execution_sha),
    ) + tuple((field, False) for field in _AUTHORITY_FALSE_FIELDS)
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Project278ManualReceiptActionError(f"trusted manual result drifted at {field}")
    _validate_manual_identity(result.get("manual_identity"))
    status = result.get("status")
    if status == "pass":
        receipt = result.get("receipt")
        if type(receipt) is not dict:
            raise Project278ManualReceiptActionError("trusted PASS lacks bounded receipt")
        byte_count = receipt.get("byte_count")
        digest = receipt.get("sha256")
        if type(byte_count) is not int or byte_count <= 0 or type(digest) is not str or not _DIGEST_RE.fullmatch(digest):
            raise Project278ManualReceiptActionError("trusted PASS receipt is invalid")
        return True
    if status == "blocked":
        if result.get("failure_class") != "acquisition_failure" or result.get("receipt") is not None:
            raise Project278ManualReceiptActionError("trusted blocked result is not safely bounded")
        return True
    raise Project278ManualReceiptActionError("trusted manual result has non-terminal status")


def has_terminal_manual_result(*, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20) -> bool:
    """Fail closed unless the complete bounded Issue #291 ledger is known."""
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise Project278ManualReceiptActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Project278ManualReceiptActionError("manual result ledger is incomplete") from exc
    match_seen = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            match_seen = True
    return match_seen


def run_manual_receipt(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise Project278ManualReceiptActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        receipt = _validate_receipt(acquire_project278_manual_receipt())
    except (EfehrAcquisitionError, Project278ManualReceiptActionError):
        result.update({"status": "blocked", "failure_class": "acquisition_failure", "receipt": None})
        return result
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "receipt": {
                "retrieved_at": receipt["retrieved_at"],
                "byte_count": receipt["byte_count"],
                "sha256": receipt["sha256"],
                "content_type": receipt.get("content_type"),
                "etag": receipt.get("etag"),
            },
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
        parser.error("--output is required for execution")
    result = run_manual_receipt(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
