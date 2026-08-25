# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bind the generic receipt-first CSV profiler to the three Greece exposures.

Trusted-main issue #285 terminal comment 5397480571 freezes the exact byte
identity of all three source-declared Greece exposure CSVs.  This module adds no
provider acquisition path.  It only binds those receipts to the existing
interpretation-light CSV profiler already used by the ESRM20 Kosovo lane.

A passing profile establishes receipt-bound CSV structure only.  It does not
designate taxonomy, CRS, replacement-cost, benchmark, validation, publication,
or model-use semantics and it never returns provider rows or exact field values.
"""

from __future__ import annotations

from typing import Any

from scripts import profile_efehr_kosovo_exposure as generic_csv

SCHEMA_VERSION = "oc-esrm20-greece-exposure-3csv-content-profile-v0"
SOURCE_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
CONSUMER_EVENT_ID = "Greece_07-9-1999"
PARENT_EXPOSURE_PATH = "Exposure/OQ_Exposure_Input_Greece.xml"
RECEIPT_COMMENT_ID = 5397480571
RECEIPT_EXECUTION_SHA = "4b1d3c41a5df739b9686303eb753577ca39ec58e"

RECEIPTS: tuple[tuple[str, int, str], ...] = (
    (
        "Exposure/OQ_Exposure_Input_Greece_Com.csv",
        7_672_810,
        "2281f079a6e0b2215fab696d442f9d98b9b0ba94a2b4b24f23f1fff4018d1b57",
    ),
    (
        "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
        2_822_653,
        "ad6698199d84002d017b41668dc204a2d53835a4b2429bc7e8eea56b328549c7",
    ),
    (
        "Exposure/OQ_Exposure_Input_Greece_Res.csv",
        5_263_604,
        "928ac7f069dfc3181a936f73caafb951a5c2437f70379fa29518c002bbd3ef28",
    ),
)


class GreeceExposureCsvProfileError(ValueError):
    """Raised when the frozen three-object receipt boundary is violated."""


def _receipt_map() -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for path, byte_count, sha256 in RECEIPTS:
        if path in result:
            raise GreeceExposureCsvProfileError("duplicate frozen Greece exposure CSV path")
        if type(path) is not str or not path:
            raise GreeceExposureCsvProfileError("invalid frozen Greece exposure CSV path")
        if type(byte_count) is not int or isinstance(byte_count, bool) or byte_count < 1:
            raise GreeceExposureCsvProfileError("invalid frozen Greece exposure CSV byte count")
        if (
            type(sha256) is not str
            or len(sha256) != 64
            or any(character not in "0123456789abcdef" for character in sha256)
        ):
            raise GreeceExposureCsvProfileError("invalid frozen Greece exposure CSV SHA-256")
        result[path] = (byte_count, sha256)
    if len(result) != 3:
        raise GreeceExposureCsvProfileError("frozen Greece exposure CSV receipt set drifted")
    return result


def profile_verified_csv_bytes(raw: bytes, *, repository_path: str) -> dict[str, Any]:
    """Profile one exact source-declared Greece CSV after its receipt gate."""

    receipts = _receipt_map()
    if type(repository_path) is not str or repository_path not in receipts:
        raise GreeceExposureCsvProfileError(
            "Greece exposure CSV path left frozen three-object receipt set"
        )
    expected_byte_count, expected_sha256 = receipts[repository_path]
    try:
        profile = generic_csv.profile_verified_csv_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
    except generic_csv.ExposureProfileError as exc:
        raise GreeceExposureCsvProfileError(str(exc)) from exc
    return {
        "repository_path": repository_path,
        "byte_count": expected_byte_count,
        "sha256": expected_sha256,
        "profile": profile,
    }


def profile_verified_bundle(raw_by_path: dict[str, bytes]) -> dict[str, Any]:
    """Profile exactly the complete three-CSV bundle in canonical receipt order."""

    if type(raw_by_path) is not dict:
        raise GreeceExposureCsvProfileError("Greece exposure CSV bundle must be a dict")
    receipts = _receipt_map()
    if set(raw_by_path) != set(receipts):
        raise GreeceExposureCsvProfileError(
            "Greece exposure CSV bundle does not match frozen three-object receipt set"
        )

    files = [
        profile_verified_csv_bytes(raw_by_path[path], repository_path=path)
        for path, _, _ in RECEIPTS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "consumer_event_id": CONSUMER_EVENT_ID,
        "parent_exposure_path": PARENT_EXPOSURE_PATH,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "files": files,
        "provider_file_content_profiled": True,
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
