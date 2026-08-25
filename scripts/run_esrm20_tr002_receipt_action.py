# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main receipt action for the immutable ESRM20 TR002 PDF.

The target is fixed to the ESRM20 v1.0 release commit and exact technical-report
path. A PASS proves only an exact bounded byte receipt for that provider object.
Provider bytes are streamed, hashed and discarded; report interpretation,
component semantics, publication and model-use authority remain separate gates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-tr002-receipt-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-tr002-receipt-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-tr002-receipt-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-tr002-receipt-result-v1"
ACTION = "esrm20_tr002_release_pdf_receipt"
CONTROL_ISSUE = 596
SOURCE_SCIENCE_ISSUE = 281
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Documentation/EFEHR_TR002_ESRM20.pdf"
WORKER_OPERATION_ID = "esrm20-tr002-release-pdf-v1"
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_RESULT_UTF8_BYTES = 55_000
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

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic


class Tr002ReceiptActionError(RuntimeError):
    """Fail-closed immutable TR002 receipt action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise Tr002ReceiptActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise Tr002ReceiptActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Tr002ReceiptActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ReceiptActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Tr002ReceiptActionError("invalid TR002 receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Tr002ReceiptActionError("TR002 receipt request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Tr002ReceiptActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Tr002ReceiptActionError("invalid TR002 receipt request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Tr002ReceiptActionError("TR002 receipt request fields drifted")
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
            raise Tr002ReceiptActionError(f"TR002 receipt request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Tr002ReceiptActionError("invalid requester identity")
    return request


class _PdfMagicStream:
    """Reject a 200 response that is not actually a PDF while preserving streaming."""

    def __init__(self, stream: Any):
        self._stream = stream
        self._first = True

    def read(self, size: int = -1) -> bytes:
        chunk = self._stream.read(size)
        if self._first:
            self._first = False
            if type(chunk) is bytes and chunk and not chunk.startswith(b"%PDF-"):
                raise EfehrReceiptError("TR002 provider payload lacks PDF magic")
        return chunk


def _acquire_tr002_receipt(*, opener: Any, now: Any, monotonic: Any) -> dict[str, Any]:
    """Injectable exact-target acquisition helper for deterministic tests."""
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        target = validate_target(
            source_issue=SOURCE_SCIENCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError("trusted TR002 target is invalid") from exc

    url = raw_file_api_url(target)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/pdf,application/octet-stream;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            _declared_length(response, MAX_PDF_BYTES)
            retrieved_at = now()
            try:
                core = receipt_from_stream(
                    target,
                    _PdfMagicStream(
                        _DeadlineStream(response, deadline=deadline, monotonic=monotonic)
                    ),
                    final_url=url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=MAX_PDF_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError("TR002 receipt failed closed") from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(f"TR002 retrieval failed: {type(exc).__name__}") from exc

    result = dict(core)
    result["schema_version"] = "oc-efehr-trusted-acquisition-v1"
    result["operation_id"] = WORKER_OPERATION_ID
    return {
        "schema_version": result["schema_version"],
        "operation_id": result["operation_id"],
        "source_issue": result["source_issue"],
        "dataset_id": result["dataset_id"],
        "provider_host": result["provider_host"],
        "project_id": result["project_id"],
        "project_path": result["project_path"],
        "commit_sha": result["commit_sha"],
        "repository_path": result["repository_path"],
        "requested_url": result["requested_url"],
        "final_url": result["final_url"],
        "retrieved_at": result["retrieved_at"],
        "byte_count": result["byte_count"],
        "sha256": result["sha256"],
        "content_type": result["content_type"],
        "etag": result["etag"],
        "external_bytes_persisted": result["external_bytes_persisted"],
        "publication_authorized": result["publication_authorized"],
    }


def acquire_tr002_receipt() -> dict[str, Any]:
    """Run the one fixed production receipt with no caller-selectable target."""
    if _open_fixed is not _CANONICAL_OPEN_FIXED or time.monotonic is not _CANONICAL_MONOTONIC:
        raise EfehrAcquisitionError("TR002 production transport identity drifted")
    return _acquire_tr002_receipt(
        opener=_CANONICAL_OPEN_FIXED,
        now=utc_now,
        monotonic=_CANONICAL_MONOTONIC,
    )


def _validate_receipt(receipt: object) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise Tr002ReceiptActionError("worker returned a non-object receipt")
    exact = (
        ("schema_version", "oc-efehr-trusted-acquisition-v1"),
        ("operation_id", WORKER_OPERATION_ID),
        ("source_issue", SOURCE_SCIENCE_ISSUE),
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
            raise Tr002ReceiptActionError(f"receipt identity drifted at {field}")
    byte_count = receipt.get("byte_count")
    if type(byte_count) is not int or isinstance(byte_count, bool) or not (1 <= byte_count <= MAX_PDF_BYTES):
        raise Tr002ReceiptActionError("receipt byte count is invalid")
    digest = receipt.get("sha256")
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise Tr002ReceiptActionError("receipt SHA-256 is invalid")
    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not retrieved_at:
        raise Tr002ReceiptActionError("receipt retrieval time is invalid")
    return receipt


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "artifact_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
            "worker_operation_id": WORKER_OPERATION_ID,
        },
        "byte_identity_verified": False,
        "report_content_verified": False,
        "component_semantics_verified": False,
        "scientific_applicability_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise Tr002ReceiptActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Tr002ReceiptActionError("trusted result envelope is malformed")
    payload = after.strip()
    try:
        payload_size = len(payload.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise Tr002ReceiptActionError("trusted result is not valid UTF-8") from exc
    if payload_size > MAX_RESULT_UTF8_BYTES:
        raise Tr002ReceiptActionError("trusted result exceeds publication limit")
    try:
        result = json.loads(payload, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except Tr002ReceiptActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Tr002ReceiptActionError("trusted result JSON is malformed") from exc
    if type(result) is not dict:
        raise Tr002ReceiptActionError("trusted result is not an object")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Tr002ReceiptActionError(f"trusted result drifted at {field}")
    if result.get("status") == "pass":
        receipt = result.get("receipt")
        if type(receipt) is not dict:
            raise Tr002ReceiptActionError("trusted PASS lacks receipt")
        byte_count = receipt.get("byte_count")
        digest = receipt.get("sha256")
        if (
            type(byte_count) is not int
            or isinstance(byte_count, bool)
            or not (1 <= byte_count <= MAX_PDF_BYTES)
            or type(digest) is not str
            or _DIGEST_RE.fullmatch(digest) is None
        ):
            raise Tr002ReceiptActionError("trusted PASS receipt is invalid")
        return True
    if result.get("status") == "blocked":
        if result.get("failure_class") != "acquisition_failure" or result.get("receipt") is not None:
            raise Tr002ReceiptActionError("trusted blocked result is not safely bounded")
        return True
    raise Tr002ReceiptActionError("trusted result has non-terminal status")


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    """Fail closed unless the complete bounded Issue #596 ledger is known."""
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ReceiptActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Tr002ReceiptActionError("result ledger is incomplete") from exc
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def run_receipt(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Tr002ReceiptActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        receipt = _validate_receipt(acquire_tr002_receipt())
    except (EfehrAcquisitionError, Tr002ReceiptActionError):
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
        raise Tr002ReceiptActionError("--output is required for execution")
    result = run_receipt(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
