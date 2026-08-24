# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Receipt-bound profiler for the exact ESRM20 Greece exposure wrapper XML."""

from __future__ import annotations

import hashlib
from typing import Any

try:
    from scripts import profile_esrm20_runtime_exposure_xml as shared_profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import profile_esrm20_runtime_exposure_xml as shared_profile


SCHEMA_VERSION = "oc-esrm20-greece-exposure-content-profile-v0"
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

SHARED_MAX_PROFILE_BYTES = 4096
SHARED_ACCEPTED_NRML_NAMESPACES = frozenset(
    {
        "http://openquake.org/xmlns/nrml/0.4",
        "http://openquake.org/xmlns/nrml/0.5",
    }
)
_SHARED_PROFILE_FIELDS = frozenset(
    {
        "nrml_namespace",
        "exposure_model",
        "asset_references",
        "cost_types",
        "area",
        "occupancy_periods",
        "tag_names",
        "exposure_fields",
        "structural_cost_type_declared",
        "structural_value_inputs",
    }
)
_AUTHORITY_FALSE_FIELDS = (
    "raw_xml_returned",
    "referenced_dependency_bytes_receipted",
    "referenced_dependency_content_profiled",
    "crs_semantics_verified",
    "taxonomy_semantics_verified",
    "replacement_cost_semantics_verified",
    "benchmark_agreement_inspected",
    "independent_validation_established",
    "holdout_status_established",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)


class GreeceExposureProfileError(RuntimeError):
    """Raised when exact identity or the reviewed shared parser fails closed."""


def _verify_byte_identity(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> None:
    if type(raw) is not bytes:
        raise GreeceExposureProfileError("Greece exposure wrapper must be bytes")
    if (
        len(raw) != expected_byte_count
        or hashlib.sha256(raw).hexdigest() != expected_sha256
    ):
        raise GreeceExposureProfileError(
            "exact Greece exposure wrapper byte identity mismatch"
        )


def _require_shared_contract() -> None:
    if shared_profile.MAX_PROFILE_BYTES != SHARED_MAX_PROFILE_BYTES:
        raise GreeceExposureProfileError("shared exposure profile byte bound drifted")
    if shared_profile.ACCEPTED_NRML_NAMESPACES != SHARED_ACCEPTED_NRML_NAMESPACES:
        raise GreeceExposureProfileError("shared exposure NRML namespace set drifted")
    if not callable(shared_profile.profile_xml_bytes):
        raise GreeceExposureProfileError("shared exposure profile function drifted")
    if not isinstance(shared_profile.XmlSemanticProfileError, type):
        raise GreeceExposureProfileError("shared exposure profile error contract drifted")


def _profile_verified_greece_exposure_bytes(
    raw: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    """Private injectable bridge for deterministic synthetic/offline tests."""

    _verify_byte_identity(
        raw,
        expected_byte_count=expected_byte_count,
        expected_sha256=expected_sha256,
    )
    _require_shared_contract()
    try:
        profile = shared_profile.profile_xml_bytes(raw)
    except shared_profile.XmlSemanticProfileError as exc:
        raise GreeceExposureProfileError(
            "verified Greece exposure wrapper profile failed closed"
        ) from exc

    if type(profile) is not dict or set(profile) != _SHARED_PROFILE_FIELDS:
        raise GreeceExposureProfileError("shared exposure profile result fields drifted")
    if profile.get("nrml_namespace") not in SHARED_ACCEPTED_NRML_NAMESPACES:
        raise GreeceExposureProfileError("shared exposure profile namespace drifted")

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "parser": "profile_esrm20_runtime_exposure_xml.profile_xml_bytes",
        "profile": profile,
        "source_declarations_profiled": True,
    }
    for field in _AUTHORITY_FALSE_FIELDS:
        result[field] = False
    return result


def profile_verified_greece_exposure_xml(raw: bytes) -> dict[str, Any]:
    """Profile only the exact trusted Greece exposure wrapper bytes from #285."""

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
        "content_profile": bounded,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
