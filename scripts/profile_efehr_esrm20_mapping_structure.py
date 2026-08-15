# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Value-free structural profiling for the frozen ESRM20 mapping CSV.

The public profiler accepts immutable bytes only. It verifies the exact trusted
mapping receipt identity before UTF-8 decode or CSV parsing, then derives only
bounded structure and collision-safe fingerprints. Header strings, cell values,
raw rows, mapping semantics and vulnerability selections are deliberately not
returned.
"""

from __future__ import annotations

import csv
import hashlib
import io
from typing import Any


_CANONICAL_SCHEMA_VERSION = "oc-esrm20-mapping-structure-profile-v0"
_CANONICAL_SOURCE_ISSUE = 283
_CANONICAL_CONTROL_ISSUE = 404
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"
_CANONICAL_RECEIPT_COMMENT_ID = 5303466667
_CANONICAL_RECEIPT_EXECUTION_SHA = "9b1bb7127138247cf613dbf444d139c189c9b13a"
_CANONICAL_RECEIPT_RUN_ID = 31899242278
_CANONICAL_EXPECTED_BYTE_COUNT = 83_585
_CANONICAL_EXPECTED_SHA256 = "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"

# Public aliases are review/test surfaces only. Durable profile identity below
# is emitted from the private canonical bindings after an exact drift guard.
SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
CONTROL_ISSUE = _CANONICAL_CONTROL_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
RECEIPT_COMMENT_ID = _CANONICAL_RECEIPT_COMMENT_ID
RECEIPT_EXECUTION_SHA = _CANONICAL_RECEIPT_EXECUTION_SHA
RECEIPT_RUN_ID = _CANONICAL_RECEIPT_RUN_ID
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256

DELIMITER_CANDIDATES = (",", ";", "\t", "|")
MIN_COLUMNS = 2
MAX_COLUMNS = 256
MAX_HEADER_UTF8_BYTES = 2_048
MAX_TOTAL_HEADER_UTF8_BYTES = 16_384
MAX_RECORDS = 100_000


class MappingStructureProfileError(RuntimeError):
    """Raised when exact-byte or mapping-shape profiling fails closed."""


def _require_canonical_aliases() -> None:
    aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (CONTROL_ISSUE, _CANONICAL_CONTROL_ISSUE, "control issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (RECEIPT_COMMENT_ID, _CANONICAL_RECEIPT_COMMENT_ID, "receipt comment id"),
        (RECEIPT_EXECUTION_SHA, _CANONICAL_RECEIPT_EXECUTION_SHA, "receipt execution SHA"),
        (RECEIPT_RUN_ID, _CANONICAL_RECEIPT_RUN_ID, "receipt run id"),
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "expected byte count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "expected SHA-256"),
    )
    for observed, expected, label in aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise MappingStructureProfileError(f"frozen ESRM20 mapping {label} drifted")


def _sequence_sha256(values: list[str]) -> str:
    digest = hashlib.sha256()
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _value_set_sha256(values: set[str]) -> str:
    return _sequence_sha256(sorted(values))


def _line_ending_profile(raw: bytes) -> dict[str, int]:
    crlf = raw.count(b"\r\n")
    without_crlf = raw.replace(b"\r\n", b"")
    return {
        "crlf_count": crlf,
        "lf_count": without_crlf.count(b"\n"),
        "cr_count": without_crlf.count(b"\r"),
    }


def _contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _parse_candidate(text: str, delimiter: str) -> tuple[list[str], list[list[str]]] | None:
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error):
        return None
    if not (MIN_COLUMNS <= len(header) <= MAX_COLUMNS):
        return None

    rows: list[list[str]] = []
    try:
        for row in reader:
            if len(row) != len(header):
                return None
            rows.append(row)
            if len(rows) > MAX_RECORDS:
                return None
    except csv.Error:
        return None
    if not rows:
        return None
    return header, rows


def _select_unique_parse(text: str) -> tuple[str, list[str], list[list[str]]]:
    candidates: list[tuple[str, list[str], list[list[str]]]] = []
    for delimiter in DELIMITER_CANDIDATES:
        parsed = _parse_candidate(text, delimiter)
        if parsed is not None:
            header, rows = parsed
            candidates.append((delimiter, header, rows))
    if len(candidates) != 1:
        raise MappingStructureProfileError(
            "verified mapping CSV does not have exactly one bounded structural delimiter parse"
        )
    return candidates[0]


def profile_verified_mapping_bytes(raw: bytes) -> dict[str, Any]:
    """Verify the trusted mapping bytes, then derive value-free structure evidence."""

    _require_canonical_aliases()
    if type(raw) is not bytes:
        raise MappingStructureProfileError("mapping input must be immutable bytes")

    # Byte identity is the first content gate. No decode or CSV parser is reached
    # until both trusted receipt facts match exactly.
    if len(raw) != _CANONICAL_EXPECTED_BYTE_COUNT:
        raise MappingStructureProfileError("mapping byte count does not match trusted receipt")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != _CANONICAL_EXPECTED_SHA256:
        raise MappingStructureProfileError("mapping SHA-256 does not match trusted receipt")

    bom_present = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig" if bom_present else "utf-8")
    except UnicodeDecodeError as exc:
        raise MappingStructureProfileError("verified mapping object is not valid UTF-8") from exc
    if "\x00" in text:
        raise MappingStructureProfileError("verified mapping object contains NUL characters")

    delimiter, header, rows = _select_unique_parse(text)

    if any(name == "" for name in header):
        raise MappingStructureProfileError("verified mapping CSV contains an empty header")
    if len(set(header)) != len(header):
        raise MappingStructureProfileError("verified mapping CSV contains duplicate headers")
    if any(len(name.encode("utf-8")) > MAX_HEADER_UTF8_BYTES for name in header):
        raise MappingStructureProfileError("verified mapping CSV header exceeds bounded policy")
    header_utf8_bytes = sum(len(name.encode("utf-8")) for name in header)
    if header_utf8_bytes > MAX_TOTAL_HEADER_UTF8_BYTES:
        raise MappingStructureProfileError("verified mapping CSV total header bytes exceed bounded policy")
    if any(_contains_control(name) for name in header):
        raise MappingStructureProfileError("verified mapping CSV header contains control characters")

    seen_rows: set[tuple[str, ...]] = set()
    columns: list[list[str]] = [[] for _ in header]
    for row in rows:
        if all(value == "" for value in row):
            raise MappingStructureProfileError("verified mapping CSV contains a blank record")
        row_key = tuple(row)
        if row_key in seen_rows:
            raise MappingStructureProfileError("verified mapping CSV contains a duplicate exact record")
        seen_rows.add(row_key)
        for index, value in enumerate(row):
            if _contains_control(value):
                raise MappingStructureProfileError("verified mapping CSV contains control-bearing cell text")
            columns[index].append(value)

    column_profiles: list[dict[str, Any]] = []
    for index, values in enumerate(columns):
        distinct = set(values)
        empty_count = sum(value == "" for value in values)
        whitespace_count = sum(
            value != "" and value != value.strip()
            for value in values
        )
        column_profiles.append(
            {
                "index": index,
                "record_count": len(rows),
                "empty_count": empty_count,
                "nonempty_count": len(rows) - empty_count,
                "distinct_count": len(distinct),
                "exact_value_set_sha256": _value_set_sha256(distinct),
                "leading_or_trailing_whitespace_count": whitespace_count,
            }
        )

    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "control_issue": _CANONICAL_CONTROL_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": _CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_execution_sha": _CANONICAL_RECEIPT_EXECUTION_SHA,
        "receipt_run_id": _CANONICAL_RECEIPT_RUN_ID,
        "byte_count": _CANONICAL_EXPECTED_BYTE_COUNT,
        "sha256": _CANONICAL_EXPECTED_SHA256,
        "parser": {
            "encoding": "utf-8-sig" if bom_present else "utf-8",
            "bom_present": bom_present,
            "delimiter": delimiter,
            "line_endings": _line_ending_profile(raw),
        },
        "column_count": len(header),
        "record_count": len(rows),
        "header_utf8_byte_count": header_utf8_bytes,
        "ordered_header_sha256": _sequence_sha256(header),
        "columns": column_profiles,
        "header_values_returned": False,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "external_bytes_persisted": False,
        "derived_artifact_persisted": False,
        "publication_authorized": False,
        "mapping_interpretation_authorized": False,
        "vulnerability_selection_authorized": False,
    }
