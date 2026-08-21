# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the frozen Kosovo source/runtime Decimal comparison."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    from scripts import compare_esrm20_kosovo_exposure_runtime as comparison
    from scripts import profile_efehr_kosovo_exposure as source_profile
    from scripts import profile_esrm20_runtime_residential_csv as runtime_profile
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover
    import compare_esrm20_kosovo_exposure_runtime as comparison
    import profile_efehr_kosovo_exposure as source_profile
    import profile_esrm20_runtime_residential_csv as runtime_profile
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-source-runtime-compare-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-source-runtime-compare-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-compare-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-compare-result-v1"
ACTION = "esrm20_kosovo_source_runtime_compare"
SOURCE_ISSUE = 282
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 30_000

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "source_receipt_sha256",
    "runtime_receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "target_sha",
    "execution_sha",
    "source_receipt_identity",
    "runtime_receipt_identity",
    "status",
    "failure_class",
    "comparison",
    "comparison_executed",
    "canonical_receipt_pair_verified",
    "project186_equivalence_verified",
    "value_structural_wiring_verified",
    "source_crs_datum_epsg_verified",
    "insured_value_semantics_verified",
    "external_bytes_persisted",
    "raw_rows_returned",
    "publication_authorized",
    "model_use_authorized",
}
_COMPARISON_FIELDS = {
    "schema_version",
    "record_count",
    "canonical_receipt_pair_verified",
    "source_identity",
    "runtime_identity",
    "comparison_key",
    "numeric_comparisons",
    "project186_equivalence_verified",
    "value_structural_wiring_verified",
    "source_crs_datum_epsg_verified",
    "insured_value_semantics_verified",
    "external_bytes_persisted",
    "raw_rows_returned",
    "publication_authorized",
    "model_use_authorized",
}
_IDENTITY_FIELDS = {
    "canonical_receipt_verified",
    "byte_count",
    "sha256",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
}
_KEY_FIELDS = {
    "source_fields",
    "runtime_fields",
    "provider_business_key_authorized",
    "source_unique_count",
    "runtime_unique_count",
    "exact_key_set_equal",
    "key_set_sha256",
}
_NUMERIC_FIELDS = {
    "source_field",
    "runtime_field",
    "record_count",
    "exact_decimal_equal_count",
    "non_equal_count",
    "all_exact_decimal_equal",
    "maximum_absolute_difference",
    "relation_sha256",
}


