# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted transient acquisition of exact ESRM20 mapping headers only.

The worker re-materializes only the already-receipted immutable ESRM20 v1.0
mapping object, verifies its byte identity, and passes the transient bytes to
the reviewed header-disclosure helper merged by PR #416. Raw provider bytes,
rows, and cell values are never returned or persisted.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts import acquire_efehr_esrm20_mapping_receipt as mapping_receipt
    from scripts import profile_efehr_esrm20_mapping_headers as header_profile
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_mapping_receipt as mapping_receipt
    import profile_efehr_esrm20_mapping_headers as header_profile
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )

_CANONICAL_SCHEMA_VERSION = "oc-esrm20-mapping-header-acquisition-v1"
_CANONICAL_OPERATION_ID = "esrm20-exposure-vulnerability-mapping-header-disclosure-v1"
_CANONICAL_SOURCE_ISSUE = 283
_CANONICAL_CONTROL_ISSUE = 410
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROVIDER_HOST = "gitlab.seismo.ethz.ch"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"
_CANONICAL_EXPECTED_BYTE_COUNT = 83_585
_CANONICAL_EXPECTED_SHA256 = (
    "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
)
_CANONICAL_RECEIPT_COMMENT_ID = 5303466667
_CANONICAL_RECEIPT_RUN_ID = 31899242278
_CANONICAL_RECEIPT_EXECUTION_SHA = "9b1bb7127138247cf613dbf444d139c189c9b13a"
_CANONICAL_HEADER_SOURCE_COMMIT = "e54b1f7a6220bafc67da540a57ed6fc7f6534e28"
_CANONICAL_HEADER_PATH = "scripts/profile_efehr_esrm20_mapping_headers.py"
_CANONICAL_HEADER_FUNCTION = "disclose_verified_mapping_headers"
_CANONICAL_HEADER_GIT_BLOB_SHA1 = "cd0aa5cb573dbd8db431ef27b6a762c0a1d54c7c"
_CANONICAL_HEADER_SCHEMA_VERSION = "oc-esrm20-mapping-header-disclosure-v1"
_CANONICAL_DISCLOSURE_SCOPE = "exact_header_strings_only"
_CANONICAL_HEADER_DISCLOSER = header_profile.disclose_verified_mapping_headers
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
OPERATION_ID = _CANONICAL_OPERATION_ID
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
CONTROL_ISSUE = _CANONICAL_CONTROL_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256
RECEIPT_COMMENT_ID = _CANONICAL_RECEIPT_COMMENT_ID
RECEIPT_RUN_ID = _CANONICAL_RECEIPT_RUN_ID
RECEIPT_EXECUTION_SHA = _CANONICAL_RECEIPT_EXECUTION_SHA
HEADER_SOURCE_COMMIT = _CANONICAL_HEADER_SOURCE_COMMIT
HEADER_PATH = _CANONICAL_HEADER_PATH
HEADER_FUNCTION = _CANONICAL_HEADER_FUNCTION
HEADER_GIT_BLOB_SHA1 = _CANONICAL_HEADER_GIT_BLOB_SHA1


class Esrm20MappingHeaderAcquisitionError(RuntimeError):
    """Raised when exact bounded mapping-header acquisition cannot close safely."""


