# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed ESRM20 site-tool candidate-tree profile."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_esrm20_sitemodel_candidate_trees as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-sitemodel-candidate-tree-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-sitemodel-candidate-tree-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-sitemodel-candidate-tree-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-sitemodel-candidate-tree-result-v1"
SOURCE_ISSUE = 291
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4_096
MAX_TERMINAL_UTF8_BYTES = 60_000

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_CANDIDATE_PROFILE_FIELDS = {
    "commit_sha",
    "pages_read",
    "entry_count",
    "blob_count",
    "tree_identity_sha256",
}
_CHANGED_BLOB_FIELDS = {"path", "states"}
_CHANGED_STATE_FIELDS = {"commit_sha", "present", "mode", "object_sha1"}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "project_id",
    "project_path",
    "history_identity_sha256",
    "candidate_tree_profiles",
    "changed_blob_count",
    "changed_blob_identity_sha256",
    "changed_blobs",
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

_PROFILE = profile.profile_candidate_trees
_FETCH_COMMENTS = fetch_repository_comments
_CHANGED_BLOB_IDENTITY = profile._changed_blob_identity_sha256
_CANONICAL_PROFILE = _PROFILE
_CANONICAL_FETCH_COMMENTS = _FETCH_COMMENTS
_CANONICAL_CHANGED_BLOB_IDENTITY = _CHANGED_BLOB_IDENTITY


