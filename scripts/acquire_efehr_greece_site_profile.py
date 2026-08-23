# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Transiently acquire and profile the frozen ESRM20 Greece site model.

This worker owns no caller-selectable provider surface. It reuses the hardened
EFEHR transport, verifies the canonical #285 byte receipt before XML
interpretation, and delegates content profiling to the reviewed Greece wrapper.
Provider bytes exist only in memory for the duration of the call.
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
    from scripts import profile_efehr_greece_site_model as profile
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
    import profile_efehr_greece_site_model as profile


_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_PROFILER = profile.profile_verified_greece_site_model
_CANONICAL_PROVIDER_ROOT = "https://gitlab.seismo.ethz.ch"
_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_SOURCE_SCIENCE_ISSUE = 284
_CANONICAL_RECEIPT_ISSUE = 285
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_RELEASE = "v1.0"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_CONSUMER_EVENT = "Greece_07-9-1999"
_CANONICAL_REPOSITORY_PATH = "Vs30/Site_model_Greece.xml"
_CANONICAL_RECEIPT_COMMENT_ID = 5_388_640_521
_CANONICAL_RECEIPT_EXECUTION_SHA = "9bf3fee5d80431dfa873ee5ae03e07891e6f154a"
_CANONICAL_RECEIPT_RETRIEVED_AT = "2026-08-23T21:47:08Z"
_CANONICAL_BYTE_COUNT = 235_015
_CANONICAL_SHA256 = "613938c3f9e63fb94490ba4514ef7faf4bf3141b86c33fdd5eb7f21f8c175f85"


class GreeceSiteProfileError(RuntimeError):
    """Base class for fixed Greece site-profile worker failures."""


class GreeceSiteProfileAcquisitionError(GreeceSiteProfileError):
    """Raised when fixed provider transport cannot return the exact object."""


class GreeceSiteProfileContentError(GreeceSiteProfileError):
    """Raised when exact provider bytes fail the reviewed content profiler."""


class GreeceSiteProfileContractError(GreeceSiteProfileError):
    """Raised when trusted code/provenance/authority contracts drift."""


