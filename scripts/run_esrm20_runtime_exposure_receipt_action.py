# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the frozen ESRM20 Kosovo runtime exposure XML."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.acquire_efehr_esrm20_runtime_exposure_receipt import (
        acquire_runtime_exposure_receipt,
    )
    from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from acquire_efehr_esrm20_runtime_exposure_receipt import (
        acquire_runtime_exposure_receipt,
    )
    from acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-runtime-exposure-receipt-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-runtime-exposure-receipt-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-runtime-exposure-receipt-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-runtime-exposure-receipt-result-v1"
ACTION = "esrm20_runtime_exposure_receipt"
SOURCE_ISSUE = 282
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Kosovo.xml"
WORKER_OPERATION_ID = "esrm20-v1-kosovo-runtime-exposure-xml-v1"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 20_000
MAX_RECEIPT_BYTES = 64 * 1024 * 1024

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
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
    "runtime_exposure_identity",
    "status",
    "failure_class",
    "receipt",
    "xml_content_interpreted",
    "exact_kosovo_exposure_selected",
    "value_structural_wiring_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_IDENTITY_FIELDS = {
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "worker_operation_id",
}
_RECEIPT_FIELDS = {"retrieved_at", "byte_count", "sha256", "content_type", "etag"}


class RuntimeExposureReceiptActionError(RuntimeError):
    """Fail-closed trusted action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeExposureReceiptActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise RuntimeExposureReceiptActionError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise RuntimeExposureReceiptActionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except RuntimeExposureReceiptActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeExposureReceiptActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str, *, label: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RuntimeExposureReceiptActionError(f"{label} is not UTF-8 encodable") from exc


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise RuntimeExposureReceiptActionError("wrong runtime exposure issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureReceiptActionError("invalid execution SHA")
    if type(body) is not str:
        raise RuntimeExposureReceiptActionError("runtime exposure request is not text")
    if _utf8_size(body, label="runtime exposure request") > MAX_REQUEST_UTF8_BYTES:
        raise RuntimeExposureReceiptActionError("runtime exposure request exceeds limit")
    if body.count(REQUEST_MARKER) != 1:
        raise RuntimeExposureReceiptActionError("invalid runtime exposure request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuntimeExposureReceiptActionError("runtime exposure request envelope is not canonical")
    request = _strict_loads(after.strip(), label="runtime exposure request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise RuntimeExposureReceiptActionError("runtime exposure request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise RuntimeExposureReceiptActionError(
                f"runtime exposure request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise RuntimeExposureReceiptActionError("invalid requester identity")
    return request


def _validate_receipt(receipt: object) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise RuntimeExposureReceiptActionError("worker returned a non-object receipt")
    exact = (
        ("schema_version", "oc-efehr-trusted-acquisition-v1"),
        ("operation_id", WORKER_OPERATION_ID),
        ("source_issue", SOURCE_ISSUE),
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
            raise RuntimeExposureReceiptActionError(
                f"runtime exposure receipt identity drifted at {field}"
            )
    byte_count = receipt.get("byte_count")
    if (
        type(byte_count) is not int
        or isinstance(byte_count, bool)
        or not (1 <= byte_count <= MAX_RECEIPT_BYTES)
    ):
        raise RuntimeExposureReceiptActionError("runtime exposure byte count is invalid")
    digest = receipt.get("sha256")
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        raise RuntimeExposureReceiptActionError("runtime exposure SHA-256 is invalid")
    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not retrieved_at:
        raise RuntimeExposureReceiptActionError("runtime exposure retrieval time is invalid")
    for field, value in receipt.items():
        if field.endswith("_authorized") or field.endswith("_persisted"):
            if value is not False:
                raise RuntimeExposureReceiptActionError(
                    f"runtime exposure receipt widened authority at {field}"
                )
    return receipt


def _identity() -> dict[str, Any]:
    return {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "worker_operation_id": WORKER_OPERATION_ID,
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "runtime_exposure_identity": _identity(),
        "xml_content_interpreted": False,
        "exact_kosovo_exposure_selected": False,
        "value_structural_wiring_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise RuntimeExposureReceiptActionError("trusted runtime exposure result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureReceiptActionError("trusted result execution SHA is invalid")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("runtime_exposure_identity", _identity()),
        ("xml_content_interpreted", False),
        ("exact_kosovo_exposure_selected", False),
        ("value_structural_wiring_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise RuntimeExposureReceiptActionError(
                f"trusted runtime exposure result drifted at {field}"
            )
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise RuntimeExposureReceiptActionError("trusted PASS has a failure class")
        receipt = result.get("receipt")
        if type(receipt) is not dict or set(receipt) != _RECEIPT_FIELDS:
            raise RuntimeExposureReceiptActionError("trusted PASS receipt fields drifted")
        byte_count = receipt.get("byte_count")
        digest = receipt.get("sha256")
        retrieved_at = receipt.get("retrieved_at")
        if (
            type(byte_count) is not int
            or isinstance(byte_count, bool)
            or not (1 <= byte_count <= MAX_RECEIPT_BYTES)
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
            or type(retrieved_at) is not str
            or not retrieved_at
        ):
            raise RuntimeExposureReceiptActionError("trusted PASS receipt is invalid")
        for field in ("content_type", "etag"):
            value = receipt.get(field)
            if value is not None and type(value) is not str:
                raise RuntimeExposureReceiptActionError(
                    f"trusted PASS receipt {field} is invalid"
                )
        return execution_sha
    if status == "blocked":
        if (
            result.get("failure_class") != "acquisition_failure"
            or result.get("receipt") is not None
        ):
            raise RuntimeExposureReceiptActionError(
                "trusted blocked result is not safely bounded"
            )
        return execution_sha
    raise RuntimeExposureReceiptActionError("trusted result has non-terminal status")


def parse_terminal_result(body: object) -> str | None:
    """Validate a trusted terminal under its own SHA and return that SHA."""
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body, label="runtime exposure result") > MAX_TERMINAL_UTF8_BYTES:
        raise RuntimeExposureReceiptActionError("trusted result exceeds limit")
    if body.count(RESULT_MARKER) != 1:
        raise RuntimeExposureReceiptActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuntimeExposureReceiptActionError("trusted result envelope is malformed")
    result = _strict_loads(after.strip(), label="runtime exposure result")
    return _validate_terminal_result(result)


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = MAX_LEDGER_PAGES,
) -> bool:
    """Validate every trusted terminal, deduplicating only the exact execution SHA."""
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureReceiptActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise RuntimeExposureReceiptActionError("runtime exposure ledger is incomplete") from exc
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


def run_receipt(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureReceiptActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        receipt = _validate_receipt(acquire_runtime_exposure_receipt())
    except (EfehrAcquisitionError, RuntimeExposureReceiptActionError):
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipt": None,
            }
        )
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
    _validate_terminal_result(result)
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
    result = run_receipt(execution_sha=args.execution_sha)
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    terminal = RESULT_MARKER + "\n" + encoded
    if _utf8_size(terminal, label="runtime exposure result") > MAX_TERMINAL_UTF8_BYTES:
        raise RuntimeExposureReceiptActionError("runtime exposure result exceeds limit")
    Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
