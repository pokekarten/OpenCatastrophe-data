# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extract the exact ESRM20 Kosovo taxonomy set from receipt-bound CSV bytes.

This module deliberately does not acquire provider data and does not normalize
source taxonomy strings. The public worker accepts only the already-receipted
Kosovo residential object: exact byte count and SHA-256 are checked before any
decode or CSV parse. The emitted values are the literal source TAXONOMY cells,
sorted only to make the derived set deterministic.
"""

from __future__ import annotations

import csv
import hashlib
import io
from typing import Any

try:
    from scripts import profile_efehr_kosovo_exposure as exposure
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_kosovo_exposure as exposure

SCHEMA_VERSION = "oc-esrm20-kosovo-taxonomy-set-v1"
TAXONOMY_FIELD = "TAXONOMY"
EXPECTED_DISTINCT_COUNT = 86
EXPECTED_VALUE_SET_SHA256 = "d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945"
EXPECTED_HEADER = (
    "LONGITUDE",
    "LATITUDE",
    "TAXONOMY",
    "MACRO_TAXONOMY",
    "BUILDINGS",
    "DWELLINGS",
    "OCCUPANCY",
    "OCCUPANCY_TYPE",
    "SETTLEMENT_TYPE",
    "AREA_PER_DWELLING_SQM",
    "COST_PER_AREA_EUR",
    "TOTAL_REPL_COST_EUR",
    "COST_STRUCTURAL_EUR",
    "COST_NONSTRUCTURAL_EUR",
    "COST_CONTENTS_EUR",
    "OCCUPANTS_PER_ASSET",
    "OCCUPANTS_PER_ASSET_DAY",
    "OCCUPANTS_PER_ASSET_NIGHT",
    "OCCUPANTS_PER_ASSET_TRANSIT",
    "OCCUPANTS_PER_ASSET_AVERAGE",
    "ID_2",
    "NAME_2",
    "ID_1",
    "NAME_1",
)


class KosovoTaxonomyError(ValueError):
    """Raised when frozen byte identity or exact taxonomy extraction drifts."""


def _value_set_sha256(values: set[str]) -> str:
    """Match the canonical exact-value-set fingerprint used by the profiler."""

    digest = hashlib.sha256()
    for value in sorted(values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _extract_taxonomy_values(
    text: str,
    *,
    expected_distinct_count: int,
    expected_value_set_sha256: str,
) -> list[str]:
    """Parse an already byte-verified CSV and return literal taxonomy strings."""

    if type(text) is not str:
        raise KosovoTaxonomyError("verified exposure text must be a string")
    if type(expected_distinct_count) is not int or isinstance(expected_distinct_count, bool):
        raise KosovoTaxonomyError("expected taxonomy count must be an integer")
    if expected_distinct_count < 1:
        raise KosovoTaxonomyError("expected taxonomy count must be positive")
    if (
        type(expected_value_set_sha256) is not str
        or len(expected_value_set_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_value_set_sha256)
    ):
        raise KosovoTaxonomyError("expected taxonomy fingerprint must be lowercase SHA-256")
    if "\x00" in text:
        raise KosovoTaxonomyError("verified exposure text contains NUL characters")

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=exposure.DELIMITER, strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise KosovoTaxonomyError("verified exposure CSV has no header") from exc
    except csv.Error as exc:
        raise KosovoTaxonomyError("verified exposure CSV header is malformed") from exc

    if tuple(header) != EXPECTED_HEADER:
        raise KosovoTaxonomyError("verified exposure CSV header does not match trusted profile")
    taxonomy_index = header.index(TAXONOMY_FIELD)

    values: set[str] = set()
    record_count = 0
    try:
        for row in reader:
            if len(row) != len(EXPECTED_HEADER):
                raise KosovoTaxonomyError("verified exposure CSV contains a ragged row")
            record_count += 1
            taxonomy = row[taxonomy_index]
            if taxonomy == "":
                raise KosovoTaxonomyError("verified exposure CSV contains an empty taxonomy")
            values.add(taxonomy)
    except csv.Error as exc:
        raise KosovoTaxonomyError("verified exposure CSV is malformed") from exc

    if record_count < 1:
        raise KosovoTaxonomyError("verified exposure CSV contains no data records")
    if len(values) != expected_distinct_count:
        raise KosovoTaxonomyError("taxonomy distinct count does not match trusted profile")
    observed_fingerprint = _value_set_sha256(values)
    if observed_fingerprint != expected_value_set_sha256:
        raise KosovoTaxonomyError("taxonomy value-set fingerprint does not match trusted profile")
    return sorted(values)


def extract_verified_kosovo_taxonomy(raw: bytes) -> dict[str, Any]:
    """Verify the frozen Kosovo bytes first, then emit the exact taxonomy set."""

    if type(raw) is not bytes:
        raise KosovoTaxonomyError("exposure input must be immutable bytes")

    # Receipt identity is the first gate. No decode or CSV parse occurs before
    # exact byte count and digest are both proven.
    if len(raw) != exposure.EXPECTED_BYTE_COUNT:
        raise KosovoTaxonomyError("exposure byte count does not match trusted receipt")
    observed_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_sha256 != exposure.EXPECTED_SHA256:
        raise KosovoTaxonomyError("exposure SHA-256 does not match trusted receipt")

    if raw.startswith(b"\xef\xbb\xbf"):
        raise KosovoTaxonomyError("trusted Kosovo exposure unexpectedly contains a UTF-8 BOM")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise KosovoTaxonomyError("verified exposure object is not valid UTF-8") from exc

    taxonomies = _extract_taxonomy_values(
        text,
        expected_distinct_count=EXPECTED_DISTINCT_COUNT,
        expected_value_set_sha256=EXPECTED_VALUE_SET_SHA256,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": exposure.SOURCE_ISSUE,
        "dataset_id": exposure.DATASET_ID,
        "project_id": exposure.PROJECT_ID,
        "project_path": exposure.PROJECT_PATH,
        "commit_sha": exposure.COMMIT_SHA,
        "repository_path": exposure.REPOSITORY_PATH,
        "receipt_comment_id": exposure.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": exposure.RECEIPT_EXECUTION_SHA,
        "byte_count": exposure.EXPECTED_BYTE_COUNT,
        "sha256": exposure.EXPECTED_SHA256,
        "taxonomy_field": TAXONOMY_FIELD,
        "taxonomy_count": EXPECTED_DISTINCT_COUNT,
        "taxonomy_value_set_sha256": EXPECTED_VALUE_SET_SHA256,
        "taxonomies": taxonomies,
        "normalization_applied": False,
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