def _git_blob_sha1(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Esrm20MappingHeaderAcquisitionError(
            "reviewed mapping header helper source is unavailable"
        ) from exc
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def _is_lower_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_production_transport_identity() -> None:
    identities = (
        (_open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (utc_now, _CANONICAL_UTC_NOW, "UTC clock"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise Esrm20MappingHeaderAcquisitionError(
                f"frozen ESRM20 mapping header production {label} drifted"
            )


def _require_canonical_authority() -> None:
    aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (CONTROL_ISSUE, _CANONICAL_CONTROL_ISSUE, "control issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "byte count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "SHA-256"),
        (RECEIPT_COMMENT_ID, _CANONICAL_RECEIPT_COMMENT_ID, "receipt comment"),
        (RECEIPT_RUN_ID, _CANONICAL_RECEIPT_RUN_ID, "receipt run"),
        (RECEIPT_EXECUTION_SHA, _CANONICAL_RECEIPT_EXECUTION_SHA, "receipt execution"),
        (HEADER_SOURCE_COMMIT, _CANONICAL_HEADER_SOURCE_COMMIT, "header source commit"),
        (HEADER_PATH, _CANONICAL_HEADER_PATH, "header helper path"),
        (HEADER_FUNCTION, _CANONICAL_HEADER_FUNCTION, "header helper function"),
        (HEADER_GIT_BLOB_SHA1, _CANONICAL_HEADER_GIT_BLOB_SHA1, "header helper blob"),
    )
    for observed, expected, label in aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingHeaderAcquisitionError(
                f"frozen ESRM20 mapping header {label} drifted"
            )

    dependencies = (
        (mapping_receipt.SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "receipt source issue"),
        (mapping_receipt.DATASET_ID, _CANONICAL_DATASET_ID, "receipt dataset id"),
        (mapping_receipt.PROJECT_ID, _CANONICAL_PROJECT_ID, "receipt project id"),
        (mapping_receipt.COMMIT_SHA, _CANONICAL_COMMIT_SHA, "receipt commit"),
        (mapping_receipt.REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "receipt path"),
        (header_profile.DECISION_ISSUE, _CANONICAL_CONTROL_ISSUE, "header decision issue"),
        (header_profile.DISCLOSURE_SCOPE, _CANONICAL_DISCLOSURE_SCOPE, "header scope"),
        (header_profile.SCHEMA_VERSION, _CANONICAL_HEADER_SCHEMA_VERSION, "header schema"),
    )
    for observed, expected, label in dependencies:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingHeaderAcquisitionError(
                f"frozen ESRM20 mapping header dependency {label} drifted"
            )

    if header_profile.disclose_verified_mapping_headers is not _CANONICAL_HEADER_DISCLOSER:
        raise Esrm20MappingHeaderAcquisitionError(
            "frozen ESRM20 mapping header helper function identity drifted"
        )
    source_file = getattr(header_profile, "__file__", None)
    if type(source_file) is not str or not source_file:
        raise Esrm20MappingHeaderAcquisitionError(
            "reviewed mapping header helper source is unavailable"
        )
    source_path = Path(source_file)
    if source_path.name != Path(_CANONICAL_HEADER_PATH).name:
        raise Esrm20MappingHeaderAcquisitionError(
            "frozen ESRM20 mapping header helper source path drifted"
        )
    if _git_blob_sha1(source_path) != _CANONICAL_HEADER_GIT_BLOB_SHA1:
        raise Esrm20MappingHeaderAcquisitionError(
            "frozen ESRM20 mapping header helper source blob drifted"
        )


def _validate_disclosure(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise Esrm20MappingHeaderAcquisitionError("mapping header disclosure is invalid")
    exact = (
        ("schema_version", _CANONICAL_HEADER_SCHEMA_VERSION),
        ("decision_issue", _CANONICAL_CONTROL_ISSUE),
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("profile_issue", 404),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("repository_path", _CANONICAL_REPOSITORY_PATH),
        ("receipt_comment_id", _CANONICAL_RECEIPT_COMMENT_ID),
        ("receipt_run_id", _CANONICAL_RECEIPT_RUN_ID),
        ("receipt_execution_sha", _CANONICAL_RECEIPT_EXECUTION_SHA),
        ("byte_count", _CANONICAL_EXPECTED_BYTE_COUNT),
        ("sha256", _CANONICAL_EXPECTED_SHA256),
        ("disclosure_scope", _CANONICAL_DISCLOSURE_SCOPE),
        ("header_strings_returned", True),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingHeaderAcquisitionError(
                f"mapping header disclosure drifted at {field}"
            )

    for field in (
        "cell_values_returned",
        "raw_rows_returned",
        "normalization_applied",
        "mapping_interpretation_authorized",
        "taxonomy_join_authorized",
        "vulnerability_selection_authorized",
        "external_bytes_persisted",
        "derived_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    ):
        if result.get(field) is not False:
            raise Esrm20MappingHeaderAcquisitionError(
                f"mapping header disclosure widened authority at {field}"
            )

    count = result.get("column_count")
    headers = result.get("headers")
    if type(count) is not int or isinstance(count, bool) or count <= 0:
        raise Esrm20MappingHeaderAcquisitionError("mapping header column count is invalid")
    if type(headers) is not list or len(headers) != count:
        raise Esrm20MappingHeaderAcquisitionError("mapping header list is invalid")
    if any(type(value) is not str or not value for value in headers):
        raise Esrm20MappingHeaderAcquisitionError("mapping header literal is invalid")
    if len(set(headers)) != count:
        raise Esrm20MappingHeaderAcquisitionError("mapping header literals are not unique")
    if not _is_lower_sha256(result.get("ordered_header_sha256")):
        raise Esrm20MappingHeaderAcquisitionError(
            "mapping header fingerprint is invalid"
        )
    return result


def _acquire_esrm20_mapping_headers(
    *,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    """Private injectable helper for deterministic offline tests."""

    _require_canonical_authority()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        target = validate_target(
            source_issue=_CANONICAL_SOURCE_ISSUE,
            dataset_id=_CANONICAL_DATASET_ID,
            project_id=_CANONICAL_PROJECT_ID,
            commit_sha=_CANONICAL_COMMIT_SHA,
            repository_path=_CANONICAL_REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Esrm20MappingHeaderAcquisitionError(
            "trusted mapping header target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-ESRM20-mapping-headers-v1",
        },
        method="GET",
    )

    raw = b""
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            declared = _declared_length(response, _CANONICAL_EXPECTED_BYTE_COUNT)
            if declared is not None and declared != _CANONICAL_EXPECTED_BYTE_COUNT:
                raise EfehrAcquisitionError(
                    "mapping Content-Length does not match trusted receipt"
                )
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
            if len(raw) != _CANONICAL_EXPECTED_BYTE_COUNT:
                raise EfehrAcquisitionError("mapping byte count does not match trusted receipt")
            if hashlib.sha256(raw).hexdigest() != _CANONICAL_EXPECTED_SHA256:
                raise EfehrAcquisitionError("mapping SHA-256 does not match trusted receipt")
            retrieved_at = now()
    except EfehrAcquisitionError as exc:
        raise Esrm20MappingHeaderAcquisitionError(
            "mapping header retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Esrm20MappingHeaderAcquisitionError(
            f"mapping header retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        disclosure = _validate_disclosure(_CANONICAL_HEADER_DISCLOSER(raw))
    except header_profile.MappingHeaderDisclosureError as exc:
        raise Esrm20MappingHeaderAcquisitionError(
            "trusted mapping header disclosure failed closed"
        ) from exc
    finally:
        raw = b""

    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "operation_id": _CANONICAL_OPERATION_ID,
        "control_issue": _CANONICAL_CONTROL_ISSUE,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": _CANONICAL_PROVIDER_HOST,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": _CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_run_id": _CANONICAL_RECEIPT_RUN_ID,
        "receipt_execution_sha": _CANONICAL_RECEIPT_EXECUTION_SHA,
        "header_source_commit": _CANONICAL_HEADER_SOURCE_COMMIT,
        "header_path": _CANONICAL_HEADER_PATH,
        "header_function": _CANONICAL_HEADER_FUNCTION,
        "header_git_blob_sha1": _CANONICAL_HEADER_GIT_BLOB_SHA1,
        "retrieved_at": retrieved_at,
        "disclosure": disclosure,
        "raw_bytes_returned": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }


def acquire_esrm20_mapping_headers() -> dict[str, Any]:
    """Acquire exact mapping bytes transiently and return bounded headers only."""

    _require_production_transport_identity()
    return _acquire_esrm20_mapping_headers(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )
