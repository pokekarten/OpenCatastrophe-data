# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted byte-receipt workers for source-derived ESRM20 v1.0 risk INI candidates.

The three repository paths in this module come only from the trusted-main
project-269/v1.0 Configuration_files inventory recorded under #281. Provider
filenames are preserved as provider metadata; they do not establish a Kosovo
historical-group assignment or any model-use/publication authority.

Public entry points are zero-argument and own the fixed transport/clock
identities. Test injection is confined to the private helper. Provider bytes
are hashed in memory and are never persisted by this worker.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _DeadlineStream,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )

SCHEMA_VERSION = "oc-efehr-trusted-acquisition-v1"
SOURCE_ISSUE = 281
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"

GROUP1_REPOSITORY_PATH = "Configuration_files/config_ebrisk_Group1.ini"
GROUP2_REPOSITORY_PATH = "Configuration_files/config_ebrisk_Group2.ini"
ICELAND_REPOSITORY_PATH = "Configuration_files/config_ebrisk_Iceland.ini"

GROUP1_OPERATION_ID = "esrm20-ebrisk-group1-config-candidate-v1"
GROUP2_OPERATION_ID = "esrm20-ebrisk-group2-config-candidate-v1"
ICELAND_OPERATION_ID = "esrm20-ebrisk-iceland-config-candidate-v1"
MAX_CONFIG_BYTES = 1024 * 1024

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_DEADLINE_STREAM = _DeadlineStream
_CANONICAL_DECLARED_LENGTH = _declared_length
_CANONICAL_REMAINING = _remaining
_CANONICAL_VALIDATE_EXACT_RESPONSE = _validate_exact_response
_CANONICAL_VALIDATE_TARGET = validate_target
_CANONICAL_RAW_FILE_API_URL = raw_file_api_url
_CANONICAL_RECEIPT_FROM_STREAM = receipt_from_stream
_CANONICAL_REQUEST = urllib.request.Request

_CANONICAL_SCHEMA_VERSION = SCHEMA_VERSION
_CANONICAL_TOTAL_DEADLINE_SECONDS = TOTAL_DEADLINE_SECONDS
_CANONICAL_MAX_CONFIG_BYTES = MAX_CONFIG_BYTES
_CANONICAL_SOURCE_ISSUE = SOURCE_ISSUE
_CANONICAL_DATASET_ID = DATASET_ID
_CANONICAL_PROJECT_ID = PROJECT_ID
_CANONICAL_PROJECT_PATH = PROJECT_PATH
_CANONICAL_COMMIT_SHA = COMMIT_SHA
_CANONICAL_PATHS = (
    GROUP1_REPOSITORY_PATH,
    GROUP2_REPOSITORY_PATH,
    ICELAND_REPOSITORY_PATH,
)
_CANONICAL_OPERATIONS = (
    GROUP1_OPERATION_ID,
    GROUP2_OPERATION_ID,
    ICELAND_OPERATION_ID,
)