def _require_profile_contract() -> None:
    exact = (
        (PROVIDER_ROOT, _CANONICAL_PROVIDER_ROOT, "provider root"),
        (profile.SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (profile.SOURCE_SCIENCE_ISSUE, _CANONICAL_SOURCE_SCIENCE_ISSUE, "science issue"),
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
            raise GreeceSiteProfileContractError(
                f"merged Greece site profiler {label} drifted"
            )


def _require_production_transport_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise GreeceSiteProfileContractError(
            "frozen Greece site-profile production transport drifted"
        )
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise GreeceSiteProfileContractError(
            "frozen Greece site-profile monotonic clock drifted"
        )
    if profile.profile_verified_greece_site_model is not _CANONICAL_PROFILER:
        raise GreeceSiteProfileContractError(
            "frozen Greece site-profile profiler identity drifted"
        )


def _raw_file_url() -> str:
    encoded_path = urllib.parse.quote(_CANONICAL_REPOSITORY_PATH, safe="")
    encoded_ref = urllib.parse.quote(_CANONICAL_COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{_CANONICAL_PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _validate_text(value: object, *, label: str, allow_none: bool = False) -> None:
    if allow_none and value is None:
        return
    if type(value) is not str or not value or len(value.encode("utf-8")) > 256:
        raise GreeceSiteProfileContractError(
            f"Greece site profile {label} is outside bounded policy"
        )


def _validate_count(
    value: object, *, label: str, lower: int = 0, upper: int = 10_000
) -> int:
    if type(value) is not int or isinstance(value, bool) or not (lower <= value <= upper):
        raise GreeceSiteProfileContractError(
            f"Greece site profile {label} is outside bounded policy"
        )
    return value


def _validate_qname(value: object, *, label: str) -> None:
    if type(value) is not dict or set(value) != {"namespace", "local_name"}:
        raise GreeceSiteProfileContractError(
            f"Greece site profile {label} fields drifted"
        )
    _validate_text(value.get("namespace"), label=f"{label}.namespace", allow_none=True)
    _validate_text(value.get("local_name"), label=f"{label}.local_name")


def _validate_sha256(value: object, *, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise GreeceSiteProfileContractError(
            f"Greece site profile {label} is not lowercase SHA-256"
        )


def _validate_profile_result(result: object) -> dict[str, Any]:
    expected_fields = {
        "schema_version",
        "source_issue",
        "source_science_issue",
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
        "profile",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(result) is not dict or set(result) != expected_fields:
        raise GreeceSiteProfileContractError("Greece site profiler result fields drifted")

    exact = (
        ("schema_version", profile.SCHEMA_VERSION),
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("source_science_issue", _CANONICAL_SOURCE_SCIENCE_ISSUE),
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
            raise GreeceSiteProfileContractError(
                f"Greece site profile drifted at {field}"
            )

    bounded = result.get("profile")
    profile_fields = {
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
    if type(bounded) is not dict or set(bounded) != profile_fields:
        raise GreeceSiteProfileContractError(
            "Greece site profile evidence fields drifted"
        )
    if bounded.get("schema_version") != profile.SCHEMA_VERSION:
        raise GreeceSiteProfileContractError("Greece site profile schema version drifted")

    for field in (
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
    ):
        if bounded.get(field) is not False:
            raise GreeceSiteProfileContractError(
                f"Greece site profile widened authority at {field}"
            )

    parser = bounded.get("parser")
    if (
        type(parser) is not dict
        or set(parser)
        != {"xml_parser", "verified_encoding", "bom_present", "dtd_or_entity_allowed"}
        or parser.get("xml_parser")
        != "strict-utf8-text->xml.etree.ElementTree.fromstring"
        or parser.get("verified_encoding") != "utf-8"
        or parser.get("dtd_or_entity_allowed") is not False
        or type(parser.get("bom_present")) is not bool
    ):
        raise GreeceSiteProfileContractError(
            "Greece site profile parser boundary drifted"
        )

    element_count = _validate_count(
        bounded.get("element_count"),
        label="element_count",
        lower=1,
        upper=10_000,
    )
    leaf_count = _validate_count(
        bounded.get("leaf_element_count"),
        label="leaf_element_count",
        upper=10_000,
    )
    _validate_count(bounded.get("max_depth"), label="max_depth", lower=1, upper=16)
    text_count = _validate_count(
        bounded.get("non_whitespace_text_element_count"),
        label="non_whitespace_text_element_count",
        upper=10_000,
    )
    if leaf_count > element_count:
        raise GreeceSiteProfileContractError(
            "Greece site profile leaf count exceeds element count"
        )
    if text_count > element_count:
        raise GreeceSiteProfileContractError(
            "Greece site profile text count exceeds element count"
        )

    _validate_qname(bounded.get("root"), label="root")

    tag_counts = bounded.get("tag_counts")
    if type(tag_counts) is not list or len(tag_counts) > 10_000:
        raise GreeceSiteProfileContractError(
            "Greece site profile tag_counts is outside bounded policy"
        )
    for index, row in enumerate(tag_counts):
        label = f"tag_counts[{index}]"
        if type(row) is not dict or set(row) != {"name", "count"}:
            raise GreeceSiteProfileContractError(
                f"Greece site profile {label} fields drifted"
            )
        _validate_qname(row.get("name"), label=f"{label}.name")
        _validate_count(
            row.get("count"),
            label=f"{label}.count",
            lower=1,
            upper=element_count,
        )

    namespace_counts = bounded.get("namespace_counts")
    if type(namespace_counts) is not list or len(namespace_counts) > 1_024:
        raise GreeceSiteProfileContractError(
            "Greece site profile namespace_counts is outside bounded policy"
        )
    for index, row in enumerate(namespace_counts):
        label = f"namespace_counts[{index}]"
        if type(row) is not dict or set(row) != {"namespace", "element_count"}:
            raise GreeceSiteProfileContractError(
                f"Greece site profile {label} fields drifted"
            )
        _validate_text(row.get("namespace"), label=f"{label}.namespace")
        _validate_count(
            row.get("element_count"),
            label=f"{label}.element_count",
            lower=1,
            upper=element_count,
        )

    attribute_profiles = bounded.get("attribute_profiles")
    if type(attribute_profiles) is not list or len(attribute_profiles) > 512:
        raise GreeceSiteProfileContractError(
            "Greece site profile attribute_profiles is outside bounded policy"
        )
    attribute_fields = {
        "name",
        "occurrence_count",
        "empty_count",
        "leading_or_trailing_whitespace_count",
        "distinct_count",
        "exact_value_set_sha256",
        "finite_decimal_lexical_count",
        "true_lexical_count",
        "false_lexical_count",
    }
    for index, row in enumerate(attribute_profiles):
        label = f"attribute_profiles[{index}]"
        if type(row) is not dict or set(row) != attribute_fields:
            raise GreeceSiteProfileContractError(
                f"Greece site profile {label} fields drifted"
            )
        _validate_qname(row.get("name"), label=f"{label}.name")
        occurrences = _validate_count(
            row.get("occurrence_count"),
            label=f"{label}.occurrence_count",
            lower=1,
            upper=element_count,
        )
        for field in (
            "empty_count",
            "leading_or_trailing_whitespace_count",
            "finite_decimal_lexical_count",
            "true_lexical_count",
            "false_lexical_count",
        ):
            _validate_count(
                row.get(field),
                label=f"{label}.{field}",
                upper=occurrences,
            )
        _validate_count(
            row.get("distinct_count"),
            label=f"{label}.distinct_count",
            lower=1,
            upper=occurrences,
        )
        _validate_sha256(
            row.get("exact_value_set_sha256"),
            label=f"{label}.exact_value_set_sha256",
        )
    return result


def _acquire_and_profile_greece_site(*, opener: Any, monotonic: Any) -> dict[str, Any]:
    """Private injectable helper for deterministic offline tests."""

    _require_profile_contract()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    file_url = _raw_file_url()
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-EFEHR-greece-site-profile-v1",
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
        raise GreeceSiteProfileAcquisitionError(
            "Greece site-profile retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise GreeceSiteProfileAcquisitionError(
            f"Greece site-profile retrieval failed: {type(exc).__name__}"
        ) from exc

    try:
        result = profile.profile_verified_greece_site_model(raw)
    except profile.GreeceSiteProfileError as exc:
        raise GreeceSiteProfileContentError(
            "verified Greece site bytes failed profiling"
        ) from exc
    return _validate_profile_result(result)


def acquire_and_profile_greece_site() -> dict[str, Any]:
    """Run fixed production transport and return bounded structure evidence only."""

    _require_production_transport_identity()
    return _acquire_and_profile_greece_site(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )
