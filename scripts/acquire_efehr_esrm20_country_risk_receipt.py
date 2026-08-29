# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted receipt worker for the frozen ESRM20 v1.0 country-risk table.

This module exposes one fixed target only. The caller cannot select provider,
project, commit, path, dataset, issue, or operation. A successful result proves
byte identity/retrieval provenance only; it does not publish provider rows or
establish reference-loss agreement.
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
SOURCE_ISSUE = 778
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Risk/European_Risk_Country.csv"
OPERATION_ID = "esrm20-country-risk-table-v1"
MAX_COUNTRY_RISK_BYTES = 8 * 1024 * 1024

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic


class Esrm20CountryRiskReceiptError(RuntimeError):
    """Fail-closed fixed country-risk receipt error."""


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise Esrm20CountryRiskReceiptError("production transport authority drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise Esrm20CountryRiskReceiptError("production clock authority drifted")
    exact = (
        (SOURCE_ISSUE, 778),
        (DATASET_ID, "efehr.esrm20.risk-inputs.v1.0"),
        (PROJECT_ID, 269),
        (PROJECT_PATH, "efehr/esrm20"),
        (COMMIT_SHA, "05f83bbc9df81d02ee8ddb1801d9d781355ce783"),
        (REPOSITORY_PATH, "Risk/European_Risk_Country.csv"),
        (OPERATION_ID, "esrm20-country-risk-table-v1"),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20CountryRiskReceiptError("frozen country-risk authority drifted")


def _acquire_for_test(
    *,
    opener: Any,
    now: Any,
    monotonic: Any,
) -> dict[str, Any]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Esrm20CountryRiskReceiptError("fixed country-risk target is invalid") from exc

    if target.project_path != PROJECT_PATH:
        raise Esrm20CountryRiskReceiptError("fixed country-risk project identity drifted")

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-country-risk-receipt-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, MAX_COUNTRY_RISK_BYTES)
            retrieved_at = now()
            try:
                core_receipt = receipt_from_stream(
                    target,
                    _DeadlineStream(response, deadline=deadline, monotonic=monotonic),
                    final_url=file_url,
                    retrieved_at=retrieved_at,
                    headers=getattr(response, "headers", None),
                    max_bytes=MAX_COUNTRY_RISK_BYTES,
                )
            except EfehrReceiptError as exc:
                raise Esrm20CountryRiskReceiptError("country-risk byte receipt failed") from exc
    except Esrm20CountryRiskReceiptError:
        raise
    except EfehrAcquisitionError as exc:
        raise Esrm20CountryRiskReceiptError("provider country-risk acquisition failed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Esrm20CountryRiskReceiptError(
            f"provider country-risk acquisition failed: {type(exc).__name__}"
        ) from exc

    result = dict(core_receipt)
    result["schema_version"] = SCHEMA_VERSION
    result["operation_id"] = OPERATION_ID
    result["provider_rows_exposed"] = False
    result["reference_loss_agreement_verified"] = False
    result["model_use_authorized"] = False
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
        "provider_rows_exposed": result["provider_rows_exposed"],
        "reference_loss_agreement_verified": result["reference_loss_agreement_verified"],
        "publication_authorized": result["publication_authorized"],
        "model_use_authorized": result["model_use_authorized"],
    }


def acquire_country_risk_receipt(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Receipt only the frozen ESRM20 v1.0 country-risk CSV."""
    if opener is None and now is utc_now and monotonic is time.monotonic:
        _require_production_identity()
        opener = _CANONICAL_OPEN_FIXED
        monotonic = _CANONICAL_MONOTONIC
    elif opener is None:
        opener = _CANONICAL_OPEN_FIXED
    return _acquire_for_test(opener=opener, now=now, monotonic=monotonic)
