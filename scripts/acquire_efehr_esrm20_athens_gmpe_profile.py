# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Transiently acquire and profile the frozen Athens ESRM20 v1.0 GMPE tree.

The provider, project, immutable ref and path are fixed in code. Provider bytes
are verified and profiled in memory only; no caller-selectable network surface
is exposed and no raw provider bytes are returned or persisted.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from scripts.acquire_efehr_gitlab_receipt import (
    EfehrAcquisitionError,
    TOTAL_DEADLINE_SECONDS,
    _open_fixed,
    _read_bounded,
    _remaining,
    _validate_exact_response,
)
from scripts.efehr_gitlab_receipt import PROVIDER_ROOT
from scripts import profile_esrm20_scenario_v10_greece_gmpe_logic_tree as profile

SOURCE_ISSUE = 285
RECEIPT_ISSUE = 658
DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
PROJECT_ID = 273
PROJECT_PATH = "efehr/esrm20_scenario_tests"
RELEASE_TAG = "v1.0"
COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
EVENT_ID = "Greece_07-9-1999"
REPOSITORY_PATH = "ruptures/ground-motion-models/gmpe_logic_tree_5br_shallow_default.xml"
GIT_BLOB_SHA1 = "7f6ac690bf0f0538dabc4ef957db5b48e9fd35d3"
RECEIPT_COMMENT_ID = 5_389_061_280
RECEIPT_EXECUTION_SHA = "991477641495363252764ad55e626fdfe23781d8"
RECEIPT_RETRIEVED_AT = "2026-08-23T23:24:08Z"
EXPECTED_BYTE_COUNT = 6_490
EXPECTED_SHA256 = "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78"
MAX_RESPONSE_BYTES = EXPECTED_BYTE_COUNT

_CANONICAL_PROVIDER_ROOT = "https://gitlab.seismo.ethz.ch"
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_PROFILE = profile.profile_fixed_greece_gmpe_logic_tree


class AthensGmpeProfileError(RuntimeError):
    """Base failure for the fixed Athens GMPE profile worker."""


class AthensGmpeProfileAcquisitionError(AthensGmpeProfileError):
    """Fixed provider object could not be acquired safely."""


class AthensGmpeProfileContentError(AthensGmpeProfileError):
    """Exact provider bytes failed the reviewed offline profiler."""


class AthensGmpeProfileContractError(AthensGmpeProfileError):
    """Frozen authority or bounded result contract drifted."""


