# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed exact-key join for the frozen Kosovo taxonomy and ESRM20 mapping.

This module implements only the minimum consumer contract approved by Issue
#410. It verifies both upstream byte identities before interpretation, performs
literal taxonomy equality only, and emits a bounded derived result for the 86
already-admitted Kosovo taxonomy values. It does not normalize taxonomy text,
interpret wildcard-like syntax, select vulnerability files, persist provider
bytes, or authorize publication/model use.
"""

from __future__ import annotations

import csv
import hashlib
import io
from decimal import Decimal, InvalidOperation
from typing import Any

try:
    from scripts import extract_efehr_kosovo_taxonomy as taxonomy_source
    from scripts import profile_efehr_esrm20_mapping_structure as mapping_source
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import extract_efehr_kosovo_taxonomy as taxonomy_source
    import profile_efehr_esrm20_mapping_structure as mapping_source

SCHEMA_VERSION = "oc-esrm20-kosovo-taxonomy-mapping-join-v1"
SOURCE_ISSUE = 283
DECISION_ISSUE = 410
EXPECTED_MAPPING_HEADER = ("taxonomy", "conversion", "weight")

# Bind the production path to the exact object already receipted/profiled.
_MAPPING_BYTE_COUNT = 83_585
_MAPPING_SHA256 = "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
_MAPPING_PROJECT_ID = 269
_MAPPING_PROJECT_PATH = "efehr/esrm20"
_MAPPING_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_MAPPING_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"


class KosovoMappingJoinError(ValueError):
    """Raised when the exact join cannot be proven without interpretation."""


def _require_frozen_mapping_authority() -> None:
    expected = (
        (mapping_source.PROJECT_ID, _MAPPING_PROJECT_ID, "project id"),
        (mapping_source.PROJECT_PATH, _MAPPING_PROJECT_PATH, "project path"),
        (mapping_source.COMMIT_SHA, _MAPPING_COMMIT_SHA, "commit"),
        (mapping_source.REPOSITORY_PATH, _MAPPING_REPOSITORY_PATH, "path"),
        (mapping_source.EXPECTED_BYTE_COUNT, _MAPPING_BYTE_COUNT, "byte count"),
        (mapping_source.EXPECTED_SHA256, _MAPPING_SHA256, "SHA-256"),
    )
    for observed, required, label in expected:
        if type(observed) is not type(required) or observed != required:
            raise KosovoMappingJoinError(f"frozen mapping {label} authority drifted")


def _verify_mapping_bytes(
    raw: bytes, *, expected_byte_count: int, expected_sha256: str
) -> str:
    if type(raw) is not bytes:
        raise KosovoMappingJoinError("mapping input must be immutable bytes")
    if len(raw) != expected_byte_count:
        raise KosovoMappingJoinError("mapping byte count does not match trusted receipt")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise KosovoMappingJoinError("mapping SHA-256 does not match trusted receipt")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise KosovoMappingJoinError("trusted mapping unexpectedly contains a UTF-8 BOM")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoMappingJoinError("verified mapping is not strict UTF-8") from exc


def _weight(value: str) -> Decimal | None:
    if type(value) is not str or not value or value != value.strip():
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    return parsed


def _join_exact_taxonomies(
    taxonomies: list[str],
    mapping_raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> list[dict[str, Any]]:
    if type(taxonomies) is not list or not taxonomies:
        raise KosovoMappingJoinError("admitted taxonomy set must be a non-empty list")
    if any(type(value) is not str or not value for value in taxonomies):
        raise KosovoMappingJoinError("admitted taxonomy values must be non-empty strings")
    if taxonomies != sorted(taxonomies) or len(set(taxonomies)) != len(taxonomies):
        raise KosovoMappingJoinError("admitted taxonomy set must be sorted and unique")

    text = _verify_mapping_bytes(
        mapping_raw,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )
    admitted = set(taxonomies)
    matches: dict[str, list[tuple[str, str]]] = {taxonomy: [] for taxonomy in taxonomies}
    structurally_ambiguous: set[str] = set()

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise KosovoMappingJoinError("verified mapping CSV has no header") from exc
    except csv.Error as exc:
        raise KosovoMappingJoinError("verified mapping CSV header is malformed") from exc
    if tuple(header) != EXPECTED_MAPPING_HEADER:
        raise KosovoMappingJoinError("verified mapping header is not taxonomy/conversion/weight")

    try:
        for row in reader:
            # The frozen object is governed as a three-column CSV. A ragged row
            # makes the object unsafe to consume because row boundaries would be
            # ambiguous, even if the row is unrelated to Kosovo.
            if len(row) != 3:
                raise KosovoMappingJoinError("verified mapping contains a ragged row")
            taxonomy, conversion, weight = row
            if taxonomy not in admitted:
                continue
            if not conversion or conversion != conversion.strip():
                structurally_ambiguous.add(taxonomy)
                continue
            if _weight(weight) is None:
                structurally_ambiguous.add(taxonomy)
                continue
            matches[taxonomy].append((conversion, weight))
    except csv.Error as exc:
        raise KosovoMappingJoinError("verified mapping CSV is malformed") from exc

    result: list[dict[str, Any]] = []
    for taxonomy in taxonomies:
        rows = matches[taxonomy]
        if taxonomy in structurally_ambiguous:
            result.append(
                {
                    "taxonomy": taxonomy,
                    "status": "ambiguous",
                    "reason_code": "matched_row_not_canonical",
                    "targets": [],
                }
            )
            continue
        if not rows:
            result.append(
                {
                    "taxonomy": taxonomy,
                    "status": "unsupported",
                    "reason_code": "no_exact_mapping_row",
                    "targets": [],
                }
            )
            continue

        conversions = [conversion for conversion, _ in rows]
        if len(set(conversions)) != len(conversions):
            result.append(
                {
                    "taxonomy": taxonomy,
                    "status": "ambiguous",
                    "reason_code": "duplicate_risk_id_semantics",
                    "targets": [],
                }
            )
            continue

        weights = [_weight(weight) for _, weight in rows]
        if any(weight is None for weight in weights):  # defensive; checked above
            raise KosovoMappingJoinError("weight validation became inconsistent")
        if sum(weights, Decimal(0)) != Decimal(1):
            result.append(
                {
                    "taxonomy": taxonomy,
                    "status": "ambiguous",
                    "reason_code": "weights_do_not_sum_to_one",
                    "targets": [],
                }
            )
            continue

        targets = sorted(
            (
                {"risk_id": conversion, "weight": weight}
                for conversion, weight in rows
            ),
            key=lambda item: item["risk_id"],
        )
        result.append(
            {
                "taxonomy": taxonomy,
                "status": "resolved",
                "reason_code": "exact_mapping_rows_valid",
                "targets": targets,
            }
        )
    return result


def join_verified_kosovo_taxonomy_mapping(
    exposure_raw: bytes, mapping_raw: bytes
) -> dict[str, Any]:
    """Verify both frozen objects and return the bounded exact-key join."""

    _require_frozen_mapping_authority()
    try:
        taxonomy = taxonomy_source.extract_verified_kosovo_taxonomy(exposure_raw)
    except taxonomy_source.KosovoTaxonomyError as exc:
        raise KosovoMappingJoinError("Kosovo taxonomy source gate did not pass") from exc

    taxonomies = taxonomy.get("taxonomies")
    if type(taxonomies) is not list or len(taxonomies) != taxonomy_source.EXPECTED_DISTINCT_COUNT:
        raise KosovoMappingJoinError("taxonomy source returned an invalid admitted set")
    if taxonomy.get("normalization_applied") is not False:
        raise KosovoMappingJoinError("taxonomy source unexpectedly normalized values")

    records = _join_exact_taxonomies(
        taxonomies,
        mapping_raw,
        expected_byte_count=_MAPPING_BYTE_COUNT,
        expected_sha256=_MAPPING_SHA256,
    )
    counts = {status: 0 for status in ("resolved", "unsupported", "ambiguous")}
    for record in records:
        counts[record["status"]] += 1
    if sum(counts.values()) != taxonomy_source.EXPECTED_DISTINCT_COUNT:
        raise KosovoMappingJoinError("join classification is not exhaustive")

    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "semantic_decision_issue": DECISION_ISSUE,
        "taxonomy_source": {
            "dataset_id": taxonomy["dataset_id"],
            "project_id": taxonomy["project_id"],
            "project_path": taxonomy["project_path"],
            "commit_sha": taxonomy["commit_sha"],
            "repository_path": taxonomy["repository_path"],
            "byte_count": taxonomy["byte_count"],
            "sha256": taxonomy["sha256"],
            "taxonomy_count": taxonomy["taxonomy_count"],
            "taxonomy_value_set_sha256": taxonomy["taxonomy_value_set_sha256"],
        },
        "mapping_source": {
            "dataset_id": mapping_source.DATASET_ID,
            "project_id": _MAPPING_PROJECT_ID,
            "project_path": _MAPPING_PROJECT_PATH,
            "commit_sha": _MAPPING_COMMIT_SHA,
            "repository_path": _MAPPING_REPOSITORY_PATH,
            "byte_count": _MAPPING_BYTE_COUNT,
            "sha256": _MAPPING_SHA256,
            "headers": list(EXPECTED_MAPPING_HEADER),
        },
        "classification_counts": counts,
        "records": records,
        "taxonomy_matching": "exact_literal_equality_only",
        "normalization_applied": False,
        "wildcard_or_fallback_matching_applied": False,
        "mapping_weight_rule": "positive_finite_decimal_sum_exactly_one",
        "vulnerability_file_selection_authorized": False,
        "raw_mapping_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
