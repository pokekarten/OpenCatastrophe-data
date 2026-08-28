# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the Kosovo source/runtime binary64 diagnostic.

This action reuses the exact fixed source/runtime receipt targets and bounded
transport already used by the trusted Decimal comparison. It adds no
caller-selectable provider path and never persists provider bytes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts import compare_esrm20_kosovo_exposure_runtime as comparison
    from scripts import profile_esrm20_kosovo_source_runtime_binary64 as profiler
    from scripts import profile_efehr_kosovo_exposure as source_profile
    from scripts import profile_esrm20_runtime_residential_csv as runtime_profile
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import compare_esrm20_kosovo_exposure_runtime as comparison
    import profile_esrm20_kosovo_source_runtime_binary64 as profiler
    import profile_efehr_kosovo_exposure as source_profile
    import profile_esrm20_runtime_residential_csv as runtime_profile
    from prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-source-runtime-binary64-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-source-runtime-binary64-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-binary64-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-source-runtime-binary64-result-v1"
ACTION = "esrm20_kosovo_source_runtime_binary64_profile"
SOURCE_ISSUE = 282
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 30000

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
    "profile",
    "profile_executed",
    "canonical_receipt_pair_verified",
    "source_to_runtime_transform_lineage_verified",
    "provider_generator_identity_verified",
    "runtime_values_substitutable_with_source_values",
    "source_runtime_semantic_equivalence_verified",
    "external_bytes_persisted",
    "raw_rows_returned",
    "publication_authorized",
    "model_use_authorized",
}
_PROFILE_FIELDS = {
    "schema_version",
    "hypothesis",
    "record_count",
    "canonical_receipt_pair_verified",
    "comparison_key_set_sha256",
    "numeric_fields",
    "all_fields_numerically_consistent_with_hypothesis",
    "source_to_runtime_transform_lineage_verified",
    "provider_generator_identity_verified",
    "runtime_values_substitutable_with_source_values",
    "source_runtime_semantic_equivalence_verified",
    "external_bytes_persisted",
    "raw_rows_returned",
    "publication_authorized",
    "model_use_authorized",
}
_HYPOTHESIS_FIELDS = {
    "id",
    "source_parse",
    "render",
    "comparison",
    "provider_transform_claimed",
}
_NUMERIC_FIELDS = {
    "source_field",
    "runtime_field",
    "record_count",
    "source_runtime_exact_equal_count",
    "binary64_projection_match_count",
    "binary64_projection_mismatch_count",
    "all_runtime_values_match_binary64_projection",
    "projection_relation_sha256",
}
_AUTHORITY_FALSE_FIELDS = (
    "source_to_runtime_transform_lineage_verified",
    "provider_generator_identity_verified",
    "runtime_values_substitutable_with_source_values",
    "source_runtime_semantic_equivalence_verified",
    "external_bytes_persisted",
    "raw_rows_returned",
    "publication_authorized",
    "model_use_authorized",
)


