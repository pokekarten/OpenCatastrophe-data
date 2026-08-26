# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bind the three receipted ESRM20 v1.0 Greece source CSVs to the generic profiler.

Trusted-main issue #285 terminal comment 5423879080 freezes the exact byte
identity of all three project-186 source Greece exposure CSVs. This module adds
no provider acquisition path. It only binds those receipts to the existing
receipt-first, interpretation-light CSV profiler already used by the Kosovo and
project-269 Greece lanes.

A passing profile establishes receipt-bound CSV structure only. It does not
establish source-to-runtime lineage, taxonomy, CRS, replacement-cost semantics,
benchmark agreement, publication, or model-use authority. Provider rows and
exact field values are never returned by this wrapper.
"""

from __future__ import annotations

from typing import Any, Callable

from scripts import acquire_efehr_esrm20_greece_source_csv_receipts as source_receipts
from scripts import profile_efehr_kosovo_exposure as generic_csv

SCHEMA_VERSION = "oc-esrm20-greece-source-3csv-content-profile-v0"
SOURCE_ISSUE = 285
RELATED_SOURCE_ISSUE = 282
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
PROJECT_ID = 186
PROJECT_PATH = "efehr/esrm20_exposure"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "900433ada80fbb424c0976c34d72eeef97bab1af"
RECEIPT_COMMENT_ID = 5423879080
RECEIPT_EXECUTION_SHA = "0babfcf9aa9b6f6ede911217f99e2252428e95db"

RECEIPTS: tuple[tuple[str, int, str], ...] = (
    (
        "_exposure_models/Exposure_Model_Greece_Com.csv",
        12_578_244,
        "54c689673ba7160a2cf116af44cae20fe4c74c69ebf3bf192c7dd1bccfc94125",
    ),
    (
        "_exposure_models/Exposure_Model_Greece_Ind.csv",
        4_600_971,
        "491fe2b4dfbb36418582c41818a41c8e521e64b5a4b6c369816d175469b55165",
    ),
    (
        "_exposure_models/Exposure_Model_Greece_Res.csv",
        9_011_434,
        "1104b73d2d4e5b5b89d8c3a9575fe1f348662dd7f706c7a322c70a3240dc4e3b",
    ),
)

_CANONICAL_RECEIPTS = RECEIPTS
_CANONICAL_PROFILE_FUNCTION = generic_csv.profile_verified_csv_bytes


class GreeceSourceCsvProfileError(ValueError):
    """Raised when the frozen three-object source/profile boundary is violated."""


def _require_contract() -> None:
    exact = (
        (SOURCE_ISSUE, source_receipts.CANONICAL_ISSUE, "source issue"),
        (RELATED_SOURCE_ISSUE, source_receipts.RELATED_SOURCE_ISSUE, "related source issue"),
        (
            PARENT_CONSUMER_ISSUE,
            source_receipts.PARENT_CONSUMER_ISSUE,
            "parent consumer issue",
        ),
        (DATASET_ID, source_receipts.DATASET_ID, "dataset id"),
        (PROJECT_ID, source_receipts.PROJECT_ID, "project id"),
        (PROJECT_PATH, source_receipts.PROJECT_PATH, "project path"),
        (RELEASE_TAG, source_receipts.RELEASE_TAG, "release tag"),
        (COMMIT_SHA, source_receipts.COMMIT_SHA, "commit sha"),
        (RECEIPTS, _CANONICAL_RECEIPTS, "receipt set"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceSourceCsvProfileError(
                f"Greece source CSV {label} authority drifted"
            )

    target_identity = tuple((path, byte_count) for path, _blob, byte_count in source_receipts.TARGETS)
    receipt_identity = tuple((path, byte_count) for path, byte_count, _sha256 in RECEIPTS)
    if target_identity != receipt_identity:
        raise GreeceSourceCsvProfileError(
            "Greece source CSV receipts no longer match frozen provider targets"
        )


def _require_production_identity() -> None:
    _require_contract()
    if generic_csv.profile_verified_csv_bytes is not _CANONICAL_PROFILE_FUNCTION:
        raise GreeceSourceCsvProfileError("generic CSV profiler identity drifted")


def _receipt_map() -> dict[str, tuple[int, str]]:
    _require_contract()
    result: dict[str, tuple[int, str]] = {}
    for path, byte_count, sha256 in RECEIPTS:
        if type(path) is not str or not path or path in result:
            raise GreeceSourceCsvProfileError("invalid or duplicate frozen source path")
        if type(byte_count) is not int or isinstance(byte_count, bool) or byte_count < 1:
            raise GreeceSourceCsvProfileError("invalid frozen source byte count")
        if (
            type(sha256) is not str
            or len(sha256) != 64
            or any(character not in "0123456789abcdef" for character in sha256)
        ):
            raise GreeceSourceCsvProfileError("invalid frozen source SHA-256")
        result[path] = (byte_count, sha256)
    if len(result) != 3:
        raise GreeceSourceCsvProfileError("frozen Greece source CSV receipt set drifted")
    return result


def _validate_nested_profile(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise GreeceSourceCsvProfileError("generic CSV profiler returned a non-object")
    required = {
        "schema_version",
        "parser",
        "record_count",
        "header",
        "columns",
        "raw_rows_returned",
        "external_bytes_persisted",
        "publication_authorized",
    }
    if set(value) != required:
        raise GreeceSourceCsvProfileError("generic CSV profile fields drifted")
    if value["schema_version"] != generic_csv.SCHEMA_VERSION:
        raise GreeceSourceCsvProfileError("generic CSV profile schema drifted")
    if type(value["record_count"]) is not int or value["record_count"] < 1:
        raise GreeceSourceCsvProfileError("generic CSV profile record count invalid")
    if type(value["header"]) is not list or not value["header"]:
        raise GreeceSourceCsvProfileError("generic CSV profile header invalid")
    if type(value["columns"]) is not list or len(value["columns"]) != len(value["header"]):
        raise GreeceSourceCsvProfileError("generic CSV profile columns/header drifted")
    if value["raw_rows_returned"] is not False:
        raise GreeceSourceCsvProfileError("generic CSV profile widened raw-row authority")
    if value["external_bytes_persisted"] is not False:
        raise GreeceSourceCsvProfileError("generic CSV profile widened persistence authority")
    if value["publication_authorized"] is not False:
        raise GreeceSourceCsvProfileError("generic CSV profile widened publication authority")
    return value


def _profile_for_test(
    raw: bytes,
    *,
    repository_path: str,
    profiler: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    receipts = _receipt_map()
    if type(repository_path) is not str or repository_path not in receipts:
        raise GreeceSourceCsvProfileError(
            "Greece source CSV path left frozen three-object receipt set"
        )
    expected_byte_count, expected_sha256 = receipts[repository_path]
    try:
        nested = profiler(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
    except generic_csv.ExposureProfileError as exc:
        raise GreeceSourceCsvProfileError(str(exc)) from exc
    return {
        "repository_path": repository_path,
        "byte_count": expected_byte_count,
        "sha256": expected_sha256,
        "profile": _validate_nested_profile(nested),
    }


def profile_verified_csv_bytes(raw: bytes, *, repository_path: str) -> dict[str, Any]:
    """Profile one exact receipted source CSV without widening semantic authority."""

    _require_production_identity()
    return _profile_for_test(
        raw,
        repository_path=repository_path,
        profiler=_CANONICAL_PROFILE_FUNCTION,
    )


def _profile_bundle_for_test(
    raw_by_path: dict[str, bytes],
    *,
    profiler: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    receipts = _receipt_map()
    if type(raw_by_path) is not dict or set(raw_by_path) != set(receipts):
        raise GreeceSourceCsvProfileError(
            "Greece source CSV bundle does not match frozen three-object receipt set"
        )
    files = [
        _profile_for_test(raw_by_path[path], repository_path=path, profiler=profiler)
        for path, _byte_count, _sha256 in RECEIPTS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "related_source_issue": RELATED_SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "files": files,
        "provider_file_content_profiled": True,
        "source_runtime_lineage_verified": False,
        "content_semantics_verified": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "raw_rows_returned": False,
        "exact_field_values_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_verified_bundle(raw_by_path: dict[str, bytes]) -> dict[str, Any]:
    """Profile exactly the complete three-source-CSV bundle in receipt order."""

    _require_production_identity()
    return _profile_bundle_for_test(
        raw_by_path,
        profiler=_CANONICAL_PROFILE_FUNCTION,
    )
