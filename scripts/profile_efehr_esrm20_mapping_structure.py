# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Value-free structural profiler for the exact ESRM20 v1.0 mapping bytes.

This module is deliberately offline and interpretation-light. It verifies the
trusted mapping byte identity before decoding or CSV parsing, then returns only
bounded structural counts and collision-safe fingerprints. It never returns
header strings, cell values, rows, mapping semantics, or model selections.
"""

from __future__ import annotations

import csv
import hashlib
import io
import unicodedata
from typing import Any, Iterable

SCHEMA_VERSION = "oc-esrm20-mapping-structure-profile-v0"
SCIENCE_ISSUE = 283
CONTROL_ISSUE = 340
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"
RECEIPT_RESULT_COMMENT_ID = 5_303_466_667
RECEIPT_RUN_ID = 31_899_242_278
RECEIPT_EXECUTION_SHA = "9b1bb7127138247cf613dbf444d139c189c9b13a"
EXPECTED_BYTE_COUNT = 83_585
EXPECTED_SHA256 = "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"

DELIMITER_CANDIDATES = (",", ";", "\t", "|")
MIN_COLUMNS = 2
MAX_COLUMNS = 128
MAX_HEADER_UTF8_BYTES = 256


class MappingStructureProfileError(RuntimeError):
    """Raised when exact-byte identity or value-free CSV profiling fails closed."""


class _NotDelimiterCandidate(MappingStructureProfileError):
    """Internal marker for a candidate that cannot represent a multi-column CSV."""


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


def _length_prefixed_sha256(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _exact_value_set_sha256(values: set[str]) -> str:
    return _length_prefixed_sha256(sorted(values))


def _contains_control(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def _line_ending_profile(raw: bytes) -> dict[str, int]:
    crlf_count = raw.count(b"\r\n")
    without_crlf = raw.replace(b"\r\n", b"")
    return {
        "crlf_count": crlf_count,
        "lf_count": without_crlf.count(b"\n"),
        "cr_count": without_crlf.count(b"\r"),
    }


def _parse_candidate(text: str, delimiter: str) -> tuple[list[str], list[tuple[str, ...]]]:
    reader = csv.reader(
        io.StringIO(text, newline=""),
        delimiter=delimiter,
        strict=True,
    )
    try:
        header = next(reader)
    except StopIteration as exc:
        raise MappingStructureProfileError("mapping CSV has no header") from exc
    except csv.Error as exc:
        raise MappingStructureProfileError("mapping CSV header is malformed") from exc

    if len(header) < MIN_COLUMNS:
        raise _NotDelimiterCandidate("delimiter does not produce a multi-column table")
    if len(header) > MAX_COLUMNS:
        raise MappingStructureProfileError("mapping CSV column count exceeds bounded policy")
    if any(name == "" for name in header):
        raise MappingStructureProfileError("mapping CSV contains an empty header")
    if len(set(header)) != len(header):
        raise MappingStructureProfileError("mapping CSV contains duplicate headers")
    if any(len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES for name in header):
        raise MappingStructureProfileError("mapping CSV contains an oversized header")
    if any(_contains_control(name) for name in header):
        raise MappingStructureProfileError("mapping CSV header contains control characters")

    rows: list[tuple[str, ...]] = []
    seen_rows: set[tuple[str, ...]] = set()
    try:
        for parsed in reader:
            if not parsed or all(value == "" for value in parsed):
                raise MappingStructureProfileError("mapping CSV contains a blank row")
            if len(parsed) != len(header):
                raise MappingStructureProfileError("mapping CSV contains a ragged row")
            if any(_contains_control(value) for value in parsed):
                raise MappingStructureProfileError(
                    "mapping CSV contains a control-bearing cell"
                )
            row = tuple(parsed)
            if row in seen_rows:
                raise MappingStructureProfileError("mapping CSV contains a duplicate exact row")
            seen_rows.add(row)
            rows.append(row)
    except csv.Error as exc:
        raise MappingStructureProfileError("mapping CSV is malformed") from exc

    if not rows:
        raise MappingStructureProfileError("mapping CSV contains no data records")
    return header, rows


def _select_unique_delimiter(text: str) -> tuple[str, list[str], list[tuple[str, ...]]]:
    valid: list[tuple[str, list[str], list[tuple[str, ...]]]] = []
    plausible_errors: list[MappingStructureProfileError] = []
    for delimiter in DELIMITER_CANDIDATES:
        try:
            header, rows = _parse_candidate(text, delimiter)
        except _NotDelimiterCandidate:
            continue
        except MappingStructureProfileError as exc:
            plausible_errors.append(exc)
            continue
        valid.append((delimiter, header, rows))

    if len(valid) == 1 and not plausible_errors:
        return valid[0]
    if len(valid) > 1 or (valid and plausible_errors):
        raise MappingStructureProfileError(
            "mapping CSV delimiter is structurally ambiguous"
        )
    if len(plausible_errors) == 1:
        raise plausible_errors[0]
    if plausible_errors:
        raise MappingStructureProfileError(
            "mapping CSV has multiple invalid multi-column interpretations"
        )
    raise MappingStructureProfileError(
        "mapping CSV has no structurally valid delimiter candidate"
    )


def profile_verified_mapping_bytes(
    raw: bytes,
    *,
    expected_byte_count: int = EXPECTED_BYTE_COUNT,
    expected_sha256: str = EXPECTED_SHA256,
) -> dict[str, Any]:
    """Verify immutable bytes first, then derive value-free mapping structure evidence."""

    if type(raw) is not bytes:
        raise MappingStructureProfileError("mapping input must be bytes")
    _validate_expected_identity(expected_byte_count, expected_sha256)

    # Trusted receipt identity is the first gate. No decoding or parser work may
    # occur until both the exact byte count and SHA-256 match.
    if len(raw) != expected_byte_count:
        raise MappingStructureProfileError(
            "mapping byte count does not match trusted receipt"
        )
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != expected_sha256:
        raise MappingStructureProfileError("mapping SHA-256 does not match trusted receipt")

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8")
    except UnicodeDecodeError as exc:
        raise MappingStructureProfileError(
            "verified mapping object is not valid UTF-8"
        ) from exc
    if "\x00" in text:
        raise MappingStructureProfileError("verified mapping object contains NUL characters")

    delimiter, header, rows = _select_unique_delimiter(text)
    column_count = len(header)
    record_count = len(rows)

    columns: list[dict[str, Any]] = []
    for index in range(column_count):
        values = [row[index] for row in rows]
        distinct_values = set(values)
        empty_count = sum(value == "" for value in values)
        columns.append(
            {
                "index": index,
                "empty_count": empty_count,
                "nonempty_count": record_count - empty_count,
                "distinct_count": len(distinct_values),
                "exact_value_set_sha256": _exact_value_set_sha256(distinct_values),
                "leading_or_trailing_whitespace_count": sum(
                    value != value.strip() for value in values
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "source_identity": {
            "science_issue": SCIENCE_ISSUE,
            "control_issue": CONTROL_ISSUE,
            "dataset_id": DATASET_ID,
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
            "receipt_result_comment_id": RECEIPT_RESULT_COMMENT_ID,
            "receipt_run_id": RECEIPT_RUN_ID,
            "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
            "byte_count": expected_byte_count,
            "sha256": expected_sha256,
        },
        "parser": {
            "encoding": "utf-8-sig" if bom_present else "utf-8",
            "bom_present": bom_present,
            "delimiter": delimiter,
            "line_endings": _line_ending_profile(raw),
        },
        "column_count": column_count,
        "record_count": record_count,
        "ordered_header_sha256": _length_prefixed_sha256(header),
        "header_utf8_byte_count": sum(len(name.encode("utf-8")) for name in header),
        "columns": columns,
        "header_strings_returned": False,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "vulnerability_selection_authorized": False,
        "model_use_authorized": False,
    }
