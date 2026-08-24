# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verified, interpretation-light content profiler for the frozen Kosovo exposure CSV.

The worker binds the already-receipted external object by immutable provider
identity, byte count, and SHA-256 before decoding or parsing. It deliberately
does not guess which column is taxonomy, does not emit raw rows or exact field
values, and does not authorize publication or model use.
"""

from __future__ import annotations

import csv
import hashlib
import http.client
import io
import time
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )

SCHEMA_VERSION = "oc-esrm20-exposure-content-profile-v0"
SOURCE_ISSUE = 282
DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
PROJECT_ID = 186
PROJECT_PATH = "efehr/esrm20_exposure"
COMMIT_SHA = "900433ada80fbb424c0976c34d72eeef97bab1af"
REPOSITORY_PATH = "_exposure_models/Exposure_Model_Kosovo_Res.csv"
RECEIPT_COMMENT_ID = 5300981864
RECEIPT_EXECUTION_SHA = "46d054930025553ad19d8b05fff9018dc2a49b5f"
EXPECTED_BYTE_COUNT = 316_789
EXPECTED_SHA256 = "4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea"
DELIMITER = ","
MIN_COLUMNS = 2
MAX_COLUMNS = 128
MAX_HEADER_UTF8_BYTES = 256


class ExposureProfileError(RuntimeError):
    """Raised when exact-byte or content-shape profiling fails closed."""


def _value_set_sha256(values: set[str]) -> str:
    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _decimal_summary(values: list[str]) -> dict[str, Any]:
    nonempty = [value for value in values if value != ""]
    whitespace_count = sum(value != value.strip() for value in nonempty)
    finite_decimal_count = 0
    for value in nonempty:
        if value != value.strip():
            continue
        try:
            number = Decimal(value)
        except InvalidOperation:
            continue
        if number.is_finite():
            finite_decimal_count += 1
    return {
        "all_nonempty_decimal": bool(nonempty)
        and finite_decimal_count == len(nonempty),
        "finite_decimal_count": finite_decimal_count,
        "leading_or_trailing_whitespace_count": whitespace_count,
    }


def _line_ending_profile(raw: bytes) -> dict[str, int]:
    crlf = raw.count(b"\r\n")
    without_crlf = raw.replace(b"\r\n", b"")
    return {
        "crlf_count": crlf,
        "lf_count": without_crlf.count(b"\n"),
        "cr_count": without_crlf.count(b"\r"),
    }


def profile_verified_csv_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify byte identity first, then derive bounded structure-only CSV evidence."""

    if type(raw) is not bytes:
        raise ExposureProfileError("exposure input must be bytes")
    if type(expected_byte_count) is not int or isinstance(expected_byte_count, bool):
        raise ExposureProfileError("expected byte count must be an integer")
    if expected_byte_count < 1:
        raise ExposureProfileError("expected byte count must be positive")
    if type(expected_sha256) is not str or len(expected_sha256) != 64:
        raise ExposureProfileError("expected SHA-256 must be 64 lowercase hex characters")
    if any(character not in "0123456789abcdef" for character in expected_sha256):
        raise ExposureProfileError("expected SHA-256 must be 64 lowercase hex characters")

    # The receipt identity is the first gate. No decoding or parsing occurs before
    # both exact byte count and SHA-256 have matched.
    if len(raw) != expected_byte_count:
        raise ExposureProfileError("exposure byte count does not match trusted receipt")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != expected_sha256:
        raise ExposureProfileError("exposure SHA-256 does not match trusted receipt")

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8")
    except UnicodeDecodeError as exc:
        raise ExposureProfileError("verified exposure object is not valid UTF-8") from exc
    if "\x00" in text:
        raise ExposureProfileError("verified exposure object contains NUL characters")

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=DELIMITER, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ExposureProfileError("verified exposure CSV has no header") from exc
    except csv.Error as exc:
        raise ExposureProfileError("verified exposure CSV header is malformed") from exc

    if not (MIN_COLUMNS <= len(header) <= MAX_COLUMNS):
        raise ExposureProfileError("verified exposure CSV column count is outside bounded policy")
    if any(name == "" for name in header):
        raise ExposureProfileError("verified exposure CSV contains an empty header")
    if len(set(header)) != len(header):
        raise ExposureProfileError("verified exposure CSV contains duplicate headers")
    if any(len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES for name in header):
        raise ExposureProfileError("verified exposure CSV header exceeds bounded policy")
    if any(any(ord(character) < 32 or ord(character) == 127 for character in name) for name in header):
        raise ExposureProfileError("verified exposure CSV header contains control characters")

    columns: list[list[str]] = [[] for _ in header]
    record_count = 0
    try:
        for row in reader:
            if len(row) != len(header):
                raise ExposureProfileError("verified exposure CSV contains a ragged row")
            record_count += 1
            for index, value in enumerate(row):
                columns[index].append(value)
    except csv.Error as exc:
        raise ExposureProfileError("verified exposure CSV is malformed") from exc

    if record_count < 1:
        raise ExposureProfileError("verified exposure CSV contains no data records")

    column_profiles: list[dict[str, Any]] = []
    for name, values in zip(header, columns):
        distinct = set(values)
        empty_count = sum(value == "" for value in values)
        column_profiles.append(
            {
                "name": name,
                "record_count": record_count,
                "empty_count": empty_count,
                "nonempty_count": record_count - empty_count,
                "distinct_count": len(distinct),
                "exact_value_set_sha256": _value_set_sha256(distinct),
                "decimal_summary": _decimal_summary(values),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "parser": {
            "encoding": "utf-8-sig" if bom_present else "utf-8",
            "bom_present": bom_present,
            "delimiter": DELIMITER,
            "line_endings": _line_ending_profile(raw),
        },
        "record_count": record_count,
        "header": header,
        "columns": column_profiles,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def acquire_and_profile_kosovo_exposure(
    *,
    opener: Any | None = None,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Retrieve only the frozen object, verify the public receipt, and profile it."""

    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise ExposureProfileError("trusted Kosovo exposure target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-content-profile-v0",
        },
        method="GET",
    )

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except ExposureProfileError:
        raise
    except EfehrAcquisitionError as exc:
        raise ExposureProfileError("Kosovo exposure retrieval failed closed") from exc
    except (
        OSError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        http.client.HTTPException,
        TimeoutError,
    ) as exc:
        raise ExposureProfileError(
            f"Kosovo exposure retrieval failed: {type(exc).__name__}"
        ) from exc

    profile = profile_verified_csv_bytes(
        raw,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )
    return {
        "schema_version": profile["schema_version"],
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
        "profile": profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
