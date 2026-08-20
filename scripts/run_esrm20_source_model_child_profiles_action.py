# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main structural profiles for the exact ESRM20 source-model child receipts.

This action composes two already-established primitives:
* the fixed EFEHR transport used by the source-model receipt lane; and
* ``profile_esrm20_source_model_children.profile_source_model``.

Only the ten immutable #481 receipt identities are eligible. Provider bytes are
held in memory only long enough to verify and profile one object, then discarded.
The published result contains bounded structural counts and exact byte identities;
it does not establish dependency closure, runtime compatibility, publication
rights, or model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts import profile_esrm20_source_model_children as content_profile
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-source-model-child-profiles-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-source-model-child-profiles-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-source-model-child-profiles-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-source-model-child-profiles-result-v1"
PROFILE_SET_SCHEMA_VERSION = "oc-esrm20-source-model-child-profiles-v1"
ACTION = "esrm20_source_model_child_content_profiles"
SOURCE_ISSUE = 281
CONSUMER_ISSUE = 287
RECEIPT_ISSUE = 481
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
RECEIPT_RESULT_COMMENT_ID = 5312851239
RECEIPT_SET_SHA256 = "621d16b35166cb66c86079106f1a7fd717ff07ef155184c5eed5a028292e4eb8"
EXPECTED_OBJECT_COUNT = 10
EXPECTED_TOTAL_BYTE_COUNT = 23_781_485
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

MAX_FILE_BYTES = content_profile.MAX_XML_BYTES
MAX_TOTAL_BYTES = 64 * 1024 * 1024
TOTAL_DEADLINE_SECONDS = 300.0
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 64_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_PROFILE_FIELDS = {
    "repository_path",
    "byte_count",
    "sha256",
    "root_element",
    "element_count",
    "element_type_counts",
    "byte_identity_verified",
    "source_model_content_profiled",
    "external_reference_scan_performed",
    "transitive_dependency_byte_closure_verified",
    "runtime_compatibility_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_PROFILE_SET_FIELDS = {
    "schema_version",
    "source_issue",
    "consumer_issue",
    "receipt_issue",
    "receipt_result_comment_id",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "receipt_set_sha256",
    "source_model_paths",
    "profile_count",
    "total_byte_count",
    "profiles",
    "provider_file_bytes_read",
    "raw_xml_returned",
    "source_model_content_profiled",
    "external_reference_scan_performed",
    "external_bytes_persisted",
    "transitive_dependency_byte_closure_verified",
    "runtime_compatibility_verified",
    "publication_authorized",
    "model_use_authorized",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "consumer_issue",
    "receipt_issue",
    "target_sha",
    "execution_sha",
    "dataset_id",
    "status",
    "failure_class",
    "profile_set",
    "external_bytes_persisted",
    "transitive_dependency_byte_closure_verified",
    "runtime_compatibility_verified",
    "publication_authorized",
    "model_use_authorized",
}

_FIXED_RECEIPTS = dict(content_profile.RECEIPTS)
_FIXED_PROFILE = content_profile.profile_source_model
_OPEN_FIXED = transport._open_fixed
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_SET_RESPONSE_TIMEOUT = transport._set_response_timeout
_DECLARED_LENGTH = transport._declared_length
_READ_BOUNDED = transport._read_bounded
_MONOTONIC = time.monotonic
_FETCH_COMMENTS = fetch_repository_comments


