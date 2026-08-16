# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the two fixed ESRM20 v1.0 scenario summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_esrm20_scenario_v10_summaries as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-summaries-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-summaries-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-summaries-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-summaries-result-v1"
SOURCE_ISSUE = 488
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 128_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "parent_science_issue",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "summary_paths",
    "summaries",
    "identity_value_count",
    "identity_set_sha256",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "scenario_payload_bytes_read",
    "scenario_selection_authorized",
    "publication_authorized",
    "model_use_authorized",
}
_SUMMARY_FIELDS = {
    "repository_path",
    "retrieved_at",
    "byte_count",
    "sha256",
    "encoding",
    "delimiter",
    "column_count",
    "row_count",
    "headers",
    "identity_columns",
    "identity_values",
    "identity_set_sha256",
    "raw_rows_returned",
}
_RESULT_FIELDS = {
    "schema_version",
    "source_issue",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "profile",
    "external_bytes_persisted",
    "scenario_payload_bytes_read",
    "scenario_selection_authorized",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.acquire_and_profile_summaries
_FETCH_COMMENTS = fetch_repository_comments


class ScenarioSummaryExecutionError(RuntimeError):
    """Fail-closed error for the dedicated scenario summary action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScenarioSummaryExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ScenarioSummaryExecutionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise ScenarioSummaryExecutionError("wrong scenario summary issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise ScenarioSummaryExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise ScenarioSummaryExecutionError("invalid scenario summary request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioSummaryExecutionError("scenario summary request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except ScenarioSummaryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioSummaryExecutionError("invalid scenario summary request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ScenarioSummaryExecutionError("scenario summary request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ScenarioSummaryExecutionError("scenario summary request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise ScenarioSummaryExecutionError("scenario summary request issue drifted")
    if request["target_sha"] != execution_sha:
        raise ScenarioSummaryExecutionError("scenario summary request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ScenarioSummaryExecutionError("invalid requester identity")
    return request


def _bounded_text(value: object, *, field: str, maximum: int = profile.MAX_CELL_UTF8_BYTES) -> str:
    if type(value) is not str:
        raise ScenarioSummaryExecutionError(f"{field} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ScenarioSummaryExecutionError(f"{field} is not UTF-8 encodable") from exc
    if len(encoded) > maximum:
        raise ScenarioSummaryExecutionError(f"{field} exceeds bounded policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ScenarioSummaryExecutionError(f"{field} contains forbidden control characters")
    return value


def _identity_sha(identity_values: dict[str, list[str]]) -> str:
    encoded = json.dumps(
        identity_values, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _aggregate_identity_sha(summaries: list[dict[str, Any]]) -> str:
    canonical = {
        item["repository_path"]: item["identity_values"]
        for item in sorted(summaries, key=lambda item: item["repository_path"])
    }
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_summary(value: object, *, expected_path: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _SUMMARY_FIELDS:
        raise ScenarioSummaryExecutionError("scenario summary fields drifted")
    if value["repository_path"] != expected_path:
        raise ScenarioSummaryExecutionError("scenario summary path drifted")
    if type(value["retrieved_at"]) is not str or _UTC_RE.fullmatch(value["retrieved_at"]) is None:
        raise ScenarioSummaryExecutionError("scenario summary retrieval time is invalid")
    if (
        type(value["byte_count"]) is not int
        or isinstance(value["byte_count"], bool)
        or not (1 <= value["byte_count"] <= profile.MAX_FILE_BYTES)
    ):
        raise ScenarioSummaryExecutionError("scenario summary byte count is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise ScenarioSummaryExecutionError("scenario summary SHA-256 is invalid")
    if value["encoding"] != "utf-8":
        raise ScenarioSummaryExecutionError("scenario summary encoding drifted")
    if value["delimiter"] not in {"comma", "semicolon", "tab"}:
        raise ScenarioSummaryExecutionError("scenario summary delimiter is invalid")
    if (
        type(value["column_count"]) is not int
        or isinstance(value["column_count"], bool)
        or not (2 <= value["column_count"] <= profile.MAX_COLUMNS)
    ):
        raise ScenarioSummaryExecutionError("scenario summary column count is invalid")
    if (
        type(value["row_count"]) is not int
        or isinstance(value["row_count"], bool)
        or not (1 <= value["row_count"] <= profile.MAX_ROWS)
    ):
        raise ScenarioSummaryExecutionError("scenario summary row count is invalid")

    headers = value["headers"]
    if type(headers) is not list or len(headers) != value["column_count"]:
        raise ScenarioSummaryExecutionError("scenario summary headers disagree with column count")
    for header in headers:
        _bounded_text(header, field="scenario summary header")
        if not header or header != header.strip():
            raise ScenarioSummaryExecutionError("scenario summary header is not canonical")
    if len({header.casefold() for header in headers}) != len(headers):
        raise ScenarioSummaryExecutionError("scenario summary headers are not unique")

    identity_columns = value["identity_columns"]
    if type(identity_columns) is not list:
        raise ScenarioSummaryExecutionError("scenario identity columns are invalid")
    expected_identity_columns = [
        header for header in headers if header.casefold() in profile.IDENTITY_HEADER_TOKENS
    ]
    if identity_columns != expected_identity_columns:
        raise ScenarioSummaryExecutionError("scenario identity-column selection drifted")

    identity_values = value["identity_values"]
    if type(identity_values) is not dict or list(identity_values) != identity_columns:
        raise ScenarioSummaryExecutionError("scenario identity values do not match columns")
    for column, values in identity_values.items():
        if type(values) is not list or len(values) > profile.MAX_IDENTITY_VALUES_PER_COLUMN:
            raise ScenarioSummaryExecutionError("scenario identity values exceed policy")
        if values != sorted(set(values)):
            raise ScenarioSummaryExecutionError("scenario identity values are not canonical")
        for item in values:
            _bounded_text(item, field=f"scenario identity value {column}")
            if item == "":
                raise ScenarioSummaryExecutionError("empty scenario identity value was serialized")
    if (
        type(value["identity_set_sha256"]) is not str
        or _SHA256_RE.fullmatch(value["identity_set_sha256"]) is None
        or value["identity_set_sha256"] != _identity_sha(identity_values)
    ):
        raise ScenarioSummaryExecutionError("scenario identity fingerprint drifted")
    if type(value["raw_rows_returned"]) is not bool or value["raw_rows_returned"] is not False:
        raise ScenarioSummaryExecutionError("scenario raw-row boundary widened")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise ScenarioSummaryExecutionError("scenario summary profile fields drifted")
    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("parent_science_issue", profile.PARENT_SCIENCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("release_tag", profile.RELEASE_TAG),
        ("commit_sha", profile.COMMIT_SHA),
        ("summary_paths", list(profile.SUMMARY_PATHS)),
        ("provider_file_bytes_read", True),
        ("external_bytes_persisted", False),
        ("scenario_payload_bytes_read", False),
        ("scenario_selection_authorized", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioSummaryExecutionError(f"scenario summary profile drifted at {field}")

    summaries = value["summaries"]
    if type(summaries) is not list or len(summaries) != len(profile.SUMMARY_PATHS):
        raise ScenarioSummaryExecutionError("scenario summary file count drifted")
    for item, expected_path in zip(summaries, profile.SUMMARY_PATHS):
        _validate_summary(item, expected_path=expected_path)

    expected_count = sum(
        len(values) for item in summaries for values in item["identity_values"].values()
    )
    if (
        type(value["identity_value_count"]) is not int
        or isinstance(value["identity_value_count"], bool)
        or value["identity_value_count"] != expected_count
    ):
        raise ScenarioSummaryExecutionError("scenario identity count drifted")
    if (
        type(value["identity_set_sha256"]) is not str
        or _SHA256_RE.fullmatch(value["identity_set_sha256"]) is None
        or value["identity_set_sha256"] != _aggregate_identity_sha(summaries)
    ):
        raise ScenarioSummaryExecutionError("aggregate scenario identity fingerprint drifted")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_bytes_persisted": False,
        "scenario_payload_bytes_read": False,
        "scenario_selection_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _terminal_result_execution_sha(body: object) -> str | None:
    """Return a trusted result envelope's own execution SHA after basic validation."""
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise ScenarioSummaryExecutionError("scenario summary result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioSummaryExecutionError("scenario summary result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except ScenarioSummaryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioSummaryExecutionError("scenario summary result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise ScenarioSummaryExecutionError("scenario summary result fields drifted")
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ScenarioSummaryExecutionError("scenario summary result schema drifted")
    if type(result["source_issue"]) is not int or result["source_issue"] != SOURCE_ISSUE:
        raise ScenarioSummaryExecutionError("scenario summary result source issue drifted")
    target_sha = result["target_sha"]
    execution_sha = result["execution_sha"]
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None:
        raise ScenarioSummaryExecutionError("scenario summary result target SHA is invalid")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise ScenarioSummaryExecutionError("scenario summary result execution SHA is invalid")
    if target_sha != execution_sha:
        raise ScenarioSummaryExecutionError("scenario summary result target/execution SHA mismatch")
    return execution_sha


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise ScenarioSummaryExecutionError("scenario summary result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioSummaryExecutionError("scenario summary result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except ScenarioSummaryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioSummaryExecutionError("scenario summary result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise ScenarioSummaryExecutionError("scenario summary result fields drifted")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioSummaryExecutionError(f"scenario summary result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise ScenarioSummaryExecutionError("scenario summary PASS carries failure class")
        validate_profile(result["profile"])
        return True
    if result["status"] == "blocked":
        if (
            result["failure_class"] != "summary_acquisition_or_profile_failure"
            or result["profile"] is not None
        ):
            raise ScenarioSummaryExecutionError("scenario summary blocked result widened evidence")
        return True
    if result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise ScenarioSummaryExecutionError("scenario summary duplicate result carries evidence")
        return True
    raise ScenarioSummaryExecutionError("scenario summary result has non-terminal status")


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise ScenarioSummaryExecutionError("scenario summary result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise ScenarioSummaryExecutionError("scenario summary ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_execution_sha = _terminal_result_execution_sha(body)
        if own_execution_sha is None:
            continue
        terminal = parse_terminal_result(body, execution_sha=own_execution_sha)
        if own_execution_sha != execution_sha:
            continue
        if terminal:
            return True
    return False


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if profile.acquire_and_profile_summaries is not _PROFILE or fetch_repository_comments is not _FETCH_COMMENTS:
        raise ScenarioSummaryExecutionError("trusted scenario summary execution authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        summary_profile = _PROFILE()
        validate_profile(summary_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": summary_profile,
        }
    except profile.ScenarioSummaryProfileError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "summary_acquisition_or_profile_failure",
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise ScenarioSummaryExecutionError("scenario summary result exceeds publication limit")
    parse_terminal_result(
        RESULT_MARKER + "\n" + encoded.decode("utf-8"),
        execution_sha=execution_sha,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--token-env")
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error("--repository, --token-env and --output are required for execution")
    token = os.environ.get(args.token_env)
    if not token:
        raise ScenarioSummaryExecutionError("GitHub ledger token is absent")
    result = execute_profile(
        repository=args.repository, token=token, execution_sha=args.execution_sha
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
