# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Acquire the frozen Kosovo exposure object and emit taxonomy artifact identity only.

This pre-publication worker deliberately does not return literal taxonomy values.
It transiently re-verifies the already-receipted ESRM20 v1.0 Kosovo residential
bytes, delegates exact TAXONOMY extraction to the merged fail-closed extractor,
and then reduces the verified values to one deterministic canonical artifact
identity.

Canonical representation ``oc-taxonomy-u64be-utf8-sorted-v1`` is defined as the
concatenation, in ascending UTF-8 byte lexicographic order, of
``uint64_be(len(value_utf8)) || value_utf8`` for every exact source taxonomy
string. No trimming, case-folding, aliasing or other normalization is applied.
The canonical bytes are hashed and counted in memory only; neither provider
bytes, canonical derived bytes nor literal taxonomy strings are returned or
persisted by this worker.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
from typing import Any

try:
    from scripts import profile_efehr_kosovo_exposure as exposure
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
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
    from scripts.extract_efehr_kosovo_taxonomy import (
        EXPECTED_DISTINCT_COUNT,
        EXPECTED_VALUE_SET_SHA256,
        SCHEMA_VERSION as TAXONOMY_SET_SCHEMA_VERSION,
        TAXONOMY_FIELD,
        KosovoTaxonomyError,
        extract_verified_kosovo_taxonomy,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_kosovo_exposure as exposure
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
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
    from extract_efehr_kosovo_taxonomy import (
        EXPECTED_DISTINCT_COUNT,
        EXPECTED_VALUE_SET_SHA256,
        SCHEMA_VERSION as TAXONOMY_SET_SCHEMA_VERSION,
        TAXONOMY_FIELD,
        KosovoTaxonomyError,
        extract_verified_kosovo_taxonomy,
    )

SCHEMA_VERSION = "oc-esrm20-kosovo-taxonomy-artifact-identity-v1"
OPERATION_ID = "esrm20-kosovo-residential-taxonomy-identity-v1"
CONTROL_ISSUE = 363
WORKER_IDENTITY = "scripts.extract_efehr_kosovo_taxonomy.extract_verified_kosovo_taxonomy"
ARTIFACT_REPRESENTATION = "oc-taxonomy-u64be-utf8-sorted-v1"
MAX_TAXONOMY_UTF8_BYTES = 1024

_TAXONOMY_EVIDENCE_FIELDS = {
    "schema_version",
    "source_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "receipt_comment_id",
    "receipt_execution_sha",
    "byte_count",
    "sha256",
    "taxonomy_field",
    "taxonomy_count",
    "taxonomy_value_set_sha256",
    "taxonomies",
    "normalization_applied",
    "raw_rows_returned",
    "external_bytes_persisted",
    "publication_authorized",
}


class KosovoTaxonomyAcquisitionError(RuntimeError):
    """Raised when fixed acquisition or closed taxonomy identity evidence drifts."""


def _canonical_artifact_identity(values: list[str]) -> tuple[int, str]:
    """Return byte count and SHA-256 for the predeclared canonical taxonomy stream."""

    if type(values) is not list or not values:
        raise KosovoTaxonomyAcquisitionError("taxonomy values must be a non-empty list")

    encoded_values: list[bytes] = []
    for value in values:
        if type(value) is not str or value == "":
            raise KosovoTaxonomyAcquisitionError("taxonomy worker returned an invalid taxonomy value")
        encoded = value.encode("utf-8")
        if not encoded or len(encoded) > MAX_TAXONOMY_UTF8_BYTES:
            raise KosovoTaxonomyAcquisitionError("taxonomy worker returned an unbounded taxonomy value")
        if any(byte < 32 or byte == 127 for byte in encoded):
            raise KosovoTaxonomyAcquisitionError("taxonomy worker returned control characters")
        encoded_values.append(encoded)

    if encoded_values != sorted(encoded_values) or len(set(encoded_values)) != len(encoded_values):
        raise KosovoTaxonomyAcquisitionError(
            "taxonomy worker result must be unique and canonically sorted"
        )

    digest = hashlib.sha256()
    byte_count = 0
    for encoded in encoded_values:
        length_prefix = len(encoded).to_bytes(8, "big")
        digest.update(length_prefix)
        digest.update(encoded)
        byte_count += len(length_prefix) + len(encoded)

    if byte_count < 1 or byte_count > exposure.EXPECTED_BYTE_COUNT:
        raise KosovoTaxonomyAcquisitionError("canonical taxonomy artifact byte count is outside policy")
    return byte_count, digest.hexdigest()


def _validate_taxonomy_evidence(evidence: Any) -> tuple[int, str]:
    """Validate transient extractor evidence and reduce it immediately to identity."""

    if type(evidence) is not dict:
        raise KosovoTaxonomyAcquisitionError("taxonomy worker result must be an object")
    if set(evidence) != _TAXONOMY_EVIDENCE_FIELDS:
        raise KosovoTaxonomyAcquisitionError("taxonomy worker result fields drifted")

    exact_fields = {
        "schema_version": TAXONOMY_SET_SCHEMA_VERSION,
        "source_issue": exposure.SOURCE_ISSUE,
        "dataset_id": exposure.DATASET_ID,
        "project_id": exposure.PROJECT_ID,
        "project_path": exposure.PROJECT_PATH,
        "commit_sha": exposure.COMMIT_SHA,
        "repository_path": exposure.REPOSITORY_PATH,
        "receipt_comment_id": exposure.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": exposure.RECEIPT_EXECUTION_SHA,
        "byte_count": exposure.EXPECTED_BYTE_COUNT,
        "sha256": exposure.EXPECTED_SHA256,
        "taxonomy_field": TAXONOMY_FIELD,
        "taxonomy_count": EXPECTED_DISTINCT_COUNT,
        "taxonomy_value_set_sha256": EXPECTED_VALUE_SET_SHA256,
    }
    for field, expected in exact_fields.items():
        if type(evidence[field]) is not type(expected) or evidence[field] != expected:
            raise KosovoTaxonomyAcquisitionError(
                f"taxonomy worker result drifted from frozen {field}"
            )

    for field in (
        "normalization_applied",
        "raw_rows_returned",
        "external_bytes_persisted",
        "publication_authorized",
    ):
        if evidence[field] is not False:
            raise KosovoTaxonomyAcquisitionError(
                f"taxonomy worker widened {field} authority"
            )

    taxonomies = evidence["taxonomies"]
    if type(taxonomies) is not list or len(taxonomies) != EXPECTED_DISTINCT_COUNT:
        raise KosovoTaxonomyAcquisitionError("taxonomy worker returned an invalid taxonomy count")
    artifact_byte_count, artifact_sha256 = _canonical_artifact_identity(taxonomies)
    if artifact_sha256 != EXPECTED_VALUE_SET_SHA256:
        raise KosovoTaxonomyAcquisitionError("taxonomy worker result fingerprint drifted")
    return artifact_byte_count, artifact_sha256


def acquire_verified_kosovo_taxonomy_identity(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Retrieve the frozen Kosovo object and return no literal taxonomy values."""

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        target = validate_target(
            source_issue=exposure.SOURCE_ISSUE,
            dataset_id=exposure.DATASET_ID,
            project_id=exposure.PROJECT_ID,
            commit_sha=exposure.COMMIT_SHA,
            repository_path=exposure.REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise KosovoTaxonomyAcquisitionError("trusted Kosovo taxonomy target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-taxonomy-identity-v1",
        },
        method="GET",
    )

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=exposure.EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
            retrieved_at = now()
    except EfehrAcquisitionError as exc:
        raise KosovoTaxonomyAcquisitionError("Kosovo taxonomy retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise KosovoTaxonomyAcquisitionError(
            f"Kosovo taxonomy retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        artifact_byte_count, artifact_sha256 = _validate_taxonomy_evidence(
            extract_verified_kosovo_taxonomy(raw)
        )
    except KosovoTaxonomyError as exc:
        raise KosovoTaxonomyAcquisitionError("Kosovo taxonomy extraction failed closed") from exc
    finally:
        raw = b""

    return {
        "schema_version": SCHEMA_VERSION,
        "operation_id": OPERATION_ID,
        "control_issue": CONTROL_ISSUE,
        "worker_identity": WORKER_IDENTITY,
        "retrieved_at": retrieved_at,
        "source_issue": exposure.SOURCE_ISSUE,
        "dataset_id": exposure.DATASET_ID,
        "project_id": exposure.PROJECT_ID,
        "project_path": exposure.PROJECT_PATH,
        "commit_sha": exposure.COMMIT_SHA,
        "repository_path": exposure.REPOSITORY_PATH,
        "receipt_comment_id": exposure.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": exposure.RECEIPT_EXECUTION_SHA,
        "source_byte_count": exposure.EXPECTED_BYTE_COUNT,
        "source_sha256": exposure.EXPECTED_SHA256,
        "taxonomy_field": TAXONOMY_FIELD,
        "taxonomy_count": EXPECTED_DISTINCT_COUNT,
        "taxonomy_artifact_representation": ARTIFACT_REPRESENTATION,
        "taxonomy_artifact_byte_count": artifact_byte_count,
        "taxonomy_artifact_sha256": artifact_sha256,
        "taxonomy_values_returned": False,
        "normalization_applied": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "derived_artifact_persisted": False,
        "publication_authorized": False,
    }
