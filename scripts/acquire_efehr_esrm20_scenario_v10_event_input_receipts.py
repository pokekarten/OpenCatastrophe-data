# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main byte receipts for three fixed ESRM20 v1.0 Greece event inputs.

The operation is deliberately closed to EFEHR GitLab project 273, immutable
v1.0 commit 041f90d..., event identifier ``Greece_07-9-1999`` and exactly
three source-derived input files: the rupture definition plus the USGS
ShakeMap grid and uncertainty XML. It never reads ``shakemaps/outputs`` and
accepts no caller-controlled provider, ref, path, URL or event selector.

Successful receipts establish byte identity only. They do not establish event
locality, scenario selection, validation/holdout status, publication rights or
model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _header_value,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
    utc_now,
)
from scripts.efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

_CANONICAL_SCHEMA_VERSION = "oc-esrm20-scenario-v10-event-input-receipts-v1"
_CANONICAL_RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-event-input-receipts-result-v1"
_CANONICAL_REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-event-input-receipts-request-v1"
_CANONICAL_REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-event-input-receipts-request-v1 -->"
_CANONICAL_RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-event-input-receipts-result-v1 -->"
_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_CANONICAL_PROJECT_ID = 273
_CANONICAL_PROJECT_PATH = "efehr/esrm20_scenario_tests"
_CANONICAL_RELEASE_TAG = "v1.0"
_CANONICAL_COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
_CANONICAL_EVENT_ID = "Greece_07-9-1999"
# Canonical machine provenance: #285 trusted-bot result comment 5346096945.
_CANONICAL_INPUTS = (
    (
        "rupture_definition",
        "ruptures/source_models/rupture_Greece_07-9-1999.xml",
        "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
    ),
    (
        "usgs_shakemap_grid",
        "shakemaps/shakemaps_USGS/Greece_07-9-1999/grid.xml",
        "21e323dec41b8efb012b2595145fded5fb35fd3a",
    ),
    (
        "usgs_shakemap_uncertainty",
        "shakemaps/shakemaps_USGS/Greece_07-9-1999/uncertainty.xml",
        "30d5635260a83cd0ac91ee559d0109ff126a7b57",
    ),
)
_CANONICAL_MAX_FILE_BYTES = 64 * 1024 * 1024
_CANONICAL_MAX_TOTAL_BYTES = 128 * 1024 * 1024
_CANONICAL_TOTAL_DEADLINE_SECONDS = TOTAL_DEADLINE_SECONDS
_CANONICAL_TRUSTED_RESULT_LOGIN = "github-actions[bot]"
_CANONICAL_MAX_RESULT_UTF8_BYTES = 24_000

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
RESULT_SCHEMA_VERSION = _CANONICAL_RESULT_SCHEMA_VERSION
REQUEST_SCHEMA_VERSION = _CANONICAL_REQUEST_SCHEMA_VERSION
REQUEST_MARKER = _CANONICAL_REQUEST_MARKER
RESULT_MARKER = _CANONICAL_RESULT_MARKER
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
RELEASE_TAG = _CANONICAL_RELEASE_TAG
COMMIT_SHA = _CANONICAL_COMMIT_SHA
EVENT_ID = _CANONICAL_EVENT_ID
INPUTS = _CANONICAL_INPUTS
MAX_FILE_BYTES = _CANONICAL_MAX_FILE_BYTES
MAX_TOTAL_BYTES = _CANONICAL_MAX_TOTAL_BYTES
TRUSTED_RESULT_LOGIN = _CANONICAL_TRUSTED_RESULT_LOGIN
MAX_RESULT_UTF8_BYTES = _CANONICAL_MAX_RESULT_UTF8_BYTES

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_RECEIPT_FIELDS = {
    "role",
    "repository_path",
    "git_blob_sha1",
    "retrieved_at",
    "byte_count",
    "sha256",
    "content_type",
    "etag",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "publication_authorized",
}
_RESULT_FIELDS = {
    "schema_version",
    "source_issue",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "dataset_id",
    "provider_host",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "event_id",
    "receipts",
    "provider_file_bytes_read",
    "provider_file_content_profiled",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}

_FETCH_COMMENTS = fetch_repository_comments


class ScenarioEventInputReceiptError(RuntimeError):
    """Fail-closed error for the fixed event-input receipt action."""


def _require_canonical_target() -> None:
    exact = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (RESULT_SCHEMA_VERSION, _CANONICAL_RESULT_SCHEMA_VERSION, "result schema version"),
        (REQUEST_SCHEMA_VERSION, _CANONICAL_REQUEST_SCHEMA_VERSION, "request schema version"),
        (REQUEST_MARKER, _CANONICAL_REQUEST_MARKER, "request marker"),
        (RESULT_MARKER, _CANONICAL_RESULT_MARKER, "result marker"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROVIDER_HOST, "gitlab.seismo.ethz.ch", "provider host"),
        (PROVIDER_ROOT, "https://gitlab.seismo.ethz.ch", "provider root"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (RELEASE_TAG, _CANONICAL_RELEASE_TAG, "release tag"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit sha"),
        (EVENT_ID, _CANONICAL_EVENT_ID, "event id"),
        (INPUTS, _CANONICAL_INPUTS, "input set"),
        (MAX_FILE_BYTES, _CANONICAL_MAX_FILE_BYTES, "file byte bound"),
        (MAX_TOTAL_BYTES, _CANONICAL_MAX_TOTAL_BYTES, "total byte bound"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioEventInputReceiptError(
                f"frozen ESRM20 scenario {label} authority drifted"
            )


def _raw_file_url(repository_path: str) -> str:
    if repository_path not in {item[1] for item in _CANONICAL_INPUTS}:
        raise ScenarioEventInputReceiptError("event input path is outside the fixed set")
    encoded_path = urllib.parse.quote(repository_path, safe="")
    encoded_ref = urllib.parse.quote(_CANONICAL_COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _git_blob_sha1(raw: bytes) -> str:
    if type(raw) is not bytes or not raw:
        raise ScenarioEventInputReceiptError("event input bytes must be non-empty")
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def _bounded_header(response: Any, name: str) -> str | None:
    return _header_value(response, name)


def _acquire_one(
    *,
    role: str,
    repository_path: str,
    expected_git_blob_sha1: str,
    opener: Any,
    now: Any,
    monotonic: Any,
    deadline: float,
) -> tuple[dict[str, Any], int]:
    url = _raw_file_url(repository_path)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml,text/xml;q=0.9,application/octet-stream;q=0.5",
            "User-Agent": "OpenCatastrophe-EFEHR-scenario-input-receipts-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            retrieved_at = now()
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_MAX_FILE_BYTES,
                monotonic=monotonic,
            )
            content_type = _bounded_header(response, "Content-Type")
            etag = _bounded_header(response, "ETag")
    except (ScenarioEventInputReceiptError, EfehrAcquisitionError):
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR scenario input retrieval failed: {type(exc).__name__}"
        ) from exc

    if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
        raise ScenarioEventInputReceiptError("event input retrieval timestamp is invalid")
    observed_git_blob_sha1 = _git_blob_sha1(raw)
    if observed_git_blob_sha1 != expected_git_blob_sha1:
        raise ScenarioEventInputReceiptError(
            "event input bytes do not match immutable tree Git blob"
        )
    receipt = {
        "role": role,
        "repository_path": repository_path,
        "git_blob_sha1": observed_git_blob_sha1,
        "retrieved_at": retrieved_at,
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_type": content_type,
        "etag": etag,
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    return receipt, len(raw)


def acquire_event_input_receipts(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Acquire byte receipts for exactly the three frozen Greece event inputs."""
    _require_canonical_target()
    open_response = opener or _open_fixed
    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    receipts: list[dict[str, Any]] = []
    total_bytes = 0
    for role, path, blob_sha1 in _CANONICAL_INPUTS:
        receipt, byte_count = _acquire_one(
            role=role,
            repository_path=path,
            expected_git_blob_sha1=blob_sha1,
            opener=open_response,
            now=now,
            monotonic=monotonic,
            deadline=deadline,
        )
        total_bytes += byte_count
        if total_bytes > _CANONICAL_MAX_TOTAL_BYTES:
            raise ScenarioEventInputReceiptError(
                "event input receipts exceeded the aggregate byte bound"
            )
        receipts.append(receipt)
    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "release_tag": _CANONICAL_RELEASE_TAG,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "event_id": _CANONICAL_EVENT_ID,
        "receipts": receipts,
        "provider_file_bytes_read": True,
        "provider_file_content_profiled": False,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


_ACQUIRE = acquire_event_input_receipts


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScenarioEventInputReceiptError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ScenarioEventInputReceiptError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_canonical_target()
    if type(expected_issue) is not int or expected_issue != _CANONICAL_SOURCE_ISSUE:
        raise ScenarioEventInputReceiptError("wrong scenario input receipt issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ScenarioEventInputReceiptError("invalid execution SHA")
    if type(body) is not str or body.count(_CANONICAL_REQUEST_MARKER) != 1:
        raise ScenarioEventInputReceiptError("invalid scenario input receipt request marker")
    before, after = body.split(_CANONICAL_REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioEventInputReceiptError("scenario input receipt request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except ScenarioEventInputReceiptError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioEventInputReceiptError("invalid scenario input receipt request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ScenarioEventInputReceiptError("scenario input receipt request fields drifted")
    if request["schema_version"] != _CANONICAL_REQUEST_SCHEMA_VERSION:
        raise ScenarioEventInputReceiptError("scenario input receipt request schema drifted")
    if type(request["issue"]) is not int or request["issue"] != _CANONICAL_SOURCE_ISSUE:
        raise ScenarioEventInputReceiptError("scenario input receipt request issue drifted")
    if request["target_sha"] != execution_sha:
        raise ScenarioEventInputReceiptError("scenario input receipt request target is not trusted main")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ScenarioEventInputReceiptError("invalid requester identity")
    return request


def _validate_header_value(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or len(value.encode("utf-8")) > 1024:
        raise ScenarioEventInputReceiptError(f"{field} is outside the bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ScenarioEventInputReceiptError(f"{field} contains control characters")
    return value


def validate_receipt(value: object, *, expected: tuple[str, str, str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
        raise ScenarioEventInputReceiptError("event input receipt fields drifted")
    role, path, blob_sha1 = expected
    exact = (
        ("role", role),
        ("repository_path", path),
        ("git_blob_sha1", blob_sha1),
        ("provider_file_bytes_read", True),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    )
    for field, expected_value in exact:
        observed = value[field]
        if type(observed) is not type(expected_value) or observed != expected_value:
            raise ScenarioEventInputReceiptError(f"event input receipt drifted at {field}")
    if type(value["retrieved_at"]) is not str or _UTC_RE.fullmatch(value["retrieved_at"]) is None:
        raise ScenarioEventInputReceiptError("event input receipt timestamp is invalid")
    if type(value["byte_count"]) is not int or isinstance(value["byte_count"], bool) or not (
        1 <= value["byte_count"] <= _CANONICAL_MAX_FILE_BYTES
    ):
        raise ScenarioEventInputReceiptError("event input receipt byte count is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise ScenarioEventInputReceiptError("event input receipt SHA-256 is invalid")
    _validate_header_value(value["content_type"], field="content_type")
    _validate_header_value(value["etag"], field="etag")
    return value


def validate_acquisition(value: object) -> dict[str, Any]:
    expected_fields = _RESULT_FIELDS - {"target_sha", "execution_sha", "status", "failure_class"}
    if type(value) is not dict or set(value) != expected_fields:
        raise ScenarioEventInputReceiptError("event input acquisition fields drifted")
    exact = (
        ("schema_version", _CANONICAL_SCHEMA_VERSION),
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("provider_host", "gitlab.seismo.ethz.ch"),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("release_tag", _CANONICAL_RELEASE_TAG),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("event_id", _CANONICAL_EVENT_ID),
        ("provider_file_bytes_read", True),
        ("provider_file_content_profiled", False),
        ("output_payload_bytes_read", False),
        ("external_bytes_persisted", False),
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
            raise ScenarioEventInputReceiptError(f"event input acquisition drifted at {field}")
    receipts = value["receipts"]
    if type(receipts) is not list or len(receipts) != len(_CANONICAL_INPUTS):
        raise ScenarioEventInputReceiptError("event input receipt set is incomplete")
    total = 0
    for receipt, expected in zip(receipts, _CANONICAL_INPUTS, strict=True):
        validate_receipt(receipt, expected=expected)
        total += receipt["byte_count"]
    if total > _CANONICAL_MAX_TOTAL_BYTES:
        raise ScenarioEventInputReceiptError("event input receipt set exceeds aggregate bound")
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": _CANONICAL_RESULT_SCHEMA_VERSION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "release_tag": _CANONICAL_RELEASE_TAG,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "event_id": _CANONICAL_EVENT_ID,
        "provider_file_content_profiled": False,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_result(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _RESULT_FIELDS:
        raise ScenarioEventInputReceiptError("scenario input result fields drifted")
    if type(value["target_sha"]) is not str or _SHA1_RE.fullmatch(value["target_sha"]) is None:
        raise ScenarioEventInputReceiptError("scenario input result target SHA is invalid")
    if value["execution_sha"] != value["target_sha"]:
        raise ScenarioEventInputReceiptError("scenario input result execution SHA drifted")
    base = _base_result(execution_sha=value["target_sha"])
    for field, expected in base.items():
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise ScenarioEventInputReceiptError(f"scenario input result drifted at {field}")
    if value["status"] == "pass":
        if value["failure_class"] is not None:
            raise ScenarioEventInputReceiptError("pass result carries a failure class")
        acquisition = {
            key: value[key]
            for key in (_RESULT_FIELDS - {"target_sha", "execution_sha", "status", "failure_class"})
        }
        acquisition["schema_version"] = _CANONICAL_SCHEMA_VERSION
        validate_acquisition(acquisition)
    elif value["status"] == "blocked":
        if value["failure_class"] != "event_input_receipt_failure":
            raise ScenarioEventInputReceiptError("blocked result failure class drifted")
        if value["receipts"] is not None or value["provider_file_bytes_read"] is not None:
            raise ScenarioEventInputReceiptError("blocked result must not assert partial byte evidence")
    else:
        raise ScenarioEventInputReceiptError("scenario input result status is invalid")
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    if len(encoded) > _CANONICAL_MAX_RESULT_UTF8_BYTES:
        raise ScenarioEventInputReceiptError("scenario input result exceeds publication bound")
    return value


def _parse_result_comment(body: str) -> dict[str, Any] | None:
    if _CANONICAL_RESULT_MARKER not in body:
        return None
    if body.count(_CANONICAL_RESULT_MARKER) != 1:
        raise ScenarioEventInputReceiptError("trusted scenario input result marker is duplicated")
    before, after = body.split(_CANONICAL_RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ScenarioEventInputReceiptError("trusted scenario input result envelope is not canonical")
    try:
        payload = json.loads(
            after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant
        )
    except ScenarioEventInputReceiptError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ScenarioEventInputReceiptError("trusted scenario input result JSON is invalid") from exc
    return validate_result(payload)


def find_existing_terminal(comments: list[dict[str, Any]], *, execution_sha: str) -> int | None:
    matching_comment_id: int | None = None
    for comment in comments:
        if type(comment) is not dict:
            raise ScenarioEventInputReceiptError("scenario input ledger contains non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != _CANONICAL_TRUSTED_RESULT_LOGIN:
            continue
        body = comment.get("body")
        if type(body) is not str:
            continue
        result = _parse_result_comment(body)
        if result is None or result["execution_sha"] != execution_sha:
            continue
        comment_id = comment.get("id")
        if type(comment_id) is not int or comment_id < 1:
            raise ScenarioEventInputReceiptError("matching result lacks a positive comment id")
        if matching_comment_id is None:
            matching_comment_id = comment_id
    return matching_comment_id


def prepare_result(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
    repository: str,
    token: str,
    comments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    validate_request(body, expected_issue=expected_issue, execution_sha=execution_sha)
    try:
        ledger = comments if comments is not None else _FETCH_COMMENTS(
            repository, token, issue=_CANONICAL_SOURCE_ISSUE
        )
    except LedgerError as exc:
        raise ScenarioEventInputReceiptError(
            "cannot read complete scenario input result ledger"
        ) from exc
    duplicate_comment_id = find_existing_terminal(ledger, execution_sha=execution_sha)
    if duplicate_comment_id is not None:
        return {"status": "duplicate", "duplicate_result_comment_id": duplicate_comment_id}

    try:
        acquisition = validate_acquisition(_ACQUIRE())
    except (ScenarioEventInputReceiptError, EfehrAcquisitionError):
        blocked = {
            **_base_result(execution_sha=execution_sha),
            "status": "blocked",
            "failure_class": "event_input_receipt_failure",
            "receipts": None,
            "provider_file_bytes_read": None,
        }
        return validate_result(blocked)

    result = {
        **_base_result(execution_sha=execution_sha),
        "status": "pass",
        "failure_class": None,
        "receipts": acquisition["receipts"],
        "provider_file_bytes_read": True,
    }
    return validate_result(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--token-env", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    token = os.environ.get(args.token_env, "")
    if body is None:
        raise ScenarioEventInputReceiptError("request comment environment variable is absent")
    result = prepare_result(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
        repository=args.repository,
        token=token,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
