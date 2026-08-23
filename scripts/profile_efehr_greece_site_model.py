# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound structural profiler for the ESRM20 Greece site-model XML.

The exact Greece object is already byte-receipted by trusted main under #285.
This module does not acquire provider data. It reuses the reviewed bounded XML
structure algorithm from the Kosovo site profiler, while giving the Greece
result its own receipt/provenance and schema identity. Raw XML, coordinates and
attribute values are never returned.
"""

from __future__ import annotations

from typing import Any

try:
    from scripts import profile_efehr_kosovo_site_model as shared_profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_efehr_kosovo_site_model as shared_profile


SCHEMA_VERSION = "oc-esrm20-greece-site-content-profile-v0"
SHARED_PROFILE_SCHEMA_VERSION = "oc-esrm20-kosovo-site-content-profile-v0"
SOURCE_ISSUE = 285
SOURCE_SCIENCE_ISSUE = 284
RECEIPT_ISSUE = 285
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
RELEASE = "v1.0"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
CONSUMER_EVENT = "Greece_07-9-1999"
REPOSITORY_PATH = "Vs30/Site_model_Greece.xml"
RECEIPT_COMMENT_ID = 5_388_640_521
RECEIPT_EXECUTION_SHA = "9bf3fee5d80431dfa873ee5ae03e07891e6f154a"
RECEIPT_RETRIEVED_AT = "2026-08-23T21:47:08Z"
EXPECTED_BYTE_COUNT = 235_015
EXPECTED_SHA256 = "613938c3f9e63fb94490ba4514ef7faf4bf3141b86c33fdd5eb7f21f8c175f85"

_PROFILE_FIELDS = {
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
_AUTHORITY_FALSE_FIELDS = (
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


class GreeceSiteProfileError(RuntimeError):
    """Raised when exact identity or the bounded shared profile fails closed."""


def _require_shared_contract() -> None:
    if shared_profile.SCHEMA_VERSION != SHARED_PROFILE_SCHEMA_VERSION:
        raise GreeceSiteProfileError("reviewed shared site-profile schema drifted")
    if not callable(shared_profile.profile_verified_xml_bytes):
        raise GreeceSiteProfileError("reviewed shared site-profile function drifted")
    if not isinstance(shared_profile.KosovoSiteProfileError, type):
        raise GreeceSiteProfileError("reviewed shared site-profile error contract drifted")


def _retag_bounded_profile(result: object) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _PROFILE_FIELDS:
        raise GreeceSiteProfileError("reviewed shared site-profile result fields drifted")
    if result.get("schema_version") != SHARED_PROFILE_SCHEMA_VERSION:
        raise GreeceSiteProfileError("reviewed shared site-profile result schema drifted")
    for field in _AUTHORITY_FALSE_FIELDS:
        if result.get(field) is not False:
            raise GreeceSiteProfileError(
                f"reviewed shared site-profile widened authority at {field}"
            )

    bounded = dict(result)
    bounded["schema_version"] = SCHEMA_VERSION
    return bounded


def _profile_verified_greece_site_bytes(
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
        raise GreeceSiteProfileError(
            "verified Greece site-model structure failed closed"
        ) from exc
    return _retag_bounded_profile(result)


def profile_verified_greece_site_model(raw: bytes) -> dict[str, Any]:
    """Profile only the exact trusted Greece site-model bytes from #285."""

    bounded = _profile_verified_greece_site_bytes(
        raw,
        expected_byte_count=EXPECTED_BYTE_COUNT,
        expected_sha256=EXPECTED_SHA256,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
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
