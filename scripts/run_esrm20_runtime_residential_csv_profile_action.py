# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for exact-byte runtime residential CSV profiling."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
    from scripts.profile_esrm20_runtime_residential_csv import (
        COMMIT_SHA,
        DATASET_ID,
        EXPECTED_BYTE_COUNT,
        EXPECTED_SHA256,
        PROJECT_ID,
        PROJECT_PATH,
        RECEIPT_COMMENT_ID,
        REPOSITORY_PATH,
        SOURCE_ISSUE,
        ByteIdentityMismatch,
        CsvContentProfileError,
        RuntimeResidentialCsvProfileError,
        profile_runtime_residential_csv,
    )
except ModuleNotFoundError:  # pragma: no cover
    from acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from prepare_agent_action_result import LedgerError, fetch_repository_comments
    from profile_esrm20_runtime_residential_csv import (
        COMMIT_SHA,
        DATASET_ID,
        EXPECTED_BYTE_COUNT,
        EXPECTED_SHA256,
        PROJECT_ID,
        PROJECT_PATH,
        RECEIPT_COMMENT_ID,
        REPOSITORY_PATH,
        SOURCE_ISSUE,
        ByteIdentityMismatch,
        CsvContentProfileError,
        RuntimeResidentialCsvProfileError,
        profile_runtime_residential_csv,
    )

REQUEST_MARKER = "<!-- oc-eq1-esrm20-runtime-residential-csv-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-runtime-residential-csv-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-runtime-residential-csv-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-runtime-residential-csv-profile-result-v1"
PROFILE_SCHEMA_VERSION = "oc-esrm20-exposure-content-profile-v0"
ACTION = "esrm20_runtime_residential_csv_profile"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 30_000

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "runtime_residential_identity",
    "status",
    "failure_class",
    "receipt",
    "profile",
    "csv_content_profiled",
    "taxonomy_semantics_verified",
    "crs_semantics_verified",
    "value_semantics_verified",
    "project186_equivalence_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_RECEIPT_FIELDS = {"retrieved_at", "byte_count", "sha256", "content_type", "etag"}


