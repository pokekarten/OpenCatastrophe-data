# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the exact ESHM20 Region-Main site profile."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_eshm20_site_model_profile as worker
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import acquire_eshm20_site_model_profile as worker
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-eshm20-site-model-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-eshm20-site-model-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-eshm20-site-model-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-eshm20-site-model-profile-result-v1"
ACTION = "eshm20_site_model_structural_profile"
CONTROL_ISSUE = 281
DATASET_ID = worker.DATASET_ID
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_RESULT_UTF8_BYTES = 55_000

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
_WORKER_FIELDS = {
    "schema_version",
    "source_issue",
    "control_issue",
    "receipt_source_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "byte_count",
    "sha256",
    "parser",
    "inventory_receipt_comment_id",
    "root_dependency_result_comment_id",
    "root_dependency_section",
    "root_dependency_option",
    "first_order_receipt_request_comment_id",
    "first_order_receipt_run_id",
    "first_order_receipt_execution_sha",
    "profile",
    "raw_rows_returned",
    "schema_interpretation_authorized",
    "crs_authorized",
    "coordinate_semantics_authorized",
    "site_response_authorized",
    "site_semantics_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_FALSE_CEILINGS = (
    "raw_rows_returned",
    "schema_interpretation_authorized",
    "crs_authorized",
    "coordinate_semantics_authorized",
    "site_response_authorized",
    "site_semantics_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)


class SiteModelProfileActionError(RuntimeError):
    """Fail-closed trusted ESHM20 site-profile action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise SiteModelProfileActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise SiteModelProfileActionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise SiteModelProfileActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteModelProfileActionError("invalid ESHM20 site-profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelProfileActionError("site-profile request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteModelProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelProfileActionError("invalid site-profile request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteModelProfileActionError("site-profile request fields drifted")
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
            raise SiteModelProfileActionError(f"site-profile request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise SiteModelProfileActionError("invalid requester identity")
    return request


def _require_exact(value: dict[str, Any], field: str, expected: object) -> None:
    observed = value.get(field)
    if type(observed) is not type(expected) or observed != expected:
        raise SiteModelProfileActionError(f"worker profile drifted at {field}")


def _validate_column(column: object, *, record_count: int) -> None:
    if type(column) is not dict or set(column) != {
        "name",
        "record_count",
        "empty_count",
        "nonempty_count",
        "distinct_count",
        "exact_value_set_sha256",
        "decimal_summary",
    }:
        raise SiteModelProfileActionError("worker column fields drifted")
    name = column["name"]
    if type(name) is not str or not name:
        raise SiteModelProfileActionError("worker column name is invalid")
    for field in ("record_count", "empty_count", "nonempty_count", "distinct_count"):
        value = column[field]
        if type(value) is not int or value < 0:
            raise SiteModelProfileActionError(f"worker column {field} is invalid")
    if column["record_count"] != record_count:
        raise SiteModelProfileActionError("worker column record count drifted")
    if column["empty_count"] + column["nonempty_count"] != record_count:
        raise SiteModelProfileActionError("worker column occupancy counts drifted")
    if column["distinct_count"] > record_count:
        raise SiteModelProfileActionError("worker column distinct count is impossible")
    digest = column["exact_value_set_sha256"]
    if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SiteModelProfileActionError("worker column value-set digest is invalid")
    decimal = column["decimal_summary"]
    if type(decimal) is not dict or set(decimal) != {
        "all_nonempty_decimal",
        "finite_decimal_count",
        "leading_or_trailing_whitespace_count",
    }:
        raise SiteModelProfileActionError("worker decimal summary drifted")
    if type(decimal["all_nonempty_decimal"]) is not bool:
        raise SiteModelProfileActionError("worker decimal boolean is invalid")
    for field in ("finite_decimal_count", "leading_or_trailing_whitespace_count"):
        value = decimal[field]
        if type(value) is not int or not 0 <= value <= column["nonempty_count"]:
            raise SiteModelProfileActionError(f"worker decimal {field} is invalid")


def _validate_worker_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _WORKER_FIELDS:
        raise SiteModelProfileActionError("worker profile fields drifted")
    exact = (
        ("schema_version", worker.SCHEMA_VERSION),
        ("source_issue", worker.SOURCE_ISSUE),
        ("control_issue", worker.CONTROL_ISSUE),
        ("receipt_source_issue", worker.RECEIPT_SOURCE_ISSUE),
        ("dataset_id", worker.DATASET_ID),
        ("project_id", worker.PROJECT_ID),
        ("project_path", worker.PROJECT_PATH),
        ("commit_sha", worker.COMMIT_SHA),
        ("repository_path", worker.REPOSITORY_PATH),
        ("byte_count", worker.EXPECTED_BYTE_COUNT),
        ("sha256", worker.EXPECTED_SHA256),
        ("inventory_receipt_comment_id", worker.INVENTORY_RECEIPT_COMMENT_ID),
        ("root_dependency_result_comment_id", worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID),
        ("root_dependency_section", worker.ROOT_DEPENDENCY_SECTION),
        ("root_dependency_option", worker.ROOT_DEPENDENCY_OPTION),
        ("first_order_receipt_request_comment_id", worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID),
        ("first_order_receipt_run_id", worker.FIRST_ORDER_RECEIPT_RUN_ID),
        ("first_order_receipt_execution_sha", worker.FIRST_ORDER_RECEIPT_EXECUTION_SHA),
    )
    for field, expected in exact:
        _require_exact(value, field, expected)
    for field in _FALSE_CEILINGS:
        _require_exact(value, field, False)

    parser = value["parser"]
    if type(parser) is not dict or set(parser) != {"encoding", "bom_present", "line_endings"}:
        raise SiteModelProfileActionError("worker parser metadata drifted")
    if type(parser["encoding"]) is not str or parser["encoding"] not in {"utf-8", "utf-8-sig"}:
        raise SiteModelProfileActionError("worker encoding is invalid")
    if type(parser["bom_present"]) is not bool:
        raise SiteModelProfileActionError("worker BOM flag is invalid")
    endings = parser["line_endings"]
    if type(endings) is not dict or set(endings) != {"crlf_count", "lf_count", "cr_count"}:
        raise SiteModelProfileActionError("worker line-ending profile drifted")
    if any(type(v) is not int or v < 0 for v in endings.values()):
        raise SiteModelProfileActionError("worker line-ending count is invalid")

    profile = value["profile"]
    if type(profile) is not dict or set(profile) != {"delimiter", "record_count", "header", "columns"}:
        raise SiteModelProfileActionError("worker CSV profile drifted")
    if profile["delimiter"] != "," or type(profile["delimiter"]) is not str:
        raise SiteModelProfileActionError("worker delimiter drifted")
    record_count = profile["record_count"]
    if type(record_count) is not int or record_count < 1:
        raise SiteModelProfileActionError("worker record count is invalid")
    header = profile["header"]
    columns = profile["columns"]
    if (
        type(header) is not list
        or type(columns) is not list
        or not header
        or len(header) != len(columns)
        or any(type(name) is not str or not name for name in header)
    ):
        raise SiteModelProfileActionError("worker header/column shape is invalid")
    if len(set(header)) != len(header):
        raise SiteModelProfileActionError("worker header names are duplicated")
    for name, column in zip(header, columns, strict=True):
        _validate_column(column, record_count=record_count)
        if column["name"] != name:
            raise SiteModelProfileActionError("worker column order/name drifted")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "schema_interpretation_authorized": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "site_semantics_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    expected_fields = set(base) | {"status", "failure_class", "profile"}
    if type(result) is not dict or set(result) != expected_fields:
        raise SiteModelProfileActionError("trusted site-profile result fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteModelProfileActionError(f"trusted site-profile result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise SiteModelProfileActionError("site-profile PASS cannot carry failure_class")
        _validate_worker_profile(result["profile"])
        return result
    if result["status"] == "blocked":
        if result["failure_class"] != "site_profile_failure" or result["profile"] is not None:
            raise SiteModelProfileActionError("blocked site-profile result is not safely bounded")
        return result
    raise SiteModelProfileActionError("trusted site-profile result has non-terminal status")


def _bounded_result_payload(after: str) -> str:
    payload = after.strip()
    try:
        payload_size = len(payload.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise SiteModelProfileActionError("trusted site-profile result is not valid UTF-8") from exc
    if payload_size > MAX_RESULT_UTF8_BYTES:
        raise SiteModelProfileActionError("trusted site-profile result exceeds publication limit")
    return payload


def _parse_trusted_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelProfileActionError("invalid execution SHA")
    if body.count(RESULT_MARKER) != 1:
        raise SiteModelProfileActionError("trusted site-profile result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelProfileActionError("trusted site-profile result envelope is malformed")
    payload = _bounded_result_payload(after)
    try:
        result = json.loads(payload, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteModelProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelProfileActionError("trusted site-profile result JSON is malformed") from exc
    if type(result) is not dict:
        raise SiteModelProfileActionError("trusted site-profile result fields drifted")
    result_execution_sha = result.get("execution_sha")
    if type(result_execution_sha) is not str or not _SHA_RE.fullmatch(result_execution_sha):
        raise SiteModelProfileActionError("trusted site-profile result execution SHA is invalid")
    _validate_terminal_result(result, execution_sha=result_execution_sha)
    return result_execution_sha == execution_sha


def has_terminal_site_profile_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fail closed unless the complete bounded Issue #281 ledger is known."""

    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SiteModelProfileActionError("site-profile result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteModelProfileActionError("site-profile ledger contains a non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if _parse_trusted_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def _run_site_profile(
    *,
    execution_sha: str,
    acquirer: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteModelProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquirer()
        payload = _validate_worker_profile(payload)
    except worker.Eshm20SiteModelProfileError:
        result.update({"status": "blocked", "failure_class": "site_profile_failure", "profile": None})
        return _validate_terminal_result(result, execution_sha=execution_sha)
    result.update({"status": "pass", "failure_class": None, "profile": payload})
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run_site_profile(*, execution_sha: str) -> dict[str, Any]:
    return _run_site_profile(execution_sha=execution_sha, acquirer=worker.acquire_eshm20_site_model_profile)


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
    result = run_site_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