class SiteModelCandidateTreeExecutionError(RuntimeError):
    """Fail-closed error for the dedicated candidate-tree action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SiteModelCandidateTreeExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SiteModelCandidateTreeExecutionError(f"non-finite JSON constant: {value}")


def _reject_float_overflow(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise SiteModelCandidateTreeExecutionError("invalid JSON float") from exc
    if not math.isfinite(parsed):
        raise SiteModelCandidateTreeExecutionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_reject_float_overflow,
        )
    except SiteModelCandidateTreeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteModelCandidateTreeExecutionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str, *, label: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise SiteModelCandidateTreeExecutionError(f"{label} is not UTF-8 encodable") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SiteModelCandidateTreeExecutionError("wrong candidate-tree issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SiteModelCandidateTreeExecutionError("invalid execution SHA")
    if type(body) is not str:
        raise SiteModelCandidateTreeExecutionError("candidate-tree request is not text")
    if _utf8_size(body, label="candidate-tree request") > MAX_REQUEST_UTF8_BYTES:
        raise SiteModelCandidateTreeExecutionError("candidate-tree request exceeds publication limit")
    if body.count(REQUEST_MARKER) != 1:
        raise SiteModelCandidateTreeExecutionError("invalid candidate-tree request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelCandidateTreeExecutionError("candidate-tree request envelope is not canonical")
    request = _strict_loads(after.strip(), label="candidate-tree request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteModelCandidateTreeExecutionError("candidate-tree request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise SiteModelCandidateTreeExecutionError("candidate-tree request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise SiteModelCandidateTreeExecutionError("candidate-tree request issue drifted")
    if request["target_sha"] != execution_sha:
        raise SiteModelCandidateTreeExecutionError("candidate-tree request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SiteModelCandidateTreeExecutionError("invalid requester identity")
    return request


def _canonical_path(value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed path is invalid")
    if _utf8_size(value, label="candidate-tree changed path") > profile.MAX_PATH_UTF8_BYTES:
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed path exceeds policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed path has control characters")
    if "\\" in value:
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed path is not canonical POSIX")
    pure = PurePosixPath(value)
    if pure.is_absolute() or str(pure) != value or any(part in ("", ".", "..") for part in pure.parts):
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed path is not canonical POSIX")
    return value


def _false_authority_fields() -> tuple[str, ...]:
    return (
        "provider_file_bytes_read",
        "external_bytes_persisted",
        "exact_kosovo_generator_commit_verified",
        "crs_coordinate_semantics_verified",
        "missingness_semantics_verified",
        "site_model_compatibility_verified",
        "publication_authorized",
        "model_use_authorized",
    )


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise SiteModelCandidateTreeExecutionError("candidate-tree profile fields drifted")

    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("history_identity_sha256", profile.HISTORY_IDENTITY_SHA256),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteModelCandidateTreeExecutionError(f"candidate-tree profile drifted at {field}")
    for field in _false_authority_fields():
        if value.get(field) is not False:
            raise SiteModelCandidateTreeExecutionError(f"candidate-tree profile widened {field}")

    expected_commits = [item["commit_sha"] for item in profile.CANDIDATE_HISTORY]
    candidate_profiles = value["candidate_tree_profiles"]
    if type(candidate_profiles) is not list or len(candidate_profiles) != len(expected_commits):
        raise SiteModelCandidateTreeExecutionError("candidate-tree profile candidate count drifted")
    observed_commits: list[str] = []
    for item in candidate_profiles:
        if type(item) is not dict or set(item) != _CANDIDATE_PROFILE_FIELDS:
            raise SiteModelCandidateTreeExecutionError("candidate-tree candidate profile shape drifted")
        commit_sha = item["commit_sha"]
        if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
            raise SiteModelCandidateTreeExecutionError("candidate-tree candidate SHA is invalid")
        observed_commits.append(commit_sha)
        pages_read = item["pages_read"]
        entry_count = item["entry_count"]
        blob_count = item["blob_count"]
        if type(pages_read) is not int or isinstance(pages_read, bool) or not (1 <= pages_read <= profile.MAX_PAGES_PER_COMMIT):
            raise SiteModelCandidateTreeExecutionError("candidate-tree page count is invalid")
        if type(entry_count) is not int or isinstance(entry_count, bool) or not (1 <= entry_count <= profile.MAX_ENTRIES_PER_COMMIT):
            raise SiteModelCandidateTreeExecutionError("candidate-tree entry count is invalid")
        if type(blob_count) is not int or isinstance(blob_count, bool) or not (0 <= blob_count <= entry_count):
            raise SiteModelCandidateTreeExecutionError("candidate-tree blob count is invalid")
        digest = item["tree_identity_sha256"]
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise SiteModelCandidateTreeExecutionError("candidate-tree identity SHA-256 is invalid")
    if observed_commits != expected_commits:
        raise SiteModelCandidateTreeExecutionError("candidate-tree candidate identity/order drifted")

    changed_count = value["changed_blob_count"]
    changed = value["changed_blobs"]
    if type(changed_count) is not int or isinstance(changed_count, bool) or not (0 <= changed_count <= profile.MAX_CHANGED_BLOBS):
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed-blob count is invalid")
    if type(changed) is not list or len(changed) != changed_count:
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed-blob count disagrees")
    changed_digest = value["changed_blob_identity_sha256"]
    if type(changed_digest) is not str or _SHA256_RE.fullmatch(changed_digest) is None:
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed-blob SHA-256 is invalid")

    paths: list[str] = []
    for item in changed:
        if type(item) is not dict or set(item) != _CHANGED_BLOB_FIELDS:
            raise SiteModelCandidateTreeExecutionError("candidate-tree changed-blob shape drifted")
        path = _canonical_path(item["path"])
        paths.append(path)
        states = item["states"]
        if type(states) is not list or len(states) != len(expected_commits):
            raise SiteModelCandidateTreeExecutionError("candidate-tree changed-blob state count drifted")
        state_commits: list[str] = []
        state_identities: list[tuple[bool, str | None, str | None]] = []
        for state in states:
            if type(state) is not dict or set(state) != _CHANGED_STATE_FIELDS:
                raise SiteModelCandidateTreeExecutionError("candidate-tree changed state shape drifted")
            commit_sha = state["commit_sha"]
            if type(commit_sha) is not str or _SHA1_RE.fullmatch(commit_sha) is None:
                raise SiteModelCandidateTreeExecutionError("candidate-tree changed state SHA is invalid")
            state_commits.append(commit_sha)
            present = state["present"]
            if type(present) is not bool:
                raise SiteModelCandidateTreeExecutionError("candidate-tree changed state presence is invalid")
            mode = state["mode"]
            object_sha1 = state["object_sha1"]
            if present:
                if mode not in ("100644", "100755", "120000"):
                    raise SiteModelCandidateTreeExecutionError("candidate-tree changed state mode is invalid")
                if type(object_sha1) is not str or _SHA1_RE.fullmatch(object_sha1) is None:
                    raise SiteModelCandidateTreeExecutionError("candidate-tree changed state object SHA is invalid")
            elif mode is not None or object_sha1 is not None:
                raise SiteModelCandidateTreeExecutionError("candidate-tree absent state carries blob identity")
            state_identities.append((present, mode, object_sha1))
        if state_commits != expected_commits:
            raise SiteModelCandidateTreeExecutionError("candidate-tree changed state commit order drifted")
        if len(set(state_identities)) == 1:
            raise SiteModelCandidateTreeExecutionError("candidate-tree unchanged blob was published as changed")
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed paths are not canonical/unique")
    if _CHANGED_BLOB_IDENTITY(changed) != changed_digest:
        raise SiteModelCandidateTreeExecutionError("candidate-tree changed-blob identity does not match payload")
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


def _terminal_body(result: dict[str, Any]) -> str:
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    body = RESULT_MARKER + "\n" + encoded
    if _utf8_size(body, label="candidate-tree result") > MAX_TERMINAL_UTF8_BYTES:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result exceeds publication limit")
    return body


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    """Validate a trusted terminal fully, then scope dedup to its exact SHA."""
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise SiteModelCandidateTreeExecutionError("invalid execution SHA")
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if _utf8_size(body, label="candidate-tree result") > MAX_TERMINAL_UTF8_BYTES:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result exceeds publication limit")
    if body.count(RESULT_MARKER) != 1:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteModelCandidateTreeExecutionError("candidate-tree result envelope is malformed")
    result = _strict_loads(after.strip(), label="candidate-tree result")
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result fields drifted")
    if result["schema_version"] != RESULT_SCHEMA_VERSION or result["source_issue"] != SOURCE_ISSUE:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result identity drifted")
    target = result["target_sha"]
    observed_execution = result["execution_sha"]
    if (
        type(target) is not str
        or _SHA1_RE.fullmatch(target) is None
        or type(observed_execution) is not str
        or _SHA1_RE.fullmatch(observed_execution) is None
        or target != observed_execution
    ):
        raise SiteModelCandidateTreeExecutionError("candidate-tree result SHA binding is invalid")

    own_execution_sha = target
    for field, expected in _base_result(execution_sha=own_execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteModelCandidateTreeExecutionError(f"candidate-tree result drifted at {field}")
    status = result["status"]
    if status == "pass":
        if result["failure_class"] is not None:
            raise SiteModelCandidateTreeExecutionError("candidate-tree PASS carries failure class")
        validate_profile(result["profile"])
    elif status == "blocked":
        if result["failure_class"] not in ("metadata_acquisition_failure", "result_publication_limit") or result["profile"] is not None:
            raise SiteModelCandidateTreeExecutionError("candidate-tree blocked result widened evidence")
    elif status == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise SiteModelCandidateTreeExecutionError("candidate-tree duplicate result carries evidence")
    else:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result has non-terminal status")
    return own_execution_sha == execution_sha


def _require_execution_authority() -> None:
    if (
        _PROFILE is not _CANONICAL_PROFILE
        or profile.profile_candidate_trees is not _CANONICAL_PROFILE
        or _FETCH_COMMENTS is not _CANONICAL_FETCH_COMMENTS
        or fetch_repository_comments is not _CANONICAL_FETCH_COMMENTS
        or _CHANGED_BLOB_IDENTITY is not _CANONICAL_CHANGED_BLOB_IDENTITY
        or profile._changed_blob_identity_sha256 is not _CANONICAL_CHANGED_BLOB_IDENTITY
    ):
        raise SiteModelCandidateTreeExecutionError("trusted candidate-tree execution authority drifted")


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise SiteModelCandidateTreeExecutionError("candidate-tree result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SiteModelCandidateTreeExecutionError("candidate-tree ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body"), execution_sha=execution_sha):
            return True
    return False


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    _require_execution_authority()
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        candidate_profile = _PROFILE()
    except profile.SiteModelCandidateTreeError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "metadata_acquisition_failure",
            "profile": None,
        }
        _terminal_body(result)
        return result

    validate_profile(candidate_profile)
    result = {
        **_base_result(execution_sha=execution_sha),
        "status": "pass",
        "failure_class": None,
        "profile": candidate_profile,
    }
    try:
        body = _terminal_body(result)
    except SiteModelCandidateTreeExecutionError as exc:
        if str(exc) != "candidate-tree result exceeds publication limit":
            raise
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "result_publication_limit",
            "profile": None,
        }
        body = _terminal_body(result)
    parse_terminal_result(body, execution_sha=execution_sha)
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
        raise SiteModelCandidateTreeExecutionError("GitHub ledger token is absent")
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
