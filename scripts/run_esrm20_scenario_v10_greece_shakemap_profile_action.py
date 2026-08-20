# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Trusted-main-only action for the fixed ESRM20 v1.0 Greece ShakeMap pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.acquire_efehr_esrm20_scenario_v10_event_input_receipts import (
        COMMIT_SHA,
        DATASET_ID,
        EVENT_ID,
        INPUTS,
        PROJECT_ID,
        PROJECT_PATH,
        RELEASE_TAG,
        SOURCE_ISSUE,
        _bounded_header,
        _git_blob_sha1,
        _raw_file_url,
        utc_now,
    )
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
    from scripts.profile_esrm20_scenario_v10_greece_shakemap import (
        EVENT_ID as PROFILE_EVENT_ID,
        GRID_BYTE_COUNT,
        GRID_SHA256,
        MAX_XML_BYTES,
        UNCERTAINTY_BYTE_COUNT,
        UNCERTAINTY_SHA256,
        ShakeMapProfileError,
        profile_fixed_greece_shakemap_pair,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from acquire_efehr_esrm20_scenario_v10_event_input_receipts import (
        COMMIT_SHA,
        DATASET_ID,
        EVENT_ID,
        INPUTS,
        PROJECT_ID,
        PROJECT_PATH,
        RELEASE_TAG,
        SOURCE_ISSUE,
        _bounded_header,
        _git_blob_sha1,
        _raw_file_url,
        utc_now,
    )
    from prepare_agent_action_result import LedgerError, fetch_repository_comments
    from profile_esrm20_scenario_v10_greece_shakemap import (
        EVENT_ID as PROFILE_EVENT_ID,
        GRID_BYTE_COUNT,
        GRID_SHA256,
        MAX_XML_BYTES,
        UNCERTAINTY_BYTE_COUNT,
        UNCERTAINTY_SHA256,
        ShakeMapProfileError,
        profile_fixed_greece_shakemap_pair,
    )

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-profile-result-v1"
ACTION = "esrm20_scenario_v10_greece_shakemap_profile"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 24000

_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_CANONICAL_PROJECT_ID = 273
_CANONICAL_PROJECT_PATH = "efehr/esrm20_scenario_tests"
_CANONICAL_RELEASE_TAG = "v1.0"
_CANONICAL_COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
_CANONICAL_EVENT_ID = "Greece_07-9-1999"
_CANONICAL_GRID_ROLE = "usgs_shakemap_grid"
_CANONICAL_GRID_PATH = "shakemaps/shakemaps_USGS/Greece_07-9-1999/grid.xml"
_CANONICAL_GRID_GIT_BLOB_SHA1 = "21e323dec41b8efb012b2595145fded5fb35fd3a"
_CANONICAL_GRID_BYTE_COUNT = 5_290_966
_CANONICAL_GRID_SHA256 = "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f"
_CANONICAL_UNCERTAINTY_ROLE = "usgs_shakemap_uncertainty"
_CANONICAL_UNCERTAINTY_PATH = "shakemaps/shakemaps_USGS/Greece_07-9-1999/uncertainty.xml"
_CANONICAL_UNCERTAINTY_GIT_BLOB_SHA1 = "30d5635260a83cd0ac91ee559d0109ff126a7b57"
_CANONICAL_UNCERTAINTY_BYTE_COUNT = 5_340_320
_CANONICAL_UNCERTAINTY_SHA256 = "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417"
_CANONICAL_MAX_XML_BYTES = 6_000_000

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version", "action", "issue", "target_sha", "dataset_id",
    "grid_receipt_sha256", "uncertainty_receipt_sha256", "requester",
}
_RESULT_FIELDS = {
    "schema_version", "action", "source_issue", "dataset_id", "target_sha",
    "execution_sha", "shakemap_identity", "status", "failure_class",
    "failure_code", "receipts", "profile", "provider_file_bytes_read",
    "provider_file_content_profiled", "output_payload_bytes_read",
    "external_bytes_persisted", "event_location_inference_authorized",
    "scenario_selection_authorized", "independent_validation_established",
    "holdout_status_established", "publication_authorized", "model_use_authorized",
}
_RECEIPT_FIELDS = {"role", "retrieved_at", "byte_count", "sha256", "git_blob_sha1", "content_type", "etag"}
_PROFILE_FIELDS = {
    "schema_version", "receipt_event_id", "root_local_name", "root_namespace",
    "metadata", "grid", "uncertainty", "openquake_3_12_1_paired_imts",
    "coordinate_grids_equal", "provider_file_content_profiled",
    "event_location_inference_authorized", "scenario_selection_authorized",
    "independent_validation_established", "holdout_status_established",
    "publication_authorized", "model_use_authorized",
}
_GRID_PROFILE_FIELDS = {
    "byte_count", "sha256", "fields", "specification", "observed_row_count",
    "coordinate_sha256", "openquake_3_12_1_present_imts", "ignored_fields",
}
_METADATA_FIELDS = {
    "event_id", "shakemap_id", "shakemap_version", "code_version",
    "shakemap_originator", "map_status", "shakemap_event_type",
}
_SPEC_FIELDS = {
    "nlon", "nlat", "lon_min", "lat_min", "lon_max", "lat_max",
    "nominal_lon_spacing", "nominal_lat_spacing",
}
_ALLOWED_IMTS = {"MMI", "PGA", "SA(0.3)", "SA(1.0)", "SA(3.0)"}


class GreeceShakeMapProfileActionError(RuntimeError):
    """Fail-closed action-envelope or authority error."""


class ShakeMapByteIdentityError(RuntimeError):
    """A fixed provider object did not match its receipted byte identity."""


class ShakeMapAcquisitionError(RuntimeError):
    """A fixed provider object could not be acquired completely."""

    def __init__(self, *, completed_files: int) -> None:
        super().__init__("fixed ShakeMap acquisition failed")
        self.completed_files = completed_files


def _require_canonical_authority() -> None:
    exact = (
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (RELEASE_TAG, _CANONICAL_RELEASE_TAG, "release tag"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit sha"),
        (EVENT_ID, _CANONICAL_EVENT_ID, "event id"),
        (PROFILE_EVENT_ID, _CANONICAL_EVENT_ID, "profiler event id"),
        (GRID_BYTE_COUNT, _CANONICAL_GRID_BYTE_COUNT, "grid byte count"),
        (GRID_SHA256, _CANONICAL_GRID_SHA256, "grid sha256"),
        (UNCERTAINTY_BYTE_COUNT, _CANONICAL_UNCERTAINTY_BYTE_COUNT, "uncertainty byte count"),
        (UNCERTAINTY_SHA256, _CANONICAL_UNCERTAINTY_SHA256, "uncertainty sha256"),
        (MAX_XML_BYTES, _CANONICAL_MAX_XML_BYTES, "XML byte bound"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceShakeMapProfileActionError(f"canonical {label} drifted")
    expected_inputs = (
        ("rupture_definition", "ruptures/source_models/rupture_Greece_07-9-1999.xml", "fa3bfd7aedfb63869c5808785b0ca712b6e45859"),
        (_CANONICAL_GRID_ROLE, _CANONICAL_GRID_PATH, _CANONICAL_GRID_GIT_BLOB_SHA1),
        (_CANONICAL_UNCERTAINTY_ROLE, _CANONICAL_UNCERTAINTY_PATH, _CANONICAL_UNCERTAINTY_GIT_BLOB_SHA1),
    )
    if type(INPUTS) is not tuple or INPUTS != expected_inputs:
        raise GreeceShakeMapProfileActionError("canonical ShakeMap input set drifted")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GreeceShakeMapProfileActionError("duplicate JSON key")
        result[key] = value
    return result


def _strict_loads(text: str, *, label: str) -> Any:
    def reject(value: str) -> Any:
        raise GreeceShakeMapProfileActionError(f"non-finite JSON constant: {value}")
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=reject)
    except GreeceShakeMapProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceShakeMapProfileActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise GreeceShakeMapProfileActionError("text is not UTF-8 encodable") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_canonical_authority()
    if type(expected_issue) is not int or expected_issue != _CANONICAL_SOURCE_ISSUE:
        raise GreeceShakeMapProfileActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapProfileActionError("invalid execution SHA")
    if type(body) is not str or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES or body.count(REQUEST_MARKER) != 1:
        raise GreeceShakeMapProfileActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceShakeMapProfileActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceShakeMapProfileActionError("request fields drifted")
    expected = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": ACTION,
        "issue": _CANONICAL_SOURCE_ISSUE,
        "target_sha": execution_sha,
        "dataset_id": _CANONICAL_DATASET_ID,
        "grid_receipt_sha256": _CANONICAL_GRID_SHA256,
        "uncertainty_receipt_sha256": _CANONICAL_UNCERTAINTY_SHA256,
    }
    for field, value in expected.items():
        if type(request.get(field)) is not type(value) or request.get(field) != value:
            raise GreeceShakeMapProfileActionError(f"request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise GreeceShakeMapProfileActionError("invalid requester")
    return request


def _file_identity(*, role: str) -> dict[str, Any]:
    if role == _CANONICAL_GRID_ROLE:
        return {"role": role, "repository_path": _CANONICAL_GRID_PATH, "git_blob_sha1": _CANONICAL_GRID_GIT_BLOB_SHA1, "receipt_byte_count": _CANONICAL_GRID_BYTE_COUNT, "receipt_sha256": _CANONICAL_GRID_SHA256}
    if role == _CANONICAL_UNCERTAINTY_ROLE:
        return {"role": role, "repository_path": _CANONICAL_UNCERTAINTY_PATH, "git_blob_sha1": _CANONICAL_UNCERTAINTY_GIT_BLOB_SHA1, "receipt_byte_count": _CANONICAL_UNCERTAINTY_BYTE_COUNT, "receipt_sha256": _CANONICAL_UNCERTAINTY_SHA256}
    raise GreeceShakeMapProfileActionError("unknown fixed ShakeMap role")


def _identity() -> dict[str, Any]:
    return {
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "release_tag": _CANONICAL_RELEASE_TAG,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "event_id": _CANONICAL_EVENT_ID,
        "grid": _file_identity(role=_CANONICAL_GRID_ROLE),
        "uncertainty": _file_identity(role=_CANONICAL_UNCERTAINTY_ROLE),
    }


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION, "action": ACTION,
        "source_issue": _CANONICAL_SOURCE_ISSUE, "dataset_id": _CANONICAL_DATASET_ID,
        "target_sha": execution_sha, "execution_sha": execution_sha,
        "shakemap_identity": _identity(), "status": "blocked",
        "failure_class": "profile_failure", "failure_code": None,
        "receipts": None, "profile": None, "provider_file_bytes_read": False,
        "provider_file_content_profiled": False, "output_payload_bytes_read": False,
        "external_bytes_persisted": False, "event_location_inference_authorized": False,
        "scenario_selection_authorized": False, "independent_validation_established": False,
        "holdout_status_established": False, "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_receipt(receipt: object, *, role: str) -> dict[str, Any]:
    identity = _file_identity(role=role)
    if type(receipt) is not dict or set(receipt) != _RECEIPT_FIELDS or receipt.get("role") != role:
        raise GreeceShakeMapProfileActionError("receipt role or fields drifted")
    if type(receipt.get("retrieved_at")) is not str or _UTC_RE.fullmatch(receipt["retrieved_at"]) is None:
        raise GreeceShakeMapProfileActionError("receipt timestamp drifted")
    for field, expected in (("byte_count", identity["receipt_byte_count"]), ("sha256", identity["receipt_sha256"]), ("git_blob_sha1", identity["git_blob_sha1"])):
        if receipt.get(field) != expected:
            raise GreeceShakeMapProfileActionError(f"receipt {field} drifted")
    for field in ("content_type", "etag"):
        value = receipt.get(field)
        if value is not None and (type(value) is not str or _utf8_size(value) > 1024):
            raise GreeceShakeMapProfileActionError(f"invalid receipt {field}")
    return receipt


def _validate_receipts(receipts: object) -> dict[str, Any]:
    if type(receipts) is not dict or set(receipts) != {"grid", "uncertainty"}:
        raise GreeceShakeMapProfileActionError("receipts shape drifted")
    _validate_receipt(receipts["grid"], role=_CANONICAL_GRID_ROLE)
    _validate_receipt(receipts["uncertainty"], role=_CANONICAL_UNCERTAINTY_ROLE)
    return receipts


def _validate_side(side: object, *, role: str) -> dict[str, Any]:
    identity = _file_identity(role=role)
    if type(side) is not dict or set(side) != _GRID_PROFILE_FIELDS:
        raise GreeceShakeMapProfileActionError("profile grid fields drifted")
    if side.get("byte_count") != identity["receipt_byte_count"] or side.get("sha256") != identity["receipt_sha256"]:
        raise GreeceShakeMapProfileActionError("profile grid identity drifted")
    coord = side.get("coordinate_sha256")
    if type(coord) is not str or _SHA256_RE.fullmatch(coord) is None:
        raise GreeceShakeMapProfileActionError("profile coordinate digest invalid")
    spec = side.get("specification")
    if type(spec) is not dict or set(spec) != _SPEC_FIELDS:
        raise GreeceShakeMapProfileActionError("profile specification fields drifted")
    nlon, nlat = spec.get("nlon"), spec.get("nlat")
    if type(nlon) is not int or type(nlat) is not int or nlon <= 0 or nlat <= 0 or nlon * nlat > 500_000:
        raise GreeceShakeMapProfileActionError("profile grid cardinality invalid")
    for field in _SPEC_FIELDS - {"nlon", "nlat"}:
        value = spec.get(field)
        if type(value) not in {int, float} or not math.isfinite(value):
            raise GreeceShakeMapProfileActionError(f"profile specification {field} invalid")
    if side.get("observed_row_count") != nlon * nlat:
        raise GreeceShakeMapProfileActionError("profile observed row count drifted")
    fields = side.get("fields")
    if type(fields) is not list or not (2 <= len(fields) <= 32):
        raise GreeceShakeMapProfileActionError("profile field inventory invalid")
    imts = side.get("openquake_3_12_1_present_imts")
    if type(imts) is not list or imts != sorted(set(imts)) or any(type(x) is not str or x not in _ALLOWED_IMTS for x in imts):
        raise GreeceShakeMapProfileActionError("profile present IMTs invalid")
    ignored = side.get("ignored_fields")
    if type(ignored) is not list or ignored != sorted(set(ignored)) or any(type(x) is not str or len(x) > 64 for x in ignored):
        raise GreeceShakeMapProfileActionError("profile ignored fields invalid")
    return side


def _validate_profile(profile: object) -> dict[str, Any]:
    if type(profile) is not dict or set(profile) != _PROFILE_FIELDS:
        raise GreeceShakeMapProfileActionError("profile fields drifted")
    expected = {
        "schema_version": "oc-esrm20-scenario-v10-greece-shakemap-profile-v1",
        "receipt_event_id": _CANONICAL_EVENT_ID,
        "root_local_name": "shakemap_grid", "coordinate_grids_equal": True,
        "provider_file_content_profiled": True, "event_location_inference_authorized": False,
        "scenario_selection_authorized": False, "independent_validation_established": False,
        "holdout_status_established": False, "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, value in expected.items():
        if profile.get(field) != value:
            raise GreeceShakeMapProfileActionError(f"profile {field} drifted")
    namespace = profile.get("root_namespace")
    if type(namespace) is not str or _utf8_size(namespace) > 256:
        raise GreeceShakeMapProfileActionError("profile root namespace invalid")
    metadata = profile.get("metadata")
    if type(metadata) is not dict or set(metadata) != _METADATA_FIELDS or any(type(v) is not str or _utf8_size(v) > 96 for v in metadata.values()):
        raise GreeceShakeMapProfileActionError("profile metadata fields drifted")
    grid = _validate_side(profile.get("grid"), role=_CANONICAL_GRID_ROLE)
    uncertainty = _validate_side(profile.get("uncertainty"), role=_CANONICAL_UNCERTAINTY_ROLE)
    if grid["specification"] != uncertainty["specification"] or grid["observed_row_count"] != uncertainty["observed_row_count"]:
        raise GreeceShakeMapProfileActionError("profile paired grid structure drifted")
    if grid["coordinate_sha256"] != uncertainty["coordinate_sha256"]:
        raise GreeceShakeMapProfileActionError("profile coordinate pairing drifted")
    paired = profile.get("openquake_3_12_1_paired_imts")
    expected_paired = sorted(set(grid["openquake_3_12_1_present_imts"]) & set(uncertainty["openquake_3_12_1_present_imts"]))
    if type(paired) is not list or paired != expected_paired:
        raise GreeceShakeMapProfileActionError("profile paired IMTs drifted")
    return profile


def _validate_terminal_result(result: object) -> str:
    _require_canonical_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise GreeceShakeMapProfileActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapProfileActionError("invalid result SHA")
    expected = {
        "schema_version": RESULT_SCHEMA_VERSION, "action": ACTION,
        "source_issue": _CANONICAL_SOURCE_ISSUE, "dataset_id": _CANONICAL_DATASET_ID,
        "target_sha": execution_sha, "shakemap_identity": _identity(),
        "output_payload_bytes_read": False, "external_bytes_persisted": False,
        "event_location_inference_authorized": False, "scenario_selection_authorized": False,
        "independent_validation_established": False, "holdout_status_established": False,
        "publication_authorized": False, "model_use_authorized": False,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise GreeceShakeMapProfileActionError(f"result {field} drifted")
    failure_class = result.get("failure_class")
    if result.get("status") == "pass":
        if failure_class is not None or result.get("failure_code") is not None or result.get("provider_file_bytes_read") is not True or result.get("provider_file_content_profiled") is not True:
            raise GreeceShakeMapProfileActionError("invalid PASS state")
        _validate_receipts(result.get("receipts")); _validate_profile(result.get("profile"))
    elif result.get("status") == "blocked":
        if failure_class not in {"acquisition_failure", "byte_identity_mismatch", "profile_failure"}:
            raise GreeceShakeMapProfileActionError("invalid blocked failure class")
        if result.get("receipts") is not None or result.get("profile") is not None or result.get("provider_file_content_profiled") is not False or type(result.get("provider_file_bytes_read")) is not bool:
            raise GreeceShakeMapProfileActionError("blocked result widened evidence")
        if failure_class == "byte_identity_mismatch" and result.get("provider_file_bytes_read") is not True:
            raise GreeceShakeMapProfileActionError("identity mismatch without completed bytes")
        if failure_class == "profile_failure":
            if result.get("provider_file_bytes_read") is not True or result.get("failure_code") != "shakemap_pair_profile_rejected":
                raise GreeceShakeMapProfileActionError("invalid profile failure state")
        elif result.get("failure_code") is not None:
            raise GreeceShakeMapProfileActionError("non-profile failure carries code")
    else:
        raise GreeceShakeMapProfileActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise GreeceShakeMapProfileActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceShakeMapProfileActionError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(*, repository: str, token: str, execution_sha: str, opener: Any | None = None) -> bool:
    kwargs: dict[str, Any] = {"issue": _CANONICAL_SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceShakeMapProfileActionError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
        user = comment.get("user")
        if (user.get("login") if type(user) is dict else None) != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body")) == execution_sha:
            found = True
    return found


def _acquire_one_fixed(*, role: str, repository_path: str, expected_git_blob_sha1: str, expected_byte_count: int, expected_sha256: str, opener: Any, now: Callable[[], str], monotonic: Callable[[], float], deadline: float) -> tuple[bytes, dict[str, Any]]:
    url = _raw_file_url(repository_path)
    request = urllib.request.Request(url, headers={"Accept": "application/xml,text/xml;q=0.9,application/octet-stream;q=0.5", "User-Agent": "OpenCatastrophe-EFEHR-greece-shakemap-profile-v1"}, method="GET")
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            retrieved_at = now()
            raw = _read_bounded(response, deadline=deadline, maximum=_CANONICAL_MAX_XML_BYTES, monotonic=monotonic)
            content_type = _bounded_header(response, "Content-Type")
            etag = _bounded_header(response, "ETag")
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(f"EFEHR Greece ShakeMap retrieval failed: {type(exc).__name__}") from exc
    if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
        raise GreeceShakeMapProfileActionError("invalid retrieval timestamp")
    if len(raw) != expected_byte_count or hashlib.sha256(raw).hexdigest() != expected_sha256 or _git_blob_sha1(raw) != expected_git_blob_sha1:
        raise ShakeMapByteIdentityError("fixed ShakeMap byte identity mismatch")
    receipt = {"role": role, "retrieved_at": retrieved_at, "byte_count": len(raw), "sha256": expected_sha256, "git_blob_sha1": expected_git_blob_sha1, "content_type": content_type, "etag": etag}
    _validate_receipt(receipt, role=role)
    return raw, receipt


def _acquire_fixed_shakemap_pair(*, opener: Any | None = None, now: Callable[[], str] = utc_now, monotonic: Callable[[], float] = time.monotonic) -> tuple[tuple[bytes, bytes], dict[str, Any]]:
    _require_canonical_authority()
    open_response = opener or _open_fixed
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    completed = 0
    try:
        grid_raw, grid_receipt = _acquire_one_fixed(role=_CANONICAL_GRID_ROLE, repository_path=_CANONICAL_GRID_PATH, expected_git_blob_sha1=_CANONICAL_GRID_GIT_BLOB_SHA1, expected_byte_count=_CANONICAL_GRID_BYTE_COUNT, expected_sha256=_CANONICAL_GRID_SHA256, opener=open_response, now=now, monotonic=monotonic, deadline=deadline)
        completed = 1
        uncertainty_raw, uncertainty_receipt = _acquire_one_fixed(role=_CANONICAL_UNCERTAINTY_ROLE, repository_path=_CANONICAL_UNCERTAINTY_PATH, expected_git_blob_sha1=_CANONICAL_UNCERTAINTY_GIT_BLOB_SHA1, expected_byte_count=_CANONICAL_UNCERTAINTY_BYTE_COUNT, expected_sha256=_CANONICAL_UNCERTAINTY_SHA256, opener=open_response, now=now, monotonic=monotonic, deadline=deadline)
    except EfehrAcquisitionError as exc:
        raise ShakeMapAcquisitionError(completed_files=completed) from exc
    receipts = {"grid": grid_receipt, "uncertainty": uncertainty_receipt}
    _validate_receipts(receipts)
    return (grid_raw, uncertainty_raw), receipts


def _run_profile_with(*, execution_sha: str, fetcher: Callable[[], tuple[tuple[bytes, bytes], dict[str, Any]]], profiler: Callable[[bytes, bytes], dict[str, object]]) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceShakeMapProfileActionError("invalid execution SHA")
    _require_canonical_authority()
    result = _base_result(execution_sha)
    try:
        (grid_raw, uncertainty_raw), receipts = fetcher()
    except ShakeMapAcquisitionError as exc:
        result["failure_class"] = "acquisition_failure"
        result["provider_file_bytes_read"] = exc.completed_files > 0
    except ShakeMapByteIdentityError:
        result["failure_class"] = "byte_identity_mismatch"
        result["provider_file_bytes_read"] = True
    else:
        _validate_receipts(receipts); result["provider_file_bytes_read"] = True
        try:
            profile = profiler(grid_raw, uncertainty_raw)
        except ShakeMapProfileError:
            result["failure_class"] = "profile_failure"
            result["failure_code"] = "shakemap_pair_profile_rejected"
        else:
            _validate_profile(profile)
            result.update({"status": "pass", "failure_class": None, "failure_code": None, "receipts": receipts, "profile": profile, "provider_file_content_profiled": True})
    _validate_terminal_result(result)
    return result


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    return _run_profile_with(execution_sha=execution_sha, fetcher=_acquire_fixed_shakemap_pair, profiler=profile_fixed_greece_shakemap_pair)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(os.environ.get(args.comment_body_env), expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        raise GreeceShakeMapProfileActionError("output path is required")
    result = run_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
