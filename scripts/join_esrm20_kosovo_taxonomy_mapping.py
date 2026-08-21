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
import math
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
OPENQUAKE_WEIGHT_PRECISION = 1e-7
MAX_TAXONOMY_UTF8_BYTES = 1024
MAX_RISK_ID_UTF8_BYTES = 1024
MAX_WEIGHT_CHARS = 128

RIGHTS_PROVIDER = "European Facilities for Earthquake Hazard and Risk (EFEHR)"
RIGHTS_LICENSE_ID = "CC-BY-4.0"
RIGHTS_SOURCE_REVIEWS = (
    "docs/source-reviews/efehr-esrm20-european-exposure-model-v1.0.md",
    "docs/source-reviews/efehr-esrm20-risk-inputs-v1.0.md",
)
RIGHTS_TRANSFORMATION_NOTICE = (
    "Derived exact-key Kosovo taxonomy to ESRM20 risk-id mapping join; "
    "no taxonomy normalization and no provider rows or source bytes republished."
)

# Bind the production path to the exact object already receipted/profiled.
# Keep separate import-time canonical values so paired mutation of the local
# aliases and the upstream profile module cannot silently move the authority.
_FROZEN_MAPPING_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_FROZEN_MAPPING_BYTE_COUNT = 83_585
_FROZEN_MAPPING_SHA256 = "94b9ee800e9435a346ca200ecf34d0d46c8d8b895cc56e3be85c323006b4ee4c"
_FROZEN_MAPPING_PROJECT_ID = 269
_FROZEN_MAPPING_PROJECT_PATH = "efehr/esrm20"
_FROZEN_MAPPING_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_FROZEN_MAPPING_REPOSITORY_PATH = "Vulnerability/esrm20_exposure_vulnerability_mapping.csv"

_MAPPING_DATASET_ID = _FROZEN_MAPPING_DATASET_ID
_MAPPING_BYTE_COUNT = _FROZEN_MAPPING_BYTE_COUNT
_MAPPING_SHA256 = _FROZEN_MAPPING_SHA256
_MAPPING_PROJECT_ID = _FROZEN_MAPPING_PROJECT_ID
_MAPPING_PROJECT_PATH = _FROZEN_MAPPING_PROJECT_PATH
_MAPPING_COMMIT_SHA = _FROZEN_MAPPING_COMMIT_SHA
_MAPPING_REPOSITORY_PATH = _FROZEN_MAPPING_REPOSITORY_PATH


class KosovoMappingJoinError(ValueError):
    """Raised when the exact join cannot be proven without interpretation."""


def _require_frozen_mapping_authority() -> None:
    expected = (
        (
            _MAPPING_DATASET_ID,
            mapping_source.DATASET_ID,
            _FROZEN_MAPPING_DATASET_ID,
            "dataset id",
        ),
        (
            _MAPPING_PROJECT_ID,
            mapping_source.PROJECT_ID,
            _FROZEN_MAPPING_PROJECT_ID,
            "project id",
        ),
        (
            _MAPPING_PROJECT_PATH,
            mapping_source.PROJECT_PATH,
            _FROZEN_MAPPING_PROJECT_PATH,
            "project path",
        ),
        (
            _MAPPING_COMMIT_SHA,
            mapping_source.COMMIT_SHA,
            _FROZEN_MAPPING_COMMIT_SHA,
            "commit",
        ),
        (
            _MAPPING_REPOSITORY_PATH,
            mapping_source.REPOSITORY_PATH,
            _FROZEN_MAPPING_REPOSITORY_PATH,
            "path",
        ),
        (
            _MAPPING_BYTE_COUNT,
            mapping_source.EXPECTED_BYTE_COUNT,
            _FROZEN_MAPPING_BYTE_COUNT,
            "byte count",
        ),
        (
            _MAPPING_SHA256,
            mapping_source.EXPECTED_SHA256,
            _FROZEN_MAPPING_SHA256,
            "SHA-256",
        ),
    )
    for local, upstream, required, label in expected:
        if type(local) is not type(required) or local != required:
            raise KosovoMappingJoinError(f"frozen mapping {label} authority drifted")
        if type(upstream) is not type(required) or upstream != required:
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


def _is_bounded_literal(value: object, *, max_utf8_bytes: int) -> bool:
    if type(value) is not str or not value:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    if len(encoded) > max_utf8_bytes:
        return False
    return not any(ord(character) < 32 or ord(character) == 127 for character in value)


def _weight(value: str) -> float | None:
    """Parse exactly the numeric type OpenQuake 3.14 requests from pandas."""

    if (
        type(value) is not str
        or not value
        or len(value) > MAX_WEIGHT_CHARS
        or value != value.strip()
    ):
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    # This consumer is deliberately stricter than the engine on zero: #410
    # admits only positive finite mapping weights.
    if not math.isfinite(parsed) or parsed <= 0:
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
    if any(
        not _is_bounded_literal(value, max_utf8_bytes=MAX_TAXONOMY_UTF8_BYTES)
        for value in taxonomies
    ):
        raise KosovoMappingJoinError("admitted taxonomy values are not bounded literals")
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
            if len(row) != 3:
                raise KosovoMappingJoinError("verified mapping contains a ragged row")
            taxonomy, conversion, weight = row
            if taxonomy not in admitted:
                continue
            if (
                not _is_bounded_literal(
                    conversion, max_utf8_bytes=MAX_RISK_ID_UTF8_BYTES
                )
                or conversion != conversion.strip()
            ):
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
        # Mirror OpenQuake 3.14 `_taxonomy_mapping`: pandas converts weights to
        # float and compares abs(sum - 1) against pmf.PRECISION == 1e-7.
        weight_error = abs(sum(weights) - 1.0)
        if weight_error > OPENQUAKE_WEIGHT_PRECISION:
            result.append(
                {
                    "taxonomy": taxonomy,
                    "status": "ambiguous",
                    "reason_code": "weights_outside_openquake_precision",
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
            "dataset_id": _MAPPING_DATASET_ID,
            "project_id": _MAPPING_PROJECT_ID,
            "project_path": _MAPPING_PROJECT_PATH,
            "commit_sha": _MAPPING_COMMIT_SHA,
            "repository_path": _MAPPING_REPOSITORY_PATH,
            "byte_count": _MAPPING_BYTE_COUNT,
            "sha256": _MAPPING_SHA256,
            "headers": list(EXPECTED_MAPPING_HEADER),
        },
        "rights": {
            "provider": RIGHTS_PROVIDER,
            "license_id": RIGHTS_LICENSE_ID,
            "attribution_required": True,
            "source_reviews": list(RIGHTS_SOURCE_REVIEWS),
            "transformation_notice": RIGHTS_TRANSFORMATION_NOTICE,
        },
        "classification_counts": counts,
        "records": records,
        "taxonomy_matching": "exact_literal_equality_only",
        "normalization_applied": False,
        "wildcard_or_fallback_matching_applied": False,
        "mapping_weight_rule": "positive_finite_float_sum_within_openquake_1e-7",
        "bounded_derived_disclosure_authorized": True,
        "vulnerability_file_selection_authorized": False,
        "raw_mapping_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
