# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for profiling the fixed ESRM20 v1.0 Greece rupture."""

from __future__ import annotations

import argparse
import hashlib
import json
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
    from scripts.profile_esrm20_scenario_v10_greece_rupture import (
        EXPECTED_BYTE_COUNT,
        EXPECTED_NRML_NAMESPACE,
        EXPECTED_SHA256,
        OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
        RuptureProfileError,
        profile_fixed_greece_rupture,
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
    from profile_esrm20_scenario_v10_greece_rupture import (
        EXPECTED_BYTE_COUNT,
        EXPECTED_NRML_NAMESPACE,
        EXPECTED_SHA256,
        OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
        RuptureProfileError,
        profile_fixed_greece_rupture,
    )

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-profile-result-v1"
ACTION = "esrm20_scenario_v10_greece_rupture_profile"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 12000

_CANONICAL_SOURCE_ISSUE = 285
_CANONICAL_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_CANONICAL_PROJECT_ID = 273
_CANONICAL_PROJECT_PATH = "efehr/esrm20_scenario_tests"
_CANONICAL_RELEASE_TAG = "v1.0"
_CANONICAL_COMMIT_SHA = "041f90d950d6ff84180b2faa11319a42c66c74cc"
_CANONICAL_EVENT_ID = "Greece_07-9-1999"
_CANONICAL_ROLE = "rupture_definition"
_CANONICAL_REPOSITORY_PATH = "ruptures/source_models/rupture_Greece_07-9-1999.xml"
_CANONICAL_GIT_BLOB_SHA1 = "fa3bfd7aedfb63869c5808785b0ca712b6e45859"
_CANONICAL_EXPECTED_BYTE_COUNT = 666
_CANONICAL_EXPECTED_SHA256 = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
_CANONICAL_EXPECTED_NRML_NAMESPACE = "http://openquake.org/xmlns/nrml/0.5"
_CANONICAL_MAX_RUPTURE_BYTES = 4096

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "rupture_identity",
    "status",
    "failure_class",
    "failure_code",
    "receipt",
    "profile",
    "provider_file_bytes_read",
    "provider_file_content_profiled",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}
_RECEIPT_FIELDS = {
    "retrieved_at",
    "byte_count",
    "sha256",
    "git_blob_sha1",
    "content_type",
    "etag",
}
_PROFILE_FIELDS = {
    "schema_version",
    "byte_count",
    "sha256",
    "nrml_namespace",
    "rupture_element_local_name",
    "element_count",
    "max_depth",
    "magnitude_element_count",
    "rake_element_count",
    "hypocenter_element_count",
    "provider_file_content_profiled",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}


class GreeceRuptureProfileActionError(RuntimeError):
    """Fail-closed action-envelope or authority error."""


class RuptureByteIdentityError(RuntimeError):
    """The fixed provider object did not match its receipted byte identity."""


