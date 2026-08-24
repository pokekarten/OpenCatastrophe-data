# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Transiently acquire and profile the frozen ESRM20 Greece exposure wrapper.

The worker owns no caller-selectable provider surface. It reuses the hardened
EFEHR transport, verifies the canonical #285 byte receipt before XML
interpretation via the merged receipt-bound profiler, and returns bounded source
declarations only. Provider bytes exist only in memory for the duration of the
call.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
    from scripts import profile_efehr_greece_exposure_xml as profile
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import PROVIDER_ROOT
    import profile_efehr_greece_exposure_xml as profile


_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_PROFILER = profile.profile_verified_greece_exposure_xml
_CANONICAL_PROVIDER_ROOT = "https://gitlab.seismo.ethz.ch"
_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_RECEIPT_ISSUE = 285
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_RELEASE = "v1.0"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_CONSUMER_EVENT = "Greece_07-9-1999"
_CANONICAL_REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Greece.xml"
_CANONICAL_RECEIPT_COMMENT_ID = 5_388_640_521
_CANONICAL_RECEIPT_EXECUTION_SHA = "9bf3fee5d80431dfa873ee5ae03e07891e6f154a"
_CANONICAL_RECEIPT_RETRIEVED_AT = "2026-08-23T21:47:08Z"
_CANONICAL_BYTE_COUNT = 697
_CANONICAL_SHA256 = "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556"
_MAX_TEXT_BYTES = 4096
_MAX_LIST_ITEMS = 128


class GreeceExposureWorkerError(RuntimeError):
    """Base class for fixed Greece exposure worker failures."""


class GreeceExposureAcquisitionError(GreeceExposureWorkerError):
    """Raised when fixed provider transport cannot return the exact object."""


class GreeceExposureContentError(GreeceExposureWorkerError):
    """Raised when exact provider bytes fail the reviewed content profiler."""


class GreeceExposureContractError(GreeceExposureWorkerError):
    """Raised when trusted code/provenance/authority contracts drift."""