class SourceRuntimeBinary64ActionError(RuntimeError):
    """Fail-closed request/result/action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceRuntimeBinary64ActionError("duplicate JSON key")
        result[key] = value
    return result


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs)
    except SourceRuntimeBinary64ActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SourceRuntimeBinary64ActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise SourceRuntimeBinary64ActionError("text is not UTF-8 encodable") from exc


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SourceRuntimeBinary64ActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SourceRuntimeBinary64ActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise SourceRuntimeBinary64ActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceRuntimeBinary64ActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SourceRuntimeBinary64ActionError("request fields drifted")

    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("source_receipt_sha256", source_profile.EXPECTED_SHA256),
        ("runtime_receipt_sha256", runtime_profile.EXPECTED_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if observed != expected or type(observed) is not type(expected):
            raise SourceRuntimeBinary64ActionError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SourceRuntimeBinary64ActionError("invalid requester")
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
        "failure_class": "binary64_profile_failure",
        "profile": None,
        "profile_executed": False,
        "canonical_receipt_pair_verified": False,
        "source_to_runtime_transform_lineage_verified": False,
        "provider_generator_identity_verified": False,
        "runtime_values_substitutable_with_source_values": False,
        "source_runtime_semantic_equivalence_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise SourceRuntimeBinary64ActionError("profile fields drifted")
    if value.get("schema_version") != profiler.SCHEMA_VERSION:
        raise SourceRuntimeBinary64ActionError("profile schema version drifted")
    if value.get("record_count") != comparison.EXPECTED_RECORD_COUNT:
        raise SourceRuntimeBinary64ActionError("profile record count drifted")
    if value.get("canonical_receipt_pair_verified") is not True:
        raise SourceRuntimeBinary64ActionError("canonical receipt pair not verified")

    digest = value.get("comparison_key_set_sha256")
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        raise SourceRuntimeBinary64ActionError("invalid comparison key digest")

    hypothesis = value.get("hypothesis")
    if type(hypothesis) is not dict or set(hypothesis) != _HYPOTHESIS_FIELDS:
        raise SourceRuntimeBinary64ActionError("hypothesis fields drifted")
    expected_hypothesis = {
        "id": profiler.HYPOTHESIS_ID,
        "source_parse": "python-float-from-decimal-text-ieee754-binary64",
        "render": "python-repr-shortest-roundtrip-decimal",
        "comparison": "exact-decimal-equality-to-runtime-token",
        "provider_transform_claimed": False,
    }
    if hypothesis != expected_hypothesis:
        raise SourceRuntimeBinary64ActionError("hypothesis identity drifted")

    numeric = value.get("numeric_fields")
    if type(numeric) is not list or len(numeric) != len(comparison.NUMERIC_FIELD_PAIRS):
        raise SourceRuntimeBinary64ActionError("numeric field set drifted")
    all_match = True
    for item, (source_field, runtime_field) in zip(
        numeric, comparison.NUMERIC_FIELD_PAIRS
    ):
        if type(item) is not dict or set(item) != _NUMERIC_FIELDS:
            raise SourceRuntimeBinary64ActionError("numeric field result drifted")
        if (
            item.get("source_field") != source_field
            or item.get("runtime_field") != runtime_field
            or item.get("record_count") != comparison.EXPECTED_RECORD_COUNT
        ):
            raise SourceRuntimeBinary64ActionError("numeric field identity drifted")
        exact_count = item.get("source_runtime_exact_equal_count")
        match_count = item.get("binary64_projection_match_count")
        mismatch_count = item.get("binary64_projection_mismatch_count")
        for count in (exact_count, match_count, mismatch_count):
            if (
                type(count) is not int
                or isinstance(count, bool)
                or count < 0
                or count > comparison.EXPECTED_RECORD_COUNT
            ):
                raise SourceRuntimeBinary64ActionError("invalid numeric field count")
        if match_count + mismatch_count != comparison.EXPECTED_RECORD_COUNT:
            raise SourceRuntimeBinary64ActionError("binary64 counts do not close")
        matched = item.get("all_runtime_values_match_binary64_projection")
        if type(matched) is not bool or matched is not (mismatch_count == 0):
            raise SourceRuntimeBinary64ActionError("binary64 match flag drifted")
        all_match = all_match and matched
        relation = item.get("projection_relation_sha256")
        if type(relation) is not str or _SHA256_RE.fullmatch(relation) is None:
            raise SourceRuntimeBinary64ActionError("invalid projection relation digest")

    observed_all = value.get("all_fields_numerically_consistent_with_hypothesis")
    if type(observed_all) is not bool or observed_all is not all_match:
        raise SourceRuntimeBinary64ActionError("all-fields consistency flag drifted")

    for field in _AUTHORITY_FALSE_FIELDS:
        if value.get(field) is not False:
            raise SourceRuntimeBinary64ActionError(f"profile widened {field}")
    return value


def _validate_terminal_result(result: object) -> str:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SourceRuntimeBinary64ActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SourceRuntimeBinary64ActionError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("source_receipt_identity", _receipt_identity(source_profile)),
        ("runtime_receipt_identity", _receipt_identity(runtime_profile)),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise SourceRuntimeBinary64ActionError(f"result {field} drifted")
    for field in _AUTHORITY_FALSE_FIELDS:
        if result.get(field) is not False:
            raise SourceRuntimeBinary64ActionError(f"result widened {field}")

    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("profile_executed") is not True
            or result.get("canonical_receipt_pair_verified") is not True
        ):
            raise SourceRuntimeBinary64ActionError("invalid PASS state")
        _validate_profile(result.get("profile"))
    elif status == "blocked":
        if (
            result.get("failure_class") != "binary64_profile_failure"
            or result.get("profile") is not None
            or result.get("profile_executed") is not False
            or result.get("canonical_receipt_pair_verified") is not False
        ):
            raise SourceRuntimeBinary64ActionError("invalid blocked state")
    else:
        raise SourceRuntimeBinary64ActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise SourceRuntimeBinary64ActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceRuntimeBinary64ActionError("non-canonical result envelope")
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
        raise SourceRuntimeBinary64ActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise SourceRuntimeBinary64ActionError("binary64 ledger is incomplete") from exc
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


def _acquire_profile() -> dict[str, Any]:
    source_raw = comparison._fetch_fixed_payload(
        dataset_id=source_profile.DATASET_ID,
        project_id=source_profile.PROJECT_ID,
        commit_sha=source_profile.COMMIT_SHA,
        repository_path=source_profile.REPOSITORY_PATH,
        maximum=source_profile.EXPECTED_BYTE_COUNT,
        opener=comparison._CANONICAL_OPEN_FIXED,
        monotonic=comparison._CANONICAL_MONOTONIC,
    )
    runtime_raw = comparison._fetch_fixed_payload(
        dataset_id=runtime_profile.DATASET_ID,
        project_id=runtime_profile.PROJECT_ID,
        commit_sha=runtime_profile.COMMIT_SHA,
        repository_path=runtime_profile.REPOSITORY_PATH,
        maximum=runtime_profile.EXPECTED_BYTE_COUNT,
        opener=comparison._CANONICAL_OPEN_FIXED,
        monotonic=comparison._CANONICAL_MONOTONIC,
    )
    return profiler.profile_verified_exposure_binary64_projection(source_raw, runtime_raw)


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SourceRuntimeBinary64ActionError("invalid execution SHA")
    result = _base_result(execution_sha)
    try:
        evidence = _acquire_profile()
    except (
        comparison.ExposureRuntimeComparisonError,
        profiler.KosovoBinary64ProjectionError,
    ):
        return result
    _validate_profile(evidence)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "profile": evidence,
            "profile_executed": True,
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
        raise SourceRuntimeBinary64ActionError("--output is required")
    result = run_profile(execution_sha=args.execution_sha)
    _validate_terminal_result(result)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
