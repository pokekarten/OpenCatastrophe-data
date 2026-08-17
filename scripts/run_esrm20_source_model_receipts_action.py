# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main receipts for the ten source models derived by the #481 profile.

Only exact byte identity is established here. Provider bytes are streamed into a
SHA-256 digest and are never written to disk or returned. No source-model XML is
parsed and no HDF5 companion, runtime-compatibility, publication or model-use
claim is made by this action.
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
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-source-model-receipts-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-source-model-receipts-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-source-model-receipts-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-source-model-receipts-result-v1"
PROFILE_SCHEMA_VERSION = "oc-esrm20-source-model-receipts-profile-v1"
ACTION = "esrm20_source_model_byte_receipts"
SOURCE_ISSUE = 481
PARENT_SCIENCE_ISSUE = 281
SOURCE_PROFILE_RESULT_COMMENT_ID = 5310194089
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

SOURCE_MODEL_PATHS = (
    "Hazard/source_models/asm_v12e/asm_ver12e_winGT_fs017_combined.xml",
    "Hazard/source_models/asm_v12e/asm_ver12e_winGT_fs017_twingr.xml",
    "Hazard/source_models/deep_v12e/asm_deep_ver12e_winGT_fs017_combined.xml",
    "Hazard/source_models/fsm_v09/fs_ver09e_model_aGR_fMthr_combined.xml",
    "Hazard/source_models/interface_v12b/CaA_IF2222222_M40.xml",
    "Hazard/source_models/interface_v12b/CyA_IF2222222_M40.xml",
    "Hazard/source_models/interface_v12b/GiA_IF2222222_M40.xml",
    "Hazard/source_models/interface_v12b/HeA_IF2222222_M40.xml",
    "Hazard/source_models/ssm_v09/seis_ver12b_fMthr_asm_ver12e_winGT_fs017_agbrs_point.xml",
    "Hazard/source_models/volcanic_v12e/asm_volcanic_ver12e_winGT_fs017_combined.xml",
)

MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
TOTAL_DEADLINE_SECONDS = 300.0
CHUNK_SIZE = 64 * 1024
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 64_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_RECEIPT_FIELDS = {"repository_path", "retrieved_at", "byte_count", "sha256"}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "parent_science_issue",
    "source_profile_result_comment_id",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "source_model_paths",
    "receipts",
    "receipt_count",
    "total_byte_count",
    "receipt_set_sha256",
    "provider_file_bytes_read",
    "raw_xml_returned",
    "source_model_content_profiled",
    "hdf5_companions_inferred",
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
    "parent_science_issue",
    "target_sha",
    "execution_sha",
    "dataset_id",
    "status",
    "failure_class",
    "profile",
    "external_bytes_persisted",
    "transitive_dependency_byte_closure_verified",
    "runtime_compatibility_verified",
    "publication_authorized",
    "model_use_authorized",
}

_OPEN_FIXED = transport._open_fixed
_VALIDATE_RESPONSE = transport._validate_exact_response
_REMAINING = transport._remaining
_SET_RESPONSE_TIMEOUT = transport._set_response_timeout
_DECLARED_LENGTH = transport._declared_length
_MONOTONIC = time.monotonic
_NOW = transport.utc_now
_FETCH_COMMENTS = fetch_repository_comments