class SourceRuntimeCompareActionError(RuntimeError):
    """Fail-closed request/result/action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceRuntimeCompareActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SourceRuntimeCompareActionError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise SourceRuntimeCompareActionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except SourceRuntimeCompareActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SourceRuntimeCompareActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise SourceRuntimeCompareActionError("text is not UTF-8 encodable") from exc


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SourceRuntimeCompareActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SourceRuntimeCompareActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise SourceRuntimeCompareActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceRuntimeCompareActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SourceRuntimeCompareActionError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("source_receipt_sha256", source_profile.EXPECTED_SHA256),
        ("runtime_receipt_sha256", runtime_profile.EXPECTED_SHA256),
    )
    for field, expected in exact:
        if request.get(field) != expected or type(request.get(field)) is not type(expected):
            raise SourceRuntimeCompareActionError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SourceRuntimeCompareActionError("invalid requester")
    return request


def _receipt_identity(profile: Any) -> dict[str, Any]:
    return {
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "commit_sha": profile.COMMIT_SHA,
        "repository_path": profile.REPOSITORY_PATH,
        "receipt_comment_id": profile.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": profile.RECEIPT_EXECUTION_SHA,
        "receipt_byte_count": profile.EXPECTED_BYTE_COUNT,
        "receipt_sha256": profile.EXPECTED_SHA256,
    }


def _comparison_identity(profile: Any) -> dict[str, Any]:
    return {
        "canonical_receipt_verified": True,
        "byte_count": profile.EXPECTED_BYTE_COUNT,
        "sha256": profile.EXPECTED_SHA256,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "commit_sha": profile.COMMIT_SHA,
        "repository_path": profile.REPOSITORY_PATH,
    }


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "source_receipt_identity": _receipt_identity(source_profile),
        "runtime_receipt_identity": _receipt_identity(runtime_profile),
        "status": "blocked",
        "failure_class": "comparison_failure",
        "comparison": None,
        "comparison_executed": False,
        "canonical_receipt_pair_verified": False,
        "project186_equivalence_verified": False,
        "value_structural_wiring_verified": False,
        "source_crs_datum_epsg_verified": False,
        "insured_value_semantics_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_decimal_text(value: object, *, label: str) -> Decimal:
    if type(value) is not str or not value:
        raise SourceRuntimeCompareActionError(f"invalid {label}")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise SourceRuntimeCompareActionError(f"invalid {label}") from exc
    if not parsed.is_finite() or parsed < 0:
        raise SourceRuntimeCompareActionError(f"invalid {label}")
    if comparison.source_value._canonical_decimal(parsed) != value:
        raise SourceRuntimeCompareActionError(f"non-canonical {label}")
    return parsed


def _validate_comparison(result: object) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _COMPARISON_FIELDS:
        raise SourceRuntimeCompareActionError("comparison fields drifted")
    if result.get("schema_version") != comparison.SCHEMA_VERSION:
        raise SourceRuntimeCompareActionError("comparison schema version drifted")
    if result.get("record_count") != comparison.EXPECTED_RECORD_COUNT:
        raise SourceRuntimeCompareActionError("comparison record count drifted")
    if result.get("canonical_receipt_pair_verified") is not True:
        raise SourceRuntimeCompareActionError("canonical receipt pair not verified")

    for label, identity, expected in (
        ("source", result.get("source_identity"), _comparison_identity(source_profile)),
        ("runtime", result.get("runtime_identity"), _comparison_identity(runtime_profile)),
    ):
        if type(identity) is not dict or set(identity) != _IDENTITY_FIELDS or identity != expected:
            raise SourceRuntimeCompareActionError(f"{label} comparison identity drifted")

    key = result.get("comparison_key")
    if type(key) is not dict or set(key) != _KEY_FIELDS:
        raise SourceRuntimeCompareActionError("comparison key fields drifted")
    expected_source_fields = [source for source, _runtime in comparison.KEY_FIELD_PAIRS]
    expected_runtime_fields = [runtime for _source, runtime in comparison.KEY_FIELD_PAIRS]
    exact_key = (
        ("source_fields", expected_source_fields),
        ("runtime_fields", expected_runtime_fields),
        ("provider_business_key_authorized", False),
        ("source_unique_count", comparison.EXPECTED_RECORD_COUNT),
        ("runtime_unique_count", comparison.EXPECTED_RECORD_COUNT),
        ("exact_key_set_equal", True),
    )
    for field, expected in exact_key:
        if key.get(field) != expected or type(key.get(field)) is not type(expected):
            raise SourceRuntimeCompareActionError(f"comparison key {field} drifted")
    if type(key.get("key_set_sha256")) is not str or _SHA256_RE.fullmatch(key["key_set_sha256"]) is None:
        raise SourceRuntimeCompareActionError("invalid comparison key digest")

    numeric = result.get("numeric_comparisons")
    if type(numeric) is not list or len(numeric) != len(comparison.NUMERIC_FIELD_PAIRS):
        raise SourceRuntimeCompareActionError("numeric comparison set drifted")
    for item, (source_field, runtime_field) in zip(numeric, comparison.NUMERIC_FIELD_PAIRS):
        if type(item) is not dict or set(item) != _NUMERIC_FIELDS:
            raise SourceRuntimeCompareActionError("numeric comparison fields drifted")
        if item.get("source_field") != source_field or item.get("runtime_field") != runtime_field:
            raise SourceRuntimeCompareActionError("numeric comparison identity drifted")
        if item.get("record_count") != comparison.EXPECTED_RECORD_COUNT:
            raise SourceRuntimeCompareActionError("numeric record count drifted")
        equal_count = item.get("exact_decimal_equal_count")
        non_equal_count = item.get("non_equal_count")
        if (
            type(equal_count) is not int
            or isinstance(equal_count, bool)
            or type(non_equal_count) is not int
            or isinstance(non_equal_count, bool)
            or equal_count < 0
            or non_equal_count < 0
            or equal_count + non_equal_count != comparison.EXPECTED_RECORD_COUNT
        ):
            raise SourceRuntimeCompareActionError("numeric equality counts do not close")
        all_equal = item.get("all_exact_decimal_equal")
        if type(all_equal) is not bool or all_equal is not (non_equal_count == 0):
            raise SourceRuntimeCompareActionError("numeric equality flag drifted")
        maximum_difference = _validate_decimal_text(
            item.get("maximum_absolute_difference"),
            label="maximum absolute difference",
        )
        if (maximum_difference == 0) is not all_equal:
            raise SourceRuntimeCompareActionError(
                "numeric maximum difference/equality state drifted"
            )
        digest = item.get("relation_sha256")
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise SourceRuntimeCompareActionError("invalid relation digest")

    for field in (
        "project186_equivalence_verified",
        "value_structural_wiring_verified",
        "source_crs_datum_epsg_verified",
        "insured_value_semantics_verified",
        "external_bytes_persisted",
        "raw_rows_returned",
        "publication_authorized",
        "model_use_authorized",
    ):
        if result.get(field) is not False:
            raise SourceRuntimeCompareActionError(f"comparison widened {field}")
    return result


def _validate_terminal_result(result: object) -> str:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SourceRuntimeCompareActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SourceRuntimeCompareActionError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("source_receipt_identity", _receipt_identity(source_profile)),
        ("runtime_receipt_identity", _receipt_identity(runtime_profile)),
        ("project186_equivalence_verified", False),
        ("value_structural_wiring_verified", False),
        ("source_crs_datum_epsg_verified", False),
        ("insured_value_semantics_verified", False),
        ("external_bytes_persisted", False),
        ("raw_rows_returned", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise SourceRuntimeCompareActionError(f"result {field} drifted")

    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("comparison_executed") is not True
            or result.get("canonical_receipt_pair_verified") is not True
        ):
            raise SourceRuntimeCompareActionError("invalid PASS state")
        _validate_comparison(result.get("comparison"))
    elif status == "blocked":
        if (
            result.get("failure_class") != "comparison_failure"
            or result.get("comparison") is not None
            or result.get("comparison_executed") is not False
            or result.get("canonical_receipt_pair_verified") is not False
        ):
            raise SourceRuntimeCompareActionError("invalid blocked state")
    else:
        raise SourceRuntimeCompareActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise SourceRuntimeCompareActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceRuntimeCompareActionError("non-canonical result envelope")
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
        raise SourceRuntimeCompareActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SourceRuntimeCompareActionError("comparison ledger is incomplete") from exc
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


def run_comparison(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SourceRuntimeCompareActionError("invalid execution SHA")
    result = _base_result(execution_sha)
    try:
        evidence = comparison.acquire_and_compare_kosovo_exposure_runtime()
    except comparison.ExposureRuntimeComparisonError:
        return result
    _validate_comparison(evidence)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "comparison": evidence,
            "comparison_executed": True,
            "canonical_receipt_pair_verified": True,
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
        raise SourceRuntimeCompareActionError("--output is required")
    result = run_comparison(execution_sha=args.execution_sha)
    _validate_terminal_result(result)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
