# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Disclose only exact header strings from the frozen ESRM20 v1.0 mapping.

The reviewed #407 value-free profiler remains the byte and complete-CSV
authority. This helper calls it before decoding anything, then re-reads only the
header row and proves that its ordered fingerprint matches the reviewed profile.
No cell value, row, taxonomy join, vulnerability selection, or semantic role is
returned or authorized here.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Callable, Sequence
from typing import Any

try:
    from scripts import profile_efehr_esrm20_mapping_structure as mapping_structure
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_esrm20_mapping_structure as mapping_structure


SCHEMA_VERSION = "oc-esrm20-mapping-header-disclosure-v1"
DECISION_ISSUE = 410
DISCLOSURE_SCOPE = "exact_header_strings_only"

_STRUCTURE_PROFILER = mapping_structure.profile_verified_mapping_bytes
_EXPECTED_STRUCTURE_SCHEMA = "oc-esrm20-mapping-structure-profile-v0"


class MappingHeaderDisclosureError(RuntimeError):
    """Raised when bounded exact-header disclosure cannot be proven safely."""


def _length_prefixed_sha256(values: Sequence[str]) -> str:
    digest = hashlib.sha256()
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _is_lower_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_structure_profile(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise MappingHeaderDisclosureError("mapping structure authority is invalid")

    expected = (
        ("source_issue", mapping_structure.SOURCE_ISSUE),
        ("profile_issue", mapping_structure.PROFILE_ISSUE),
        ("dataset_id", mapping_structure.DATASET_ID),
        ("project_id", mapping_structure.PROJECT_ID),
        ("project_path", mapping_structure.PROJECT_PATH),
        ("commit_sha", mapping_structure.COMMIT_SHA),
        ("repository_path", mapping_structure.REPOSITORY_PATH),
        ("receipt_comment_id", mapping_structure.RECEIPT_COMMENT_ID),
        ("receipt_run_id", mapping_structure.RECEIPT_RUN_ID),
        ("receipt_execution_sha", mapping_structure.RECEIPT_EXECUTION_SHA),
        ("byte_count", mapping_structure.EXPECTED_BYTE_COUNT),
        ("sha256", mapping_structure.EXPECTED_SHA256),
    )
    for field, required in expected:
        observed = result.get(field)
        if type(observed) is not type(required) or observed != required:
            raise MappingHeaderDisclosureError(
                f"mapping structure provenance drifted at {field}"
            )

    for field in (
        "external_bytes_persisted",
        "derived_bytes_persisted",
        "publication_authorized",
        "mapping_interpretation_authorized",
        "vulnerability_selection_authorized",
        "model_use_authorized",
    ):
        if result.get(field) is not False:
            raise MappingHeaderDisclosureError(
                f"mapping structure widened authority at {field}"
            )

    profile = result.get("profile")
    if type(profile) is not dict:
        raise MappingHeaderDisclosureError("mapping structure profile is missing")
    if profile.get("schema_version") != _EXPECTED_STRUCTURE_SCHEMA:
        raise MappingHeaderDisclosureError("mapping structure schema drifted")

    for field in (
        "header_strings_returned",
        "cell_values_returned",
        "raw_rows_returned",
        "normalization_applied",
        "mapping_interpretation_authorized",
        "vulnerability_selection_authorized",
        "external_bytes_persisted",
        "derived_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    ):
        if profile.get(field) is not False:
            raise MappingHeaderDisclosureError(
                f"mapping structure profile widened authority at {field}"
            )

    column_count = profile.get("column_count")
    if (
        type(column_count) is not int
        or isinstance(column_count, bool)
        or column_count < mapping_structure.MIN_COLUMNS
        or column_count > mapping_structure.MAX_COLUMNS
    ):
        raise MappingHeaderDisclosureError("mapping structure column count is invalid")
    if not _is_lower_sha256(profile.get("ordered_header_sha256")):
        raise MappingHeaderDisclosureError(
            "mapping structure ordered-header fingerprint is invalid"
        )

    parser = profile.get("parser")
    if type(parser) is not dict:
        raise MappingHeaderDisclosureError("mapping structure parser metadata is missing")
    if parser.get("encoding") not in {"utf-8", "utf-8-sig"}:
        raise MappingHeaderDisclosureError("mapping structure encoding is invalid")
    delimiter = parser.get("delimiter")
    if delimiter not in mapping_structure.DELIMITER_CANDIDATES:
        raise MappingHeaderDisclosureError("mapping structure delimiter is invalid")
    return profile


def _extract_header(raw: bytes, profile: dict[str, Any]) -> list[str]:
    parser = profile["parser"]
    try:
        text = raw.decode(parser["encoding"])
    except UnicodeDecodeError as exc:
        raise MappingHeaderDisclosureError(
            "verified mapping cannot be decoded for header disclosure"
        ) from exc

    reader = csv.reader(
        io.StringIO(text, newline=""),
        delimiter=parser["delimiter"],
        strict=True,
    )
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise MappingHeaderDisclosureError(
            "verified mapping header cannot be parsed"
        ) from exc

    if len(header) != profile["column_count"]:
        raise MappingHeaderDisclosureError("verified mapping header width drifted")
    if any(value == "" for value in header) or len(set(header)) != len(header):
        raise MappingHeaderDisclosureError("verified mapping header is invalid")
    if any(
        any(ord(character) < 32 or ord(character) == 127 for character in value)
        for value in header
    ):
        raise MappingHeaderDisclosureError(
            "verified mapping header contains control characters"
        )
    if _length_prefixed_sha256(header) != profile["ordered_header_sha256"]:
        raise MappingHeaderDisclosureError(
            "verified mapping ordered-header fingerprint drifted"
        )
    return header


def _disclose_headers(
    raw: bytes,
    *,
    structure_profiler: Callable[[bytes], dict[str, Any]],
) -> dict[str, Any]:
    if type(raw) is not bytes:
        raise MappingHeaderDisclosureError("mapping input must be bytes")

    # This call is deliberately first: production therefore inherits #407's
    # exact byte-count/SHA check and complete CSV validation before this module
    # decodes or exposes a single literal.
    try:
        structure = structure_profiler(raw)
    except Exception as exc:
        raise MappingHeaderDisclosureError(
            "mapping structure authority rejected input"
        ) from exc

    profile = _require_structure_profile(structure)
    headers = _extract_header(raw, profile)

    return {
        "schema_version": SCHEMA_VERSION,
        "decision_issue": DECISION_ISSUE,
        "source_issue": structure["source_issue"],
        "profile_issue": structure["profile_issue"],
        "dataset_id": structure["dataset_id"],
        "project_id": structure["project_id"],
        "project_path": structure["project_path"],
        "commit_sha": structure["commit_sha"],
        "repository_path": structure["repository_path"],
        "receipt_comment_id": structure["receipt_comment_id"],
        "receipt_run_id": structure["receipt_run_id"],
        "receipt_execution_sha": structure["receipt_execution_sha"],
        "byte_count": structure["byte_count"],
        "sha256": structure["sha256"],
        "column_count": profile["column_count"],
        "ordered_header_sha256": profile["ordered_header_sha256"],
        "headers": headers,
        "disclosure_scope": DISCLOSURE_SCOPE,
        "header_strings_returned": True,
        "cell_values_returned": False,
        "raw_rows_returned": False,
        "normalization_applied": False,
        "mapping_interpretation_authorized": False,
        "taxonomy_join_authorized": False,
        "vulnerability_selection_authorized": False,
        "external_bytes_persisted": False,
        "derived_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def disclose_verified_mapping_headers(raw: bytes) -> dict[str, Any]:
    """Disclose only headers from the exact mapping identity already frozen by #340."""

    if mapping_structure.profile_verified_mapping_bytes is not _STRUCTURE_PROFILER:
        raise MappingHeaderDisclosureError(
            "mapping structure profiler identity drifted"
        )
    return _disclose_headers(raw, structure_profiler=_STRUCTURE_PROFILER)
