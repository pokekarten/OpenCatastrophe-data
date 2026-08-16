# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted acquisition worker for the frozen ESRM20 Kosovo site-model input.

This module adds no provider-selection surface. It reuses the reviewed EFEHR
transport and receipt primitives while fixing project, commit, repository path,
dataset identity, and operation identity in code. A receipt proves byte identity
only; site-field, CRS, unit, missingness, and model-use semantics remain separate
post-receipt review gates.
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


# Production authority is private. Public names below are review/back-compat
# aliases only; any drift fails before provider I/O.
_CANONICAL_SCHEMA_VERSION = "oc-efehr-trusted-acquisition-v1"
_CANONICAL_OPERATION_ID = "esrm20-kosovo-site-model-v1"
_CANONICAL_SOURCE_ISSUE = 284
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROVIDER_HOST = "gitlab.seismo.ethz.ch"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
_CANONICAL_MAX_SITE_MODEL_BYTES = MAX_FILE_BYTES

# Bind trusted production transport/time identities at module initialization.
# Later module-global rebinding is treated as authority drift rather than as a
# caller-selectable transport/clock surface.
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
MAX_SITE_MODEL_BYTES = _CANONICAL_MAX_SITE_MODEL_BYTES


def _require_canonical_aliases() -> None:
    aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (
            MAX_SITE_MODEL_BYTES,
            _CANONICAL_MAX_SITE_MODEL_BYTES,
            "maximum byte count",
        ),
    )
    for observed, expected, label in aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise EfehrAcquisitionError(
                f"frozen Kosovo site-model {label} drifted"
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
                f"frozen Kosovo site-model production {label} drifted"
            )


def _is_lower_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_core_receipt(receipt: object, *, file_url: str) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise EfehrAcquisitionError("Kosovo site-model receipt is invalid")

    exact = (
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("provider_host", _CANONICAL_PROVIDER_HOST),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("repository_path", _CANONICAL_REPOSITORY_PATH),
        ("requested_url", file_url),
        ("final_url", file_url),
    )
    for field, expected in exact:
        observed = receipt.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EfehrAcquisitionError(
                f"Kosovo site-model receipt identity drifted at {field}"
            )

    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not retrieved_at:
        raise EfehrAcquisitionError(
            "Kosovo site-model receipt retrieval time is invalid"
        )
    byte_count = receipt.get("byte_count")
    if (
        type(byte_count) is not int
        or isinstance(byte_count, bool)
        or byte_count <= 0
        or byte_count > _CANONICAL_MAX_SITE_MODEL_BYTES
    ):
        raise EfehrAcquisitionError(
            "Kosovo site-model receipt byte count is invalid"
        )
    if not _is_lower_sha256(receipt.get("sha256")):
        raise EfehrAcquisitionError(
            "Kosovo site-model receipt SHA-256 is invalid"
        )

    for field, value in receipt.items():
        if field.endswith("_authorized") or field.endswith("_persisted"):
            if value is not False:
                raise EfehrAcquisitionError(
                    f"Kosovo site-model receipt widened authority at {field}"
                )
    for field in ("external_bytes_persisted", "publication_authorized"):
        if receipt.get(field) is not False:
            raise EfehrAcquisitionError(
                f"Kosovo site-model receipt widened authority at {field}"
            )

    for field in ("content_type", "etag"):
        value = receipt.get(field)
        if value is not None and type(value) is not str:
            raise EfehrAcquisitionError(
                f"Kosovo site-model receipt {field} is invalid"
            )
    return receipt


def _acquire_kosovo_site_receipt(
    *,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    """Private injectable helper used only for deterministic offline tests."""

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
            "Accept": (
                "application/xml,text/xml,text/plain;q=0.9,"
                "application/octet-stream;q=0.8"
            ),
            "User-Agent": "OpenCatastrophe-EFEHR-acquisition-v1",
        },
        method="GET",
    )

    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, _CANONICAL_MAX_SITE_MODEL_BYTES)
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
                    max_bytes=_CANONICAL_MAX_SITE_MODEL_BYTES,
                )
            except EfehrReceiptError as exc:
                raise EfehrAcquisitionError(
                    "EFEHR artifact receipt failed"
                ) from exc
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR artifact retrieval failed: {type(exc).__name__}"
        ) from exc

    receipt = _validate_core_receipt(core_receipt, file_url=file_url)
    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "operation_id": _CANONICAL_OPERATION_ID,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "provider_host": _CANONICAL_PROVIDER_HOST,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "requested_url": file_url,
        "final_url": file_url,
        "retrieved_at": receipt["retrieved_at"],
        "byte_count": receipt["byte_count"],
        "sha256": receipt["sha256"],
        "content_type": receipt["content_type"],
        "etag": receipt["etag"],
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def acquire_kosovo_site_receipt() -> dict[str, Any]:
    """Fetch only the frozen Kosovo site XML with immutable production authority."""

    _require_production_transport_identity()
    return _acquire_kosovo_site_receipt(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )
