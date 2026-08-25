# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main execution for the exact three Greece exposure CSV profiles.

The three provider objects are already byte-receipted by trusted-main #285
terminal 5397480571 and are bound by the merged receipt-first profiler from
#724. This module adds only a closed execution bridge: fixed provider/project/
commit/paths, issue-local trusted-terminal dedup, exact-byte verification before
CSV interpretation, and a bounded structural result.

Provider bytes remain in memory only and are never returned or persisted. A
PASS establishes receipt-bound CSV structure only. It does not designate a
taxonomy column or values, CRS, replacement-cost semantics, vulnerability/IMT
selection, benchmark agreement, independent validation/holdout, publication,
or model-use authority.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):  # pragma: no cover - direct script execution
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import acquire_efehr_esrm20_greece_exposure_csv_receipts as receipts
from scripts import profile_efehr_esrm20_greece_exposure_csvs as profile
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

SOURCE_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-csv-profiles-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-exposure-csv-profiles-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-exposure-csv-profiles-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-greece-exposure-csv-profiles-result-v1"
ACTION = "esrm20_greece_exposure_three_csv_content_profile"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 8_000
MAX_RESULT_UTF8_BYTES = 60_000
MAX_COMMENT_PAGES = 20

_CANONICAL_PROVIDER_HOST = "gitlab.seismo.ethz.ch"
_CANONICAL_PROVIDER_ROOT = "https://gitlab.seismo.ethz.ch"
_CANONICAL_OPEN_FIXED = receipts._open_fixed
_CANONICAL_MONOTONIC = time.monotonic
_CANONICAL_PROFILE_FUNCTION = profile.profile_verified_bundle

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}


class GreeceExposureCsvProfileActionError(RuntimeError):
    """Base fail-closed error for the trusted Greece 3CSV profile action."""


class GreeceExposureCsvProfileAcquisitionError(GreeceExposureCsvProfileActionError):
    """The frozen provider objects could not all be acquired."""


class GreeceExposureCsvProfileContentError(GreeceExposureCsvProfileActionError):
    """The exact bytes or bounded content profile failed closed."""


class GreeceExposureCsvProfileContractError(GreeceExposureCsvProfileActionError):
    """Frozen authority, request, ledger, or result contract drifted."""


def _canonical_receipts() -> tuple[tuple[str, int, str], ...]:
    return (
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


def _require_contract() -> None:
    exact = (
        (PROVIDER_HOST, _CANONICAL_PROVIDER_HOST, "provider host"),
        (PROVIDER_ROOT, _CANONICAL_PROVIDER_ROOT, "provider root"),
        (SOURCE_ISSUE, 285, "source issue"),
        (PARENT_CONSUMER_ISSUE, 287, "parent consumer issue"),
        (profile.SOURCE_ISSUE, 285, "profile source issue"),
        (profile.PARENT_CONSUMER_ISSUE, 287, "profile parent consumer"),
        (profile.DATASET_ID, "efehr.esrm20.risk-inputs.v1.0", "dataset id"),
        (profile.PROJECT_ID, 269, "project id"),
        (profile.PROJECT_PATH, "efehr/esrm20", "project path"),
        (profile.RELEASE_TAG, "v1.0", "release tag"),
        (
            profile.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
            "commit sha",
        ),
        (profile.CONSUMER_EVENT_ID, "Greece_07-9-1999", "consumer event"),
        (
            profile.PARENT_EXPOSURE_PATH,
            "Exposure/OQ_Exposure_Input_Greece.xml",
            "parent exposure path",
        ),
        (profile.RECEIPT_COMMENT_ID, 5397480571, "receipt comment"),
        (
            profile.RECEIPT_EXECUTION_SHA,
            "4b1d3c41a5df739b9686303eb753577ca39ec58e",
            "receipt execution sha",
        ),
        (profile.RECEIPTS, _canonical_receipts(), "receipt identities"),
        (receipts.SOURCE_ISSUE, profile.SOURCE_ISSUE, "receipt source issue"),
        (receipts.PARENT_CONSUMER_ISSUE, profile.PARENT_CONSUMER_ISSUE, "receipt parent"),
        (receipts.DATASET_ID, profile.DATASET_ID, "receipt dataset"),
        (receipts.PROJECT_ID, profile.PROJECT_ID, "receipt project id"),
        (receipts.PROJECT_PATH, profile.PROJECT_PATH, "receipt project path"),
        (receipts.RELEASE_TAG, profile.RELEASE_TAG, "receipt release"),
        (receipts.COMMIT_SHA, profile.COMMIT_SHA, "receipt commit"),
        (receipts.CONSUMER_EVENT_ID, profile.CONSUMER_EVENT_ID, "receipt event"),
        (
            receipts.PARENT_EXPOSURE_PATH,
            profile.PARENT_EXPOSURE_PATH,
            "receipt parent exposure path",
        ),
        (
            tuple(receipts.REPOSITORY_PATHS),
            tuple(path for path, _, _ in profile.RECEIPTS),
            "receipt repository paths",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvProfileContractError(
                f"Greece exposure 3CSV {label} authority drifted"
            )


def _require_production_identity() -> None:
    identities = (
        (receipts._open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
        (profile.profile_verified_bundle, _CANONICAL_PROFILE_FUNCTION, "merged profiler"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise GreeceExposureCsvProfileContractError(
                f"Greece exposure 3CSV production {label} drifted"
            )


def _bounded_json_text(value: str, *, maximum: int, label: str) -> str:
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise GreeceExposureCsvProfileContractError(
            f"{label} is not UTF-8 encodable"
        ) from exc
    if len(encoded) > maximum:
        raise GreeceExposureCsvProfileContractError(f"{label} is too large")
    return value


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GreeceExposureCsvProfileContractError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise GreeceExposureCsvProfileContractError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    _require_contract()
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise GreeceExposureCsvProfileContractError("wrong Greece exposure 3CSV issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceExposureCsvProfileContractError("invalid Greece exposure execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise GreeceExposureCsvProfileContractError("invalid Greece exposure request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    payload = after.strip()
    if before.strip() or not payload:
        raise GreeceExposureCsvProfileContractError(
            "Greece exposure request envelope is not canonical"
        )
    _bounded_json_text(
        payload,
        maximum=MAX_REQUEST_UTF8_BYTES,
        label="Greece exposure request JSON",
    )
    try:
        request = json.loads(
            payload,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceExposureCsvProfileContractError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureCsvProfileContractError(
            "invalid Greece exposure request JSON"
        ) from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceExposureCsvProfileContractError("Greece exposure request fields drifted")
    exact = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "action": ACTION,
        "issue": SOURCE_ISSUE,
        "target_sha": execution_sha,
        "dataset_id": profile.DATASET_ID,
    }
    for field, expected in exact.items():
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvProfileContractError(
                f"Greece exposure request {field} drifted"
            )
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise GreeceExposureCsvProfileContractError("invalid requester identity")
    return request


def _validate_csv_profile(value: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "parser",
        "record_count",
        "header",
        "columns",
        "raw_rows_returned",
        "external_bytes_persisted",
        "publication_authorized",
    }
    if type(value) is not dict or set(value) != fields:
        raise GreeceExposureCsvProfileContractError("nested CSV profile fields drifted")
    if value["schema_version"] != profile.generic_csv.SCHEMA_VERSION:
        raise GreeceExposureCsvProfileContractError("nested CSV profile schema drifted")
    if value["raw_rows_returned"] is not False:
        raise GreeceExposureCsvProfileContractError("nested CSV profile leaked rows")
    if value["external_bytes_persisted"] is not False:
        raise GreeceExposureCsvProfileContractError("nested CSV profile persisted bytes")
    if value["publication_authorized"] is not False:
        raise GreeceExposureCsvProfileContractError("nested CSV profile widened publication")

    parser = value["parser"]
    if type(parser) is not dict or set(parser) != {
        "encoding",
        "bom_present",
        "delimiter",
        "line_endings",
    }:
        raise GreeceExposureCsvProfileContractError("nested CSV parser fields drifted")
    if parser["encoding"] not in {"utf-8", "utf-8-sig"}:
        raise GreeceExposureCsvProfileContractError("nested CSV encoding drifted")
    if type(parser["bom_present"]) is not bool:
        raise GreeceExposureCsvProfileContractError("nested CSV BOM flag drifted")
    if (parser["encoding"] == "utf-8-sig") is not parser["bom_present"]:
        raise GreeceExposureCsvProfileContractError("nested CSV BOM/encoding mismatch")
    if parser["delimiter"] != profile.generic_csv.DELIMITER:
        raise GreeceExposureCsvProfileContractError("nested CSV delimiter drifted")
    line_endings = parser["line_endings"]
    if type(line_endings) is not dict or set(line_endings) != {
        "crlf_count",
        "lf_count",
        "cr_count",
    }:
        raise GreeceExposureCsvProfileContractError("nested CSV line endings drifted")
    for count in line_endings.values():
        if type(count) is not int or isinstance(count, bool) or count < 0:
            raise GreeceExposureCsvProfileContractError("nested CSV line-ending count invalid")

    record_count = value["record_count"]
    if type(record_count) is not int or isinstance(record_count, bool) or record_count < 1:
        raise GreeceExposureCsvProfileContractError("nested CSV record count invalid")
    header = value["header"]
    if (
        type(header) is not list
        or not (profile.generic_csv.MIN_COLUMNS <= len(header) <= profile.generic_csv.MAX_COLUMNS)
        or len(set(header)) != len(header)
    ):
        raise GreeceExposureCsvProfileContractError("nested CSV header invalid")
    for name in header:
        if (
            type(name) is not str
            or not name
            or len(name.encode("utf-8")) > profile.generic_csv.MAX_HEADER_UTF8_BYTES
            or any(ord(character) < 32 or ord(character) == 127 for character in name)
        ):
            raise GreeceExposureCsvProfileContractError("nested CSV header token invalid")

    columns = value["columns"]
    if type(columns) is not list or len(columns) != len(header):
        raise GreeceExposureCsvProfileContractError("nested CSV columns/header drifted")
    for index, column in enumerate(columns):
        if type(column) is not dict or set(column) != {
            "name",
            "record_count",
            "empty_count",
            "nonempty_count",
            "distinct_count",
            "exact_value_set_sha256",
            "decimal_summary",
        }:
            raise GreeceExposureCsvProfileContractError("nested CSV column fields drifted")
        if column["name"] != header[index] or column["record_count"] != record_count:
            raise GreeceExposureCsvProfileContractError("nested CSV column order/name drifted")
        empty_count = column["empty_count"]
        nonempty_count = column["nonempty_count"]
        distinct_count = column["distinct_count"]
        for count in (empty_count, nonempty_count, distinct_count):
            if type(count) is not int or isinstance(count, bool) or count < 0:
                raise GreeceExposureCsvProfileContractError("nested CSV column count invalid")
        if empty_count + nonempty_count != record_count:
            raise GreeceExposureCsvProfileContractError("nested CSV column counts do not conserve")
        if not (1 <= distinct_count <= record_count):
            raise GreeceExposureCsvProfileContractError("nested CSV distinct count invalid")
        digest = column["exact_value_set_sha256"]
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise GreeceExposureCsvProfileContractError("nested CSV value-set SHA-256 invalid")
        decimal = column["decimal_summary"]
        if type(decimal) is not dict or set(decimal) != {
            "all_nonempty_decimal",
            "finite_decimal_count",
            "leading_or_trailing_whitespace_count",
        }:
            raise GreeceExposureCsvProfileContractError("nested CSV decimal summary drifted")
        if type(decimal["all_nonempty_decimal"]) is not bool:
            raise GreeceExposureCsvProfileContractError("nested CSV decimal flag invalid")
        finite = decimal["finite_decimal_count"]
        whitespace = decimal["leading_or_trailing_whitespace_count"]
        for count in (finite, whitespace):
            if type(count) is not int or isinstance(count, bool) or count < 0:
                raise GreeceExposureCsvProfileContractError("nested CSV decimal count invalid")
        if finite > nonempty_count or whitespace > nonempty_count:
            raise GreeceExposureCsvProfileContractError("nested CSV decimal counts exceed nonempty")
        expected_all_decimal = nonempty_count > 0 and finite == nonempty_count
        if decimal["all_nonempty_decimal"] is not expected_all_decimal:
            raise GreeceExposureCsvProfileContractError("nested CSV decimal flag inconsistent")
    return value


def _validate_profile_bundle(value: object) -> dict[str, Any]:
    fields = {
        "schema_version",
        "source_issue",
        "parent_consumer_issue",
        "dataset_id",
        "project_id",
        "project_path",
        "release_tag",
        "commit_sha",
        "consumer_event_id",
        "parent_exposure_path",
        "receipt_comment_id",
        "receipt_execution_sha",
        "files",
        "provider_file_content_profiled",
        "content_semantics_verified",
        "crs_semantics_verified",
        "taxonomy_semantics_verified",
        "replacement_cost_semantics_verified",
        "benchmark_agreement_inspected",
        "independent_validation_established",
        "holdout_status_established",
        "raw_rows_returned",
        "exact_field_values_returned",
        "external_bytes_persisted",
        "publication_authorized",
        "model_use_authorized",
    }
    if type(value) is not dict or set(value) != fields:
        raise GreeceExposureCsvProfileContractError("Greece exposure bundle profile fields drifted")
    exact = {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": profile.SOURCE_ISSUE,
        "parent_consumer_issue": profile.PARENT_CONSUMER_ISSUE,
        "dataset_id": profile.DATASET_ID,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "release_tag": profile.RELEASE_TAG,
        "commit_sha": profile.COMMIT_SHA,
        "consumer_event_id": profile.CONSUMER_EVENT_ID,
        "parent_exposure_path": profile.PARENT_EXPOSURE_PATH,
        "receipt_comment_id": profile.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": profile.RECEIPT_EXECUTION_SHA,
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
    for field, expected in exact.items():
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvProfileContractError(
                f"Greece exposure bundle profile drifted at {field}"
            )
    files = value["files"]
    if type(files) is not list or len(files) != 3:
        raise GreeceExposureCsvProfileContractError("Greece exposure profile file count drifted")
    for item, (path, byte_count, sha256) in zip(files, profile.RECEIPTS, strict=True):
        if type(item) is not dict or set(item) != {
            "repository_path",
            "byte_count",
            "sha256",
            "profile",
        }:
            raise GreeceExposureCsvProfileContractError("Greece exposure file profile fields drifted")
        for field, expected in (
            ("repository_path", path),
            ("byte_count", byte_count),
            ("sha256", sha256),
        ):
            observed = item[field]
            if type(observed) is not type(expected) or observed != expected:
                raise GreeceExposureCsvProfileContractError(
                    f"Greece exposure file profile drifted at {field}"
                )
        _validate_csv_profile(item["profile"])
    return value


def _acquire_and_profile_for_test(
    *,
    opener: Any,
    monotonic: Callable[[], float],
    profiler: Callable[[dict[str, bytes]], dict[str, Any]],
) -> dict[str, Any]:
    _require_contract()
    deadline = monotonic() + receipts._CANONICAL_TOTAL_DEADLINE_SECONDS
    raw_by_path: dict[str, bytes] = {}
    try:
        for repository_path, expected_byte_count, _ in profile.RECEIPTS:
            url = receipts._raw_file_url(repository_path)
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "text/csv,text/plain;q=0.9,application/octet-stream;q=0.7",
                    "User-Agent": "OpenCatastrophe-EFEHR-Greece-exposure-3CSV-profile-v1",
                },
                method="GET",
            )
            with opener(
                request,
                timeout=receipts._remaining(deadline, monotonic),
            ) as response:
                receipts._validate_exact_response(response, url)
                raw_by_path[repository_path] = receipts._read_bounded(
                    response,
                    deadline=deadline,
                    maximum=expected_byte_count,
                    monotonic=monotonic,
                )
    except (
        EfehrAcquisitionError,
        http.client.HTTPException,
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ) as exc:
        raise GreeceExposureCsvProfileAcquisitionError(
            "fixed Greece exposure 3CSV acquisition failed"
        ) from exc

    try:
        return _validate_profile_bundle(profiler(raw_by_path))
    except profile.GreeceExposureCsvProfileError as exc:
        raise GreeceExposureCsvProfileContentError(
            "verified Greece exposure CSV bytes failed profiling"
        ) from exc


def acquire_and_profile() -> dict[str, Any]:
    """Run the fixed production acquisition and merged profile composition."""
    _require_contract()
    _require_production_identity()
    return _acquire_and_profile_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
        profiler=_CANONICAL_PROFILE_FUNCTION,
    )


_ACQUIRE = acquire_and_profile


def _identity() -> dict[str, Any]:
    return {
        "provider_host": PROVIDER_HOST,
        "project_id": profile.PROJECT_ID,
        "project_path": profile.PROJECT_PATH,
        "release_tag": profile.RELEASE_TAG,
        "commit_sha": profile.COMMIT_SHA,
        "consumer_event_id": profile.CONSUMER_EVENT_ID,
        "parent_exposure_path": profile.PARENT_EXPOSURE_PATH,
        "receipt_comment_id": profile.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": profile.RECEIPT_EXECUTION_SHA,
        "files": [
            {
                "repository_path": path,
                "byte_count": byte_count,
                "sha256": sha256,
            }
            for path, byte_count, sha256 in profile.RECEIPTS
        ],
    }


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": profile.DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "exposure_identity": _identity(),
        "content_semantics_verified": False,
        "crs_semantics_verified": False,
        "taxonomy_semantics_verified": False,
        "replacement_cost_semantics_verified": False,
        "vulnerability_imt_selection_verified": False,
        "benchmark_agreement_inspected": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(value: object, *, execution_sha: str) -> dict[str, Any]:
    base = _base_result(execution_sha=execution_sha)
    fields = set(base) | {
        "status",
        "failure_class",
        "profile",
        "provider_file_bytes_read",
        "provider_file_content_profiled",
        "byte_identity_verified",
    }
    if type(value) is not dict or set(value) != fields:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result fields drifted")
    for field, expected in base.items():
        observed = value[field]
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceExposureCsvProfileContractError(
                f"trusted Greece exposure result drifted at {field}"
            )
    if value["status"] == "pass":
        if (
            value["failure_class"] is not None
            or value["provider_file_bytes_read"] is not True
            or value["provider_file_content_profiled"] is not True
            or value["byte_identity_verified"] is not True
        ):
            raise GreeceExposureCsvProfileContractError("Greece exposure PASS state drifted")
        _validate_profile_bundle(value["profile"])
    elif value["status"] == "blocked":
        failure = value["failure_class"]
        if failure not in {"acquisition_failure", "profile_failure"}:
            raise GreeceExposureCsvProfileContractError("Greece exposure BLOCKED class drifted")
        if (
            value["profile"] is not None
            or value["provider_file_content_profiled"] is not False
            or value["byte_identity_verified"] is not False
        ):
            raise GreeceExposureCsvProfileContractError("Greece exposure BLOCKED state widened evidence")
        if failure == "acquisition_failure":
            if value["provider_file_bytes_read"] is not None:
                raise GreeceExposureCsvProfileContractError("acquisition failure overclaims byte reads")
        elif value["provider_file_bytes_read"] is not True:
            raise GreeceExposureCsvProfileContractError("profile failure lost complete byte-read state")
    else:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result is not terminal")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    _bounded_json_text(encoded, maximum=MAX_RESULT_UTF8_BYTES, label="trusted Greece exposure result")
    return value


def _parse_terminal(body: object, *, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    payload = after.strip()
    if before.strip() or not payload:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result envelope is malformed")
    _bounded_json_text(payload, maximum=MAX_RESULT_UTF8_BYTES, label="trusted Greece exposure result JSON")
    try:
        result = json.loads(payload, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except GreeceExposureCsvProfileContractError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result JSON is malformed") from exc
    if type(result) is not dict:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result is not an object")
    result_sha = result.get("execution_sha")
    if type(result_sha) is not str or _SHA1_RE.fullmatch(result_sha) is None:
        raise GreeceExposureCsvProfileContractError("trusted Greece exposure result SHA is invalid")
    _validate_terminal_result(result, execution_sha=result_sha)
    return result_sha == execution_sha


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None
) -> bool:
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": MAX_COMMENT_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceExposureCsvProfileContractError(
            "Greece exposure result ledger is incomplete"
        ) from exc
    matched = False
    for comment in comments:
        if type(comment) is not dict:
            raise GreeceExposureCsvProfileContractError("Greece exposure ledger contains non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login == TRUSTED_RESULT_LOGIN:
            matched = _parse_terminal(comment.get("body"), execution_sha=execution_sha) or matched
    return matched


def _run(
    *, execution_sha: str, acquirer: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        profiled = acquirer()
    except GreeceExposureCsvProfileAcquisitionError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "profile": None,
                "provider_file_bytes_read": None,
                "provider_file_content_profiled": False,
                "byte_identity_verified": False,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)
    except GreeceExposureCsvProfileContentError:
        result.update(
            {
                "status": "blocked",
                "failure_class": "profile_failure",
                "profile": None,
                "provider_file_bytes_read": True,
                "provider_file_content_profiled": False,
                "byte_identity_verified": False,
            }
        )
        return _validate_terminal_result(result, execution_sha=execution_sha)

    profiled = _validate_profile_bundle(profiled)
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "profile": profiled,
            "provider_file_bytes_read": True,
            "provider_file_content_profiled": True,
            "byte_identity_verified": True,
        }
    )
    return _validate_terminal_result(result, execution_sha=execution_sha)


def run(*, execution_sha: str) -> dict[str, Any]:
    return _run(execution_sha=execution_sha, acquirer=_ACQUIRE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")

    result = run(execution_sha=args.execution_sha)
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    _bounded_json_text(encoded, maximum=MAX_RESULT_UTF8_BYTES, label="Greece exposure result")
    Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
