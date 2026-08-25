# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed ESRM20 ebrisk v1.0 tree profile."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ""):  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import profile_esrm20_ebrisk_v10_tree as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-ebrisk-v10-tree-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-ebrisk-v10-tree-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-ebrisk-v10-tree-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-ebrisk-v10-tree-result-v1"
SOURCE_ISSUE = 281
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 64_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "pages_read",
    "entry_count",
    "blob_count",
    "tree_count",
    "tree_identity_sha256",
    "top_level_entry_counts",
    "ebrisk_templates",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "historical_group_assignment_authorized",
    "publication_authorized",
    "model_use_authorized",
}
LEGACY_BLOCKED_FAILURE_CLASS = "metadata_acquisition_failure"
_BLOCKED_FAILURE_CLASSES = frozenset(
    {LEGACY_BLOCKED_FAILURE_CLASS, *profile.FAILURE_CLASSES}
)

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
    "historical_group_assignment_authorized",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.profile_v10_tree
_FETCH_COMMENTS = fetch_repository_comments


class EbriskTreeExecutionError(RuntimeError):
    """Fail-closed error for the dedicated ebrisk metadata action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EbriskTreeExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise EbriskTreeExecutionError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise EbriskTreeExecutionError("wrong ebrisk metadata issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskTreeExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise EbriskTreeExecutionError("invalid ebrisk request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskTreeExecutionError("ebrisk request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EbriskTreeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskTreeExecutionError("invalid ebrisk request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise EbriskTreeExecutionError("ebrisk request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise EbriskTreeExecutionError("ebrisk request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise EbriskTreeExecutionError("ebrisk request issue drifted")
    if request["target_sha"] != execution_sha:
        raise EbriskTreeExecutionError("ebrisk request target is not trusted main")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise EbriskTreeExecutionError("invalid requester identity")
    return request


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise EbriskTreeExecutionError(f"{field} must be bounded text")
    if len(value.encode("utf-8")) > profile.MAX_PATH_UTF8_BYTES:
        raise EbriskTreeExecutionError(f"{field} exceeds bounded policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise EbriskTreeExecutionError(f"{field} contains control characters")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise EbriskTreeExecutionError("ebrisk profile fields drifted")
    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("release_tag", profile.RELEASE_TAG),
        ("commit_sha", profile.EXPECTED_COMMIT_SHA),
        ("provider_file_bytes_read", False),
        ("external_bytes_persisted", False),
        ("historical_group_assignment_authorized", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskTreeExecutionError(f"ebrisk profile drifted at {field}")
    if type(value["tree_identity_sha256"]) is not str or _SHA256_RE.fullmatch(value["tree_identity_sha256"]) is None:
        raise EbriskTreeExecutionError("ebrisk tree identity SHA-256 is invalid")
    for field in ("pages_read", "entry_count", "blob_count", "tree_count"):
        observed = value[field]
        if type(observed) is not int or isinstance(observed, bool) or observed < 0:
            raise EbriskTreeExecutionError(f"ebrisk {field} is invalid")
    if not (1 <= value["pages_read"] <= profile.MAX_PAGES):
        raise EbriskTreeExecutionError("ebrisk page count is invalid")
    if not (1 <= value["entry_count"] <= profile.MAX_ENTRIES):
        raise EbriskTreeExecutionError("ebrisk entry count is invalid")
    if value["entry_count"] != value["blob_count"] + value["tree_count"]:
        raise EbriskTreeExecutionError("ebrisk entry counts disagree")

    top = value["top_level_entry_counts"]
    if type(top) is not dict:
        raise EbriskTreeExecutionError("ebrisk top-level counts are invalid")
    if list(top) != sorted(top):
        raise EbriskTreeExecutionError("ebrisk top-level counts are not canonical")
    for key, count in top.items():
        _bounded_text(key, field="ebrisk top-level name")
        if type(count) is not int or isinstance(count, bool) or count < 1:
            raise EbriskTreeExecutionError("ebrisk top-level count is invalid")
    if sum(top.values()) != value["entry_count"]:
        raise EbriskTreeExecutionError("ebrisk top-level counts do not cover inventory")

    templates = value["ebrisk_templates"]
    if type(templates) is not list or len(templates) != len(profile.TEMPLATE_BASENAMES):
        raise EbriskTreeExecutionError("ebrisk template set is incomplete")
    expected_order = list(profile.TEMPLATE_BASENAMES)
    observed_basenames: list[str] = []
    observed_paths: set[str] = set()
    for item in templates:
        if type(item) is not dict or set(item) != {"basename", "path", "type", "object_sha1"}:
            raise EbriskTreeExecutionError("ebrisk template shape drifted")
        basename = item["basename"]
        if basename not in profile.TEMPLATE_BASENAMES:
            raise EbriskTreeExecutionError("ebrisk template basename drifted")
        path = _bounded_text(item["path"], field="ebrisk template path")
        pure = PurePosixPath(path)
        if (
            pure.is_absolute()
            or str(pure) != path
            or any(part in ("", ".", "..") for part in pure.parts)
        ):
            raise EbriskTreeExecutionError("ebrisk template path is not canonical relative POSIX")
        if pure.name != basename:
            raise EbriskTreeExecutionError("ebrisk template path/basename identity drifted")
        if item["type"] != "blob":
            raise EbriskTreeExecutionError("ebrisk template is not a blob")
        if type(item["object_sha1"]) is not str or _SHA_RE.fullmatch(item["object_sha1"]) is None:
            raise EbriskTreeExecutionError("ebrisk template object SHA is invalid")
        if path in observed_paths:
            raise EbriskTreeExecutionError("ebrisk template paths are not unique")
        observed_basenames.append(basename)
        observed_paths.add(path)
    if observed_basenames != expected_order:
        raise EbriskTreeExecutionError("ebrisk templates are not in canonical provider order")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_group_assignment_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _bounded_result_payload(after: str) -> str:
    payload = after.strip()
    try:
        payload_size = len(payload.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise EbriskTreeExecutionError("ebrisk result is not valid UTF-8") from exc
    if payload_size > MAX_RESULT_UTF8_BYTES:
        raise EbriskTreeExecutionError("ebrisk result exceeds publication limit")
    return payload


def _terminal_result_execution_sha(body: object) -> str | None:
    """Return a terminal result's own SHA after fail-closed envelope checks."""
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise EbriskTreeExecutionError("ebrisk result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskTreeExecutionError("ebrisk result envelope is malformed")
    payload = _bounded_result_payload(after)
    try:
        result = json.loads(payload, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EbriskTreeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskTreeExecutionError("ebrisk result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise EbriskTreeExecutionError("ebrisk result fields drifted")
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise EbriskTreeExecutionError("ebrisk result schema drifted")
    if type(result.get("source_issue")) is not int or result["source_issue"] != SOURCE_ISSUE:
        raise EbriskTreeExecutionError("ebrisk result source issue drifted")
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None:
        raise EbriskTreeExecutionError("ebrisk result target SHA is invalid")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskTreeExecutionError("ebrisk result execution SHA is invalid")
    if target_sha != execution_sha:
        raise EbriskTreeExecutionError("ebrisk result target/execution SHA mismatch")
    return execution_sha


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise EbriskTreeExecutionError("ebrisk result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskTreeExecutionError("ebrisk result envelope is malformed")
    payload = _bounded_result_payload(after)
    try:
        result = json.loads(payload, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EbriskTreeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskTreeExecutionError("ebrisk result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise EbriskTreeExecutionError("ebrisk result fields drifted")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskTreeExecutionError(f"ebrisk result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise EbriskTreeExecutionError("ebrisk PASS result carries failure class")
        validate_profile(result["profile"])
        return True
    if result["status"] == "blocked":
        if (
            result["failure_class"] not in _BLOCKED_FAILURE_CLASSES
            or result["profile"] is not None
        ):
            raise EbriskTreeExecutionError("ebrisk blocked result widened evidence")
        return True
    if result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise EbriskTreeExecutionError("ebrisk duplicate result carries evidence")
        return True
    raise EbriskTreeExecutionError("ebrisk result has non-terminal status")


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskTreeExecutionError("invalid execution SHA")
    try:
        comments = _FETCH_COMMENTS(repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES)
    except LedgerError as exc:
        raise EbriskTreeExecutionError("ebrisk result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise EbriskTreeExecutionError("ebrisk ledger contains non-object")
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
    if profile.profile_v10_tree is not _PROFILE or fetch_repository_comments is not _FETCH_COMMENTS:
        raise EbriskTreeExecutionError("trusted ebrisk execution authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        tree_profile = _PROFILE()
        validate_profile(tree_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": tree_profile,
        }
    except profile.EbriskTreeProfileError as exc:
        if exc.failure_class not in profile.FAILURE_CLASSES:
            raise EbriskTreeExecutionError(
                "ebrisk profiler failure is not safely classified"
            ) from exc
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": exc.failure_class,
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise EbriskTreeExecutionError("ebrisk result exceeds publication limit")
    parse_terminal_result(RESULT_MARKER + "\n" + encoded.decode("utf-8"), execution_sha=execution_sha)
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
        raise EbriskTreeExecutionError("GitHub ledger token is absent")
    result = execute_profile(repository=args.repository, token=token, execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