class RuntimeResidentialCsvProfileActionError(RuntimeError):
    """Fail-closed request/result/action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeResidentialCsvProfileActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise RuntimeResidentialCsvProfileActionError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise RuntimeResidentialCsvProfileActionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except RuntimeResidentialCsvProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeResidentialCsvProfileActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RuntimeResidentialCsvProfileActionError("text is not UTF-8 encodable") from exc


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise RuntimeResidentialCsvProfileActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeResidentialCsvProfileActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise RuntimeResidentialCsvProfileActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuntimeResidentialCsvProfileActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise RuntimeResidentialCsvProfileActionError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
        ("receipt_sha256", EXPECTED_SHA256),
    )
    for field, expected in exact:
        if request.get(field) != expected or type(request.get(field)) is not type(expected):
            raise RuntimeResidentialCsvProfileActionError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise RuntimeResidentialCsvProfileActionError("invalid requester")
    return request


def _identity() -> dict[str, Any]:
    return {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_byte_count": EXPECTED_BYTE_COUNT,
        "receipt_sha256": EXPECTED_SHA256,
    }


def _validate_identity(identity: object) -> None:
    expected_identity = _identity()
    if type(identity) is not dict or set(identity) != set(expected_identity):
        raise RuntimeResidentialCsvProfileActionError("runtime residential identity drifted")
    for field, expected in expected_identity.items():
        observed = identity.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise RuntimeResidentialCsvProfileActionError(
                f"runtime residential identity drifted at {field}"
            )


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "runtime_residential_identity": _identity(),
        "status": "blocked",
        "failure_class": "profile_failure",
        "receipt": None,
        "profile": None,
        "csv_content_profiled": False,
        "taxonomy_semantics_verified": False,
        "crs_semantics_verified": False,
        "value_semantics_verified": False,
        "project186_equivalence_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile(profile: object) -> dict[str, Any]:
    if type(profile) is not dict or set(profile) != {
        "schema_version",
        "parser",
        "record_count",
        "header",
        "columns",
        "raw_rows_returned",
        "external_bytes_persisted",
        "publication_authorized",
    }:
        raise RuntimeResidentialCsvProfileActionError("profile fields drifted")
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise RuntimeResidentialCsvProfileActionError("profile schema version drifted")
    parser = profile.get("parser")
    if type(parser) is not dict or set(parser) != {
        "encoding",
        "bom_present",
        "delimiter",
        "line_endings",
    }:
        raise RuntimeResidentialCsvProfileActionError("parser profile drifted")
    if parser.get("encoding") not in {"utf-8", "utf-8-sig"} or parser.get("delimiter") != ",":
        raise RuntimeResidentialCsvProfileActionError("parser identity drifted")
    if type(parser.get("bom_present")) is not bool:
        raise RuntimeResidentialCsvProfileActionError("BOM profile drifted")
    line_endings = parser.get("line_endings")
    if type(line_endings) is not dict or set(line_endings) != {"crlf_count", "lf_count", "cr_count"}:
        raise RuntimeResidentialCsvProfileActionError("line ending profile drifted")
    if any(type(line_endings[key]) is not int or line_endings[key] < 0 for key in line_endings):
        raise RuntimeResidentialCsvProfileActionError("invalid line ending count")
    record_count = profile.get("record_count")
    if type(record_count) is not int or isinstance(record_count, bool) or record_count < 1:
        raise RuntimeResidentialCsvProfileActionError("invalid record count")
    header = profile.get("header")
    columns = profile.get("columns")
    if (
        type(header) is not list
        or not header
        or any(type(item) is not str or not item for item in header)
        or len(set(header)) != len(header)
        or type(columns) is not list
        or len(columns) != len(header)
    ):
        raise RuntimeResidentialCsvProfileActionError("invalid header/column profile")
    for expected_name, column in zip(header, columns):
        if type(column) is not dict or set(column) != {
            "name",
            "record_count",
            "empty_count",
            "nonempty_count",
            "distinct_count",
            "exact_value_set_sha256",
            "decimal_summary",
        }:
            raise RuntimeResidentialCsvProfileActionError("column profile drifted")
        column_record_count = column.get("record_count")
        if (
            column.get("name") != expected_name
            or type(column_record_count) is not int
            or column_record_count != record_count
        ):
            raise RuntimeResidentialCsvProfileActionError("column identity drifted")
        for key in ("empty_count", "nonempty_count", "distinct_count"):
            if type(column.get(key)) is not int or column[key] < 0:
                raise RuntimeResidentialCsvProfileActionError("invalid column count")
        if column["empty_count"] + column["nonempty_count"] != record_count:
            raise RuntimeResidentialCsvProfileActionError("column counts do not close")
        digest = column.get("exact_value_set_sha256")
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise RuntimeResidentialCsvProfileActionError("invalid value-set digest")
        decimal = column.get("decimal_summary")
        if type(decimal) is not dict or set(decimal) != {
            "all_nonempty_decimal",
            "finite_decimal_count",
            "leading_or_trailing_whitespace_count",
        }:
            raise RuntimeResidentialCsvProfileActionError("decimal profile drifted")
        if type(decimal["all_nonempty_decimal"]) is not bool:
            raise RuntimeResidentialCsvProfileActionError("decimal flag drifted")
        for key in ("finite_decimal_count", "leading_or_trailing_whitespace_count"):
            if type(decimal[key]) is not int or decimal[key] < 0:
                raise RuntimeResidentialCsvProfileActionError("invalid decimal count")
    for field in ("raw_rows_returned", "external_bytes_persisted", "publication_authorized"):
        if profile.get(field) is not False:
            raise RuntimeResidentialCsvProfileActionError(f"profile widened {field}")
    return profile


def _validate_terminal_result(result: object) -> str:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise RuntimeResidentialCsvProfileActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeResidentialCsvProfileActionError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("taxonomy_semantics_verified", False),
        ("crs_semantics_verified", False),
        ("value_semantics_verified", False),
        ("project186_equivalence_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise RuntimeResidentialCsvProfileActionError(f"result {field} drifted")
    _validate_identity(result.get("runtime_residential_identity"))
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None or result.get("csv_content_profiled") is not True:
            raise RuntimeResidentialCsvProfileActionError("invalid PASS state")
        receipt = result.get("receipt")
        if type(receipt) is not dict or set(receipt) != _RECEIPT_FIELDS:
            raise RuntimeResidentialCsvProfileActionError("PASS receipt drifted")
        byte_count = receipt.get("byte_count")
        if (
            type(byte_count) is not int
            or byte_count != EXPECTED_BYTE_COUNT
            or receipt.get("sha256") != EXPECTED_SHA256
        ):
            raise RuntimeResidentialCsvProfileActionError("PASS byte identity drifted")
        if type(receipt.get("retrieved_at")) is not str or not receipt["retrieved_at"]:
            raise RuntimeResidentialCsvProfileActionError("PASS retrieval time invalid")
        for field in ("content_type", "etag"):
            if receipt.get(field) is not None and type(receipt[field]) is not str:
                raise RuntimeResidentialCsvProfileActionError("PASS metadata drifted")
        _validate_profile(result.get("profile"))
    elif status == "blocked":
        if result.get("failure_class") not in {
            "acquisition_failure",
            "byte_identity_mismatch",
            "csv_profile_failure",
            "profile_failure",
        }:
            raise RuntimeResidentialCsvProfileActionError("invalid blocked failure class")
        if (
            result.get("receipt") is not None
            or result.get("profile") is not None
            or result.get("csv_content_profiled") is not False
        ):
            raise RuntimeResidentialCsvProfileActionError("blocked result widened evidence")
    else:
        raise RuntimeResidentialCsvProfileActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise RuntimeResidentialCsvProfileActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuntimeResidentialCsvProfileActionError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = MAX_LEDGER_PAGES,
) -> bool:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeResidentialCsvProfileActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise RuntimeResidentialCsvProfileActionError("profile ledger is incomplete") from exc
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


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeResidentialCsvProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha)
    try:
        evidence = profile_runtime_residential_csv()
    except EfehrAcquisitionError:
        result["failure_class"] = "acquisition_failure"
        return result
    except ByteIdentityMismatch:
        result["failure_class"] = "byte_identity_mismatch"
        return result
    except CsvContentProfileError:
        result["failure_class"] = "csv_profile_failure"
        return result
    except RuntimeResidentialCsvProfileError:
        result["failure_class"] = "profile_failure"
        return result

    receipt = evidence.get("receipt")
    profile = evidence.get("profile")
    byte_count = receipt.get("byte_count") if type(receipt) is dict else None
    if (
        type(receipt) is not dict
        or type(byte_count) is not int
        or byte_count != EXPECTED_BYTE_COUNT
        or receipt.get("sha256") != EXPECTED_SHA256
    ):
        result["failure_class"] = "byte_identity_mismatch"
        return result
    _validate_profile(profile)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "receipt": {field: receipt.get(field) for field in _RECEIPT_FIELDS},
            "profile": profile,
            "csv_content_profiled": True,
        }
    )
    _validate_terminal_result(result)
    return result


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args()

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        raise RuntimeResidentialCsvProfileActionError("--output is required")
    result = run_profile(execution_sha=args.execution_sha)
    _validate_terminal_result(result)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