class SourceModelReceiptError(RuntimeError):
    """Fail-closed error for the fixed source-model receipt lane."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceModelReceiptError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise SourceModelReceiptError(f"non-finite JSON constant: {value}")


def _raw_url(path: str) -> str:
    if path not in SOURCE_MODEL_PATHS:
        raise SourceModelReceiptError("source-model path is outside exact allow-list")
    encoded_path = urllib.parse.quote(path, safe="")
    encoded_ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _stream_receipt(
    path: str,
    *,
    deadline: float,
    max_bytes: int = MAX_FILE_BYTES,
    opener: Any = _OPEN_FIXED,
    monotonic: Any = _MONOTONIC,
    now: Any = _NOW,
) -> dict[str, Any]:
    if type(max_bytes) is not int or isinstance(max_bytes, bool) or not (1 <= max_bytes <= MAX_FILE_BYTES):
        raise SourceModelReceiptError("source-model effective byte budget is invalid")
    url = _raw_url(path)
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/xml", "User-Agent": "OpenCatastrophe-ESRM20-source-receipts-v1"},
        method="GET",
    )
    try:
        with opener(request, timeout=_REMAINING(deadline, monotonic)) as response:
            _VALIDATE_RESPONSE(response, url)
            declared = _DECLARED_LENGTH(response, max_bytes)
            retrieved_at = now()
            digest = hashlib.sha256()
            count = 0
            while True:
                if declared is not None:
                    byte_budget = declared - count
                    if byte_budget == 0:
                        break
                else:
                    byte_budget = max_bytes - count
                    if byte_budget == 0:
                        raise SourceModelReceiptError(
                            "source-model byte budget exhausted before EOF could be verified"
                        )
                remaining = _REMAINING(deadline, monotonic)
                _SET_RESPONSE_TIMEOUT(response, remaining)
                chunk = response.read(min(CHUNK_SIZE, byte_budget))
                _REMAINING(deadline, monotonic)
                if chunk == b"":
                    break
                if type(chunk) is not bytes:
                    raise SourceModelReceiptError("provider returned non-byte source-model content")
                count += len(chunk)
                if count > max_bytes:
                    raise SourceModelReceiptError("source-model file exceeds effective byte budget")
                digest.update(chunk)
    except (SourceModelReceiptError, transport.EfehrAcquisitionError):
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise SourceModelReceiptError("source-model acquisition failed") from exc
    if count < 1:
        raise SourceModelReceiptError("provider returned an empty source-model file")
    if declared is not None and declared != count:
        raise SourceModelReceiptError("source-model Content-Length disagrees with streamed bytes")
    if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
        raise SourceModelReceiptError("source-model retrieval timestamp is invalid")
    return {
        "repository_path": path,
        "retrieved_at": retrieved_at,
        "byte_count": count,
        "sha256": digest.hexdigest(),
    }


def _receipt_set_sha(receipts: list[dict[str, Any]]) -> str:
    canonical = [
        {"repository_path": item["repository_path"], "byte_count": item["byte_count"], "sha256": item["sha256"]}
        for item in receipts
    ]
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def acquire_receipts(
    *,
    opener: Any = _OPEN_FIXED,
    monotonic: Any = _MONOTONIC,
    now: Any = _NOW,
) -> dict[str, Any]:
    if opener is _OPEN_FIXED and transport._open_fixed is not _OPEN_FIXED:
        raise SourceModelReceiptError("trusted EFEHR transport identity drifted")
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    receipts: list[dict[str, Any]] = []
    total = 0
    for path in SOURCE_MODEL_PATHS:
        remaining_total = MAX_TOTAL_BYTES - total
        if remaining_total <= 0:
            raise SourceModelReceiptError("source-model receipt set exhausted total byte policy")
        receipt = _stream_receipt(
            path,
            deadline=deadline,
            max_bytes=min(MAX_FILE_BYTES, remaining_total),
            opener=opener,
            monotonic=monotonic,
            now=now,
        )
        total += receipt["byte_count"]
        if total > MAX_TOTAL_BYTES:
            raise SourceModelReceiptError("source-model receipt set exceeds total byte policy")
        receipts.append(receipt)
    profile = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "parent_science_issue": PARENT_SCIENCE_ISSUE,
        "source_profile_result_comment_id": SOURCE_PROFILE_RESULT_COMMENT_ID,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "source_model_paths": list(SOURCE_MODEL_PATHS),
        "receipts": receipts,
        "receipt_count": len(receipts),
        "total_byte_count": total,
        "receipt_set_sha256": _receipt_set_sha(receipts),
        "provider_file_bytes_read": True,
        "raw_xml_returned": False,
        "source_model_content_profiled": False,
        "hdf5_companions_inferred": False,
        "external_bytes_persisted": False,
        "transitive_dependency_byte_closure_verified": False,
        "runtime_compatibility_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    validate_profile(profile)
    return profile


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise SourceModelReceiptError("wrong source-model receipt issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise SourceModelReceiptError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SourceModelReceiptError("invalid source-model receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceModelReceiptError("source-model receipt request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SourceModelReceiptError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SourceModelReceiptError("invalid source-model receipt request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SourceModelReceiptError("source-model receipt request fields drifted")
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
            raise SourceModelReceiptError(f"source-model receipt request drifted at {field}")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise SourceModelReceiptError("invalid requester identity")
    return request


def _validate_receipt(value: object, *, expected_path: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
        raise SourceModelReceiptError("source-model receipt fields drifted")
    if value["repository_path"] != expected_path:
        raise SourceModelReceiptError("source-model receipt path drifted")
    if type(value["retrieved_at"]) is not str or _UTC_RE.fullmatch(value["retrieved_at"]) is None:
        raise SourceModelReceiptError("source-model receipt timestamp is invalid")
    if type(value["byte_count"]) is not int or isinstance(value["byte_count"], bool) or not (1 <= value["byte_count"] <= MAX_FILE_BYTES):
        raise SourceModelReceiptError("source-model receipt byte count is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise SourceModelReceiptError("source-model receipt SHA-256 is invalid")
    return value


def validate_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise SourceModelReceiptError("source-model receipt profile fields drifted")
    exact = (
        ("schema_version", PROFILE_SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("parent_science_issue", PARENT_SCIENCE_ISSUE),
        ("source_profile_result_comment_id", SOURCE_PROFILE_RESULT_COMMENT_ID),
        ("dataset_id", DATASET_ID),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("source_model_paths", list(SOURCE_MODEL_PATHS)),
        ("receipt_count", len(SOURCE_MODEL_PATHS)),
        ("provider_file_bytes_read", True),
        ("raw_xml_returned", False),
        ("source_model_content_profiled", False),
        ("hdf5_companions_inferred", False),
        ("external_bytes_persisted", False),
        ("transitive_dependency_byte_closure_verified", False),
        ("runtime_compatibility_verified", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelReceiptError(f"source-model receipt profile drifted at {field}")
    receipts = value["receipts"]
    if type(receipts) is not list or len(receipts) != len(SOURCE_MODEL_PATHS):
        raise SourceModelReceiptError("source-model receipt count drifted")
    for receipt, path in zip(receipts, SOURCE_MODEL_PATHS):
        _validate_receipt(receipt, expected_path=path)
    total = sum(item["byte_count"] for item in receipts)
    if type(value["total_byte_count"]) is not int or isinstance(value["total_byte_count"], bool) or value["total_byte_count"] != total or total > MAX_TOTAL_BYTES:
        raise SourceModelReceiptError("source-model total byte count drifted")
    if type(value["receipt_set_sha256"]) is not str or _SHA256_RE.fullmatch(value["receipt_set_sha256"]) is None or value["receipt_set_sha256"] != _receipt_set_sha(receipts):
        raise SourceModelReceiptError("source-model receipt-set fingerprint drifted")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "parent_science_issue": PARENT_SCIENCE_ISSUE,
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
        raise SourceModelReceiptError("source-model receipt result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise SourceModelReceiptError("source-model receipt result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except SourceModelReceiptError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SourceModelReceiptError("source-model receipt result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise SourceModelReceiptError("source-model receipt result fields drifted")
    return result


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _parse_result_object(body)
    if result is None:
        return False
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelReceiptError(f"source-model receipt result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise SourceModelReceiptError("source-model receipt PASS carries failure class")
        validate_profile(result.get("profile"))
        return True
    if status == "blocked":
        if result.get("failure_class") != "source_model_receipt_failure" or result.get("profile") is not None:
            raise SourceModelReceiptError("source-model blocked result widened evidence")
        return True
    if status == "duplicate":
        if result.get("failure_class") is not None or result.get("profile") is not None:
            raise SourceModelReceiptError("source-model duplicate result carries evidence")
        return True
    raise SourceModelReceiptError("source-model receipt result has non-terminal status")


def _result_execution_sha(body: object) -> str | None:
    result = _parse_result_object(body)
    if result is None:
        return None
    fixed = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("parent_science_issue", PARENT_SCIENCE_ISSUE),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in fixed:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SourceModelReceiptError(f"historical source-model receipt result drifted at {field}")
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if type(target_sha) is not str or _SHA_RE.fullmatch(target_sha) is None or type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None or target_sha != execution_sha:
        raise SourceModelReceiptError("historical source-model receipt SHA binding is malformed")
    return execution_sha


def has_terminal_result(*, repository: str, token: str, execution_sha: str) -> bool:
    try:
        comments = _FETCH_COMMENTS(repository, token, issue=SOURCE_ISSUE, max_pages=MAX_LEDGER_PAGES)
    except LedgerError as exc:
        raise SourceModelReceiptError("source-model receipt ledger is incomplete") from exc
    for comment in comments:
        if type(comment) is not dict:
            raise SourceModelReceiptError("source-model receipt ledger contains non-object")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        own_sha = _result_execution_sha(body)
        if own_sha is None or own_sha != execution_sha:
            continue
        if parse_terminal_result(body, execution_sha=execution_sha):
            return True
    return False


def execute(*, repository: str, token: str, execution_sha: str) -> dict[str, Any]:
    if transport._open_fixed is not _OPEN_FIXED or fetch_repository_comments is not _FETCH_COMMENTS:
        raise SourceModelReceiptError("trusted source-model receipt authority drifted")
    if has_terminal_result(repository=repository, token=token, execution_sha=execution_sha):
        result = {**_base_result(execution_sha=execution_sha), "status": "duplicate", "failure_class": None, "profile": None}
    else:
        try:
            profile = acquire_receipts()
            result = {**_base_result(execution_sha=execution_sha), "status": "pass", "failure_class": None, "profile": profile}
        except (SourceModelReceiptError, transport.EfehrAcquisitionError):
            result = {**_base_result(execution_sha=execution_sha), "status": "blocked", "failure_class": "source_model_receipt_failure", "profile": None}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise SourceModelReceiptError("source-model receipt result exceeds publication limit")
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
    validate_request(os.environ.get(args.comment_body_env), expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error("--repository, --token-env and --output are required for execution")
    token = os.environ.get(args.token_env)
    if not token:
        raise SourceModelReceiptError("GitHub ledger token is absent")
    result = execute(repository=args.repository, token=token, execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
