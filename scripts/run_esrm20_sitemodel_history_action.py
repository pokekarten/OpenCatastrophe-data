# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed ESRM20 site-tool history profile."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_esrm20_sitemodel_history as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-sitemodel-history-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-sitemodel-history-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-sitemodel-history-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-sitemodel-history-result-v1"
SOURCE_ISSUE = 291
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 96_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_CANDIDATE_FIELDS = {"commit_sha", "committed_at_utc", "parent_shas"}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "project_id",
    "project_path",
    "ref_name",
    "since_utc",
    "until_utc",
    "pages_read",
    "candidate_commit_count",
    "history_identity_sha256",
    "candidate_commits",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "exact_kosovo_generator_commit_verified",
    "crs_coordinate_semantics_verified",
    "missingness_semantics_verified",
    "site_model_compatibility_verified",
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
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "exact_kosovo_generator_commit_verified",
    "crs_coordinate_semantics_verified",
    "missingness_semantics_verified",
    "site_model_compatibility_verified",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.profile_history
_FETCH_COMMENTS = fetch_repository_comments


class SiteModelHistoryExecutionError(RuntimeError):
    """Fail-closed error for the dedicated site-tool history action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SiteModelHistoryExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SiteModelHistoryExecutionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SiteModelHistoryExecutionError("wrong site-tool history issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteModelHistoryExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteModelHistoryExecutionError("invalid site-tool history request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelHistoryExecutionError("site-tool history request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteModelHistoryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelHistoryExecutionError("invalid site-tool history request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteModelHistoryExecutionError("site-tool history request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise SiteModelHistoryExecutionError("site-tool history request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise SiteModelHistoryExecutionError("site-tool history request issue drifted")
    if request["target_sha"] != execution_sha:
        raise SiteModelHistoryExecutionError("site-tool history request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SiteModelHistoryExecutionError("invalid requester identity")
    return request


def _parse_utc(value: object) -> datetime:
    if type(value) is not str or not value or value != value.strip():
        raise SiteModelHistoryExecutionError("site-tool candidate timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SiteModelHistoryExecutionError("site-tool candidate timestamp is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SiteModelHistoryExecutionError("site-tool candidate timestamp is timezone-naive")
    return parsed


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise SiteModelHistoryExecutionError("site-tool history profile fields drifted")
    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("ref_name", profile.REF_NAME),
        ("since_utc", profile.SINCE_UTC),
        ("until_utc", profile.UNTIL_UTC),
        ("provider_file_bytes_read", False),
        ("external_bytes_persisted", False),
        ("exact_kosovo_generator_commit_verified", False),
        ("crs_coordinate_semantics_verified", False),
        ("missingness_semantics_verified", False),
        ("site_model_compatibility_verified", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteModelHistoryExecutionError(f"site-tool history profile drifted at {field}")

    pages_read = value["pages_read"]
    count = value["candidate_commit_count"]
    if type(pages_read) is not int or isinstance(pages_read, bool) or not (1 <= pages_read <= profile.MAX_PAGES):
        raise SiteModelHistoryExecutionError("site-tool history page count is invalid")
    if type(count) is not int or isinstance(count, bool) or not (1 <= count <= profile.MAX_COMMITS):
        raise SiteModelHistoryExecutionError("site-tool history candidate count is invalid")
    digest = value["history_identity_sha256"]
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        raise SiteModelHistoryExecutionError("site-tool history identity SHA-256 is invalid")

    candidates = value["candidate_commits"]
    if type(candidates) is not list or len(candidates) != count:
        raise SiteModelHistoryExecutionError("site-tool history candidate count disagrees")
    identities: list[str] = []
    sort_keys: list[tuple[float, str]] = []
    for candidate in candidates:
        if type(candidate) is not dict or set(candidate) != _CANDIDATE_FIELDS:
            raise SiteModelHistoryExecutionError("site-tool history candidate shape drifted")
        commit_sha = candidate["commit_sha"]
        if type(commit_sha) is not str or _SHA_RE.fullmatch(commit_sha) is None:
            raise SiteModelHistoryExecutionError("site-tool history candidate SHA is invalid")
        committed = _parse_utc(candidate["committed_at_utc"])
        if not (
            _parse_utc(profile.SINCE_UTC) <= committed <= _parse_utc(profile.UNTIL_UTC)
        ):
            raise SiteModelHistoryExecutionError("site-tool history candidate lies outside fixed window")
        parents = candidate["parent_shas"]
        if type(parents) is not list or len(parents) > profile.MAX_PARENT_IDS:
            raise SiteModelHistoryExecutionError("site-tool history parent list exceeds policy")
        for parent in parents:
            if type(parent) is not str or _SHA_RE.fullmatch(parent) is None:
                raise SiteModelHistoryExecutionError("site-tool history parent SHA is invalid")
        if len(set(parents)) != len(parents):
            raise SiteModelHistoryExecutionError("site-tool history candidate repeats parent SHA")
        identities.append(commit_sha)
        sort_keys.append((-committed.timestamp(), commit_sha))
    if len(set(identities)) != len(identities):
        raise SiteModelHistoryExecutionError("site-tool history candidates repeat commit SHA")
    if sort_keys != sorted(sort_keys):
        raise SiteModelHistoryExecutionError("site-tool history candidates are not canonical")
    if profile._history_sha256(candidates) != digest:
        raise SiteModelHistoryExecutionError("site-tool history identity does not match candidates")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_generator_commit_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "site_model_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    """Validate a trusted terminal result fully, then scope dedup to one SHA."""
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SiteModelHistoryExecutionError("invalid execution SHA")
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise SiteModelHistoryExecutionError("site-tool history result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelHistoryExecutionError("site-tool history result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SiteModelHistoryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelHistoryExecutionError("site-tool history result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SiteModelHistoryExecutionError("site-tool history result fields drifted")
    if result["schema_version"] != RESULT_SCHEMA_VERSION or result["source_issue"] != SOURCE_ISSUE:
        raise SiteModelHistoryExecutionError("site-tool history result identity drifted")
    target = result["target_sha"]
    observed_execution = result["execution_sha"]
    if (
        type(target) is not str
        or _SHA_RE.fullmatch(target) is None
        or type(observed_execution) is not str
        or _SHA_RE.fullmatch(observed_execution) is None
        or target != observed_execution
    ):
        raise SiteModelHistoryExecutionError("site-tool history result SHA binding is invalid")

    own_execution_sha = target
    for field, expected in _base_result(execution_sha=own_execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteModelHistoryExecutionError(f"site-tool history result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise SiteModelHistoryExecutionError("site-tool history PASS carries failure class")
        validate_profile(result["profile"])
    elif result["status"] == "blocked":
        if result["failure_class"] != "metadata_acquisition_failure" or result["profile"] is not None:
            raise SiteModelHistoryExecutionError("site-tool history blocked result widened evidence")
    elif result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise SiteModelHistoryExecutionError("site-tool history duplicate result carries evidence")
    else:
        raise SiteModelHistoryExecutionError("site-tool history result has non-terminal status")
    return own_execution_sha == execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise SiteModelHistoryExecutionError("site-tool history result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteModelHistoryExecutionError("site-tool history ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if profile.profile_history is not _PROFILE or fetch_repository_comments is not _FETCH_COMMENTS:
        raise SiteModelHistoryExecutionError("trusted site-tool history execution authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        history_profile = _PROFILE()
        validate_profile(history_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": history_profile,
        }
    except profile.SiteModelHistoryProfileError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "metadata_acquisition_failure",
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise SiteModelHistoryExecutionError("site-tool history result exceeds publication limit")
    parse_terminal_result(
        RESULT_MARKER + "\n" + encoded.decode("utf-8"), execution_sha=execution_sha
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
        raise SiteModelHistoryExecutionError("GitHub ledger token is absent")
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
