# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted acquisition worker for the frozen ESRM20 project-278 site manual.

This module deliberately adds no provider-selection or PDF-parsing surface. It
reuses the reviewed EFEHR transport and receipt primitives while fixing project,
commit, repository path, dataset identity, and operation identity in code.
Provider bytes are streamed only into the receipt hash and are never returned or
persisted by this worker.

The public production entry point is deliberately parameterless. Injectable
transport and clock seams exist only behind the private test helper so synthetic
offline receipts cannot be confused with production acquisition evidence.
"""

from __future__ import annotations

import http.client
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
        MAX_FILE_BYTES,
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
        MAX_FILE_BYTES,
        raw_file_api_url,
        receipt_from_stream,
        validate_target,
    )


_CANONICAL_SCHEMA_VERSION = "oc-efehr-trusted-acquisition-v1"
_CANONICAL_OPERATION_ID = "esrm20-project278-exposure-manual-receipt-v1"
_CANONICAL_SOURCE_ISSUE = 291
_CANONICAL_DATASET_ID = "efehr.esrm20.sitemodel-source"
_CANONICAL_PROJECT_ID = 278
_CANONICAL_COMMIT_SHA = "038c91d2bf5a07f6b54ff51639aad874d6837ea9"
_CANONICAL_REPOSITORY_PATH = "ExposureReadme.pdf"
_CANONICAL_MAX_FILE_BYTES = MAX_FILE_BYTES

# Freeze production authority at module initialization. Tests exercise injected
# seams only through _acquire_for_test(); the public worker rejects later drift.
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
OPERATION_ID = _CANONICAL_OPERATION_ID
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH


def _require_canonical_aliases() -> None:
    aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (MAX_FILE_BYTES, _CANONICAL_MAX_FILE_BYTES, "maximum byte count"),
    )
    for observed, expected, label in aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise EfehrAcquisitionError(
                f"frozen project-278 manual {label} authority drifted"
            )


def _require_production_transport_identity() -> None:
    identities = (
        (_open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (utc_now, _CANONICAL_UTC_NOW, "UTC clock"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise EfehrAcquisitionError(
                f"frozen project-278 manual production {label} drifted"
            )


def _acquire_for_test(
    *,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    """Private injectable helper for deterministic offline tests only."""

    _require_canonical_aliases()
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
        raise EfehrAcquisitionError("trusted EFEHR target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/pdf,application/octet-stream;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )

    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, _CANONICAL_MAX_FILE_BYTES)
            retrieved_at = now()
            try:
                core_receipt = receipt_from_stream(
                    target,
                    _DeadlineStream(
                        response,
                        deadline=deadline,
                        monotonic=monotonic,
                    ),
                    final_url=file_url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=_CANONICAL_MAX_FILE_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError("EFEHR artifact receipt failed") from exc
    except EfehrAcquisitionError:
        raise
    except (
        OSError,
        http.client.HTTPException,
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
    ) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    result = dict(core_receipt)
    result["schema_version"] = _CANONICAL_SCHEMA_VERSION
    result["operation_id"] = _CANONICAL_OPERATION_ID
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


def acquire_project278_manual_receipt() -> dict[str, Any]:
    """Fetch only the frozen manual using immutable production authority."""

    _require_canonical_aliases()
    _require_production_transport_identity()
    return _acquire_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )
