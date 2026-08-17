# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed ESRM20 v1.0 workbook identity profile."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_esrm20_scenario_v10_workbook_identity as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-workbook-identity-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-workbook-identity-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-workbook-identity-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-workbook-identity-result-v1"
SOURCE_ISSUE = 285
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 32_000

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "workbook_path",
    "tree_identity_sha256",
    "workbook_git_blob_sha1",
    "retrieved_at",
    "byte_count",
    "sha256",
    "target_event_id",
    "zip_member_count",
    "total_uncompressed_bytes",
    "worksheet_count",
    "shared_string_count",
    "scanned_row_count",
    "scanned_cell_count",
    "target_event_id_exact_cell_count",
    "target_event_id_row_count",
    "name_literal_cell_counts",
    "name_literal_row_counts",
    "target_same_row_name_literal_counts",
    "same_row_name_literal_binding",
    "raw_workbook_cells_returned",
    "raw_workbook_rows_returned",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "rupture_or_shakemap_payload_bytes_read",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
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
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.acquire_and_profile_workbook_identity
_FETCH_COMMENTS = fetch_repository_comments


class ScenarioWorkbookIdentityExecutionError(RuntimeError):
    """Fail-closed error for the dedicated workbook identity action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScenarioWorkbookIdentityExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ScenarioWorkbookIdentityExecutionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise ScenarioWorkbookIdentityExecutionError("wrong workbook identity issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ScenarioWorkbookIdentityExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise ScenarioWorkbookIdentityExecutionError("invalid workbook identity request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity request envelope is not canonical"
        )
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except ScenarioWorkbookIdentityExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioWorkbookIdentityExecutionError(
            "invalid workbook identity request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity request fields drifted"
        )
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity request schema drifted"
        )
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity request issue drifted"
        )
    if request["target_sha"] != execution_sha:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity request target is not trusted main"
        )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ScenarioWorkbookIdentityExecutionError("invalid requester identity")
    return request


def _nonnegative_int(value: object, *, field: str, maximum: int | None = None) -> int:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise ScenarioWorkbookIdentityExecutionError(
            f"{field} is not a nonnegative integer"
        )
    if maximum is not None and value > maximum:
        raise ScenarioWorkbookIdentityExecutionError(f"{field} exceeds bounded policy")
    return value


def _literal_counts(value: object, *, field: str) -> dict[str, int]:
    if type(value) is not dict or set(value) != set(profile.NAME_LITERALS):
        raise ScenarioWorkbookIdentityExecutionError(f"{field} keys drifted")
    return {
        name: _nonnegative_int(value[name], field=f"{field}.{name}")
        for name in profile.NAME_LITERALS
    }


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity profile fields drifted"
        )
    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("release_tag", profile.RELEASE_TAG),
        ("commit_sha", profile.COMMIT_SHA),
        ("workbook_path", profile.WORKBOOK_PATH),
        ("target_event_id", profile.TARGET_EVENT_ID),
        ("raw_workbook_cells_returned", False),
        ("raw_workbook_rows_returned", False),
        ("provider_file_bytes_read", True),
        ("external_bytes_persisted", False),
        ("rupture_or_shakemap_payload_bytes_read", False),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioWorkbookIdentityExecutionError(
                f"workbook identity profile drifted at {field}"
            )

    if (
        type(value["tree_identity_sha256"]) is not str
        or _SHA256_RE.fullmatch(value["tree_identity_sha256"]) is None
    ):
        raise ScenarioWorkbookIdentityExecutionError("tree identity SHA-256 is invalid")
    if (
        type(value["workbook_git_blob_sha1"]) is not str
        or _SHA1_RE.fullmatch(value["workbook_git_blob_sha1"]) is None
    ):
        raise ScenarioWorkbookIdentityExecutionError("workbook Git blob SHA-1 is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise ScenarioWorkbookIdentityExecutionError("workbook SHA-256 is invalid")
    if type(value["retrieved_at"]) is not str or _UTC_RE.fullmatch(value["retrieved_at"]) is None:
        raise ScenarioWorkbookIdentityExecutionError("workbook retrieval time is invalid")

    byte_count = _nonnegative_int(
        value["byte_count"], field="byte_count", maximum=profile.MAX_FILE_BYTES
    )
    if byte_count < 1:
        raise ScenarioWorkbookIdentityExecutionError("workbook byte count is empty")
    members = _nonnegative_int(
        value["zip_member_count"],
        field="zip_member_count",
        maximum=profile.MAX_ZIP_MEMBERS,
    )
    if members < 1:
        raise ScenarioWorkbookIdentityExecutionError("workbook ZIP has no members")
    _nonnegative_int(
        value["total_uncompressed_bytes"],
        field="total_uncompressed_bytes",
        maximum=profile.MAX_TOTAL_UNCOMPRESSED_BYTES,
    )
    worksheets = _nonnegative_int(
        value["worksheet_count"],
        field="worksheet_count",
        maximum=profile.MAX_WORKSHEETS,
    )
    if worksheets < 1:
        raise ScenarioWorkbookIdentityExecutionError("workbook has no worksheets")
    _nonnegative_int(
        value["shared_string_count"],
        field="shared_string_count",
        maximum=profile.MAX_SHARED_STRINGS,
    )
    scanned_rows = _nonnegative_int(
        value["scanned_row_count"],
        field="scanned_row_count",
        maximum=profile.MAX_ROWS,
    )
    scanned_cells = _nonnegative_int(
        value["scanned_cell_count"],
        field="scanned_cell_count",
        maximum=profile.MAX_CELLS,
    )
    target_cells = _nonnegative_int(
        value["target_event_id_exact_cell_count"],
        field="target_event_id_exact_cell_count",
    )
    target_rows = _nonnegative_int(
        value["target_event_id_row_count"], field="target_event_id_row_count"
    )
    if target_cells > scanned_cells or target_rows > scanned_rows or target_rows > target_cells:
        raise ScenarioWorkbookIdentityExecutionError("target row/cell counts disagree")

    cell_counts = _literal_counts(
        value["name_literal_cell_counts"], field="name_literal_cell_counts"
    )
    row_counts = _literal_counts(
        value["name_literal_row_counts"], field="name_literal_row_counts"
    )
    same_row = _literal_counts(
        value["target_same_row_name_literal_counts"],
        field="target_same_row_name_literal_counts",
    )
    for name in profile.NAME_LITERALS:
        if cell_counts[name] > scanned_cells:
            raise ScenarioWorkbookIdentityExecutionError(
                "name cell counts exceed scanned evidence"
            )
        if row_counts[name] > scanned_rows or row_counts[name] > cell_counts[name]:
            raise ScenarioWorkbookIdentityExecutionError(
                "name row/cell counts disagree"
            )
        if same_row[name] > row_counts[name] or same_row[name] > target_rows:
            raise ScenarioWorkbookIdentityExecutionError(
                "same-row binding counts disagree"
            )

    binding = value["same_row_name_literal_binding"]
    if binding is not None and binding not in profile.NAME_LITERALS:
        raise ScenarioWorkbookIdentityExecutionError(
            "same-row name binding is outside closed set"
        )
    positive = [name for name in profile.NAME_LITERALS if same_row[name] > 0]
    expected_binding = positive[0] if len(positive) == 1 else None
    if len(positive) > 1 or binding != expected_binding:
        raise ScenarioWorkbookIdentityExecutionError(
            "same-row name binding is contradictory"
        )
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _load_result(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity result marker is malformed"
        )
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity result envelope is malformed"
        )
    try:
        value = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except ScenarioWorkbookIdentityExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity result JSON is malformed"
        ) from exc
    if type(value) is not dict or set(value) != _RESULT_FIELDS:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook identity result fields drifted"
        )
    return value


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    value = _load_result(body)
    if value is None:
        return False
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioWorkbookIdentityExecutionError(
                f"workbook identity result drifted at {field}"
            )
    if value["status"] == "pass":
        if value["failure_class"] is not None:
            raise ScenarioWorkbookIdentityExecutionError("PASS result carries failure class")
        validate_profile(value["profile"])
        return True
    if value["status"] == "blocked":
        if (
            value["failure_class"] != "workbook_identity_failure"
            or value["profile"] is not None
        ):
            raise ScenarioWorkbookIdentityExecutionError(
                "blocked result widened workbook evidence"
            )
        return True
    if value["status"] == "duplicate":
        if value["failure_class"] is not None or value["profile"] is not None:
            raise ScenarioWorkbookIdentityExecutionError(
                "duplicate result carries evidence"
            )
        return True
    raise ScenarioWorkbookIdentityExecutionError(
        "workbook identity result status is invalid"
    )


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook result ledger is incomplete"
        ) from exc
    for comment in comments:
        if type(comment) is not dict:
            raise ScenarioWorkbookIdentityExecutionError(
                "workbook result ledger contains non-object"
            )
        user = comment.get("user")
        if type(user) is not dict or user.get("login") != TRUSTED_RESULT_LOGIN:
            continue
        value = _load_result(comment.get("body"))
        if value is None:
            continue
        own_sha = value.get("execution_sha")
        if type(own_sha) is not str or _SHA1_RE.fullmatch(own_sha) is None:
            raise ScenarioWorkbookIdentityExecutionError(
                "trusted workbook result SHA is invalid"
            )
        parse_terminal_result(comment.get("body"), execution_sha=own_sha)
        if own_sha == execution_sha:
            return True
    return False


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if profile.acquire_and_profile_workbook_identity is not _PROFILE:
        raise ScenarioWorkbookIdentityExecutionError(
            "trusted workbook profile authority drifted"
        )
    if fetch_repository_comments is not _FETCH_COMMENTS:
        raise ScenarioWorkbookIdentityExecutionError(
            "trusted workbook ledger authority drifted"
        )
    if has_terminal_result(
        repository=repository, token=token, execution_sha=execution_sha
    ):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        evidence = _PROFILE()
        validate_profile(evidence)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": evidence,
        }
    except profile.ScenarioWorkbookIdentityError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "workbook_identity_failure",
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise ScenarioWorkbookIdentityExecutionError(
            "workbook result exceeds publication limit"
        )
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
        raise ScenarioWorkbookIdentityExecutionError("GitHub ledger token is absent")
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