def _require_canonical_authority() -> None:
    exact = (
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset id"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project id"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (RELEASE_TAG, _CANONICAL_RELEASE_TAG, "release tag"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit sha"),
        (EVENT_ID, _CANONICAL_EVENT_ID, "event id"),
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "byte count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "sha256"),
        (EXPECTED_NRML_NAMESPACE, _CANONICAL_EXPECTED_NRML_NAMESPACE, "NRML namespace"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceRuptureProfileActionError(f"canonical {label} drifted")
    if (
        type(INPUTS) is not tuple
        or len(INPUTS) != 3
        or INPUTS[0]
        != (
            _CANONICAL_ROLE,
            _CANONICAL_REPOSITORY_PATH,
            _CANONICAL_GIT_BLOB_SHA1,
        )
    ):
        raise GreeceRuptureProfileActionError("canonical rupture input set drifted")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GreeceRuptureProfileActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise GreeceRuptureProfileActionError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceRuptureProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceRuptureProfileActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise GreeceRuptureProfileActionError("text is not UTF-8 encodable") from exc


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_canonical_authority()
    if type(expected_issue) is not int or expected_issue != _CANONICAL_SOURCE_ISSUE:
        raise GreeceRuptureProfileActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureProfileActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise GreeceRuptureProfileActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceRuptureProfileActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceRuptureProfileActionError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", _CANONICAL_SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("receipt_sha256", _CANONICAL_EXPECTED_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceRuptureProfileActionError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise GreeceRuptureProfileActionError("invalid requester")
    return request


def _identity() -> dict[str, Any]:
    return {
        "project_id": _CANONICAL_PROJECT_ID,
        "project_path": _CANONICAL_PROJECT_PATH,
        "release_tag": _CANONICAL_RELEASE_TAG,
        "commit_sha": _CANONICAL_COMMIT_SHA,
        "event_id": _CANONICAL_EVENT_ID,
        "role": _CANONICAL_ROLE,
        "repository_path": _CANONICAL_REPOSITORY_PATH,
        "git_blob_sha1": _CANONICAL_GIT_BLOB_SHA1,
        "receipt_byte_count": _CANONICAL_EXPECTED_BYTE_COUNT,
        "receipt_sha256": _CANONICAL_EXPECTED_SHA256,
    }


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": _CANONICAL_SOURCE_ISSUE,
        "dataset_id": _CANONICAL_DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "rupture_identity": _identity(),
        "status": "blocked",
        "failure_class": "profile_failure",
        "failure_code": None,
        "receipt": None,
        "profile": None,
        "provider_file_bytes_read": False,
        "provider_file_content_profiled": False,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_optional_header(value: object, *, field: str) -> None:
    if value is None:
        return
    if type(value) is not str or _utf8_size(value) > 1024:
        raise GreeceRuptureProfileActionError(f"invalid receipt {field}")


def _validate_receipt(receipt: object) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _RECEIPT_FIELDS:
        raise GreeceRuptureProfileActionError("receipt fields drifted")
    if (
        type(receipt.get("retrieved_at")) is not str
        or _UTC_RE.fullmatch(receipt["retrieved_at"]) is None
    ):
        raise GreeceRuptureProfileActionError("receipt timestamp drifted")
    if receipt.get("byte_count") != _CANONICAL_EXPECTED_BYTE_COUNT:
        raise GreeceRuptureProfileActionError("receipt byte count drifted")
    if receipt.get("sha256") != _CANONICAL_EXPECTED_SHA256:
        raise GreeceRuptureProfileActionError("receipt sha256 drifted")
    if receipt.get("git_blob_sha1") != _CANONICAL_GIT_BLOB_SHA1:
        raise GreeceRuptureProfileActionError("receipt Git blob identity drifted")
    _validate_optional_header(receipt.get("content_type"), field="content type")
    _validate_optional_header(receipt.get("etag"), field="etag")
    return receipt


def _validate_profile(profile: object) -> dict[str, Any]:
    if type(profile) is not dict or set(profile) != _PROFILE_FIELDS:
        raise GreeceRuptureProfileActionError("profile fields drifted")
    exact = (
        ("schema_version", "oc-esrm20-scenario-v10-greece-rupture-profile-v1"),
        ("byte_count", _CANONICAL_EXPECTED_BYTE_COUNT),
        ("sha256", _CANONICAL_EXPECTED_SHA256),
        ("nrml_namespace", _CANONICAL_EXPECTED_NRML_NAMESPACE),
        ("provider_file_content_profiled", True),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if profile.get(field) != expected:
            raise GreeceRuptureProfileActionError(f"profile {field} drifted")
    rupture_kind = profile.get("rupture_element_local_name")
    if (
        type(rupture_kind) is not str
        or rupture_kind not in OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS
    ):
        raise GreeceRuptureProfileActionError("profile rupture kind drifted")
    for field in (
        "element_count",
        "max_depth",
        "magnitude_element_count",
        "rake_element_count",
        "hypocenter_element_count",
    ):
        value = profile.get(field)
        if type(value) is not int or value < 0:
            raise GreeceRuptureProfileActionError(f"profile {field} invalid")
    if not (2 <= profile["element_count"] <= 64):
        raise GreeceRuptureProfileActionError("profile element count out of bounds")
    if not (2 <= profile["max_depth"] <= 12):
        raise GreeceRuptureProfileActionError("profile depth out of bounds")
    for field in (
        "magnitude_element_count",
        "rake_element_count",
        "hypocenter_element_count",
    ):
        if profile[field] > profile["element_count"]:
            raise GreeceRuptureProfileActionError(f"profile {field} out of bounds")
    return profile


def _validate_terminal_result(result: object) -> str:
    _require_canonical_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise GreeceRuptureProfileActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureProfileActionError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _CANONICAL_SOURCE_ISSUE),
        ("dataset_id", _CANONICAL_DATASET_ID),
        ("target_sha", execution_sha),
        ("rupture_identity", _identity()),
        ("output_payload_bytes_read", False),
        ("external_bytes_persisted", False),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise GreeceRuptureProfileActionError(f"result {field} drifted")
    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("failure_code") is not None
            or result.get("provider_file_bytes_read") is not True
            or result.get("provider_file_content_profiled") is not True
        ):
            raise GreeceRuptureProfileActionError("invalid PASS state")
        _validate_receipt(result.get("receipt"))
        _validate_profile(result.get("profile"))
    elif status == "blocked":
        failure_class = result.get("failure_class")
        if failure_class not in {
            "acquisition_failure",
            "byte_identity_mismatch",
            "profile_failure",
        }:
            raise GreeceRuptureProfileActionError("invalid blocked failure class")
        if result.get("receipt") is not None or result.get("profile") is not None:
            raise GreeceRuptureProfileActionError("blocked result widened evidence")
        if result.get("provider_file_content_profiled") is not False:
            raise GreeceRuptureProfileActionError("blocked result profiled content")
        expected_bytes_read = failure_class != "acquisition_failure"
        if result.get("provider_file_bytes_read") is not expected_bytes_read:
            raise GreeceRuptureProfileActionError("blocked byte-read state drifted")
        if failure_class == "profile_failure":
            if result.get("failure_code") != "rupture_profile_rejected":
                raise GreeceRuptureProfileActionError("invalid profile failure code")
        elif result.get("failure_code") is not None:
            raise GreeceRuptureProfileActionError("non-profile failure carries code")
    else:
        raise GreeceRuptureProfileActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if (
        _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES
        or body.count(RESULT_MARKER) != 1
    ):
        raise GreeceRuptureProfileActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceRuptureProfileActionError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    kwargs: dict[str, Any] = {
        "issue": _CANONICAL_SOURCE_ISSUE,
        "max_pages": MAX_LEDGER_PAGES,
    }
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceRuptureProfileActionError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        terminal_sha = parse_terminal_result(comment.get("body"))
        if terminal_sha == execution_sha:
            found = True
    return found


def _acquire_fixed_rupture(
    *,
    opener: Any | None = None,
    now: Callable[[], str] = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
) -> tuple[bytes, dict[str, Any]]:
    _require_canonical_authority()
    url = _raw_file_url(_CANONICAL_REPOSITORY_PATH)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml,text/xml;q=0.9,application/octet-stream;q=0.5",
            "User-Agent": "OpenCatastrophe-EFEHR-greece-rupture-profile-v1",
        },
        method="GET",
    )
    open_response = opener or _open_fixed
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    try:
        with open_response(
            request,
            timeout=_remaining(deadline, monotonic),
        ) as response:
            _validate_exact_response(response, url)
            retrieved_at = now()
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=_CANONICAL_MAX_RUPTURE_BYTES,
                monotonic=monotonic,
            )
            content_type = _bounded_header(response, "Content-Type")
            etag = _bounded_header(response, "ETag")
    except EfehrAcquisitionError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise EfehrAcquisitionError(
            f"EFEHR Greece rupture retrieval failed: {type(exc).__name__}"
        ) from exc

    if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
        raise GreeceRuptureProfileActionError("invalid retrieval timestamp")
    if (
        len(raw) != _CANONICAL_EXPECTED_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest() != _CANONICAL_EXPECTED_SHA256
        or _git_blob_sha1(raw) != _CANONICAL_GIT_BLOB_SHA1
    ):
        raise RuptureByteIdentityError("fixed rupture byte identity mismatch")
    receipt = {
        "retrieved_at": retrieved_at,
        "byte_count": len(raw),
        "sha256": _CANONICAL_EXPECTED_SHA256,
        "git_blob_sha1": _CANONICAL_GIT_BLOB_SHA1,
        "content_type": content_type,
        "etag": etag,
    }
    _validate_receipt(receipt)
    return raw, receipt


def _run_profile_with(
    *,
    execution_sha: str,
    fetcher: Callable[[], tuple[bytes, dict[str, Any]]],
    profiler: Callable[[bytes], dict[str, object]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureProfileActionError("invalid execution SHA")
    _require_canonical_authority()
    result = _base_result(execution_sha)
    try:
        raw, receipt = fetcher()
    except RuptureByteIdentityError:
        result["failure_class"] = "byte_identity_mismatch"
        result["provider_file_bytes_read"] = True
    except EfehrAcquisitionError:
        result["failure_class"] = "acquisition_failure"
    else:
        _validate_receipt(receipt)
        result["provider_file_bytes_read"] = True
        try:
            profile = profiler(raw)
        except RuptureProfileError:
            result["failure_class"] = "profile_failure"
            result["failure_code"] = "rupture_profile_rejected"
        else:
            _validate_profile(profile)
            result.update(
                {
                    "status": "pass",
                    "failure_class": None,
                    "failure_code": None,
                    "receipt": receipt,
                    "profile": profile,
                    "provider_file_content_profiled": True,
                }
            )
    _validate_terminal_result(result)
    return result


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    return _run_profile_with(
        execution_sha=execution_sha,
        fetcher=_acquire_fixed_rupture,
        profiler=profile_fixed_greece_rupture,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        raise GreeceRuptureProfileActionError("output path is required")
    result = run_profile(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