class SourceModelChildProfileActionError(RuntimeError):
    """Fail-closed error for the fixed source-model child profiling lane."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceModelChildProfileActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SourceModelChildProfileActionError(f"non-finite JSON constant: {value}")


def _receipt_set_sha(receipts: Mapping[str, tuple[int, str]]) -> str:
    canonical = [
        {"repository_path": path, "byte_count": identity[0], "sha256": identity[1]}
        for path, identity in receipts.items()
    ]
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _assert_fixed_contract() -> None:
    exact = (
        ("project_id", content_profile.PROJECT_ID, PROJECT_ID),
        ("project_path", content_profile.PROJECT_PATH, PROJECT_PATH),
        ("commit_sha", content_profile.COMMIT_SHA, COMMIT_SHA),
        (
            "receipt_result_comment_id",
            content_profile.RECEIPT_RESULT_COMMENT_ID,
            RECEIPT_RESULT_COMMENT_ID,
        ),
        ("receipt_set_sha256", content_profile.RECEIPT_SET_SHA256, RECEIPT_SET_SHA256),
    )
    for field, observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelChildProfileActionError(
                f"trusted source-model profiler contract drifted at {field}"
            )
    if content_profile.profile_source_model is not _FIXED_PROFILE:
        raise SourceModelChildProfileActionError("trusted source-model profiler identity drifted")
    if content_profile.RECEIPTS != _FIXED_RECEIPTS:
        raise SourceModelChildProfileActionError("trusted source-model receipt set drifted")
    if len(_FIXED_RECEIPTS) != EXPECTED_OBJECT_COUNT:
        raise SourceModelChildProfileActionError("trusted source-model object count drifted")
    if sum(identity[0] for identity in _FIXED_RECEIPTS.values()) != EXPECTED_TOTAL_BYTE_COUNT:
        raise SourceModelChildProfileActionError("trusted source-model total byte count drifted")
    if _receipt_set_sha(_FIXED_RECEIPTS) != RECEIPT_SET_SHA256:
        raise SourceModelChildProfileActionError("trusted source-model receipt-set hash drifted")


def _raw_url(path: str, *, receipts: Mapping[str, tuple[int, str]] = _FIXED_RECEIPTS) -> str:
    if path not in receipts:
        raise SourceModelChildProfileActionError("source-model path is outside exact receipt set")
    encoded_path = urllib.parse.quote(path, safe="")
    encoded_ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{transport.PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _fetch_verified_profile(
    path: str,
    identity: tuple[int, str],
    *,
    deadline: float,
    opener: Any,
    monotonic: Any,
    profiler: Callable[[str, bytes], dict[str, Any]],
    receipts: Mapping[str, tuple[int, str]],
) -> dict[str, Any]:
    expected_count, expected_sha256 = identity
    if type(expected_count) is not int or isinstance(expected_count, bool) or not (
        1 <= expected_count <= MAX_FILE_BYTES
    ):
        raise SourceModelChildProfileActionError("source-model receipt byte count is invalid")
    if type(expected_sha256) is not str or _SHA256_RE.fullmatch(expected_sha256) is None:
        raise SourceModelChildProfileActionError("source-model receipt SHA-256 is invalid")

    url = _raw_url(path, receipts=receipts)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml",
            "User-Agent": "OpenCatastrophe-ESRM20-source-child-profiles-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
            _VALIDATE_RESPONSE(response, url)
            declared = _DECLARED_LENGTH(response, expected_count)
            if declared is not None and declared != expected_count:
                raise SourceModelChildProfileActionError(
                    "source-model Content-Length disagrees with exact receipt"
                )
            _SET_RESPONSE_TIMEOUT(response, _REMAINING(deadline, monotonic))
            payload = _READ_BOUNDED(
                response,
                deadline=deadline,
                maximum=expected_count,
                monotonic=monotonic,
            )
    except (SourceModelChildProfileActionError, transport.EfehrAcquisitionError):
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise SourceModelChildProfileActionError("source-model acquisition failed") from exc

    if len(payload) != expected_count or hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise SourceModelChildProfileActionError(
            "source-model bytes disagree with exact #481 receipt"
        )
    try:
        profile = profiler(path, payload)
    except content_profile.SourceModelContentProfileError:
        raise
    except Exception as exc:
        raise SourceModelChildProfileActionError("source-model profiler failed closed") from exc
    return validate_child_profile(profile, expected_path=path, expected_identity=identity)


def _acquire_profiles(
    *,
    receipts: Mapping[str, tuple[int, str]],
    profiler: Callable[[str, bytes], dict[str, Any]],
    opener: Any,
    monotonic: Any,
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    profiles: list[dict[str, Any]] = []
    total = 0
    for path, identity in receipts.items():
        total += identity[0]
        if total > MAX_TOTAL_BYTES:
            raise SourceModelChildProfileActionError("source-model profile set exceeds total byte policy")
        profiles.append(
            _fetch_verified_profile(
                path,
                identity,
                deadline=deadline,
                opener=opener,
                monotonic=monotonic,
                profiler=profiler,
                receipts=receipts,
            )
        )
    profile_set = {
        "schema_version": PROFILE_SET_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "consumer_issue": CONSUMER_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "receipt_result_comment_id": RECEIPT_RESULT_COMMENT_ID,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "receipt_set_sha256": RECEIPT_SET_SHA256,
        "source_model_paths": list(receipts),
        "profile_count": len(profiles),
        "total_byte_count": total,
        "profiles": profiles,
        "provider_file_bytes_read": True,
        "raw_xml_returned": False,
        "source_model_content_profiled": True,
        "external_reference_scan_performed": False,
        "external_bytes_persisted": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return validate_profile_set(profile_set)


def acquire_profiles() -> dict[str, Any]:
    _assert_fixed_contract()
    if transport._open_fixed is not _OPEN_FIXED:
        raise SourceModelChildProfileActionError("trusted EFEHR transport identity drifted")
    return _acquire_profiles(
        receipts=_FIXED_RECEIPTS,
        profiler=_FIXED_PROFILE,
        opener=_OPEN_FIXED,
        monotonic=_MONOTONIC,
    )


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SourceModelChildProfileActionError("wrong source-model profiling issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SourceModelChildProfileActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SourceModelChildProfileActionError("invalid source-model profile request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceModelChildProfileActionError("source-model profile request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SourceModelChildProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SourceModelChildProfileActionError("invalid source-model profile request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SourceModelChildProfileActionError("source-model profile request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelChildProfileActionError(
                f"source-model profile request drifted at {field}"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise SourceModelChildProfileActionError("invalid requester identity")
    return request


def validate_child_profile(
    value: object,
    *,
    expected_path: str,
    expected_identity: tuple[int, str],
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise SourceModelChildProfileActionError("source-model child profile fields drifted")
    expected_count, expected_sha256 = expected_identity
    exact = (
        ("repository_path", expected_path),
        ("byte_count", expected_count),
        ("sha256", expected_sha256),
        ("byte_identity_verified", True),
        ("source_model_content_profiled", True),
        ("external_reference_scan_performed", False),
        ("transitive_dependency_byte_closure_verified", False),
        ("runtime_compatibility_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelChildProfileActionError(
                f"source-model child profile drifted at {field}"
            )
    root = value["root_element"]
    if type(root) is not str or not root or len(root.encode("utf-8")) > 256:
        raise SourceModelChildProfileActionError("source-model root element is invalid")
    element_count = value["element_count"]
    if (
        type(element_count) is not int
        or isinstance(element_count, bool)
        or not (1 <= element_count <= content_profile.MAX_ELEMENTS)
    ):
        raise SourceModelChildProfileActionError("source-model element count is invalid")
    counts = value["element_type_counts"]
    if type(counts) is not dict or not counts or len(counts) > 512:
        raise SourceModelChildProfileActionError("source-model element-type counts are invalid")
    counted = 0
    for name, count in counts.items():
        if type(name) is not str or not name or len(name.encode("utf-8")) > 256:
            raise SourceModelChildProfileActionError("source-model element type is invalid")
        if type(count) is not int or isinstance(count, bool) or count < 1:
            raise SourceModelChildProfileActionError("source-model element-type count is invalid")
        counted += count
    if counted != element_count:
        raise SourceModelChildProfileActionError("source-model element counts do not reconcile")
    return value


def validate_profile_set(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_SET_FIELDS:
        raise SourceModelChildProfileActionError("source-model profile-set fields drifted")
    exact = (
        ("schema_version", PROFILE_SET_SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("consumer_issue", CONSUMER_ISSUE),
        ("receipt_issue", RECEIPT_ISSUE),
        ("receipt_result_comment_id", RECEIPT_RESULT_COMMENT_ID),
        ("dataset_id", DATASET_ID),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("receipt_set_sha256", RECEIPT_SET_SHA256),
        ("source_model_paths", list(_FIXED_RECEIPTS)),
        ("profile_count", EXPECTED_OBJECT_COUNT),
        ("total_byte_count", EXPECTED_TOTAL_BYTE_COUNT),
        ("provider_file_bytes_read", True),
        ("raw_xml_returned", False),
        ("source_model_content_profiled", True),
        ("external_reference_scan_performed", False),
        ("external_bytes_persisted", False),
        ("transitive_dependency_byte_closure_verified", False),
        ("runtime_compatibility_verified", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelChildProfileActionError(
                f"source-model profile set drifted at {field}"
            )
    profiles = value["profiles"]
    if type(profiles) is not list or len(profiles) != EXPECTED_OBJECT_COUNT:
        raise SourceModelChildProfileActionError("source-model profile count drifted")
    for profile, (path, identity) in zip(profiles, _FIXED_RECEIPTS.items()):
        validate_child_profile(profile, expected_path=path, expected_identity=identity)
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "consumer_issue": CONSUMER_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "dataset_id": DATASET_ID,
        "external_bytes_persisted": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_result_object(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise SourceModelChildProfileActionError("source-model profile result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceModelChildProfileActionError("source-model profile result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SourceModelChildProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SourceModelChildProfileActionError("source-model profile result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SourceModelChildProfileActionError("source-model profile result fields drifted")
    return result


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _parse_result_object(body)
    if result is None:
        return False
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelChildProfileActionError(
                f"source-model profile result drifted at {field}"
            )
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise SourceModelChildProfileActionError("source-model profile PASS carries failure class")
        validate_profile_set(result.get("profile_set"))
        return True
    if status == "blocked":
        if (
            result.get("failure_class") != "source_model_profile_failure"
            or result.get("profile_set") is not None
        ):
            raise SourceModelChildProfileActionError("source-model blocked result widened evidence")
        return True
    if status == "duplicate":
        if result.get("failure_class") is not None or result.get("profile_set") is not None:
            raise SourceModelChildProfileActionError("source-model duplicate result carries evidence")
        return True
    raise SourceModelChildProfileActionError("source-model profile result has non-terminal status")


def _result_execution_sha(body: object) -> str | None:
    result = _parse_result_object(body)
    if result is None:
        return None
    fixed = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("consumer_issue", CONSUMER_ISSUE),
        ("receipt_issue", RECEIPT_ISSUE),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in fixed:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelChildProfileActionError(
                f"historical source-model profile result drifted at {field}"
            )
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if (
        type(target_sha) is not str
        or _SHA_RE.fullmatch(target_sha) is None
        or type(execution_sha) is not str
        or _SHA_RE.fullmatch(execution_sha) is None
        or target_sha != execution_sha
    ):
        raise SourceModelChildProfileActionError(
            "historical source-model profile SHA binding is malformed"
        )
    return execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(
            repository,
            token,
            issue=SOURCE_ISSUE,
            max_pages=MAX_LEDGER_PAGES,
        )
    except LedgerError as exc:
        raise SourceModelChildProfileActionError("source-model profile ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SourceModelChildProfileActionError("source-model profile ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_sha = _result_execution_sha(body)
        if own_sha is None:
            continue
        if not parse_terminal_result(body, execution_sha=own_sha):
            continue
        if own_sha == execution_sha:
            return True
    return False


def execute(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    _assert_fixed_contract()
    if (
        transport._open_fixed is not _OPEN_FIXED
        or content_profile.profile_source_model is not _FIXED_PROFILE
        or fetch_repository_comments is not _FETCH_COMMENTS
    ):
        raise SourceModelChildProfileActionError("trusted source-model profiling authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "profile_set": None,
        }
    else:
        try:
            profile_set = acquire_profiles()
            result = {
                **_base_result(execution_sha=execution_sha),
                "status": "pass",
                "failure_class": None,
                "profile_set": profile_set,
            }
        except (
            SourceModelChildProfileActionError,
            content_profile.SourceModelContentProfileError,
            transport.EfehrAcquisitionError,
        ):
            result = {
                **_base_result(execution_sha=execution_sha),
                "status": "blocked",
                "failure_class": "source_model_profile_failure",
                "profile_set": None,
            }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise SourceModelChildProfileActionError("source-model profile result exceeds publication limit")
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
        raise SourceModelChildProfileActionError("GitHub ledger token is absent")
    result = execute(
        repository=args.repository,
        token=token,
        execution_sha=args.execution_sha,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