def _require_contract() -> None:
    exact = (
        (PROVIDER_ROOT, _CANONICAL_PROVIDER_ROOT, "provider root"),
        (SOURCE_ISSUE, 285, "source issue"),
        (RECEIPT_ISSUE, 658, "receipt issue"),
        (DATASET_ID, "efehr.esrm20.scenario-tests.v1.0", "dataset"),
        (PROJECT_ID, 273, "project id"),
        (PROJECT_PATH, "efehr/esrm20_scenario_tests", "project path"),
        (RELEASE_TAG, "v1.0", "release"),
        (COMMIT_SHA, "041f90d950d6ff84180b2faa11319a42c66c74cc", "commit"),
        (EVENT_ID, "Greece_07-9-1999", "event"),
        (REPOSITORY_PATH, "ruptures/ground-motion-models/gmpe_logic_tree_5br_shallow_default.xml", "path"),
        (GIT_BLOB_SHA1, "7f6ac690bf0f0538dabc4ef957db5b48e9fd35d3", "blob"),
        (RECEIPT_COMMENT_ID, 5_389_061_280, "receipt comment"),
        (RECEIPT_EXECUTION_SHA, "991477641495363252764ad55e626fdfe23781d8", "receipt execution"),
        (RECEIPT_RETRIEVED_AT, "2026-08-23T23:24:08Z", "receipt retrieval"),
        (EXPECTED_BYTE_COUNT, profile.EXPECTED_BYTE_COUNT, "byte count"),
        (EXPECTED_SHA256, profile.EXPECTED_SHA256, "SHA-256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileContractError(f"Athens GMPE {label} authority drifted")


def _require_production_identity() -> None:
    if _open_fixed is not _CANONICAL_OPEN_FIXED:
        raise AthensGmpeProfileContractError("Athens GMPE transport identity drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise AthensGmpeProfileContractError("Athens GMPE monotonic clock drifted")
    if profile.profile_fixed_greece_gmpe_logic_tree is not _CANONICAL_PROFILE:
        raise AthensGmpeProfileContractError("Athens GMPE profiler identity drifted")


def raw_file_url() -> str:
    encoded_path = urllib.parse.quote(REPOSITORY_PATH, safe="")
    encoded_ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _validate_profile_payload(payload: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "byte_count",
        "sha256",
        "nrml_namespace",
        "element_count",
        "max_depth",
        "branching_level_count",
        "branch_set_count",
        "branch_count",
        "uncertainty_model_count",
        "uncertainty_weight_count",
        "non_whitespace_text_element_count",
        "distinct_text_value_fingerprint_count",
        "attribute_name_counts",
        "raw_model_values_returned",
        "gmpe_semantics_verified",
        "gmpe_applicability_verified",
        "numerical_equivalence_verified",
        "scenario_selection_authorized",
        "independent_validation_established",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(payload) is not dict or set(payload) != fields:
        raise AthensGmpeProfileContractError("Athens GMPE profile fields drifted")
    exact = {
        "schema_version": "oc-esrm20-scenario-v10-greece-gmpe-logic-tree-profile-v1",
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "nrml_namespace": profile.EXPECTED_NRML_NAMESPACE,
        "raw_model_values_returned": False,
        "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False,
        "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(payload.get(field)) is not type(expected) or payload.get(field) != expected:
            raise AthensGmpeProfileContractError(f"Athens GMPE profile drifted at {field}")
    for field in (
        "element_count",
        "max_depth",
        "branching_level_count",
        "branch_set_count",
        "branch_count",
        "uncertainty_model_count",
        "uncertainty_weight_count",
        "non_whitespace_text_element_count",
        "distinct_text_value_fingerprint_count",
    ):
        value = payload.get(field)
        if type(value) is not int or isinstance(value, bool) or value < 0 or value > 10_000:
            raise AthensGmpeProfileContractError(f"Athens GMPE profile count drifted at {field}")
    if payload["element_count"] < 1 or payload["max_depth"] < 1:
        raise AthensGmpeProfileContractError("Athens GMPE profile is empty")
    if payload["uncertainty_model_count"] != payload["branch_count"]:
        raise AthensGmpeProfileContractError("Athens GMPE model cardinality drifted")
    if payload["uncertainty_weight_count"] != payload["branch_count"]:
        raise AthensGmpeProfileContractError("Athens GMPE weight cardinality drifted")
    names = payload.get("attribute_name_counts")
    if type(names) is not dict or len(names) > 128:
        raise AthensGmpeProfileContractError("Athens GMPE attribute-name surface drifted")
    for name, count in names.items():
        if type(name) is not str or not name or len(name.encode("utf-8")) > 128:
            raise AthensGmpeProfileContractError("Athens GMPE attribute name is unsafe")
        if type(count) is not int or isinstance(count, bool) or count < 1 or count > 10_000:
            raise AthensGmpeProfileContractError("Athens GMPE attribute count is unsafe")
    return payload


def _profile_bytes(data: bytes, profiler: Callable[[bytes], dict[str, object]]) -> dict[str, Any]:
    try:
        return _validate_profile_payload(profiler(data))
    except profile.GmpeLogicTreeProfileError as exc:
        raise AthensGmpeProfileContentError("exact Athens GMPE bytes failed profile") from exc


def acquire_and_profile_athens_gmpe(
    *,
    opener: Any | None = None,
    monotonic: Any | None = None,
    profiler: Callable[[bytes], dict[str, object]] | None = None,
) -> dict[str, Any]:
    """Read only the fixed immutable GMPE object and return bounded evidence."""

    _require_contract()
    production = opener is None and monotonic is None and profiler is None
    if production:
        _require_production_identity()
    open_response = opener or _open_fixed
    clock = monotonic or time.monotonic
    selected_profiler = profiler or profile.profile_fixed_greece_gmpe_logic_tree
    deadline = clock() + TOTAL_DEADLINE_SECONDS
    url = raw_file_url()
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/octet-stream", "User-Agent": "OpenCatastrophe-Athens-GMPE-Profile-v1"},
        method="GET",
    )
    try:
        with open_response(request, timeout=_remaining(deadline, clock)) as response:
            _validate_exact_response(response, url)
            data = _read_bounded(
                response,
                deadline=deadline,
                maximum=MAX_RESPONSE_BYTES,
                monotonic=clock,
            )
    except (EfehrAcquisitionError, urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as exc:
        raise AthensGmpeProfileAcquisitionError("fixed Athens GMPE acquisition failed") from exc
    if len(data) != EXPECTED_BYTE_COUNT:
        raise AthensGmpeProfileAcquisitionError("fixed Athens GMPE byte count drifted")
    bounded = _profile_bytes(data, selected_profiler)
    return {
        "schema_version": "oc-esrm20-athens-gmpe-profile-evidence-v1",
        "source_issue": SOURCE_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "release_tag": RELEASE_TAG,
        "commit_sha": COMMIT_SHA,
        "event_id": EVENT_ID,
        "repository_path": REPOSITORY_PATH,
        "git_blob_sha1": GIT_BLOB_SHA1,
        "receipt_comment_id": RECEIPT_COMMENT_ID,
        "receipt_execution_sha": RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": RECEIPT_RETRIEVED_AT,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
        "profile": bounded,
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