def _require_profile_contract() -> None:
    exact = (
        (PROVIDER_ROOT, _CANONICAL_PROVIDER_ROOT, "provider root"),
        (profile.SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (profile.RECEIPT_ISSUE, _CANONICAL_RECEIPT_ISSUE, "receipt issue"),
        (profile.DATASET_ID, _CANONICAL_DATASET_ID, "dataset"),
        (profile.PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (profile.PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (profile.RELEASE, _CANONICAL_RELEASE, "release"),
        (profile.COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (profile.CONSUMER_EVENT, _CANONICAL_CONSUMER_EVENT, "consumer event"),
        (profile.REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "repository path"),
        (profile.RECEIPT_COMMENT_ID, _CANONICAL_RECEIPT_COMMENT_ID, "receipt comment"),
        (profile.RECEIPT_EXECUTION_SHA, _CANONICAL_RECEIPT_EXECUTION_SHA, "receipt execution"),
        (profile.RECEIPT_RETRIEVED_AT, _CANONICAL_RECEIPT_RETRIEVED_AT, "receipt retrieval"),
        (profile.EXPECTED_BYTE_COUNT, _CANONICAL_BYTE_COUNT, "byte count"),
        (profile.EXPECTED_SHA256, _CANONICAL_SHA256, "SHA-256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureContractError(
                f"merged Greece exposure profiler {label} drifted"
            )


def _require_production_transport_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise GreeceExposureContractError(
            "frozen Greece exposure production transport drifted"
        )
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise GreeceExposureContractError(
            "frozen Greece exposure monotonic clock drifted"
        )
    if profile.profile_verified_greece_exposure_xml is not _CANONICAL_PROFILER:
        raise GreeceExposureContractError(
            "frozen Greece exposure profiler identity drifted"
        )


def _raw_file_url() -> str:
    encoded_path = urllib.parse.quote(_CANONICAL_REPOSITORY_PATH, safe="")
    encoded_ref = urllib.parse.quote(_CANONICAL_COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _bounded_text(value: object, *, label: str, allow_none: bool = False) -> None:
    if allow_none and value is None:
        return
    if type(value) is not str or not value or len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
        raise GreeceExposureContractError(
            f"Greece exposure profile {label} is outside bounded policy"
        )


def _bounded_text_list(value: object, *, label: str) -> None:
    if type(value) is not list or len(value) > _MAX_LIST_ITEMS:
        raise GreeceExposureContractError(
            f"Greece exposure profile {label} is outside bounded policy"
        )
    for index, item in enumerate(value):
        _bounded_text(item, label=f"{label}[{index}]")


def _validate_declared_profile(value: object) -> None:
    fields = {
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
    if type(value) is not dict or set(value) != fields:
        raise GreeceExposureContractError(
            "Greece exposure declaration profile fields drifted"
        )
    if value.get("nrml_namespace") not in profile.SHARED_ACCEPTED_NRML_NAMESPACES:
        raise GreeceExposureContractError("Greece exposure NRML namespace drifted")

    model = value.get("exposure_model")
    if type(model) is not dict or set(model) != {
        "id",
        "category",
        "taxonomy_source",
        "description",
    }:
        raise GreeceExposureContractError("Greece exposure model fields drifted")
    _bounded_text(model.get("id"), label="exposure_model.id")
    _bounded_text(model.get("category"), label="exposure_model.category", allow_none=True)
    _bounded_text(
        model.get("taxonomy_source"),
        label="exposure_model.taxonomy_source",
        allow_none=True,
    )
    _bounded_text(model.get("description"), label="exposure_model.description")

    _bounded_text_list(value.get("asset_references"), label="asset_references")
    _bounded_text_list(value.get("occupancy_periods"), label="occupancy_periods")
    _bounded_text_list(value.get("tag_names"), label="tag_names")
    _bounded_text_list(value.get("structural_value_inputs"), label="structural_value_inputs")

    cost_types = value.get("cost_types")
    if type(cost_types) is not list or len(cost_types) > _MAX_LIST_ITEMS:
        raise GreeceExposureContractError("Greece exposure cost_types is outside bounded policy")
    for index, row in enumerate(cost_types):
        if type(row) is not dict or set(row) != {"name", "type", "unit"}:
            raise GreeceExposureContractError(
                f"Greece exposure cost_types[{index}] fields drifted"
            )
        for key in ("name", "type", "unit"):
            _bounded_text(row.get(key), label=f"cost_types[{index}].{key}")

    area = value.get("area")
    if area is not None:
        if type(area) is not dict or set(area) != {"type", "unit"}:
            raise GreeceExposureContractError("Greece exposure area fields drifted")
        _bounded_text(area.get("type"), label="area.type")
        _bounded_text(area.get("unit"), label="area.unit")

    exposure_fields = value.get("exposure_fields")
    if type(exposure_fields) is not list or len(exposure_fields) > _MAX_LIST_ITEMS:
        raise GreeceExposureContractError(
            "Greece exposure exposure_fields is outside bounded policy"
        )
    for index, row in enumerate(exposure_fields):
        if type(row) is not dict or not {"oq", "input"} <= set(row) <= {
            "oq",
            "type",
            "input",
        }:
            raise GreeceExposureContractError(
                f"Greece exposure exposure_fields[{index}] fields drifted"
            )
        for key, item in row.items():
            _bounded_text(item, label=f"exposure_fields[{index}].{key}")

    if type(value.get("structural_cost_type_declared")) is not bool:
        raise GreeceExposureContractError(
            "Greece exposure structural_cost_type_declared type drifted"
        )


def _validate_profile_result(result: object) -> dict[str, Any]:
    expected_fields = {
        "schema_version",
        "source_issue",
        "receipt_issue",
        "dataset_id",
        "project_id",
        "project_path",
        "release",
        "commit_sha",
        "consumer_event",
        "repository_path",
        "receipt_comment_id",
        "receipt_execution_sha",
        "receipt_retrieved_at",
        "byte_count",
        "sha256",
        "content_profile",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(result) is not dict or set(result) != expected_fields:
        raise GreeceExposureContractError("Greece exposure profiler result fields drifted")

    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("receipt_issue", _CANONICAL_RECEIPT_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("project_id", _CANONICAL_PROJECT_ID),
        ("project_path", _CANONICAL_PROJECT_PATH),
        ("release", _CANONICAL_RELEASE),
        ("commit_sha", _CANONICAL_COMMIT_SHA),
        ("consumer_event", _CANONICAL_CONSUMER_EVENT),
        ("repository_path", _CANONICAL_REPOSITORY_PATH),
        ("receipt_comment_id", _CANONICAL_RECEIPT_COMMENT_ID),
        ("receipt_execution_sha", _CANONICAL_RECEIPT_EXECUTION_SHA),
        ("receipt_retrieved_at", _CANONICAL_RECEIPT_RETRIEVED_AT),
        ("byte_count", _CANONICAL_BYTE_COUNT),
        ("sha256", _CANONICAL_SHA256),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureContractError(
                f"Greece exposure profile drifted at {field}"
            )

    bounded = result.get("content_profile")
    bounded_fields = {
        "schema_version",
        "parser",
        "profile",
        "source_declarations_profiled",
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
    }
    if type(bounded) is not dict or set(bounded) != bounded_fields:
        raise GreeceExposureContractError(
            "Greece exposure bounded evidence fields drifted"
        )
    if bounded.get("schema_version") != profile.SCHEMA_VERSION:
        raise GreeceExposureContractError("Greece exposure schema version drifted")
    if (
        bounded.get("parser")
        != "profile_esrm20_runtime_exposure_xml.profile_xml_bytes"
        or bounded.get("source_declarations_profiled") is not True
    ):
        raise GreeceExposureContractError("Greece exposure parser contract drifted")
    for field in (
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
    ):
        if bounded.get(field) is not False:
            raise GreeceExposureContractError(
                f"Greece exposure profile widened authority at {field}"
            )
    _validate_declared_profile(bounded.get("profile"))
    return result


def _acquire_and_profile_greece_exposure(
    *, opener: Any, monotonic: Any
) -> dict[str, Any]:
    """Private injectable helper for deterministic offline tests."""

    _require_profile_contract()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    file_url = _raw_file_url()
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-greece-exposure-profile-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            _declared_length(response, _CANONICAL_BYTE_COUNT)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_BYTE_COUNT,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError as exc:
        raise GreeceExposureAcquisitionError(
            "Greece exposure retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise GreeceExposureAcquisitionError(
            f"Greece exposure retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        result = profile.profile_verified_greece_exposure_xml(raw)
    except profile.GreeceExposureProfileError as exc:
        raise GreeceExposureContentError(
            "verified Greece exposure bytes failed profiling"
        ) from exc
    return _validate_profile_result(result)


def acquire_and_profile_greece_exposure() -> dict[str, Any]:
    """Run fixed production transport and return bounded declarations only."""

    _require_production_transport_identity()
    return _acquire_and_profile_greece_exposure(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )
