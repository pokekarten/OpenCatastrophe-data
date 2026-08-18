# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed ESRM20 exposure v1.0 tree profile."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from scripts import profile_esrm20_exposure_v10_tree as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-exposure-v10-tree-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-exposure-v10-tree-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-exposure-v10-tree-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-exposure-v10-tree-result-v1"
SOURCE_ISSUE = 282
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
    "dataset_id",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "subtree_path",
    "pages_read",
    "entry_count",
    "blob_count",
    "tree_count",
    "tree_identity_sha256",
    "kosovo_named_xml_candidates",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "exact_kosovo_exposure_selected",
    "value_structural_wiring_verified",
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
    "exact_kosovo_exposure_selected",
    "value_structural_wiring_verified",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.profile_v10_tree
_FETCH_COMMENTS = fetch_repository_comments


class ExposureTreeExecutionError(RuntimeError):
    """Fail-closed error for trusted exposure-tree execution."""


def _pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise ExposureTreeExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ExposureTreeExecutionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise ExposureTreeExecutionError("wrong exposure-tree issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise ExposureTreeExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise ExposureTreeExecutionError("invalid exposure-tree request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ExposureTreeExecutionError("exposure-tree request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_PAIRS, parse_constant=_REJECT_CONSTANT
        )
    except ExposureTreeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ExposureTreeExecutionError("invalid exposure-tree request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ExposureTreeExecutionError("exposure-tree request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ExposureTreeExecutionError("exposure-tree request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise ExposureTreeExecutionError("exposure-tree request issue drifted")
    if request["target_sha"] != execution_sha:
        raise ExposureTreeExecutionError("exposure-tree request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ExposureTreeExecutionError("invalid requester identity")
    return request


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ExposureTreeExecutionError(f"{field} must be bounded text")
    if len(value.encode("utf-8")) > profile.MAX_PATH_UTF8_BYTES:
        raise ExposureTreeExecutionError(f"{field} exceeds bounded policy")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ExposureTreeExecutionError(f"{field} contains control characters")
    return value


def _validate_candidate(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {
        "mode",
        "object_sha1",
        "path",
        "type",
    }:
        raise ExposureTreeExecutionError("exposure candidate shape drifted")
    if value["type"] != "blob" or value["mode"] not in ("100644", "100755"):
        raise ExposureTreeExecutionError("exposure candidate type/mode drifted")
    object_sha1 = value["object_sha1"]
    if type(object_sha1) is not str or _SHA_RE.fullmatch(object_sha1) is None:
        raise ExposureTreeExecutionError("exposure candidate object SHA is invalid")
    path = _BOUNDED_TEXT(value["path"], field="exposure candidate path")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or str(pure) != path
        or any(part in ("", ".", "..") for part in pure.parts)
        or "\\" in path
        or not path.startswith(profile.SUBTREE_PATH + "/")
    ):
        raise ExposureTreeExecutionError("exposure candidate path is not canonical")
    if profile.PROVIDER_KOSOVO_TOKEN not in pure.name or not pure.name.endswith(".xml"):
        raise ExposureTreeExecutionError("exposure candidate provider naming drifted")
    return {
        "mode": value["mode"],
        "object_sha1": object_sha1,
        "path": path,
        "type": "blob",
    }


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise ExposureTreeExecutionError("exposure profile fields drifted")
    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", profile.DATASET_ID),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("release_tag", profile.RELEASE_TAG),
        ("commit_sha", profile.EXPECTED_COMMIT_SHA),
        ("subtree_path", profile.SUBTREE_PATH),
        ("provider_file_bytes_read", False),
        ("external_bytes_persisted", False),
        ("exact_kosovo_exposure_selected", False),
        ("value_structural_wiring_verified", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ExposureTreeExecutionError(f"exposure profile drifted at {field}")
    tree_sha = value["tree_identity_sha256"]
    if type(tree_sha) is not str or _SHA256_RE.fullmatch(tree_sha) is None:
        raise ExposureTreeExecutionError("exposure tree identity SHA-256 is invalid")
    for field in ("pages_read", "entry_count", "blob_count", "tree_count"):
        observed = value[field]
        if type(observed) is not int or isinstance(observed, bool) or observed < 0:
            raise ExposureTreeExecutionError(f"exposure {field} is invalid")
    if not (1 <= value["pages_read"] <= profile.MAX_TREE_PAGES):
        raise ExposureTreeExecutionError("exposure pages_read is outside policy")
    if not (1 <= value["entry_count"] <= profile.MAX_TREE_ENTRIES):
        raise ExposureTreeExecutionError("exposure entry_count is outside policy")
    if value["entry_count"] != value["blob_count"] + value["tree_count"]:
        raise ExposureTreeExecutionError("exposure entry counts disagree")
    candidates = value["kosovo_named_xml_candidates"]
    if (
        type(candidates) is not list
        or not (1 <= len(candidates) <= profile.MAX_KOSOVO_XML_CANDIDATES)
    ):
        raise ExposureTreeExecutionError("exposure candidate cardinality is invalid")
    canonical = [_VALIDATE_CANDIDATE(item) for item in candidates]
    if canonical != sorted(canonical, key=lambda item: (item["path"], item["object_sha1"])):
        raise ExposureTreeExecutionError("exposure candidates are not canonical")
    if len({item["path"] for item in canonical}) != len(canonical):
        raise ExposureTreeExecutionError("exposure candidate paths are not unique")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "exact_kosovo_exposure_selected": False,
        "value_structural_wiring_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_result(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise ExposureTreeExecutionError("exposure-tree result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ExposureTreeExecutionError("exposure-tree result envelope is malformed")
    if len(after.encode("utf-8")) > MAX_RESULT_UTF8_BYTES:
        raise ExposureTreeExecutionError("exposure-tree result exceeds policy")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_PAIRS, parse_constant=_REJECT_CONSTANT
        )
    except ExposureTreeExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ExposureTreeExecutionError("exposure-tree result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise ExposureTreeExecutionError("exposure-tree result fields drifted")
    return result


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _PARSE_RESULT(body)
    if result is None:
        return False
    for field, expected in _BASE_RESULT(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ExposureTreeExecutionError(f"exposure-tree result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise ExposureTreeExecutionError("PASS carries a failure class")
        _VALIDATE_PROFILE(result["profile"])
        return True
    if result["status"] == "blocked":
        if (
            result["failure_class"] not in profile.FAILURE_CLASSES
            or result["profile"] is not None
        ):
            raise ExposureTreeExecutionError("blocked result widened evidence")
        return True
    if result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise ExposureTreeExecutionError("duplicate result carries evidence")
        return True
    raise ExposureTreeExecutionError("result has non-terminal status")


def _terminal_result_execution_sha(body: object) -> str | None:
    result = _PARSE_RESULT(body)
    if result is None:
        return None
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if (
        type(target_sha) is not str
        or _SHA_RE.fullmatch(target_sha) is None
        or type(execution_sha) is not str
        or _SHA_RE.fullmatch(execution_sha) is None
        or target_sha != execution_sha
    ):
        raise ExposureTreeExecutionError("result SHA identity is invalid")
    _PARSE_TERMINAL_RESULT(body, execution_sha=execution_sha)
    return execution_sha


_PAIRS = _pairs
_REJECT_CONSTANT = _reject_constant
_VALIDATE_REQUEST = validate_request
_BOUNDED_TEXT = _bounded_text
_VALIDATE_CANDIDATE = _validate_candidate
_VALIDATE_PROFILE = validate_profile
_BASE_RESULT = _base_result
_PARSE_RESULT = _parse_result
_PARSE_TERMINAL_RESULT = parse_terminal_result
_TERMINAL_RESULT_EXECUTION_SHA = _terminal_result_execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise ExposureTreeExecutionError("invalid execution SHA")
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise ExposureTreeExecutionError("exposure-tree result ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise ExposureTreeExecutionError("exposure-tree ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        own_sha = _TERMINAL_RESULT_EXECUTION_SHA(comment.get("body"))
        if own_sha == execution_sha:
            return True
    return False


def _execute_for_test(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    profile_fn: Callable[[], dict[str, Any]],
    terminal_fn: Callable[..., bool],
) -> dict[str, Any]:
    if terminal_fn(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_BASE_RESULT(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        value = profile_fn()
        _VALIDATE_PROFILE(value)
    except profile.ExposureTreeProfileError as exc:
        if exc.failure_class not in profile.FAILURE_CLASSES:
            raise ExposureTreeExecutionError("profile failed without bounded class") from exc
        return {
            **_BASE_RESULT(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": exc.failure_class,
            "profile": None,
        }
    return {
        **_BASE_RESULT(execution_sha=execution_sha),
        "status": "pass",
        "failure_class": None,
        "profile": value,
    }


_HAS_TERMINAL_RESULT = has_terminal_result
_EXECUTE_FOR_TEST = _execute_for_test


def _require_production_authority() -> None:
    if profile.profile_v10_tree is not _PROFILE:
        raise ExposureTreeExecutionError("trusted exposure profile authority drifted")
    if fetch_repository_comments is not _FETCH_COMMENTS:
        raise ExposureTreeExecutionError("trusted exposure ledger authority drifted")
    functions = (
        (_pairs, _PAIRS),
        (_reject_constant, _REJECT_CONSTANT),
        (validate_request, _VALIDATE_REQUEST),
        (_bounded_text, _BOUNDED_TEXT),
        (_validate_candidate, _VALIDATE_CANDIDATE),
        (validate_profile, _VALIDATE_PROFILE),
        (_base_result, _BASE_RESULT),
        (_parse_result, _PARSE_RESULT),
        (parse_terminal_result, _PARSE_TERMINAL_RESULT),
        (_terminal_result_execution_sha, _TERMINAL_RESULT_EXECUTION_SHA),
        (has_terminal_result, _HAS_TERMINAL_RESULT),
        (_execute_for_test, _EXECUTE_FOR_TEST),
    )
    if any(observed is not expected for observed, expected in functions):
        raise ExposureTreeExecutionError("trusted exposure action authority drifted")


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()
    return _EXECUTE_FOR_TEST(
        repository=repository,
        token=token,
        execution_sha=execution_sha,
        profile_fn=_PROFILE,
        terminal_fn=_HAS_TERMINAL_RESULT,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True, type=int)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--token-env", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    _require_production_authority()
    _VALIDATE_REQUEST(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    token = os.environ.get(args.token_env)
    if type(token) is not str or not token:
        raise ExposureTreeExecutionError("missing GitHub token")
    result = execute_profile(
        repository=args.repository,
        token=token,
        execution_sha=args.execution_sha,
    )
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
