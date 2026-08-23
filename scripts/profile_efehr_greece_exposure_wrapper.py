# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound structure profiler for the ESRM20 Greece exposure wrapper.

The exact Greece exposure XML is already byte-receipted by trusted main under
#285. This module does not acquire provider data and does not follow any path or
reference that the XML may contain. It reuses the reviewed bounded XML parser
from the Kosovo site profiler only as a structure algorithm, then projects that
result into an exposure-specific authority ceiling. Raw XML, text values and
attribute values are never returned.

A successful profile establishes exact-byte structure only. It does not prove
exposure taxonomy, cost/value basis, currency, dependency references, CRS,
missingness, benchmark agreement, publication rights, or model-use authority.
"""

from __future__ import annotations

from typing import Any

try:
    from scripts import profile_efehr_kosovo_site_model as shared_profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_kosovo_site_model as shared_profile


SCHEMA_VERSION = "oc-esrm20-greece-exposure-wrapper-profile-v0"
SHARED_PROFILE_SCHEMA_VERSION = "oc-esrm20-kosovo-site-content-profile-v0"
SOURCE_ISSUE = 285
RECEIPT_ISSUE = 285
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE = "v1.0"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
CONSUMER_EVENT = "Greece_07-9-1999"
REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Greece.xml"
RECEIPT_COMMENT_ID = 5_388_640_521
RECEIPT_EXECUTION_SHA = "9bf3fee5d80431dfa873ee5ae03e07891e6f154a"
RECEIPT_RETRIEVED_AT = "2026-08-23T21:47:08Z"
EXPECTED_BYTE_COUNT = 697
EXPECTED_SHA256 = "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556"

_SHARED_PROFILE_FIELDS = {
    "schema_version",
    "parser",
    "root",
    "element_count",
    "leaf_element_count",
    "max_depth",
    "tag_counts",
    "namespace_counts",
    "attribute_profiles",
    "non_whitespace_text_element_count",
    "raw_xml_returned",
    "raw_attribute_values_returned",
    "crs_coordinate_semantics_verified",
    "site_parameter_units_verified",
    "missingness_semantics_verified",
    "gsim_site_parameter_sufficiency_verified",
    "site_adjusted_reference_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_SHARED_FALSE_FIELDS = (
    "raw_xml_returned",
    "raw_attribute_values_returned",
    "crs_coordinate_semantics_verified",
    "site_parameter_units_verified",
    "missingness_semantics_verified",
    "gsim_site_parameter_sufficiency_verified",
    "site_adjusted_reference_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)
_EXPOSURE_FALSE_FIELDS = (
    "raw_xml_returned",
    "raw_attribute_values_returned",
    "raw_text_values_returned",
    "dependency_references_verified",
    "taxonomy_semantics_verified",
    "cost_type_semantics_verified",
    "currency_semantics_verified",
    "replacement_cost_basis_verified",
    "asset_value_semantics_verified",
    "crs_coordinate_semantics_verified",
    "missingness_semantics_verified",
    "benchmark_agreement_inspected",
    "independent_validation_established",
    "holdout_status_established",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)


class GreeceExposureProfileError(RuntimeError):
    """Raised when exact identity or bounded structure profiling fails closed."""


def _require_shared_contract() -> None:
    if shared_profile.SCHEMA_VERSION != SHARED_PROFILE_SCHEMA_VERSION:
        raise GreeceExposureProfileError("reviewed shared XML-profile schema drifted")
    if not callable(shared_profile.profile_verified_xml_bytes):
        raise GreeceExposureProfileError("reviewed shared XML-profile function drifted")
    if not isinstance(shared_profile.KosovoSiteProfileError, type):
        raise GreeceExposureProfileError("reviewed shared XML-profile error contract drifted")


def _project_exposure_structure(result: object) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _SHARED_PROFILE_FIELDS:
        raise GreeceExposureProfileError("reviewed shared XML-profile fields drifted")
    if result.get("schema_version") != SHARED_PROFILE_SCHEMA_VERSION:
        raise GreeceExposureProfileError("reviewed shared XML-profile result schema drifted")
    for field in _SHARED_FALSE_FIELDS:
        if result.get(field) is not False:
            raise GreeceExposureProfileError(
                f"reviewed shared XML-profile widened authority at {field}"
            )

    projected = {
        "schema_version": SCHEMA_VERSION,
        "parser": result["parser"],
        "root": result["root"],
        "element_count": result["element_count"],
        "leaf_element_count": result["leaf_element_count"],
        "max_depth": result["max_depth"],
        "tag_counts": result["tag_counts"],
        "namespace_counts": result["namespace_counts"],
        "attribute_profiles": result["attribute_profiles"],
        "non_whitespace_text_element_count": result[
            "non_whitespace_text_element_count"
        ],
        "raw_xml_returned": False,
        "raw_attribute_values_returned": False,
        "raw_text_values_returned": False,
        "dependency_references_verified": False,
        "taxonomy_semantics_verified": False,
        "cost_type_semantics_verified": False,
        "currency_semantics_verified": False,
        "replacement_cost_basis_verified": False,
        "asset_value_semantics_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field in _EXPOSURE_FALSE_FIELDS:
        if projected[field] is not False:  # pragma: no cover - construction invariant
            raise GreeceExposureProfileError(
                f"Greece exposure authority unexpectedly widened at {field}"
            )
    return projected


def _profile_verified_greece_exposure_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Private injectable bridge used only for deterministic synthetic tests."""

    _require_shared_contract()
    try:
        result = shared_profile.profile_verified_xml_bytes(
            raw,
            expected_byte_count=expected_byte_count,
            expected_sha256=expected_sha256,
        )
    except shared_profile.KosovoSiteProfileError as exc:
        raise GreeceExposureProfileError(
            "verified Greece exposure-wrapper structure failed closed"
        ) from exc
    return _project_exposure_structure(result)


def profile_verified_greece_exposure_wrapper(raw: bytes) -> dict[str, Any]:
    """Profile only the exact trusted Greece exposure-wrapper bytes from #285."""

    bounded = _profile_verified_greece_exposure_bytes(
        raw,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release": RELEASE,
        "commit_sha": COMMIT_SHA,
        "consumer_event": CONSUMER_EVENT,
        "repository_path": REPOSITORY_PATH,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": RECEIPT_RETRIEVED_AT,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "profile": bounded,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
