# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the frozen Kosovo source/runtime comparison."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.compare_esrm20_kosovo_exposure_runtime import (
        EXPECTED_RECORD_COUNT,
        KEY_FIELD_PAIRS,
        NUMERIC_FIELD_PAIRS,
        SCHEMA_VERSION as COMPARISON_SCHEMA_VERSION,
        ExposureRuntimeComparisonError,
        acquire_and_compare_kosovo_exposure_runtime,
        runtime_profile,
        source_profile,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from compare_esrm20_kosovo_exposure_runtime import (
        EXPECTED_RECORD_COUNT,
        KEY_FIELD_PAIRS,
        NUMERIC_FIELD_PAIRS,
        SCHEMA_VERSION as COMPARISON_SCHEMA_VERSION,
        ExposureRuntimeComparisonError,
        acquire_and_compare_kosovo_exposure_runtime,
        runtime_profile,
        source_profile,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

SOURCE_ISSUE = 282
REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-source-runtime-compare-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-source-runtime-compare-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-compare-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-compare-result-v1"
ACTION = "esrm20_kosovo_source_runtime_compare"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 30_000

SOURCE_DATASET_ID = source_profile.DATASET_ID
RUNTIME_DATASET_ID = runtime_profile.DATASET_ID
SOURCE_EXPECTED_BYTE_COUNT = source_profile.EXPECTED_BYTE_COUNT
SOURCE_EXPECTED_SHA256 = source_profile.EXPECTED_SHA256
RUNTIME_EXPECTED_BYTE_COUNT = runtime_profile.EXPECTED_BYTE_COUNT
RUNTIME_EXPECTED_SHA256 = runtime_profile.EXPECTED_SHA256

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "source_dataset_id",
    "source_receipt_sha256",
    "runtime_dataset_id",
    "runtime_receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "target_sha",
    "execution_sha",
    "source_dataset_id",
    "runtime_dataset_id",
    "status",
    "failure_class",
    "comparison",
    "exact_decimal_comparison_completed",
    "project186_equivalence_verified",
    "value_structural_wiring_verified",
    "source_crs_datum_epsg_verified",
    "insured_value_semantics_verified",
    "external_bytes_persisted",
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
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "byte_count",
    "sha256",
}
_COMPARISON_KEY_FIELDS = {
    "source_fields",
    "runtime_fields",
    "provider_business_key_authorized",
    "source_unique_count",
    "runtime_unique_count",
    "exact_key_set_equal",
    "key_set_sha256",
}
_NUMERIC_COMPARISON_FIELDS = {
    "source_field",
    "runtime_field",
    "record_count",
    "exact_decimal_equal_count",
    "non_equal_count",
    "all_exact_decimal_equal",
    "maximum_absolute_difference",
    "relation_sha256",
}


