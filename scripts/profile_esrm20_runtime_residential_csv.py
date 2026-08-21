# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed exact-byte profiler for the receipted ESRM20 Kosovo runtime residential CSV.

Production has no caller-selectable provider target. The worker transiently reads one
immutable GitLab object, proves the already-established byte count and SHA-256, and
only then delegates to the existing interpretation-light CSV structure profiler.
Provider bytes are never persisted and this module does not promote taxonomy, CRS,
value, publication, equivalence, or model-use semantics.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
from typing import Any

try:
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
    from scripts.profile_efehr_kosovo_exposure import (
        ExposureProfileError,
        profile_verified_csv_bytes,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
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
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
    from profile_efehr_kosovo_exposure import (
        ExposureProfileError,
        profile_verified_csv_bytes,
    )

SOURCE_ISSUE = 282
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"
RECEIPT_COMMENT_ID = 5369154884
RECEIPT_EXECUTION_SHA = "032464963f72a38e01f47b1e5eba6200a9e6d658"
EXPECTED_BYTE_COUNT = 160_627
EXPECTED_SHA256 = "12a20d393c8d677d304263aed96eb05f81098104fd7e3fb0d119aafc336aa00f"
MAX_PROFILE_BYTES = EXPECTED_BYTE_COUNT

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic


class RuntimeResidentialCsvProfileError(RuntimeError):
    """Base fail-closed runtime CSV profile error."""


class ByteIdentityMismatch(RuntimeResidentialCsvProfileError):
    """Fetched provider bytes no longer match the trusted receipt."""


class CsvContentProfileError(RuntimeResidentialCsvProfileError):
    """Exact bytes fail the existing bounded CSV structure profile contract."""


def _fetch_exact_payload(
    *, opener: Any, now: Any, monotonic: Any
) -> tuple[bytes, dict[str, Any]]:
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
        url = raw_file_api_url(target)
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError("trusted runtime residential CSV target is invalid") from exc

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-runtime-csv-profile-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            _declared_length(response, MAX_PROFILE_BYTES)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=MAX_PROFILE_BYTES,
                monotonic=monotonic,
            )
            headers = getattr(response, "headers", {})
            receipt = {
                "retrieved_at": now(),
                "byte_count": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "content_type": headers.get("Content-Type")
                if hasattr(headers, "get")
                else None,
                "etag": headers.get("ETag") if hasattr(headers, "get") else None,
            }
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"runtime residential CSV retrieval failed: {type(exc).__name__}"
        ) from exc
    return raw, receipt


def _verify_receipt_identity(raw: bytes, receipt: dict[str, Any]) -> None:
    if type(raw) is not bytes:
        raise ByteIdentityMismatch("runtime residential CSV payload is not bytes")
    if len(raw) != EXPECTED_BYTE_COUNT:
        raise ByteIdentityMismatch("runtime residential CSV byte count drifted")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ByteIdentityMismatch("runtime residential CSV SHA-256 drifted")
    if receipt.get("byte_count") != EXPECTED_BYTE_COUNT or receipt.get("sha256") != EXPECTED_SHA256:
        raise ByteIdentityMismatch("runtime residential CSV retrieval receipt drifted")


def profile_runtime_residential_csv(
    *,
    opener: Any = _CANONICAL_OPEN_FIXED,
    now: Any = _CANONICAL_UTC_NOW,
    monotonic: Any = _CANONICAL_MONOTONIC,
) -> dict[str, Any]:
    """Fetch, prove exact identity, and profile only bounded CSV structure facts."""

    if opener is _CANONICAL_OPEN_FIXED:
        if _open_fixed is not _CANONICAL_OPEN_FIXED:
            raise RuntimeResidentialCsvProfileError("production transport drifted")
        if now is not _CANONICAL_UTC_NOW or utc_now is not _CANONICAL_UTC_NOW:
            raise RuntimeResidentialCsvProfileError("production UTC clock drifted")
        if monotonic is not _CANONICAL_MONOTONIC or time.monotonic is not _CANONICAL_MONOTONIC:
            raise RuntimeResidentialCsvProfileError("production monotonic clock drifted")

    raw, receipt = _fetch_exact_payload(opener=opener, now=now, monotonic=monotonic)
    _verify_receipt_identity(raw, receipt)
    try:
        profile = profile_verified_csv_bytes(
            raw,
            expected_byte_count=EXPECTED_BYTE_COUNT,
            expected_sha256=EXPECTED_SHA256,
        )
    except ExposureProfileError as exc:
        raise CsvContentProfileError("runtime residential CSV structure profile failed") from exc

    if profile.get("external_bytes_persisted") is not False:
        raise CsvContentProfileError("CSV profile widened persistence authority")
    if profile.get("publication_authorized") is not False:
        raise CsvContentProfileError("CSV profile widened publication authority")
    if profile.get("raw_rows_returned") is not False:
        raise CsvContentProfileError("CSV profile exposed raw rows")

    return {
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "receipt": receipt,
        "profile": profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
