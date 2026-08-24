# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main byte receipts for the three source-declared Greece exposure CSVs.

The exact dependency names come from trusted-main #285 terminal 5393778961,
which profiled the already receipted 697-byte Greece exposure wrapper. This
module is closed to those three files at the immutable ESRM20 v1.0 commit.
Provider bytes are hashed in memory and are never returned or persisted.

A passing result establishes byte identity for the three declared dependencies
only. It does not establish CSV schema/content semantics, CRS, taxonomy/value
semantics, benchmark agreement, validation/holdout status, publication rights,
or model-use authority.
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
from pathlib import Path, PurePosixPath
from typing import Any

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    import sys
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

_CANONICAL_SCHEMA_VERSION = "oc-esrm20-greece-exposure-csv-receipts-v1"
_CANONICAL_RESULT_SCHEMA_VERSION = "oc-esrm20-greece-exposure-csv-receipts-result-v1"
_CANONICAL_REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-exposure-csv-receipts-request-v1"
_CANONICAL_REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-csv-receipts-request-v1 -->"
_CANONICAL_RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-csv-receipts-result-v1 -->"
_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_PARENT_CONSUMER_ISSUE = 287
_CANONICAL_SOURCE_DECLARATION_COMMENT_ID = 5393778961
_CANONICAL_SOURCE_DECLARATION_EXECUTION_SHA = "64df54ef071937b49dac40650ef9e1cc93e014fb"
_CANONICAL_PARENT_RECEIPT_SHA256 = "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556"
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_RELEASE_TAG = "v1.0"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_CONSUMER_EVENT_ID = "Greece_07-9-1999"
_CANONICAL_PARENT_EXPOSURE_PATH = "Exposure/OQ_Exposure_Input_Greece.xml"
_CANONICAL_SOURCE_ASSET_REFERENCES = (
    "OQ_Exposure_Input_Greece_Com.csv",
    "OQ_Exposure_Input_Greece_Ind.csv",
    "OQ_Exposure_Input_Greece_Res.csv",
)
_CANONICAL_REPOSITORY_PATHS = (
    "Exposure/OQ_Exposure_Input_Greece_Com.csv",
    "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
    "Exposure/OQ_Exposure_Input_Greece_Res.csv",
)
_CANONICAL_MAX_FILE_BYTES = 64 * 1024 * 1024
_CANONICAL_TOTAL_DEADLINE_SECONDS = TOTAL_DEADLINE_SECONDS
_CANONICAL_TRUSTED_RESULT_LOGIN = "github-actions[bot]"
_CANONICAL_MAX_RESULT_UTF8_BYTES = 20_000
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
RESULT_SCHEMA_VERSION = _CANONICAL_RESULT_SCHEMA_VERSION
REQUEST_SCHEMA_VERSION = _CANONICAL_REQUEST_SCHEMA_VERSION
REQUEST_MARKER = _CANONICAL_REQUEST_MARKER
RESULT_MARKER = _CANONICAL_RESULT_MARKER
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
PARENT_CONSUMER_ISSUE = _CANONICAL_PARENT_CONSUMER_ISSUE
SOURCE_DECLARATION_COMMENT_ID = _CANONICAL_SOURCE_DECLARATION_COMMENT_ID
SOURCE_DECLARATION_EXECUTION_SHA = _CANONICAL_SOURCE_DECLARATION_EXECUTION_SHA
PARENT_RECEIPT_SHA256 = _CANONICAL_PARENT_RECEIPT_SHA256
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
RELEASE_TAG = _CANONICAL_RELEASE_TAG
COMMIT_SHA = _CANONICAL_COMMIT_SHA
CONSUMER_EVENT_ID = _CANONICAL_CONSUMER_EVENT_ID
PARENT_EXPOSURE_PATH = _CANONICAL_PARENT_EXPOSURE_PATH
SOURCE_ASSET_REFERENCES = _CANONICAL_SOURCE_ASSET_REFERENCES
REPOSITORY_PATHS = _CANONICAL_REPOSITORY_PATHS
MAX_FILE_BYTES = _CANONICAL_MAX_FILE_BYTES
TRUSTED_RESULT_LOGIN = _CANONICAL_TRUSTED_RESULT_LOGIN
MAX_RESULT_UTF8_BYTES = _CANONICAL_MAX_RESULT_UTF8_BYTES

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "issue", "target_sha", "requester"}
_RECEIPT_FIELDS = {
    "repository_path", "retrieved_at", "byte_count", "sha256",
    "content_type", "etag", "provider_file_bytes_read",
    "external_bytes_persisted", "publication_authorized",
}
_RESULT_FIELDS = {
    "schema_version", "source_issue", "parent_consumer_issue",
    "source_declaration_comment_id", "source_declaration_execution_sha",
    "parent_receipt_sha256", "target_sha", "execution_sha", "status",
    "failure_class", "dataset_id", "provider_host", "project_id",
    "project_path", "release_tag", "commit_sha", "consumer_event_id",
    "parent_exposure_path", "source_asset_references", "repository_paths",
    "receipts", "provider_file_bytes_read", "provider_file_content_profiled",
    "content_semantics_verified", "crs_semantics_verified",
    "taxonomy_semantics_verified", "replacement_cost_semantics_verified",
    "benchmark_agreement_inspected", "independent_validation_established",
    "holdout_status_established", "external_bytes_persisted",
    "publication_authorized", "model_use_authorized",
}

_FETCH_COMMENTS = fetch_repository_comments


class GreeceExposureCsvReceiptsError(RuntimeError):
    """Fail-closed error for the exact Greece exposure CSV receipt bundle."""


def _expected_repository_paths() -> tuple[str, str, str]:
    parent = PurePosixPath(_CANONICAL_PARENT_EXPOSURE_PATH)
    derived = tuple((parent.parent / name).as_posix() for name in _CANONICAL_SOURCE_ASSET_REFERENCES)
    if derived != _CANONICAL_REPOSITORY_PATHS:
        raise GreeceExposureCsvReceiptsError("frozen Greece exposure CSV path derivation drifted")
    return derived


def _require_canonical_target() -> None:
    exact = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (RESULT_SCHEMA_VERSION, _CANONICAL_RESULT_SCHEMA_VERSION, "result schema version"),
        (REQUEST_SCHEMA_VERSION, _CANONICAL_REQUEST_SCHEMA_VERSION, "request schema version"),
        (REQUEST_MARKER, _CANONICAL_REQUEST_MARKER, "request marker"),
        (RESULT_MARKER, _CANONICAL_RESULT_MARKER, "result marker"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (PARENT_CONSUMER_ISSUE, _CANONICAL_PARENT_CONSUMER_ISSUE, "parent consumer issue"),
        (SOURCE_DECLARATION_COMMENT_ID, _CANONICAL_SOURCE_DECLARATION_COMMENT_ID, "declaration comment"),
        (SOURCE_DECLARATION_EXECUTION_SHA, _CANONICAL_SOURCE_DECLARATION_EXECUTION_SHA, "declaration execution SHA"),
        (PARENT_RECEIPT_SHA256, _CANONICAL_PARENT_RECEIPT_SHA256, "parent receipt SHA-256"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROVIDER_HOST, "gitlab.seismo.ethz.ch", "provider host"),
        (PROVIDER_ROOT, "https://gitlab.seismo.ethz.ch", "provider root"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (RELEASE_TAG, _CANONICAL_RELEASE_TAG, "release tag"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit sha"),
        (CONSUMER_EVENT_ID, _CANONICAL_CONSUMER_EVENT_ID, "consumer event id"),
        (PARENT_EXPOSURE_PATH, _CANONICAL_PARENT_EXPOSURE_PATH, "parent exposure path"),
        (SOURCE_ASSET_REFERENCES, _CANONICAL_SOURCE_ASSET_REFERENCES, "source asset references"),
        (REPOSITORY_PATHS, _CANONICAL_REPOSITORY_PATHS, "repository paths"),
        (MAX_FILE_BYTES, _CANONICAL_MAX_FILE_BYTES, "file byte bound"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvReceiptsError(f"frozen Greece exposure CSV {label} authority drifted")
    if _expected_repository_paths() != _CANONICAL_REPOSITORY_PATHS:
        raise GreeceExposureCsvReceiptsError("frozen Greece exposure CSV path authority drifted")


def _require_production_transport_identity() -> None:
    identities = (
        (_open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (utc_now, _CANONICAL_UTC_NOW, "UTC clock"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise GreeceExposureCsvReceiptsError(f"frozen Greece exposure CSV production {label} drifted")


def _raw_file_url(repository_path: str) -> str:
    _require_canonical_target()
    if repository_path not in _CANONICAL_REPOSITORY_PATHS:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV path left frozen dependency set")
    encoded_path = urllib.parse.quote(repository_path, safe="")
    encoded_ref = urllib.parse.quote(_CANONICAL_COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _bounded_header(response: Any, name: str) -> str | None:
    return _header_value(response, name)


def _acquire_for_test(*, opener: Any, now: Any, monotonic: Any) -> list[dict[str, Any]]:
    _require_canonical_target()
    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    receipts: list[dict[str, Any]] = []
    for repository_path in _CANONICAL_REPOSITORY_PATHS:
        url = _raw_file_url(repository_path)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/csv,application/octet-stream;q=0.5",
                "User-Agent": "OpenCatastrophe-EFEHR-Greece-exposure-3CSV-receipts-v1",
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
        except (GreeceExposureCsvReceiptsError, EfehrAcquisitionError):
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            raise EfehrAcquisitionError(
                f"EFEHR Greece exposure CSV retrieval failed: {type(exc).__name__}"
            ) from exc

        if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
            raise GreeceExposureCsvReceiptsError("Greece exposure CSV retrieval timestamp is invalid")
        receipts.append(
            validate_receipt(
                {
                    "repository_path": repository_path,
                    "retrieved_at": retrieved_at,
                    "byte_count": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "content_type": content_type,
                    "etag": etag,
                    "provider_file_bytes_read": True,
                    "external_bytes_persisted": False,
                    "publication_authorized": False,
                },
                expected_path=repository_path,
            )
        )
    return validate_receipts(receipts)


def acquire_receipts() -> list[dict[str, Any]]:
    """Acquire byte receipts for exactly the three source-declared CSVs."""
    _require_canonical_target()
    _require_production_transport_identity()
    return _acquire_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )


_ACQUIRE = acquire_receipts


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GreeceExposureCsvReceiptsError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise GreeceExposureCsvReceiptsError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_canonical_target()
    if type(expected_issue) is not int or expected_issue != _CANONICAL_SOURCE_ISSUE:
        raise GreeceExposureCsvReceiptsError("wrong Greece exposure CSV receipts issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceExposureCsvReceiptsError("invalid execution SHA")
    if type(body) is not str or body.count(_CANONICAL_REQUEST_MARKER) != 1:
        raise GreeceExposureCsvReceiptsError("invalid Greece exposure CSV receipts request marker")
    before, after = body.split(_CANONICAL_REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except GreeceExposureCsvReceiptsError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureCsvReceiptsError("invalid Greece exposure CSV receipts request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts request fields drifted")
    for field, expected in (
        ("schema_version", _CANONICAL_REQUEST_SCHEMA_VERSION),
        ("issue", _CANONICAL_SOURCE_ISSUE),
        ("target_sha", execution_sha),
    ):
        observed = request[field]
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvReceiptsError(f"Greece exposure CSV receipts request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise GreeceExposureCsvReceiptsError("invalid requester identity")
    return request


def _validate_header_value(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or len(value.encode("utf-8")) > 1024:
        raise GreeceExposureCsvReceiptsError(f"{field} is outside the bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise GreeceExposureCsvReceiptsError(f"{field} contains control characters")
    return value


def validate_receipt(value: object, *, expected_path: str) -> dict[str, Any]:
    if expected_path not in _CANONICAL_REPOSITORY_PATHS:
        raise GreeceExposureCsvReceiptsError("receipt expected path left frozen dependency set")
    if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipt fields drifted")
    for field, expected in (
        ("repository_path", expected_path),
        ("provider_file_bytes_read", True),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    ):
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvReceiptsError(f"Greece exposure CSV receipt drifted at {field}")
    if type(value["retrieved_at"]) is not str or _UTC_RE.fullmatch(value["retrieved_at"]) is None:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipt timestamp is invalid")
    if (
        type(value["byte_count"]) is not int
        or isinstance(value["byte_count"], bool)
        or not (1 <= value["byte_count"] <= _CANONICAL_MAX_FILE_BYTES)
    ):
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipt byte count is invalid")
    if type(value["sha256"]) is not str or _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipt SHA-256 is invalid")
    _validate_header_value(value["content_type"], field="content_type")
    _validate_header_value(value["etag"], field="etag")
    return value


def validate_receipts(value: object) -> list[dict[str, Any]]:
    if type(value) is not list or len(value) != len(_CANONICAL_REPOSITORY_PATHS):
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipt bundle cardinality drifted")
    return [
        validate_receipt(receipt, expected_path=expected_path)
        for receipt, expected_path in zip(value, _CANONICAL_REPOSITORY_PATHS, strict=True)
    ]


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": _CANONICAL_RESULT_SCHEMA_VERSION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "parent_consumer_issue": _CANONICAL_PARENT_CONSUMER_ISSUE,
        "source_declaration_comment_id": _CANONICAL_SOURCE_DECLARATION_COMMENT_ID,
        "source_declaration_execution_sha": _CANONICAL_SOURCE_DECLARATION_EXECUTION_SHA,
        "parent_receipt_sha256": _CANONICAL_PARENT_RECEIPT_SHA256,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "release_tag": _CANONICAL_RELEASE_TAG,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "consumer_event_id": _CANONICAL_CONSUMER_EVENT_ID,
        "parent_exposure_path": _CANONICAL_PARENT_EXPOSURE_PATH,
        "source_asset_references": list(_CANONICAL_SOURCE_ASSET_REFERENCES),
        "repository_paths": list(_CANONICAL_REPOSITORY_PATHS),
        "provider_file_content_profiled": False,
        "content_semantics_verified": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_result(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _RESULT_FIELDS:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts result fields drifted")
    target_sha = value["target_sha"]
    if type(target_sha) is not str or _SHA1_RE.fullmatch(target_sha) is None:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts result target SHA is invalid")
    if value["execution_sha"] != target_sha:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts result execution SHA drifted")
    for field, expected in _base_result(execution_sha=target_sha).items():
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvReceiptsError(f"Greece exposure CSV receipts result drifted at {field}")
    if value["status"] == "pass":
        if value["failure_class"] is not None:
            raise GreeceExposureCsvReceiptsError("pass result carries a failure class")
        validate_receipts(value["receipts"])
        if value["provider_file_bytes_read"] is not True:
            raise GreeceExposureCsvReceiptsError("pass result did not assert complete byte reads")
    elif value["status"] == "blocked":
        if value["failure_class"] not in {"greece_exposure_csv_receipts_failure", "ledger_incomplete"}:
            raise GreeceExposureCsvReceiptsError("blocked result failure class drifted")
        if value["receipts"] is not None or value["provider_file_bytes_read"] is not None:
            raise GreeceExposureCsvReceiptsError("blocked result must not assert partial byte evidence")
    else:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts result status is invalid")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(encoded) > _CANONICAL_MAX_RESULT_UTF8_BYTES:
        raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts result exceeds publication bound")
    return value


def _parse_result_comment(body: str) -> dict[str, Any] | None:
    if _CANONICAL_RESULT_MARKER not in body:
        return None
    if body.count(_CANONICAL_RESULT_MARKER) != 1:
        raise GreeceExposureCsvReceiptsError("trusted Greece exposure CSV receipts result marker is duplicated")
    before, after = body.split(_CANONICAL_RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceExposureCsvReceiptsError("trusted Greece exposure CSV receipts result envelope is not canonical")
    try:
        payload = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except GreeceExposureCsvReceiptsError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureCsvReceiptsError("trusted Greece exposure CSV receipts result JSON is invalid") from exc
    return validate_result(payload)


def find_existing_terminal(comments: list[dict[str, Any]], *, execution_sha: str) -> int | None:
    matching_comment_id: int | None = None
    for comment in comments:
        if type(comment) is not dict:
            raise GreeceExposureCsvReceiptsError("Greece exposure CSV receipts ledger contains non-object comment")
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
            raise GreeceExposureCsvReceiptsError("matching Greece exposure CSV receipts result lacks a positive comment id")
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
        ledger = (
            comments
            if comments is not None
            else _FETCH_COMMENTS(repository, token, issue=_CANONICAL_SOURCE_ISSUE)
        )
    except LedgerError as exc:
        raise GreeceExposureCsvReceiptsError(
            "cannot read complete Greece exposure CSV receipts result ledger"
        ) from exc
    duplicate_comment_id = find_existing_terminal(ledger, execution_sha=execution_sha)
    if duplicate_comment_id is not None:
        return {"status": "duplicate", "duplicate_result_comment_id": duplicate_comment_id}

    try:
        receipts = validate_receipts(_ACQUIRE())
    except (GreeceExposureCsvReceiptsError, EfehrAcquisitionError):
        return validate_result(
            {
                **_base_result(execution_sha=execution_sha),
                "status": "blocked",
                "failure_class": "greece_exposure_csv_receipts_failure",
                "receipts": None,
                "provider_file_bytes_read": None,
            }
        )

    return validate_result(
        {
            **_base_result(execution_sha=execution_sha),
            "status": "pass",
            "failure_class": None,
            "receipts": receipts,
            "provider_file_bytes_read": True,
        }
    )


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
        raise GreeceExposureCsvReceiptsError(
            "Greece exposure CSV receipts request comment environment variable is absent"
        )
    result = prepare_result(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
        repository=args.repository,
        token=token,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
