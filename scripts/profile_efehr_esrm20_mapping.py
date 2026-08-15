# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Verified, interpretation-light content profiler for the frozen ESRM20 mapping CSV.

The worker binds the already-receipted external object by immutable provider
identity, exact byte count, and SHA-256 before decoding or parsing. It does not
interpret mapping semantics, join taxonomy values, return provider rows or exact
cell values, select vulnerability identifiers/files, or authorize publication
or model use.
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

# Production authority comes only from these private canonical bindings. Public
# aliases remain reviewable/backwards-compatible, but a pre-network drift guard
# rejects any rebinding before an opener can receive a request. Pure structural
# parser tests remain parameterized only for the input byte identity.
_CANONICAL_SCHEMA_VERSION = "oc-esrm20-mapping-content-profile-v0"
_CANONICAL_SOURCE_ISSUE = 283
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"
_CANONICAL_RECEIPT_COMMENT_ID = 5303466667
_CANONICAL_RECEIPT_EXECUTION_SHA = "9b1bb7127138247cf613dbf444d139c189c9b13a"
_CANONICAL_EXPECTED_BYTE_COUNT = 83_585
_CANONICAL_EXPECTED_SHA256 = "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
_CANONICAL_DELIMITER_CANDIDATES = (",", ";", "\t")
_CANONICAL_MIN_COLUMNS = 2
_CANONICAL_MAX_COLUMNS = 128
_CANONICAL_MAX_HEADER_UTF8_BYTES = 256

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
RECEIPT_COMMENT_ID = _CANONICAL_RECEIPT_COMMENT_ID
RECEIPT_EXECUTION_SHA = _CANONICAL_RECEIPT_EXECUTION_SHA
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256
DELIMITER_CANDIDATES = _CANONICAL_DELIMITER_CANDIDATES
MIN_COLUMNS = _CANONICAL_MIN_COLUMNS
MAX_COLUMNS = _CANONICAL_MAX_COLUMNS
MAX_HEADER_UTF8_BYTES = _CANONICAL_MAX_HEADER_UTF8_BYTES


class MappingProfileError(RuntimeError):
    """Raised when exact-byte or content-shape profiling fails closed."""


def _require_canonical_authority() -> None:
    """Fail before provider work if any published fixed authority drifts."""

    exact_aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit SHA"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (RECEIPT_COMMENT_ID, _CANONICAL_RECEIPT_COMMENT_ID, "receipt comment id"),
        (
            RECEIPT_EXECUTION_SHA,
            _CANONICAL_RECEIPT_EXECUTION_SHA,
            "receipt execution SHA",
        ),
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "expected byte count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "expected SHA-256"),
        (
            DELIMITER_CANDIDATES,
            _CANONICAL_DELIMITER_CANDIDATES,
            "delimiter candidates",
        ),
        (MIN_COLUMNS, _CANONICAL_MIN_COLUMNS, "minimum column count"),
        (MAX_COLUMNS, _CANONICAL_MAX_COLUMNS, "maximum column count"),
        (
            MAX_HEADER_UTF8_BYTES,
            _CANONICAL_MAX_HEADER_UTF8_BYTES,
            "maximum header byte count",
        ),
    )
    for observed, expected, label in exact_aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise MappingProfileError(f"frozen ESRM20 mapping {label} authority drifted")


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


def _parse_candidate(
    text: str,
    delimiter: str,
) -> tuple[list[str], list[list[str]], int] | None:
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error):
        return None

    if not (_CANONICAL_MIN_COLUMNS <= len(header) <= _CANONICAL_MAX_COLUMNS):
        return None
    if any(name == "" for name in header):
        return None
    if len(set(header)) != len(header):
        return None
    if any(
        len(name.encode("utf-8")) > _CANONICAL_MAX_HEADER_UTF8_BYTES
        for name in header
    ):
        return None
    if any(
        any(ord(character) < 32 or ord(character) == 127 for character in name)
        for name in header
    ):
        return None

    columns: list[list[str]] = [[] for _ in header]
    record_count = 0
    try:
        for row in reader:
            if len(row) != len(header):
                return None
            record_count += 1
            for index, value in enumerate(row):
                columns[index].append(value)
    except csv.Error:
        return None

    if record_count < 1:
        return None
    return header, columns, record_count


def profile_verified_mapping_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify byte identity first, then derive bounded structure-only CSV evidence."""

    if type(raw) is not bytes:
        raise MappingProfileError("mapping input must be immutable bytes")
    if type(expected_byte_count) is not int or isinstance(expected_byte_count, bool):
        raise MappingProfileError("expected byte count must be an integer")
    if expected_byte_count < 1:
        raise MappingProfileError("expected byte count must be positive")
    if type(expected_sha256) is not str or len(expected_sha256) != 64:
        raise MappingProfileError("expected SHA-256 must be 64 lowercase hex characters")
    if any(character not in "0123456789abcdef" for character in expected_sha256):
        raise MappingProfileError("expected SHA-256 must be 64 lowercase hex characters")

    # Receipt identity is the first gate. No decoding or CSV parsing occurs until
    # exact byte count and SHA-256 both match the caller's already trusted receipt.
    if len(raw) != expected_byte_count:
        raise MappingProfileError("mapping byte count does not match trusted receipt")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != expected_sha256:
        raise MappingProfileError("mapping SHA-256 does not match trusted receipt")

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise MappingProfileError("verified mapping object is not valid UTF-8") from exc
    if "\x00" in text:
        raise MappingProfileError("verified mapping object contains NUL characters")

    valid_candidates: list[tuple[str, list[str], list[list[str]], int]] = []
    for delimiter in _CANONICAL_DELIMITER_CANDIDATES:
        parsed = _parse_candidate(text, delimiter)
        if parsed is not None:
            header, columns, record_count = parsed
            valid_candidates.append((delimiter, header, columns, record_count))

    if not valid_candidates:
        raise MappingProfileError(
            "verified mapping CSV has no structurally valid delimiter candidate"
        )
    if len(valid_candidates) != 1:
        raise MappingProfileError("verified mapping CSV delimiter is structurally ambiguous")

    delimiter, header, columns, record_count = valid_candidates[0]
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
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "parser": {
            "encoding": "utf-8-sig" if bom_present else "utf-8",
            "bom_present": bom_present,
            "delimiter": delimiter,
            "delimiter_candidates": list(_CANONICAL_DELIMITER_CANDIDATES),
            "line_endings": _line_ending_profile(raw),
        },
        "record_count": record_count,
        "header": header,
        "columns": column_profiles,
        "raw_rows_returned": False,
        "exact_cell_values_returned": False,
        "normalization_applied": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_and_profile_esrm20_mapping(
    *,
    opener: Any | None = None,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Retrieve only the frozen mapping object, re-verify its receipt, and profile it."""

    _require_canonical_authority()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed
    try:
        target = validate_target(
            source_issue=_CANONICAL_SOURCE_ISSUE,
            dataset_id=_CANONICAL_DATASET_ID,
            project_id=_CANONICAL_PROJECT_ID,
            commit_sha=_CANONICAL_COMMIT_SHA,
            repository_path=_CANONICAL_REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise MappingProfileError("trusted ESRM20 mapping target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-EFEHR-mapping-content-profile-v0",
        },
        method="GET",
    )

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError as exc:
        raise MappingProfileError("ESRM20 mapping retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise MappingProfileError(
            f"ESRM20 mapping retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        profile = profile_verified_mapping_bytes(
            raw,
            expected_byte_count=_CANONICAL_EXPECTED_BYTE_COUNT,
            expected_sha256=_CANONICAL_EXPECTED_SHA256,
        )
    finally:
        raw = b""

    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": _CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_execution_sha": _CANONICAL_RECEIPT_EXECUTION_SHA,
        "byte_count": _CANONICAL_EXPECTED_BYTE_COUNT,
        "sha256": _CANONICAL_EXPECTED_SHA256,
        "profile": profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
