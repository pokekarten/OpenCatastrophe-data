# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile only the structure of the frozen ESRM20 exposure-vulnerability mapping.

Issue #340 already established the immutable byte identity of the ESRM20 v1.0
exposure-to-vulnerability mapping. This worker may re-materialize only that
fixed provider object, verifies its exact byte count and SHA-256 before any
text or CSV work, and returns bounded structural metadata. It deliberately
does not interpret mapping semantics, join exposure taxonomies, select
vulnerability identifiers/files, or persist provider rows.
"""

from __future__ import annotations

import csv
import hashlib
import io
import time
import urllib.error
import urllib.request
from typing import Any

try:
    from scripts import acquire_efehr_esrm20_mapping_receipt as mapping_receipt
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
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_mapping_receipt as mapping_receipt
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
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )

# Freeze every durable identity. Public aliases below remain reviewable, while
# production acquisition and durable output use only the private bindings.
_CANONICAL_SCHEMA_VERSION = "oc-esrm20-exposure-vulnerability-mapping-structure-v1"
_CANONICAL_OPERATION_ID = "esrm20-exposure-vulnerability-mapping-structure-v1"
_CANONICAL_PROFILE_ISSUE = 283
_CANONICAL_RECEIPT_CONTROL_ISSUE = 340
_CANONICAL_RECEIPT_RESULT_COMMENT_ID = 5303466667
_CANONICAL_RECEIPT_RUN_ID = 31899242278
_CANONICAL_PARSER_IDENTITY = (
    "scripts.profile_efehr_esrm20_mapping_structure."
    "profile_verified_esrm20_mapping_structure"
)
_CANONICAL_SOURCE_ISSUE = mapping_receipt.SOURCE_ISSUE
_CANONICAL_DATASET_ID = mapping_receipt.DATASET_ID
_CANONICAL_PROJECT_ID = mapping_receipt.PROJECT_ID
_CANONICAL_COMMIT_SHA = mapping_receipt.COMMIT_SHA
_CANONICAL_REPOSITORY_PATH = mapping_receipt.REPOSITORY_PATH
_CANONICAL_EXPECTED_BYTE_COUNT = 83_585
_CANONICAL_EXPECTED_SHA256 = (
    "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
)

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
OPERATION_ID = _CANONICAL_OPERATION_ID
PROFILE_ISSUE = _CANONICAL_PROFILE_ISSUE
RECEIPT_CONTROL_ISSUE = _CANONICAL_RECEIPT_CONTROL_ISSUE
RECEIPT_RESULT_COMMENT_ID = _CANONICAL_RECEIPT_RESULT_COMMENT_ID
RECEIPT_RUN_ID = _CANONICAL_RECEIPT_RUN_ID
PARSER_IDENTITY = _CANONICAL_PARSER_IDENTITY

_DELIMITER_CANDIDATES = (
    ("comma", ","),
    ("semicolon", ";"),
    ("tab", "\t"),
    ("pipe", "|"),
)


class Esrm20MappingStructureError(RuntimeError):
    """Raised when fixed mapping bytes cannot be profiled unambiguously."""


def _require_canonical_aliases() -> None:
    """Fail before provider work if a published fixed identity has drifted."""

    exact_aliases = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (OPERATION_ID, _CANONICAL_OPERATION_ID, "operation id"),
        (PROFILE_ISSUE, _CANONICAL_PROFILE_ISSUE, "profile issue"),
        (
            RECEIPT_CONTROL_ISSUE,
            _CANONICAL_RECEIPT_CONTROL_ISSUE,
            "receipt control issue",
        ),
        (
            RECEIPT_RESULT_COMMENT_ID,
            _CANONICAL_RECEIPT_RESULT_COMMENT_ID,
            "receipt result comment id",
        ),
        (RECEIPT_RUN_ID, _CANONICAL_RECEIPT_RUN_ID, "receipt run id"),
        (PARSER_IDENTITY, _CANONICAL_PARSER_IDENTITY, "parser identity"),
    )
    for observed, expected, label in exact_aliases:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20MappingStructureError(
                f"frozen ESRM20 mapping structure {label} drifted"
            )


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise Esrm20MappingStructureError("mapping payload must be immutable bytes")
    if len(payload) != _CANONICAL_EXPECTED_BYTE_COUNT:
        raise Esrm20MappingStructureError(
            "mapping byte count does not match the trusted #340 receipt"
        )
    observed = hashlib.sha256(payload).hexdigest()
    if observed != _CANONICAL_EXPECTED_SHA256:
        raise Esrm20MappingStructureError(
            "mapping SHA-256 does not match the trusted #340 receipt"
        )
    return observed


def _newline_style(payload: bytes) -> str:
    """Return one exact physical newline style; mixed styles fail closed."""

    crlf = b"\r\n" in payload
    remainder = payload.replace(b"\r\n", b"")
    lf = b"\n" in remainder
    cr = b"\r" in remainder
    styles = [
        name
        for name, present in (("crlf", crlf), ("lf", lf), ("cr", cr))
        if present
    ]
    if len(styles) != 1:
        raise Esrm20MappingStructureError(
            "mapping must use exactly one physical newline style"
        )
    return styles[0]


def _parse_header(line: str, delimiter: str) -> list[str]:
    try:
        rows = list(
            csv.reader(
                [line],
                delimiter=delimiter,
                quotechar='"',
                doublequote=True,
                strict=True,
            )
        )
    except csv.Error as exc:
        raise Esrm20MappingStructureError("mapping header CSV syntax is invalid") from exc
    if len(rows) != 1:
        raise Esrm20MappingStructureError("mapping header shape is invalid")
    return rows[0]


def _detect_delimiter(text: str) -> tuple[str, str]:
    physical_lines = text.splitlines()
    if not physical_lines or physical_lines[0] == "":
        raise Esrm20MappingStructureError("mapping header is missing")

    candidates: list[tuple[str, str]] = []
    for name, delimiter in _DELIMITER_CANDIDATES:
        header = _parse_header(physical_lines[0], delimiter)
        if len(header) > 1:
            candidates.append((name, delimiter))
    if len(candidates) != 1:
        raise Esrm20MappingStructureError(
            "mapping delimiter is absent or structurally ambiguous"
        )
    return candidates[0]


def _require_safe_cell(value: object, *, header: bool) -> str:
    if type(value) is not str:
        raise Esrm20MappingStructureError("mapping CSV parser returned non-text data")
    if header and value == "":
        raise Esrm20MappingStructureError("mapping header contains an empty field")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Esrm20MappingStructureError("mapping contains control characters")
    if len(value.encode("utf-8")) > _CANONICAL_EXPECTED_BYTE_COUNT:
        raise Esrm20MappingStructureError("mapping cell exceeds the source byte bound")
    return value


def _header_fingerprint(header: list[str]) -> str:
    digest = hashlib.sha256()
    for value in header:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _parse_rows(text: str, delimiter: str) -> tuple[list[str], int]:
    try:
        reader = csv.reader(
            io.StringIO(text, newline=""),
            delimiter=delimiter,
            quotechar='"',
            doublequote=True,
            strict=True,
        )
        rows = list(reader)
    except csv.Error as exc:
        raise Esrm20MappingStructureError("mapping CSV syntax is invalid") from exc

    if len(rows) < 2:
        raise Esrm20MappingStructureError("mapping must contain a header and records")
    if any(not row for row in rows):
        raise Esrm20MappingStructureError("mapping contains a blank record")

    header = [_require_safe_cell(value, header=True) for value in rows[0]]
    if len(header) < 2:
        raise Esrm20MappingStructureError("mapping header has fewer than two columns")
    if len(set(header)) != len(header):
        raise Esrm20MappingStructureError("mapping contains duplicate header fields")

    width = len(header)
    records: set[tuple[str, ...]] = set()
    for row in rows[1:]:
        if len(row) != width:
            raise Esrm20MappingStructureError("mapping contains a ragged record")
        record = tuple(_require_safe_cell(value, header=False) for value in row)
        if record in records:
            raise Esrm20MappingStructureError("mapping contains a duplicate record")
        records.add(record)

    return header, len(records)


def profile_verified_esrm20_mapping_structure(payload: bytes) -> dict[str, Any]:
    """Verify exact mapping bytes, then derive structure without mapping semantics."""

    observed_sha256 = _verify_payload_identity(payload)
    newline_style = _newline_style(payload)
    utf8_bom = payload.startswith(b"\xef\xbb\xbf")
    try:
        text = payload.decode("utf-8-sig" if utf8_bom else "utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Esrm20MappingStructureError("mapping is not strict UTF-8") from exc

    delimiter_name, delimiter = _detect_delimiter(text)
    header, record_count = _parse_rows(text, delimiter)

    return {
        "schema_version": _CANONICAL_SCHEMA_VERSION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "profile_issue": _CANONICAL_PROFILE_ISSUE,
        "receipt_control_issue": _CANONICAL_RECEIPT_CONTROL_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "project_id": _CANONICAL_PROJECT_ID,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "receipt_result_comment_id": _CANONICAL_RECEIPT_RESULT_COMMENT_ID,
        "receipt_run_id": _CANONICAL_RECEIPT_RUN_ID,
        "source_byte_count": len(payload),
        "source_sha256": observed_sha256,
        "parser_identity": _CANONICAL_PARSER_IDENTITY,
        "encoding": "utf-8",
        "utf8_bom": utf8_bom,
        "newline_style": newline_style,
        "delimiter": delimiter_name,
        "header": header,
        "header_count": len(header),
        "header_sha256": _header_fingerprint(header),
        "record_count": record_count,
        "duplicate_headers": False,
        "duplicate_records": False,
        "ragged_rows": False,
        "normalization_applied": False,
        "mapping_semantics_interpreted": False,
        "taxonomy_join_performed": False,
        "vulnerability_ids_selected": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_verified_esrm20_mapping_structure(
    *,
    opener: Any | None = None,
    now: Any = utc_now,
    monotonic: Any = time.monotonic,
) -> dict[str, Any]:
    """Re-materialize only the frozen mapping object and profile it in memory."""

    _require_canonical_aliases()
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
        raise Esrm20MappingStructureError("trusted mapping target is invalid") from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "text/csv,text/plain;q=0.9",
            "User-Agent": "OpenCatastrophe-ESRM20-mapping-structure-v1",
        },
        method="GET",
    )

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, _CANONICAL_EXPECTED_BYTE_COUNT)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
            retrieved_at = now()
    except EfehrAcquisitionError as exc:
        raise Esrm20MappingStructureError("mapping retrieval failed closed") from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Esrm20MappingStructureError(
            f"mapping retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        profile = profile_verified_esrm20_mapping_structure(raw)
    finally:
        raw = b""

    return {
        "operation_id": _CANONICAL_OPERATION_ID,
        "retrieved_at": retrieved_at,
        **profile,
    }