def _require_production_identity() -> None:
    """Fail before transport if mutable production authority was rebound."""

    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise EfehrAcquisitionError("frozen EBRISK risk-config production transport drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise EfehrAcquisitionError("frozen EBRISK risk-config monotonic clock drifted")
    if utc_now is not _CANONICAL_UTC_NOW:
        raise EfehrAcquisitionError("frozen EBRISK risk-config wall clock drifted")
    if validate_target is not _CANONICAL_VALIDATE_TARGET:
        raise EfehrAcquisitionError("frozen EBRISK risk-config target validator drifted")
    if raw_file_api_url is not _CANONICAL_RAW_FILE_API_URL:
        raise EfehrAcquisitionError("frozen EBRISK risk-config URL builder drifted")
    if receipt_from_stream is not _CANONICAL_RECEIPT_FROM_STREAM:
        raise EfehrAcquisitionError("frozen EBRISK risk-config receipt function drifted")
    if _DeadlineStream is not _CANONICAL_DEADLINE_STREAM:
        raise EfehrAcquisitionError("frozen EBRISK risk-config deadline stream drifted")
    if _declared_length is not _CANONICAL_DECLARED_LENGTH:
        raise EfehrAcquisitionError("frozen EBRISK risk-config length validator drifted")
    if _remaining is not _CANONICAL_REMAINING:
        raise EfehrAcquisitionError("frozen EBRISK risk-config deadline helper drifted")
    if _validate_exact_response is not _CANONICAL_VALIDATE_EXACT_RESPONSE:
        raise EfehrAcquisitionError("frozen EBRISK risk-config response validator drifted")
    if urllib.request.Request is not _CANONICAL_REQUEST:
        raise EfehrAcquisitionError("frozen EBRISK risk-config request constructor drifted")
    if _acquire_candidate_receipt is not _CANONICAL_ACQUIRE_CANDIDATE_RECEIPT:
        raise EfehrAcquisitionError("frozen EBRISK risk-config private helper drifted")

    exact = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (TOTAL_DEADLINE_SECONDS, _CANONICAL_TOTAL_DEADLINE_SECONDS, "deadline"),
        (MAX_CONFIG_BYTES, _CANONICAL_MAX_CONFIG_BYTES, "maximum config bytes"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (
            (GROUP1_REPOSITORY_PATH, GROUP2_REPOSITORY_PATH, ICELAND_REPOSITORY_PATH),
            _CANONICAL_PATHS,
            "repository paths",
        ),
        (
            (GROUP1_OPERATION_ID, GROUP2_OPERATION_ID, ICELAND_OPERATION_ID),
            _CANONICAL_OPERATIONS,
            "operation ids",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise EfehrAcquisitionError(f"frozen EBRISK risk-config {label} drifted")


def _acquire_candidate_receipt(
    *,
    repository_path: str,
    operation_id: str,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    """Private injectable helper for deterministic offline tests."""

    if repository_path not in _CANONICAL_PATHS:
        raise EfehrAcquisitionError("EBRISK risk-config path is outside the frozen candidate set")
    path_index = _CANONICAL_PATHS.index(repository_path)
    if operation_id != _CANONICAL_OPERATIONS[path_index]:
        raise EfehrAcquisitionError("EBRISK risk-config operation/path binding drifted")

    deadline = monotonic() + _CANONICAL_TOTAL_DEADLINE_SECONDS
    try:
        target = _CANONICAL_VALIDATE_TARGET(
            source_issue=_CANONICAL_SOURCE_ISSUE,
            dataset_id=_CANONICAL_DATASET_ID,
            project_id=_CANONICAL_PROJECT_ID,
            commit_sha=_CANONICAL_COMMIT_SHA,
            repository_path=repository_path,
        )
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError("trusted EBRISK risk-config target is invalid") from exc

    if target.project_path != _CANONICAL_PROJECT_PATH:
        raise EfehrAcquisitionError("trusted EBRISK risk-config project path drifted")

    file_url = _CANONICAL_RAW_FILE_API_URL(target)
    request = _CANONICAL_REQUEST(
        file_url,
        headers={
            "Accept": "text/plain,text/x-ini;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-ebrisk-risk-config-receipt-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_CANONICAL_REMAINING(deadline, monotonic)) as response:
            _CANONICAL_VALIDATE_EXACT_RESPONSE(response, file_url)
            _CANONICAL_DECLARED_LENGTH(response, _CANONICAL_MAX_CONFIG_BYTES)
            retrieved_at = now()
            try:
                core_receipt = _CANONICAL_RECEIPT_FROM_STREAM(
                    target,
                    _CANONICAL_DEADLINE_STREAM(
                        response, deadline=deadline, monotonic=monotonic
                    ),
                    final_url=file_url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=_CANONICAL_MAX_CONFIG_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError(f"EFEHR artifact receipt failed: {exc}") from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    result = dict(core_receipt)
    result["schema_version"] = _CANONICAL_SCHEMA_VERSION
    result["operation_id"] = operation_id
    return {
        "schema_version": result["schema_version"],
        "operation_id": result["operation_id"],
        "source_issue": result["source_issue"],
        "dataset_id": result["dataset_id"],
        "provider_host": result["provider_host"],
        "project_id": result["project_id"],
        "project_path": result["project_path"],
        "commit_sha": result["commit_sha"],
        "repository_path": result["repository_path"],
        "requested_url": result["requested_url"],
        "final_url": result["final_url"],
        "retrieved_at": result["retrieved_at"],
        "byte_count": result["byte_count"],
        "sha256": result["sha256"],
        "content_type": result["content_type"],
        "etag": result["etag"],
        "external_bytes_persisted": result["external_bytes_persisted"],
        "publication_authorized": result["publication_authorized"],
    }


_CANONICAL_ACQUIRE_CANDIDATE_RECEIPT = _acquire_candidate_receipt


def acquire_ebrisk_group1_candidate_receipt() -> dict[str, Any]:
    """Receipt only the provider-named Group1 EBRISK risk-config candidate."""

    _require_production_identity()
    return _CANONICAL_ACQUIRE_CANDIDATE_RECEIPT(
        repository_path=_CANONICAL_PATHS[0],
        operation_id=_CANONICAL_OPERATIONS[0],
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )


def acquire_ebrisk_group2_candidate_receipt() -> dict[str, Any]:
    """Receipt only the provider-named Group2 EBRISK risk-config candidate."""

    _require_production_identity()
    return _CANONICAL_ACQUIRE_CANDIDATE_RECEIPT(
        repository_path=_CANONICAL_PATHS[1],
        operation_id=_CANONICAL_OPERATIONS[1],
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )


def acquire_ebrisk_iceland_candidate_receipt() -> dict[str, Any]:
    """Receipt only the provider-named Iceland EBRISK risk-config candidate."""

    _require_production_identity()
    return _CANONICAL_ACQUIRE_CANDIDATE_RECEIPT(
        repository_path=_CANONICAL_PATHS[2],
        operation_id=_CANONICAL_OPERATIONS[2],
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )
