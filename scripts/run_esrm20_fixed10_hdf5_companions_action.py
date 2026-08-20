# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main wrapper for fixed ESRM20 source-model HDF5 companion metadata."""

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

from scripts import profile_esrm20_fixed10_hdf5_companions as profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-fixed10-hdf5-companions-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-fixed10-hdf5-companions-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-fixed10-hdf5-companions-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-fixed10-hdf5-companions-result-v1"
SOURCE_ISSUE = 281
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 64_000
BLOCKED_FAILURE_CLASS = "hdf5_companion_profile_failure"

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
    "source_tree_entry_count",
    "source_tree_identity_sha256",
    "source_xml_count",
    "candidate_hdf5_count",
    "present_hdf5_count",
    "absent_hdf5_count",
    "companion_inventory_sha256",
    "companions",
    "provider_file_bytes_read",
    "hdf5_byte_identity_verified",
    "transitive_dependency_byte_closure_verified",
    "runtime_compatibility_verified",
    "external_bytes_persisted",
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
    "hdf5_byte_identity_verified",
    "transitive_dependency_byte_closure_verified",
    "runtime_compatibility_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}

_PROFILE = profile.profile_fixed10_hdf5_companions
_FETCH_COMMENTS = fetch_repository_comments


class Hdf5CompanionExecutionError(RuntimeError):
    """Fail-closed error for the dedicated trusted-main metadata action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Hdf5CompanionExecutionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise Hdf5CompanionExecutionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise Hdf5CompanionExecutionError("wrong HDF5 companion issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Hdf5CompanionExecutionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise Hdf5CompanionExecutionError("invalid HDF5 companion request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Hdf5CompanionExecutionError("HDF5 companion request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except Hdf5CompanionExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Hdf5CompanionExecutionError("invalid HDF5 companion request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Hdf5CompanionExecutionError("HDF5 companion request fields drifted")
    if request["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise Hdf5CompanionExecutionError("HDF5 companion request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != SOURCE_ISSUE:
        raise Hdf5CompanionExecutionError("HDF5 companion request issue drifted")
    if request["target_sha"] != execution_sha:
        raise Hdf5CompanionExecutionError("HDF5 companion request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Hdf5CompanionExecutionError("invalid requester identity")
    return request


def _bounded_path(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise Hdf5CompanionExecutionError(f"{field} must be bounded text")
    if len(value.encode("utf-8")) > profile.MAX_PATH_UTF8_BYTES:
        raise Hdf5CompanionExecutionError(f"{field} exceeds bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise Hdf5CompanionExecutionError(f"{field} contains control characters")
    if "\\" in value:
        raise Hdf5CompanionExecutionError(f"{field} is not canonical relative POSIX")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or str(pure) != value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise Hdf5CompanionExecutionError(f"{field} is not canonical relative POSIX")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise Hdf5CompanionExecutionError("HDF5 companion profile fields drifted")

    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("project_id", profile.PROJECT_ID),
        ("project_path", profile.PROJECT_PATH),
        ("release_tag", profile.RELEASE_TAG),
        ("commit_sha", profile.EXPECTED_COMMIT_SHA),
        ("source_xml_count", profile.EXPECTED_SOURCE_COUNT),
        ("candidate_hdf5_count", profile.EXPECTED_SOURCE_COUNT),
        ("provider_file_bytes_read", False),
        ("hdf5_byte_identity_verified", False),
        ("transitive_dependency_byte_closure_verified", False),
        ("runtime_compatibility_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Hdf5CompanionExecutionError(f"HDF5 companion profile drifted at {field}")

    tree_count = value["source_tree_entry_count"]
    if (
        type(tree_count) is not int
        or isinstance(tree_count, bool)
        or not 1 <= tree_count <= profile.MAX_TREE_ENTRIES
    ):
        raise Hdf5CompanionExecutionError("HDF5 companion tree count is invalid")

    for field in ("source_tree_identity_sha256", "companion_inventory_sha256"):
        observed = value[field]
        if type(observed) is not str or _SHA256_RE.fullmatch(observed) is None:
            raise Hdf5CompanionExecutionError(f"HDF5 companion {field} is invalid")

    present = value["present_hdf5_count"]
    absent = value["absent_hdf5_count"]
    for field, count in (("present", present), ("absent", absent)):
        if (
            type(count) is not int
            or isinstance(count, bool)
            or not 0 <= count <= profile.EXPECTED_SOURCE_COUNT
        ):
            raise Hdf5CompanionExecutionError(f"HDF5 companion {field} count is invalid")
    if present + absent != profile.EXPECTED_SOURCE_COUNT:
        raise Hdf5CompanionExecutionError("HDF5 companion counts disagree")

    companions = value["companions"]
    if type(companions) is not list or len(companions) != profile.EXPECTED_SOURCE_COUNT:
        raise Hdf5CompanionExecutionError("HDF5 companion list is incomplete")

    observed_present = 0
    for expected_source, item in zip(profile.SOURCE_XML_PATHS, companions, strict=True):
        if type(item) is not dict or set(item) != {
            "source_xml_path",
            "candidate_hdf5_path",
            "present",
            "mode",
            "object_sha1",
        }:
            raise Hdf5CompanionExecutionError("HDF5 companion item shape drifted")
        source_path = _bounded_path(item["source_xml_path"], field="source XML path")
        if source_path != expected_source:
            raise Hdf5CompanionExecutionError("fixed source XML order/path drifted")
        if not source_path.endswith(".xml"):
            raise Hdf5CompanionExecutionError("fixed source path is not lowercase XML")
        candidate_path = _bounded_path(
            item["candidate_hdf5_path"], field="candidate HDF5 path"
        )
        if candidate_path != str(PurePosixPath(source_path).with_suffix(".hdf5")):
            raise Hdf5CompanionExecutionError("same-stem HDF5 derivation drifted")
        if type(item["present"]) is not bool:
            raise Hdf5CompanionExecutionError("HDF5 companion presence is not boolean")
        if item["present"]:
            observed_present += 1
            if item["mode"] not in {"100644", "100755"}:
                raise Hdf5CompanionExecutionError("HDF5 companion blob mode is invalid")
            if (
                type(item["object_sha1"]) is not str
                or _SHA_RE.fullmatch(item["object_sha1"]) is None
            ):
                raise Hdf5CompanionExecutionError("HDF5 companion object SHA-1 is invalid")
        elif item["mode"] is not None or item["object_sha1"] is not None:
            raise Hdf5CompanionExecutionError("absent HDF5 companion carries object metadata")

    if observed_present != present:
        raise Hdf5CompanionExecutionError("HDF5 companion presence count disagrees")
    if profile._companion_identity(companions) != value["companion_inventory_sha256"]:
        raise Hdf5CompanionExecutionError("HDF5 companion inventory identity disagrees")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "provider_file_bytes_read": False,
        "hdf5_byte_identity_verified": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_result(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise Hdf5CompanionExecutionError("HDF5 companion result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Hdf5CompanionExecutionError("HDF5 companion result envelope is malformed")
    try:
        result = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except Hdf5CompanionExecutionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Hdf5CompanionExecutionError("HDF5 companion result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise Hdf5CompanionExecutionError("HDF5 companion result fields drifted")
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise Hdf5CompanionExecutionError("HDF5 companion result schema drifted")
    return result


def _terminal_result_execution_sha(body: object) -> str | None:
    result = _parse_result(body)
    if result is None:
        return None
    if type(result.get("source_issue")) is not int or result["source_issue"] != SOURCE_ISSUE:
        raise Hdf5CompanionExecutionError("HDF5 companion result issue drifted")
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None:
        raise Hdf5CompanionExecutionError("HDF5 companion result target SHA is invalid")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Hdf5CompanionExecutionError("HDF5 companion result execution SHA is invalid")
    if target_sha != execution_sha:
        raise Hdf5CompanionExecutionError("HDF5 companion result target/execution SHA mismatch")
    return execution_sha


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _parse_result(body)
    if result is None:
        return False
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Hdf5CompanionExecutionError(f"HDF5 companion result drifted at {field}")
    if result["status"] == "pass":
        if result["failure_class"] is not None:
            raise Hdf5CompanionExecutionError("HDF5 companion PASS carries failure class")
        validate_profile(result["profile"])
        return True
    if result["status"] == "blocked":
        if result["failure_class"] != BLOCKED_FAILURE_CLASS or result["profile"] is not None:
            raise Hdf5CompanionExecutionError("HDF5 companion blocked result widened evidence")
        return True
    if result["status"] == "duplicate":
        if result["failure_class"] is not None or result["profile"] is not None:
            raise Hdf5CompanionExecutionError("HDF5 companion duplicate carries evidence")
        return True
    raise Hdf5CompanionExecutionError("HDF5 companion result has non-terminal status")


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Hdf5CompanionExecutionError("invalid execution SHA")
    try:
        comments = _FETCH_COMMENTS(
            repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES
        )
    except LedgerError as exc:
        raise Hdf5CompanionExecutionError("HDF5 companion result ledger is incomplete") from exc
    matching_terminal_found = False
    for comment in comments:
        if type(comment) is not dict:
            raise Hdf5CompanionExecutionError("HDF5 companion ledger contains non-object")
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
            matching_terminal_found = True
    return matching_terminal_found


def execute_profile(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if (
        profile.profile_fixed10_hdf5_companions is not _PROFILE
        or fetch_repository_comments is not _FETCH_COMMENTS
    ):
        raise Hdf5CompanionExecutionError("trusted HDF5 companion execution authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        return {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile": None,
        }
    try:
        companion_profile = _PROFILE()
        validate_profile(companion_profile)
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "profile": companion_profile,
        }
    except profile.Hdf5CompanionProfileError:
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": BLOCKED_FAILURE_CLASS,
            "profile": None,
        }

    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise Hdf5CompanionExecutionError("HDF5 companion result exceeds publication limit")
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
        raise Hdf5CompanionExecutionError("GitHub ledger token is absent")
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
