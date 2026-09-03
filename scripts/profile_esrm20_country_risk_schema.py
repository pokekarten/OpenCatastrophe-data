# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile bounded country-risk CSV structure without exposing result values.

This module is deliberately offline-only. It binds supplied bytes to an
expected SHA-256 and byte count before interpreting the CSV, then emits only
content-derived structural evidence. The expected identity is caller-supplied,
so this pure profiler does *not* assert that the bytes came from a particular
provider/project/commit/path. That provenance must be bound separately to a
trusted acquisition receipt before durable source-specific claims are made.

Numeric provider result values are never returned or interpreted.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from typing import Any

SCHEMA_VERSION = "oc-esrm20-country-risk-schema-profile-v1"

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_ROWS = 512
MAX_COLUMNS = 128
MAX_CELL_UTF8_BYTES = 8 * 1024

NAME_HEADER = "Name"
KOSOVO_NAME_LITERALS = (
    "Kosova",
    "Kosovo",
    "Republic of Kosovo",
)
SECONDARY_HYPOTHESIS_HEADERS = (
    "AAL Residential (economic, M EUR)",
    "AAL Total (economic, M EUR)",
    "AALR Residential (economic, per mille)",
    "AALR Total (economic, per mille)",
)
RESIDENTIAL_AAL_HEADER = "AAL Residential (economic, M EUR)"
RESIDENTIAL_AALR_HEADER = "AALR Residential (economic, per mille)"

_DELIMITERS = ((",", "comma"), (";", "semicolon"), ("\t", "tab"))
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CountryRiskSchemaProfileError(RuntimeError):
    """Raised when bounded country-risk schema evidence cannot be proven safely."""


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str:
        raise CountryRiskSchemaProfileError(f"{field} is not text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CountryRiskSchemaProfileError(f"{field} is not UTF-8 encodable") from exc
    if len(encoded) > MAX_CELL_UTF8_BYTES:
        raise CountryRiskSchemaProfileError(f"{field} exceeds bounded policy")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise CountryRiskSchemaProfileError(f"{field} contains forbidden control characters")
    return value


def _validate_expected_identity(
    expected_sha256: object,
    expected_byte_count: object,
) -> tuple[str, int]:
    if type(expected_sha256) is not str or _SHA256_RE.fullmatch(expected_sha256) is None:
        raise CountryRiskSchemaProfileError("expected SHA-256 is invalid")
    if type(expected_byte_count) is not int or isinstance(expected_byte_count, bool):
        raise CountryRiskSchemaProfileError("expected byte count is invalid")
    if not (1 <= expected_byte_count <= MAX_FILE_BYTES):
        raise CountryRiskSchemaProfileError("expected byte count is outside bounded policy")
    return expected_sha256, expected_byte_count


def _decode_csv(payload: bytes) -> str:
    if type(payload) is not bytes or not (1 <= len(payload) <= MAX_FILE_BYTES):
        raise CountryRiskSchemaProfileError("country-risk byte size is outside bounded policy")
    if b"\x00" in payload:
        raise CountryRiskSchemaProfileError("country-risk CSV contains NUL bytes")
    try:
        text = payload.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise CountryRiskSchemaProfileError("country-risk CSV must be UTF-8") from exc
    if "\r" in text.replace("\r\n", ""):
        raise CountryRiskSchemaProfileError("country-risk CSV contains bare carriage returns")
    return text


def _parse_with_delimiter(text: str, delimiter: str) -> tuple[list[str], list[list[str]]]:
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise CountryRiskSchemaProfileError("country-risk CSV parse failed") from exc
    if not rows:
        raise CountryRiskSchemaProfileError("country-risk CSV is empty")
    if len(rows) > MAX_ROWS + 1:
        raise CountryRiskSchemaProfileError("country-risk row count exceeds bounded policy")

    width = len(rows[0])
    if not (2 <= width <= MAX_COLUMNS):
        raise CountryRiskSchemaProfileError("country-risk column count is outside bounded policy")
    if any(len(row) != width for row in rows):
        raise CountryRiskSchemaProfileError("country-risk CSV contains ragged rows")

    header = [_bounded_text(value, field="country-risk header") for value in rows[0]]
    if any(not value or value != value.strip() for value in header):
        raise CountryRiskSchemaProfileError("country-risk headers must be non-empty and trimmed")
    folded = [value.casefold() for value in header]
    if len(set(folded)) != len(folded):
        raise CountryRiskSchemaProfileError("country-risk headers are not unique")

    data_rows = rows[1:]
    if not data_rows:
        raise CountryRiskSchemaProfileError("country-risk CSV contains no data rows")
    for row in data_rows:
        for value in row:
            _bounded_text(value, field="country-risk cell")
    return header, data_rows


def _parse_csv(text: str) -> tuple[str, list[str], list[list[str]]]:
    candidates: list[tuple[str, list[str], list[list[str]]]] = []
    for delimiter, name in _DELIMITERS:
        try:
            header, rows = _parse_with_delimiter(text, delimiter)
        except CountryRiskSchemaProfileError:
            continue
        candidates.append((name, header, rows))
    if len(candidates) != 1:
        raise CountryRiskSchemaProfileError(
            "country-risk delimiter is ambiguous or outside the closed delimiter set"
        )
    return candidates[0]


def _header_sha256(header: list[str]) -> str:
    encoded = json.dumps(
        header,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _kosovo_identity(header: list[str], rows: list[list[str]]) -> dict[str, Any]:
    if NAME_HEADER not in header:
        return {
            "name_column_present": False,
            "kosovo_row_count": 0,
            "kosovo_name_literals": [],
            "kosovo_row_status": "name_column_absent",
        }

    index = header.index(NAME_HEADER)
    literals = [row[index] for row in rows if row[index] in KOSOVO_NAME_LITERALS]
    distinct = sorted(set(literals))
    count = len(literals)
    if count == 0:
        status = "absent"
    elif count == 1:
        status = "unique"
    else:
        status = "ambiguous"
    return {
        "name_column_present": True,
        "kosovo_row_count": count,
        "kosovo_name_literals": distinct,
        "kosovo_row_status": status,
    }


def profile_country_risk_schema_bytes(
    payload: bytes,
    *,
    expected_sha256: str,
    expected_byte_count: int,
) -> dict[str, Any]:
    """Return value-redacted structural evidence for byte-identity-bound content.

    The returned hash/count prove only which bytes were profiled. Source
    provenance is intentionally left unverified here because the expected
    identity is supplied by the caller rather than derived from a trusted
    acquisition receipt.
    """
    expected_sha256, expected_byte_count = _validate_expected_identity(
        expected_sha256,
        expected_byte_count,
    )
    if type(payload) is not bytes:
        raise CountryRiskSchemaProfileError("country-risk payload is not bytes")
    if len(payload) != expected_byte_count:
        raise CountryRiskSchemaProfileError("country-risk byte count does not match expected identity")
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise CountryRiskSchemaProfileError("country-risk SHA-256 does not match expected identity")

    text = _decode_csv(payload)
    delimiter, header, rows = _parse_csv(text)
    identity = _kosovo_identity(header, rows)
    field_presence = {
        field: field in header for field in SECONDARY_HYPOTHESIS_HEADERS
    }
    unique_kosovo = identity["kosovo_row_status"] == "unique"
    residential_aal_candidate = (
        unique_kosovo and field_presence[RESIDENTIAL_AAL_HEADER]
    )
    residential_aalr_candidate = (
        unique_kosovo and field_presence[RESIDENTIAL_AALR_HEADER]
    )
    residential_candidate = residential_aal_candidate or residential_aalr_candidate

    return {
        "schema_version": SCHEMA_VERSION,
        "byte_count": len(payload),
        "sha256": actual_sha256,
        "trusted_source_receipt_bound": False,
        "encoding": "utf-8",
        "delimiter": delimiter,
        "column_count": len(header),
        "row_count": len(rows),
        "headers": header,
        "header_sha256": _header_sha256(header),
        **identity,
        "secondary_hypothesis_field_presence": field_presence,
        "residential_aal_schema_candidate": residential_aal_candidate,
        "residential_aalr_schema_candidate": residential_aalr_candidate,
        "residential_reference_schema_candidate": residential_candidate,
        "provider_numeric_values_interpreted": False,
        "provider_values_returned": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "annualized_metrics_authorized": False,
        "threshold_compatibility_verified": False,
        "denominator_semantics_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
