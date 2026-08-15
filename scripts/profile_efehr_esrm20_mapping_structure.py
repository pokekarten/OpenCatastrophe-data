# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Value-free structural profiler for the exact ESRM20 v1.0 mapping bytes.

This module is deliberately interpretation-light. It verifies the already trusted
mapping byte identity before decoding or CSV parsing and returns only structural
counts and collision-safe fingerprints. Header strings, cell values, and raw rows
never appear in the durable profile.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Sequence
from typing import Any

_CANONICAL_SCHEMA_VERSION = "oc-esrm20-mapping-structure-profile-v0"
_CANONICAL_SOURCE_ISSUE = 283
_CANONICAL_PROFILE_ISSUE = 404
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"
_CANONICAL_RECEIPT_COMMENT_ID = 5303466667
_CANONICAL_RECEIPT_RUN_ID = 31899242278
_CANONICAL_RECEIPT_EXECUTION_SHA = "9b1bb7127138247cf613dbf444d139c189c9b13a"
_CANONICAL_EXPECTED_BYTE_COUNT = 83_585
_CANONICAL_EXPECTED_SHA256 = (
    "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
)
_CANONICAL_DELIMITER_CANDIDATES = (",", ";", "\t", "|")
_CANONICAL_MIN_COLUMNS = 2
_CANONICAL_MAX_COLUMNS = 256
_CANONICAL_MAX_HEADER_UTF8_BYTES = 512
_CANONICAL_MAX_TOTAL_HEADER_UTF8_BYTES = 16_384
_CANONICAL_MAX_CELL_UTF8_BYTES = 65_536
_CANONICAL_MAX_RECORDS = 100_000

# Public aliases are review/test surfaces only. Durable output, byte identity,
# and parser bounds remain bound to the private canonical values below.
SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
PROFILE_ISSUE = _CANONICAL_PROFILE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
RECEIPT_COMMENT_ID = _CANONICAL_RECEIPT_COMMENT_ID
RECEIPT_RUN_ID = _CANONICAL_RECEIPT_RUN_ID
RECEIPT_EXECUTION_SHA = _CANONICAL_RECEIPT_EXECUTION_SHA
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256
DELIMITER_CANDIDATES = _CANONICAL_DELIMITER_CANDIDATES
MIN_COLUMNS = _CANONICAL_MIN_COLUMNS
MAX_COLUMNS = _CANONICAL_MAX_COLUMNS
MAX_HEADER_UTF8_BYTES = _CANONICAL_MAX_HEADER_UTF8_BYTES
MAX_TOTAL_HEADER_UTF8_BYTES = _CANONICAL_MAX_TOTAL_HEADER_UTF8_BYTES
MAX_CELL_UTF8_BYTES = _CANONICAL_MAX_CELL_UTF8_BYTES
MAX_RECORDS = _CANONICAL_MAX_RECORDS


class MappingStructureProfileError(RuntimeError):
    """Raised when byte identity or value-free structure validation fails closed."""


def _require_canonical_aliases() -> None:
    aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (PROFILE_ISSUE, _CANONICAL_PROFILE_ISSUE, "profile issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (RECEIPT_COMMENT_ID, _CANONICAL_RECEIPT_COMMENT_ID, "receipt comment id"),
        (RECEIPT_RUN_ID, _CANONICAL_RECEIPT_RUN_ID, "receipt run id"),
        (
            RECEIPT_EXECUTION_SHA,
            _CANONICAL_RECEIPT_EXECUTION_SHA,
            "receipt execution SHA",
        ),
        (
            EXPECTED_BYTE_COUNT,
            _CANONICAL_EXPECTED_BYTE_COUNT,
            "expected byte count",
        ),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "expected SHA-256"),
        (
            DELIMITER_CANDIDATES,
            _CANONICAL_DELIMITER_CANDIDATES,
            "delimiter candidates",
        ),
        (MIN_COLUMNS, _CANONICAL_MIN_COLUMNS, "minimum columns"),
        (MAX_COLUMNS, _CANONICAL_MAX_COLUMNS, "maximum columns"),
        (
            MAX_HEADER_UTF8_BYTES,
            _CANONICAL_MAX_HEADER_UTF8_BYTES,
            "maximum header bytes",
        ),
        (
            MAX_TOTAL_HEADER_UTF8_BYTES,
            _CANONICAL_MAX_TOTAL_HEADER_UTF8_BYTES,
            "maximum total header bytes",
        ),
        (
            MAX_CELL_UTF8_BYTES,
            _CANONICAL_MAX_CELL_UTF8_BYTES,
            "maximum cell bytes",
        ),
        (MAX_RECORDS, _CANONICAL_MAX_RECORDS, "maximum records"),
    )
    for observed, expected, label in aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise MappingStructureProfileError(f"frozen ESRM20 mapping {label} drifted")


def _validate_expected_identity(expected_byte_count: int, expected_sha256: str) -> None:
    if type(expected_byte_count) is not int or isinstance(expected_byte_count, bool):
        raise MappingStructureProfileError("expected byte count must be an integer")
    if expected_byte_count < 1:
        raise MappingStructureProfileError("expected byte count must be positive")
    if type(expected_sha256) is not str or len(expected_sha256) != 64:
        raise MappingStructureProfileError(
            "expected SHA-256 must be 64 lowercase hex characters"
        )
    if any(character not in "0123456789abcdef" for character in expected_sha256):
        raise MappingStructureProfileError(
            "expected SHA-256 must be 64 lowercase hex characters"
        )


def _length_prefixed_sha256(values: Sequence[str]) -> str:
    """Hash one ordered string sequence using an unambiguous binary framing."""

    digest = hashlib.sha256()
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _line_ending_profile(raw: bytes) -> dict[str, int]:
    crlf_count = raw.count(b"\r\n")
    remaining = raw.replace(b"\r\n", b"")
    return {
        "crlf_count": crlf_count,
        "lf_count": remaining.count(b"\n"),
        "cr_count": remaining.count(b"\r"),
    }


def _parse_candidate(text: str, delimiter: str) -> tuple[list[str], list[list[str]]]:
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise MappingStructureProfileError("verified mapping CSV has no header") from exc
    except csv.Error as exc:
        raise MappingStructureProfileError("verified mapping CSV is malformed") from exc

    if not (_CANONICAL_MIN_COLUMNS <= len(header) <= _CANONICAL_MAX_COLUMNS):
        raise MappingStructureProfileError("candidate is not a bounded multi-column CSV")

    rows: list[list[str]] = []
    try:
        for row in reader:
            if len(row) != len(header):
                raise MappingStructureProfileError("candidate contains a ragged row")
            rows.append(row)
            if len(rows) > _CANONICAL_MAX_RECORDS:
                raise MappingStructureProfileError("candidate record count exceeds bounded policy")
    except csv.Error as exc:
        raise MappingStructureProfileError("candidate CSV is malformed") from exc

    if not rows:
        raise MappingStructureProfileError("candidate contains no data records")
    return header, rows


def _select_unique_delimiter(text: str) -> tuple[str, list[str], list[list[str]]]:
    valid: list[tuple[str, list[str], list[list[str]]]] = []
    for delimiter in _CANONICAL_DELIMITER_CANDIDATES:
        try:
            header, rows = _parse_candidate(text, delimiter)
        except MappingStructureProfileError:
            continue
        valid.append((delimiter, header, rows))

    if len(valid) != 1:
        raise MappingStructureProfileError(
            "verified mapping CSV does not have exactly one valid delimiter"
        )
    return valid[0]


def _validate_header(header: list[str]) -> int:
    if any(name == "" for name in header):
        raise MappingStructureProfileError("verified mapping CSV contains an empty header")
    if len(set(header)) != len(header):
        raise MappingStructureProfileError("verified mapping CSV contains duplicate headers")
    if any(
        len(name.encode("utf-8")) > _CANONICAL_MAX_HEADER_UTF8_BYTES
        for name in header
    ):
        raise MappingStructureProfileError("verified mapping CSV header exceeds bounded policy")
    total_utf8_bytes = sum(len(name.encode("utf-8")) for name in header)
    if total_utf8_bytes > _CANONICAL_MAX_TOTAL_HEADER_UTF8_BYTES:
        raise MappingStructureProfileError(
            "verified mapping CSV total header bytes exceed bounded policy"
        )
    if any(_contains_control(name) for name in header):
        raise MappingStructureProfileError(
            "verified mapping CSV header contains control characters"
        )
    return total_utf8_bytes


def _validate_rows(rows: list[list[str]]) -> None:
    seen_rows: set[tuple[str, ...]] = set()
    for row in rows:
        # Blank means every exact field is the empty string. Whitespace-only text
        # is intentionally not normalized into blank data.
        if all(value == "" for value in row):
            raise MappingStructureProfileError("verified mapping CSV contains a blank record")

        row_key = tuple(row)
        if row_key in seen_rows:
            raise MappingStructureProfileError("verified mapping CSV contains duplicate rows")
        seen_rows.add(row_key)

        for value in row:
            if len(value.encode("utf-8")) > _CANONICAL_MAX_CELL_UTF8_BYTES:
                raise MappingStructureProfileError("verified mapping CSV cell exceeds bounded policy")
            if _contains_control(value):
                raise MappingStructureProfileError(
                    "verified mapping CSV contains control-bearing cells"
                )


def _profile_verified_csv_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Verify an exact byte identity first, then derive value-free CSV structure."""

    if type(raw) is not bytes:
        raise MappingStructureProfileError("mapping input must be bytes")
    _validate_expected_identity(expected_byte_count, expected_sha256)

    # Identity is the first content gate. No decoding, delimiter detection, or CSV
    # parsing occurs before both exact byte count and SHA-256 have matched.
    if len(raw) != expected_byte_count:
        raise MappingStructureProfileError("mapping byte count does not match trusted receipt")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise MappingStructureProfileError("mapping SHA-256 does not match trusted receipt")

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8")
    except UnicodeDecodeError as exc:
        raise MappingStructureProfileError("verified mapping object is not valid UTF-8") from exc
    if "\x00" in text:
        raise MappingStructureProfileError("verified mapping object contains NUL characters")

    delimiter, header, rows = _select_unique_delimiter(text)
    header_utf8_byte_count = _validate_header(header)
    _validate_rows(rows)

    record_count = len(rows)
    column_profiles: list[dict[str, Any]] = []
    for index in range(len(header)):
        values = [row[index] for row in rows]
        distinct = set(values)
        empty_count = sum(value == "" for value in values)
        column_profiles.append(
            {
                "index": index,
                "empty_count": empty_count,
                "nonempty_count": record_count - empty_count,
                "distinct_count": len(distinct),
                "exact_value_set_sha256": _length_prefixed_sha256(sorted(distinct)),
                "leading_or_trailing_whitespace_count": sum(
                    value != value.strip() for value in values if value != ""
                ),
            }
        )

    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "parser": {
            "encoding": "utf-8-sig" if bom_present else "utf-8",
            "bom_present": bom_present,
            "delimiter": delimiter,
            "line_endings": _line_ending_profile(raw),
        },
        "column_count": len(header),
        "record_count": record_count,
        "ordered_header_sha256": _length_prefixed_sha256(header),
        "header_utf8_byte_count": header_utf8_byte_count,
        "columns": column_profiles,
        "header_strings_returned": False,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "mapping_interpretation_authorized": False,
        "vulnerability_selection_authorized": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_verified_mapping_bytes(raw: bytes) -> dict[str, Any]:
    """Profile only the exact trusted ESRM20 v1.0 mapping object."""

    _require_canonical_aliases()
    profile = _profile_verified_csv_bytes(
        raw,
        expected_byte_count=_CANONICAL_EXPECTED_BYTE_COUNT,
        expected_sha256=_CANONICAL_EXPECTED_SHA256,
    )
    return {
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "profile_issue": _CANONICAL_PROFILE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": _CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_run_id": _CANONICAL_RECEIPT_RUN_ID,
        "receipt_execution_sha": _CANONICAL_RECEIPT_EXECUTION_SHA,
        "byte_count": _CANONICAL_EXPECTED_BYTE_COUNT,
        "sha256": _CANONICAL_EXPECTED_SHA256,
        "profile": profile,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }
