# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verified, interpretation-light profiler for the frozen ESHM20 site-model CSV.

The worker binds the already-receipted external object by immutable provider
identity, exact byte count, and SHA-256 before decoding or CSV parsing. It
returns only bounded structural evidence and deliberately does not infer
coordinate, CRS, Vs30, amplification, geographic-applicability, or model-use
semantics from field names or values.
"""

from __future__ import annotations

import csv
import hashlib
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

SCHEMA_VERSION = "oc-eshm20-site-model-content-profile-v0"
CONTROL_ISSUE = 361
SOURCE_ISSUE = 281
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
REPOSITORY_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "eshm20_site_model_v06d.csv"
)
PARENT_RESULT_COMMENT_ID = 5301726249
PARENT_SECTION = "site_params"
PARENT_OPTION = "site_model_file"
RECEIPT_REQUEST_COMMENT_ID = 5301857400
RECEIPT_RESULT_COMMENT_ID = 5301858821
RECEIPT_RUN_ID = 31880089623
RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"
EXPECTED_BYTE_COUNT = 3_873_324
EXPECTED_SHA256 = "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529"
DELIMITER = ","
MIN_COLUMNS = 2
MAX_COLUMNS = 128
MAX_HEADER_UTF8_BYTES = 256


class Eshm20SiteModelProfileError(RuntimeError):
    """Raised when exact-byte or structural site-model profiling fails closed."""


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


def profile_verified_site_model_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify the exact receipt identity first, then derive structure-only evidence."""

    if type(raw) is not bytes:
        raise Eshm20SiteModelProfileError("site-model input must be bytes")
    if type(expected_byte_count) is not int:
        raise Eshm20SiteModelProfileError("expected byte count must be an integer")
    if expected_byte_count < 1:
        raise Eshm20SiteModelProfileError("expected byte count must be positive")
    if type(expected_sha256) is not str or len(expected_sha256) != 64:
        raise Eshm20SiteModelProfileError(
            "expected SHA-256 must be 64 lowercase hex characters"
        )
    if any(character not in "0123456789abcdef" for character in expected_sha256):
        raise Eshm20SiteModelProfileError(
            "expected SHA-256 must be 64 lowercase hex characters"
        )

    # The trusted #361 receipt is the first gate. No text decoding, CSV parsing,
    # or field-level observation occurs before both exact identity checks pass.
    if len(raw) != expected_byte_count:
        raise Eshm20SiteModelProfileError(
            "site-model byte count does not match trusted receipt"
        )
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != expected_sha256:
        raise Eshm20SiteModelProfileError(
            "site-model SHA-256 does not match trusted receipt"
        )

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8")
    except UnicodeDecodeError as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model object is not valid UTF-8"
        ) from exc
    if "\x00" in text:
        raise Eshm20SiteModelProfileError(
            "verified site-model object contains NUL characters"
        )

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=DELIMITER, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV has no header"
        ) from exc
    except csv.Error as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV header is malformed"
        ) from exc

    if not (MIN_COLUMNS <= len(header) <= MAX_COLUMNS):
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV column count is outside bounded policy"
        )
    if any(name == "" for name in header):
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV contains an empty header"
        )
    if len(set(header)) != len(header):
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV contains duplicate headers"
        )
    if any(len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES for name in header):
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV header exceeds bounded policy"
        )
    if any(
        any(ord(character) < 32 or ord(character) == 127 for character in name)
        for name in header
    ):
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV header contains control characters"
        )

    columns: list[list[str]] = [[] for _ in header]
    record_count = 0
    try:
        for row in reader:
            if len(row) != len(header):
                raise Eshm20SiteModelProfileError(
                    "verified site-model CSV contains a ragged row"
                )
            record_count += 1
            for index, value in enumerate(row):
                columns[index].append(value)
    except csv.Error as exc:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV is malformed"
        ) from exc

    if record_count < 1:
        raise Eshm20SiteModelProfileError(
            "verified site-model CSV contains no data records"
        )

    column_profiles: list[dict[str, Any]] = []
    for name, values in zip(header, columns, strict=True):
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
        "site_semantics_authorized": False,
        "model_use_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def acquire_and_profile_eshm20_site_model(
    *,
    opener: Any | None = None,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Retrieve only the frozen site object, verify #361 bytes, and profile it."""

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
        raise Eshm20SiteModelProfileError(
            "trusted ESHM20 site-model target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.5",
            "User-Agent": "OpenCatastrophe-ESHM20-site-model-profile-v0",
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
    except Eshm20SiteModelProfileError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20SiteModelProfileError(
            "ESHM20 site-model retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20SiteModelProfileError(
            f"ESHM20 site-model retrieval failed: {type(exc).__name__}"
        ) from exc

    profile = profile_verified_site_model_bytes(
        raw,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )
    return {
        "schema_version": profile["schema_version"],
        "control_issue": CONTROL_ISSUE,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "parent_result_comment_id": PARENT_RESULT_COMMENT_ID,
        "parent_section": PARENT_SECTION,
        "parent_option": PARENT_OPTION,
        "receipt_request_comment_id": RECEIPT_REQUEST_COMMENT_ID,
        "receipt_result_comment_id": RECEIPT_RESULT_COMMENT_ID,
        "receipt_run_id": RECEIPT_RUN_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "profile": profile,
        "site_semantics_authorized": False,
        "model_use_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
