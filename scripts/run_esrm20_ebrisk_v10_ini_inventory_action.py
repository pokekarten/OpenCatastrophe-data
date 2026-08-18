# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for the fixed ESRM20 v1.0 configuration INI inventory."""

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

from scripts import profile_esrm20_ebrisk_v10_ini_inventory as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-ebrisk-v10-ini-inventory-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-ebrisk-v10-ini-inventory-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-ebrisk-v10-ini-inventory-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-ebrisk-v10-ini-inventory-result-v1"
SOURCE_ISSUE = 281
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 64_000
BLOCKED_FAILURE_CLASS = "inventory_profile_failure"

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
    "configuration_root",
    "tree_entry_count",
    "source_tree_identity_sha256",
    "ini_blob_count",
    "ini_inventory_sha256",
    "ini_blobs",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "historical_group_assignment_authorized",
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
    "historical_group_assignment_authorized",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.profile_v10_ini_inventory
_FETCH_COMMENTS = fetch_repository_comments


class EbriskIniInventoryExecutionError(RuntimeError):
    """Fail-closed error for the dedicated trusted-main inventory action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EbriskIniInventoryExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise EbriskIniInventoryExecutionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise EbriskIniInventoryExecutionError("wrong ebrisk inventory issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskIniInventoryExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise EbriskIniInventoryExecutionError("invalid ebrisk inventory request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory request envelope is not canonical"
        )
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except EbriskIniInventoryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskIniInventoryExecutionError(
            "invalid ebrisk inventory request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise EbriskIniInventoryExecutionError("ebrisk inventory request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise EbriskIniInventoryExecutionError("ebrisk inventory request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise EbriskIniInventoryExecutionError("ebrisk inventory request issue drifted")
    if request["target_sha"] != execution_sha:
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory request target is not trusted main"
        )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise EbriskIniInventoryExecutionError("invalid requester identity")
    return request


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise EbriskIniInventoryExecutionError(f"{field} must be bounded text")
    if len(value.encode("utf-8")) > profile.MAX_PATH_UTF8_BYTES:
        raise EbriskIniInventoryExecutionError(f"{field} exceeds bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise EbriskIniInventoryExecutionError(f"{field} contains control characters")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise EbriskIniInventoryExecutionError("ebrisk inventory profile fields drifted")
    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("release_tag", profile.RELEASE_TAG),
        ("commit_sha", profile.EXPECTED_COMMIT_SHA),
        ("configuration_root", profile.CONFIGURATION_ROOT),
        ("provider_file_bytes_read", False),
        ("external_bytes_persisted", False),
        ("historical_group_assignment_authorized", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskIniInventoryExecutionError(
                f"ebrisk inventory profile drifted at {field}"
            )

    tree_count = value["tree_entry_count"]
    if (
        type(tree_count) is not int
        or isinstance(tree_count, bool)
        or not 1 <= tree_count <= profile.MAX_TREE_ENTRIES
    ):
        raise EbriskIniInventoryExecutionError("ebrisk inventory tree count is invalid")
    ini_count = value["ini_blob_count"]
    if (
        type(ini_count) is not int
        or isinstance(ini_count, bool)
        or not 0 <= ini_count <= profile.MAX_INI_BLOBS
    ):
        raise EbriskIniInventoryExecutionError("ebrisk inventory INI count is invalid")
    for field in ("source_tree_identity_sha256", "ini_inventory_sha256"):
        observed = value[field]
        if type(observed) is not str or _SHA256_RE.fullmatch(observed) is None:
            raise EbriskIniInventoryExecutionError(
                f"ebrisk inventory {field} is invalid"
            )

    blobs = value["ini_blobs"]
    if type(blobs) is not list or len(blobs) != ini_count:
        raise EbriskIniInventoryExecutionError("ebrisk inventory blob count disagrees")
    expected_order = sorted(
        blobs,
        key=lambda item: (
            item.get("path") if type(item) is dict else "",
            item.get("mode") if type(item) is dict else "",
            item.get("object_sha1") if type(item) is dict else "",
        ),
    )
    if blobs != expected_order:
        raise EbriskIniInventoryExecutionError("ebrisk inventory blobs are not canonical")

    seen_paths: set[str] = set()
    root_prefix = profile.CONFIGURATION_ROOT + "/"
    for item in blobs:
        if type(item) is not dict or set(item) != {
            "basename",
            "path",
            "mode",
            "object_sha1",
        }:
            raise EbriskIniInventoryExecutionError("ebrisk inventory blob shape drifted")
        basename = _bounded_text(item["basename"], field="ebrisk inventory basename")
        path = _bounded_text(item["path"], field="ebrisk inventory path")
        pure = PurePosixPath(path)
        if (
            pure.is_absolute()
            or str(pure) != path
            or any(part in ("", ".", "..") for part in pure.parts)
            or not path.startswith(root_prefix)
        ):
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory path is not under exact configuration root"
            )
        if pure.name != basename:
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory path/basename identity drifted"
            )
        if not basename.endswith(profile.INI_SUFFIX):
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory basename is not exact lowercase INI"
            )
        if item["mode"] not in {"100644", "100755"}:
            raise EbriskIniInventoryExecutionError("ebrisk inventory blob mode drifted")
        object_sha1 = item["object_sha1"]
        if type(object_sha1) is not str or _SHA_RE.fullmatch(object_sha1) is None:
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory object SHA-1 is invalid"
            )
        if path in seen_paths:
            raise EbriskIniInventoryExecutionError("ebrisk inventory paths are not unique")
        seen_paths.add(path)
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


def _parse_result(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise EbriskIniInventoryExecutionError("ebrisk inventory result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EbriskIniInventoryExecutionError("ebrisk inventory result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except EbriskIniInventoryExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory result JSON is malformed"
        ) from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise EbriskIniInventoryExecutionError("ebrisk inventory result fields drifted")
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise EbriskIniInventoryExecutionError("ebrisk inventory result schema drifted")
    return result


def _terminal_result_execution_sha(body: object) -> str | None:
    result = _parse_result(body)
    if result is None:
        return None
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if type(result.get("source_issue")) is not int or result["source_issue"] != SOURCE_ISSUE:
        raise EbriskIniInventoryExecutionError("ebrisk inventory result issue drifted")
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None:
        raise EbriskIniInventoryExecutionError("ebrisk inventory result target SHA is invalid")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory result execution SHA is invalid"
        )
    if target_sha != execution_sha:
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory result target/execution SHA mismatch"
        )
    return execution_sha


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _parse_result(body)
    if result is None:
        return False
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EbriskIniInventoryExecutionError(
                f"ebrisk inventory result drifted at {field}"
            )
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory PASS carries failure class"
            )
        validate_profile(result["profile"])
        return True
    if result["status"] == "blocked":
        if result["failure_class"] != BLOCKED_FAILURE_CLASS or result["profile"] is not None:
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory blocked result widened evidence"
            )
        return True
    if result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory duplicate result carries evidence"
            )
        return True
    raise EbriskIniInventoryExecutionError("ebrisk inventory result has non-terminal status")


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EbriskIniInventoryExecutionError("invalid execution SHA")
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory result ledger is incomplete"
        ) from exc
    for comment in comments:
        if type(comment) is not dict:
            raise EbriskIniInventoryExecutionError(
                "ebrisk inventory ledger contains non-object"
            )
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_execution_sha = _terminal_result_execution_sha(body)
        if own_execution_sha is None:
            continue
        terminal = parse_terminal_result(body, execution_sha=own_execution_sha)
        if own_execution_sha == execution_sha and terminal:
            return True
    return False


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if (
        profile.profile_v10_ini_inventory is not _PROFILE
        or fetch_repository_comments is not _FETCH_COMMENTS
    ):
        raise EbriskIniInventoryExecutionError(
            "trusted ebrisk inventory execution authority drifted"
        )
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        inventory_profile = _PROFILE()
        validate_profile(inventory_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": inventory_profile,
        }
    except profile.EbriskIniInventoryError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": BLOCKED_FAILURE_CLASS,
            "profile": None,
        }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise EbriskIniInventoryExecutionError(
            "ebrisk inventory result exceeds publication limit"
        )
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
        raise EbriskIniInventoryExecutionError("GitHub ledger token is absent")
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