class KosovoSourceRuntimeCompareActionError(RuntimeError):
    """Fail-closed request/result/action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KosovoSourceRuntimeCompareActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise KosovoSourceRuntimeCompareActionError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise KosovoSourceRuntimeCompareActionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except KosovoSourceRuntimeCompareActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise KosovoSourceRuntimeCompareActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise KosovoSourceRuntimeCompareActionError("text is not UTF-8 encodable") from exc


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise KosovoSourceRuntimeCompareActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise KosovoSourceRuntimeCompareActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise KosovoSourceRuntimeCompareActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoSourceRuntimeCompareActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise KosovoSourceRuntimeCompareActionError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("source_dataset_id", SOURCE_DATASET_ID),
        ("source_receipt_sha256", SOURCE_EXPECTED_SHA256),
        ("runtime_dataset_id", RUNTIME_DATASET_ID),
        ("runtime_receipt_sha256", RUNTIME_EXPECTED_SHA256),
    )
    for field, expected in exact:
        if request.get(field) != expected or type(request.get(field)) is not type(expected):
            raise KosovoSourceRuntimeCompareActionError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise KosovoSourceRuntimeCompareActionError("invalid requester")
    return request


def _expected_identity(profile: Any) -> dict[str, Any]:
    return {
        "canonical_receipt_verified": True,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "commit_sha": profile.COMMIT_SHA,
        "repository_path": profile.REPOSITORY_PATH,
        "byte_count": profile.EXPECTED_BYTE_COUNT,
        "sha256": profile.EXPECTED_SHA256,
    }


def _validate_identity(identity: object, *, profile: Any, label: str) -> dict[str, Any]:
    expected = _expected_identity(profile)
    if type(identity) is not dict or set(identity) != _IDENTITY_FIELDS:
        raise KosovoSourceRuntimeCompareActionError(f"{label} identity fields drifted")
    for field, expected_value in expected.items():
        value = identity.get(field)
        if value != expected_value or type(value) is not type(expected_value):
            raise KosovoSourceRuntimeCompareActionError(f"{label} identity {field} drifted")
    return identity


def _validate_digest(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise KosovoSourceRuntimeCompareActionError(f"invalid {label} digest")
    return value


def _validate_decimal_text(value: object) -> str:
    if type(value) is not str or not value or len(value) > 256:
        raise KosovoSourceRuntimeCompareActionError("invalid maximum absolute difference")
    if any(character not in "0123456789+-.Ee" for character in value):
        raise KosovoSourceRuntimeCompareActionError("invalid maximum absolute difference")
    try:
        from decimal import Decimal, InvalidOperation

        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise KosovoSourceRuntimeCompareActionError(
            "invalid maximum absolute difference"
        ) from exc
    if not number.is_finite() or number < 0:
        raise KosovoSourceRuntimeCompareActionError("invalid maximum absolute difference")
    return value


def _validate_comparison(comparison: object) -> dict[str, Any]:
    if type(comparison) is not dict or set(comparison) != _COMPARISON_FIELDS:
        raise KosovoSourceRuntimeCompareActionError("comparison fields drifted")
    exact = (
        ("schema_version", COMPARISON_SCHEMA_VERSION),
        ("canonical_receipt_pair_verified", True),
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
        if comparison.get(field) != expected or type(comparison.get(field)) is not type(expected):
            raise KosovoSourceRuntimeCompareActionError(f"comparison {field} drifted")
    record_count = comparison.get("record_count")
    if type(record_count) is not int or isinstance(record_count, bool) or record_count != EXPECTED_RECORD_COUNT:
        raise KosovoSourceRuntimeCompareActionError("comparison record_count drifted")
    _validate_identity(comparison.get("source_identity"), profile=source_profile, label="source")
    _validate_identity(comparison.get("runtime_identity"), profile=runtime_profile, label="runtime")

    comparison_key = comparison.get("comparison_key")
    if type(comparison_key) is not dict or set(comparison_key) != _COMPARISON_KEY_FIELDS:
        raise KosovoSourceRuntimeCompareActionError("comparison key fields drifted")
    expected_source_fields = [source for source, _runtime in KEY_FIELD_PAIRS]
    expected_runtime_fields = [runtime for _source, runtime in KEY_FIELD_PAIRS]
    key_exact = (
        ("source_fields", expected_source_fields),
        ("runtime_fields", expected_runtime_fields),
        ("provider_business_key_authorized", False),
        ("source_unique_count", EXPECTED_RECORD_COUNT),
        ("runtime_unique_count", EXPECTED_RECORD_COUNT),
        ("exact_key_set_equal", True),
    )
    for field, expected in key_exact:
        value = comparison_key.get(field)
        if value != expected or type(value) is not type(expected):
            raise KosovoSourceRuntimeCompareActionError(f"comparison key {field} drifted")
    _validate_digest(comparison_key.get("key_set_sha256"), label="key-set")

    numeric = comparison.get("numeric_comparisons")
    if type(numeric) is not list or len(numeric) != len(NUMERIC_FIELD_PAIRS):
        raise KosovoSourceRuntimeCompareActionError("numeric comparison count drifted")
    for expected_pair, item in zip(NUMERIC_FIELD_PAIRS, numeric):
        if type(item) is not dict or set(item) != _NUMERIC_COMPARISON_FIELDS:
            raise KosovoSourceRuntimeCompareActionError("numeric comparison fields drifted")
        source_field, runtime_field = expected_pair
        if item.get("source_field") != source_field or item.get("runtime_field") != runtime_field:
            raise KosovoSourceRuntimeCompareActionError("numeric comparison identity drifted")
        if (
            type(item.get("record_count")) is not int
            or isinstance(item.get("record_count"), bool)
            or item.get("record_count") != EXPECTED_RECORD_COUNT
        ):
            raise KosovoSourceRuntimeCompareActionError("numeric record count drifted")
        equal_count = item.get("exact_decimal_equal_count")
        non_equal_count = item.get("non_equal_count")
        if (
            type(equal_count) is not int
            or isinstance(equal_count, bool)
            or equal_count < 0
            or equal_count > EXPECTED_RECORD_COUNT
            or type(non_equal_count) is not int
            or isinstance(non_equal_count, bool)
            or non_equal_count < 0
            or equal_count + non_equal_count != EXPECTED_RECORD_COUNT
        ):
            raise KosovoSourceRuntimeCompareActionError("numeric equality counts drifted")
        all_equal = item.get("all_exact_decimal_equal")
        if type(all_equal) is not bool or all_equal is not (equal_count == EXPECTED_RECORD_COUNT):
            raise KosovoSourceRuntimeCompareActionError("numeric equality flag drifted")
        _validate_decimal_text(item.get("maximum_absolute_difference"))
        _validate_digest(item.get("relation_sha256"), label="relation")
    return comparison


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "source_dataset_id": SOURCE_DATASET_ID,
        "runtime_dataset_id": RUNTIME_DATASET_ID,
        "status": "blocked",
        "failure_class": "comparison_failure",
        "comparison": None,
        "exact_decimal_comparison_completed": False,
        "project186_equivalence_verified": False,
        "value_structural_wiring_verified": False,
        "source_crs_datum_epsg_verified": False,
        "insured_value_semantics_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise KosovoSourceRuntimeCompareActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise KosovoSourceRuntimeCompareActionError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("source_dataset_id", SOURCE_DATASET_ID),
        ("runtime_dataset_id", RUNTIME_DATASET_ID),
        ("project186_equivalence_verified", False),
        ("value_structural_wiring_verified", False),
        ("source_crs_datum_epsg_verified", False),
        ("insured_value_semantics_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise KosovoSourceRuntimeCompareActionError(f"result {field} drifted")

    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("exact_decimal_comparison_completed") is not True
        ):
            raise KosovoSourceRuntimeCompareActionError("invalid PASS state")
        _validate_comparison(result.get("comparison"))
    elif status == "blocked":
        if (
            result.get("failure_class") != "comparison_failure"
            or result.get("comparison") is not None
            or result.get("exact_decimal_comparison_completed") is not False
        ):
            raise KosovoSourceRuntimeCompareActionError("invalid blocked state")
    else:
        raise KosovoSourceRuntimeCompareActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise KosovoSourceRuntimeCompareActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise KosovoSourceRuntimeCompareActionError("non-canonical result envelope")
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
        raise KosovoSourceRuntimeCompareActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise KosovoSourceRuntimeCompareActionError("comparison ledger is incomplete") from exc
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
        raise KosovoSourceRuntimeCompareActionError("invalid execution SHA")
    result = _base_result(execution_sha)
    try:
        comparison = acquire_and_compare_kosovo_exposure_runtime()
    except ExposureRuntimeComparisonError:
        return result
    _validate_comparison(comparison)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "comparison": comparison,
            "exact_decimal_comparison_completed": True,
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
        raise KosovoSourceRuntimeCompareActionError("--output is required")
    result = run_comparison(execution_sha=args.execution_sha)
    _validate_terminal_result(result)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
