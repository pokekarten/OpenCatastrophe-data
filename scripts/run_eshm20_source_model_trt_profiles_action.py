# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main composition for exact ESHM20 source-model TRT evidence.

The pure profiler in ``profile_eshm20_source_model_trt`` deliberately leaves
the canonical #414 ledger binding false.  This action closes only that missing
composition layer:

1. read the one frozen github-actions result that receipted the exact 51
   project-197 source-model objects;
2. validate the receipt-set identity and every per-object byte identity;
3. reacquire only those immutable objects from the fixed provider commit;
4. feed the verified bytes into the already-reviewed pure aggregate profiler;
5. publish only aggregate source-type/TRT/provenance counts.

Provider bytes are never written to disk or returned.  This action does not
establish source physics, source/GSIM compatibility, branch-weight validity,
numerical hazard reproduction, publication authority, or model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts import profile_eshm20_source_model_trt as profiler
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-eshm20-source-model-trt-profiles-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-eshm20-source-model-trt-profiles-result-v1 -->"
ACTION_RESULT_MARKER = "<!-- oc-action-result-v1 -->"

REQUEST_SCHEMA_VERSION = "oc-eshm20-source-model-trt-profiles-request-v1"
RESULT_SCHEMA_VERSION = "oc-eshm20-source-model-trt-profiles-result-v1"
ACTION = "eshm20_source_model_trt_profiles"
REPOSITORY = "pokekarten/OpenCatastrophe-data"
SOURCE_ISSUE = 281
CONSUMER_ISSUE = 287
RECEIPT_ISSUE = 414
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
PROVIDER_HOST = "gitlab.seismo.ethz.ch"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
RECEIPT_RESULT_COMMENT_ID = 5306897047
RECEIPT_RESULT_RUN_ID = 31940875325
RECEIPT_RESULT_EXECUTION_SHA = "473f03765fd63d2da7e48d0c22b1618d4e1254d8"
CHILD_PARENT_RESULT_COMMENT_ID = 5304432768
EXPECTED_CHILD_COUNT = 51
EXPECTED_PATHS_SHA256 = "2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

MAX_TOTAL_PROVIDER_BYTES = 64 * 1024 * 1024
TOTAL_DEADLINE_SECONDS = 300.0
MAX_LEDGER_PAGES = 20
MAX_RESULT_UTF8_BYTES = 64_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_RECEIPT_FIELDS = {
    "byte_count",
    "commit_sha",
    "external_bytes_persisted",
    "model_use_authorized",
    "parent_result_comment_id",
    "project_id",
    "project_path",
    "publication_authorized",
    "repository_path",
    "retrieved_at",
    "sha256",
}
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "consumer_issue",
    "receipt_issue",
    "target_sha",
    "execution_sha",
    "dataset_id",
    "status",
    "failure_class",
    "aggregate_profile",
    "provider_file_bytes_read",
    "raw_xml_returned",
    "canonical_414_ledger_binding_verified",
    "source_gsim_trt_compatibility_verified",
    "numerical_hazard_reproduction_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}

_FIXED_AGGREGATE = profiler.aggregate_source_model_profiles
_FIXED_RECEIPT_CLASS = profiler.ExpectedChildReceipt
_FIXED_OPEN = transport._open_fixed
_FIXED_VALIDATE_RESPONSE = transport._validate_exact_response
_FIXED_DECLARED_LENGTH = transport._declared_length
_FIXED_SET_RESPONSE_TIMEOUT = transport._set_response_timeout
_FIXED_READ_BOUNDED = transport._read_bounded
_FIXED_REMAINING = transport._remaining
_FIXED_FETCH_COMMENTS = fetch_repository_comments
_FIXED_MONOTONIC = time.monotonic


class Eshm20SourceModelTrtActionError(RuntimeError):
    """Fail-closed error for the exact-51 trusted-main TRT composition."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Eshm20SourceModelTrtActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise Eshm20SourceModelTrtActionError(f"non-finite JSON constant: {value}")


def _strict_json(text: object, *, label: str) -> dict[str, Any]:
    if type(text) is not str or not text:
        raise Eshm20SourceModelTrtActionError(f"{label} JSON text is absent")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except Eshm20SourceModelTrtActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Eshm20SourceModelTrtActionError(
            f"{label} JSON is malformed"
        ) from exc
    if type(value) is not dict:
        raise Eshm20SourceModelTrtActionError(f"{label} JSON must be an object")
    return value


def _parse_marked_json(body: object, *, marker: str, label: str) -> dict[str, Any]:
    if type(body) is not str or body.count(marker) != 1:
        raise Eshm20SourceModelTrtActionError(f"{label} marker is malformed")
    before, after = body.split(marker, 1)
    if before.strip() or not after.strip():
        raise Eshm20SourceModelTrtActionError(f"{label} envelope is malformed")
    return _strict_json(after.strip(), label=label)


def _canonical_paths() -> tuple[str, ...]:
    try:
        paths = profiler._canonical_paths()
    except Exception as exc:
        raise Eshm20SourceModelTrtActionError(
            "pure TRT profiler canonical paths are unavailable"
        ) from exc
    if type(paths) is not tuple or len(paths) != EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelTrtActionError(
            "pure TRT profiler canonical path set drifted"
        )
    if any(type(path) is not str or not path for path in paths):
        raise Eshm20SourceModelTrtActionError(
            "pure TRT profiler canonical path is invalid"
        )
    fingerprint = hashlib.sha256(
        "".join(f"{path}\n" for path in paths).encode("utf-8")
    ).hexdigest()
    if fingerprint != EXPECTED_PATHS_SHA256:
        raise Eshm20SourceModelTrtActionError(
            "pure TRT profiler canonical path fingerprint drifted"
        )
    return paths


def _assert_fixed_contract() -> None:
    exact = (
        ("dataset", profiler.DATASET_ID, DATASET_ID),
        ("project id", profiler.PROJECT_ID, PROJECT_ID),
        ("project path", profiler.PROJECT_PATH, PROJECT_PATH),
        ("provider commit", profiler.COMMIT_SHA, COMMIT_SHA),
        (
            "receipt result comment",
            profiler.RECEIPT_SET_RESULT_COMMENT_ID,
            RECEIPT_RESULT_COMMENT_ID,
        ),
        ("receipt run", profiler.RECEIPT_SET_RUN_ID, RECEIPT_RESULT_RUN_ID),
        (
            "receipt execution",
            profiler.RECEIPT_SET_EXECUTION_SHA,
            RECEIPT_RESULT_EXECUTION_SHA,
        ),
        (
            "child parent result",
            profiler.CHILD_PARENT_RESULT_COMMENT_ID,
            CHILD_PARENT_RESULT_COMMENT_ID,
        ),
        ("child count", profiler.RECEIPT_SET_CHILD_COUNT, EXPECTED_CHILD_COUNT),
        (
            "path fingerprint",
            profiler.RECEIPT_SET_PATHS_SHA256,
            EXPECTED_PATHS_SHA256,
        ),
        ("provider host", transport.PROVIDER_HOST, PROVIDER_HOST),
    )
    for label, observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"frozen exact-51 authority drifted at {label}"
            )
    identities = (
        (profiler.aggregate_source_model_profiles, _FIXED_AGGREGATE, "aggregate profiler"),
        (profiler.ExpectedChildReceipt, _FIXED_RECEIPT_CLASS, "receipt class"),
        (transport._open_fixed, _FIXED_OPEN, "provider transport"),
        (transport._validate_exact_response, _FIXED_VALIDATE_RESPONSE, "response validator"),
        (transport._declared_length, _FIXED_DECLARED_LENGTH, "length validator"),
        (transport._set_response_timeout, _FIXED_SET_RESPONSE_TIMEOUT, "timeout setter"),
        (transport._read_bounded, _FIXED_READ_BOUNDED, "bounded reader"),
        (transport._remaining, _FIXED_REMAINING, "deadline helper"),
        (fetch_repository_comments, _FIXED_FETCH_COMMENTS, "GitHub ledger reader"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise Eshm20SourceModelTrtActionError(
                f"frozen exact-51 production {label} drifted"
            )
    _canonical_paths()


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise Eshm20SourceModelTrtActionError("wrong exact-51 TRT issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Eshm20SourceModelTrtActionError("invalid execution SHA")
    request = _parse_marked_json(
        body,
        marker=REQUEST_MARKER,
        label="exact-51 TRT request",
    )
    if set(request) != _REQUEST_FIELDS:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 TRT request fields drifted"
        )
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"exact-51 TRT request drifted at {field}"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Eshm20SourceModelTrtActionError(
            "invalid exact-51 TRT requester"
        )
    return request


def _validate_receipt_item(
    value: object,
    *,
    canonical_paths: set[str],
) -> profiler.ExpectedChildReceipt:
    if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt fields drifted"
        )
    exact = (
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("parent_result_comment_id", CHILD_PARENT_RESULT_COMMENT_ID),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"canonical #414 receipt drifted at {field}"
            )
    path = value["repository_path"]
    if type(path) is not str or path not in canonical_paths:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt path is outside exact 51"
        )
    count = value["byte_count"]
    if (
        type(count) is not int
        or isinstance(count, bool)
        or not (1 <= count <= profiler.MAX_ARTIFACT_BYTES)
    ):
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt byte count is invalid"
        )
    sha256 = value["sha256"]
    if type(sha256) is not str or _SHA256_RE.fullmatch(sha256) is None:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt SHA-256 is invalid"
        )
    retrieved_at = value["retrieved_at"]
    if type(retrieved_at) is not str or _UTC_RE.fullmatch(retrieved_at) is None:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt timestamp is invalid"
        )
    return profiler.ExpectedChildReceipt(
        repository_path=path,
        byte_count=count,
        sha256=sha256,
    )


def _parse_canonical_receipt_comment(
    comment: object,
) -> tuple[profiler.ExpectedChildReceipt, ...]:
    _assert_fixed_contract()
    if type(comment) is not dict or comment.get("id") != RECEIPT_RESULT_COMMENT_ID:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 result comment identity is absent"
        )
    user = comment.get("user")
    login = user.get("login") if type(user) is dict else None
    if login != TRUSTED_RESULT_LOGIN:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 result is not authored by trusted GitHub Actions"
        )
    result = _parse_marked_json(
        comment.get("body"),
        marker=ACTION_RESULT_MARKER,
        label="canonical #414 result",
    )
    exact = (
        ("schema_version", "oc-action-result-v1"),
        ("action", "efehr_eshm20_source_model_child_receipts"),
        ("dataset_id", DATASET_ID),
        ("execution_sha", RECEIPT_RESULT_EXECUTION_SHA),
        ("target_sha", RECEIPT_RESULT_EXECUTION_SHA),
        ("run_id", RECEIPT_RESULT_RUN_ID),
        ("source_issue", RECEIPT_ISSUE),
        ("repository", REPOSITORY),
        ("status", "pass"),
        ("failure_class", None),
        ("external_bytes_persisted", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"canonical #414 action result drifted at {field}"
            )

    evidence = result.get("evidence")
    if type(evidence) is not dict:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 evidence is absent"
        )
    if evidence.get("ledger_scan_complete") is not True:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 ledger scan is not complete"
        )
    if evidence.get("request_validated") is not True:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 request was not validated"
        )
    lane = evidence.get("efehr_eshm20_source_model_child_receipts")
    if type(lane) is not dict:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt-set evidence is absent"
        )
    lane_exact = (
        ("schema_version", "oc-eshm20-source-model-child-receipt-set-v1"),
        ("operation_id", "eshm20-source-model-child-receipts-v12e-region-main-v1"),
        ("source_issue", SOURCE_ISSUE),
        ("control_issue", RECEIPT_ISSUE),
        ("dataset_id", DATASET_ID),
        ("provider_host", PROVIDER_HOST),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("child_count", EXPECTED_CHILD_COUNT),
        ("child_paths_sha256", EXPECTED_PATHS_SHA256),
        ("dependency_inventory_authorized", False),
        ("dependency_receipt_authorized", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in lane_exact:
        observed = lane.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"canonical #414 receipt set drifted at {field}"
            )

    receipts = lane.get("receipts")
    if type(receipts) is not list or len(receipts) != EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt list count drifted"
        )
    canonical = _canonical_paths()
    canonical_set = set(canonical)
    parsed: dict[str, profiler.ExpectedChildReceipt] = {}
    total_bytes = 0
    for item in receipts:
        receipt = _validate_receipt_item(
            item,
            canonical_paths=canonical_set,
        )
        if receipt.repository_path in parsed:
            raise Eshm20SourceModelTrtActionError(
                "canonical #414 receipt path is duplicated"
            )
        parsed[receipt.repository_path] = receipt
        total_bytes += receipt.byte_count
        if total_bytes > MAX_TOTAL_PROVIDER_BYTES:
            raise Eshm20SourceModelTrtActionError(
                "canonical #414 receipt bytes exceed aggregate policy"
            )
    if set(parsed) != canonical_set:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt set does not cover exact 51 paths"
        )
    return tuple(parsed[path] for path in canonical)


def _load_canonical_receipts(
    *,
    repository: str,
    token: str,
) -> tuple[profiler.ExpectedChildReceipt, ...]:
    if repository != REPOSITORY:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 action repository is not canonical"
        )
    try:
        comments = _FIXED_FETCH_COMMENTS(
            repository,
            token,
            issue=RECEIPT_ISSUE,
            max_pages=MAX_LEDGER_PAGES,
        )
    except LedgerError as exc:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 receipt ledger is incomplete"
        ) from exc
    matches = [
        comment
        for comment in comments
        if type(comment) is dict and comment.get("id") == RECEIPT_RESULT_COMMENT_ID
    ]
    if len(matches) != 1:
        raise Eshm20SourceModelTrtActionError(
            "canonical #414 result comment is not uniquely present"
        )
    return _parse_canonical_receipt_comment(matches[0])


def _raw_url(path: str) -> str:
    if path not in set(_canonical_paths()):
        raise Eshm20SourceModelTrtActionError(
            "provider path is outside exact 51"
        )
    encoded_path = urllib.parse.quote(path, safe="")
    encoded_ref = urllib.parse.quote(COMMIT_SHA, safe="")
    return (
        f"{transport.PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{encoded_path}/raw?ref={encoded_ref}"
    )


def _fetch_verified_payload(
    receipt: profiler.ExpectedChildReceipt,
    *,
    deadline: float,
    opener: Any,
    monotonic: Any,
) -> bytes:
    url = _raw_url(receipt.repository_path)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml",
            "User-Agent": "OpenCatastrophe-ESHM20-exact51-TRT-v1",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=_FIXED_REMAINING(deadline, monotonic)) as response:
            _FIXED_VALIDATE_RESPONSE(response, url)
            declared = _FIXED_DECLARED_LENGTH(response, receipt.byte_count)
            if declared is not None and declared != receipt.byte_count:
                raise Eshm20SourceModelTrtActionError(
                    "provider Content-Length disagrees with canonical #414 receipt"
                )
            _FIXED_SET_RESPONSE_TIMEOUT(
                response,
                _FIXED_REMAINING(deadline, monotonic),
            )
            payload = _FIXED_READ_BOUNDED(
                response,
                deadline=deadline,
                maximum=receipt.byte_count,
                monotonic=monotonic,
            )
    except (Eshm20SourceModelTrtActionError, transport.EfehrAcquisitionError):
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 source-model acquisition failed"
        ) from exc

    if len(payload) != receipt.byte_count:
        raise Eshm20SourceModelTrtActionError(
            "provider bytes disagree with canonical #414 byte count"
        )
    if hashlib.sha256(payload).hexdigest() != receipt.sha256:
        raise Eshm20SourceModelTrtActionError(
            "provider bytes disagree with canonical #414 SHA-256"
        )
    return payload


def _verified_pairs(
    receipts: Iterable[profiler.ExpectedChildReceipt],
    *,
    opener: Any,
    monotonic: Any,
) -> Iterable[tuple[bytes, profiler.ExpectedChildReceipt]]:
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    for receipt in receipts:
        yield (
            _fetch_verified_payload(
                receipt,
                deadline=deadline,
                opener=opener,
                monotonic=monotonic,
            ),
            receipt,
        )


def _validate_bound_aggregate(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 aggregate profile is invalid"
        )
    exact = (
        ("schema_version", profiler.AGGREGATE_SCHEMA_VERSION),
        ("source_issue", SOURCE_ISSUE),
        ("control_issue", 435),
        ("dataset_id", DATASET_ID),
        ("child_count", EXPECTED_CHILD_COUNT),
        ("child_paths_sha256", EXPECTED_PATHS_SHA256),
        ("receipt_payload_identities_verified", True),
        ("canonical_414_ledger_binding_verified", True),
        ("source_structure_profile_verified", True),
        ("source_physics_validity_verified", False),
        ("source_gsim_trt_compatibility_verified", False),
        ("branch_weight_validity_verified", False),
        ("numerical_hazard_reproduction_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"bound exact-51 aggregate drifted at {field}"
            )
    locator = value.get("receipt_set_locator")
    locator_exact = {
        "result_comment_id": RECEIPT_RESULT_COMMENT_ID,
        "run_id": RECEIPT_RESULT_RUN_ID,
        "execution_sha": RECEIPT_RESULT_EXECUTION_SHA,
        "provider_commit": COMMIT_SHA,
    }
    if type(locator) is not dict or locator != locator_exact:
        raise Eshm20SourceModelTrtActionError(
            "bound exact-51 receipt locator drifted"
        )
    source_count = value.get("source_count")
    if type(source_count) is not int or isinstance(source_count, bool) or source_count < 1:
        raise Eshm20SourceModelTrtActionError(
            "bound exact-51 source count is invalid"
        )
    maps = (
        value.get("source_type_counts"),
        value.get("tectonic_region_type_counts"),
        value.get("trt_provenance_counts"),
    )
    if any(type(item) is not dict or not item for item in maps):
        raise Eshm20SourceModelTrtActionError(
            "bound exact-51 aggregate count maps are invalid"
        )
    if any(
        type(count) is not int or isinstance(count, bool) or count < 1
        for item in maps
        for count in item.values()
    ):
        raise Eshm20SourceModelTrtActionError(
            "bound exact-51 aggregate count is invalid"
        )
    if any(sum(item.values()) != source_count for item in maps):
        raise Eshm20SourceModelTrtActionError(
            "bound exact-51 aggregate counts do not reconcile"
        )
    return value


def _acquire_bound_aggregate(
    receipts: tuple[profiler.ExpectedChildReceipt, ...],
    *,
    opener: Any,
    monotonic: Any,
    aggregate: Any,
) -> dict[str, Any]:
    if len(receipts) != EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 receipt tuple count drifted"
        )
    try:
        pure = aggregate(
            _verified_pairs(
                receipts,
                opener=opener,
                monotonic=monotonic,
            )
        )
    except profiler.Eshm20SourceModelTrtProfileError:
        raise
    except transport.EfehrAcquisitionError:
        raise
    except Eshm20SourceModelTrtActionError:
        raise
    except Exception as exc:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 aggregate profiler failed closed"
        ) from exc
    if (
        type(pure) is not dict
        or pure.get("canonical_414_ledger_binding_verified") is not False
    ):
        raise Eshm20SourceModelTrtActionError(
            "pure TRT profiler unexpectedly widened canonical ledger authority"
        )
    bound = dict(pure)
    bound["canonical_414_ledger_binding_verified"] = True
    return _validate_bound_aggregate(bound)


def acquire_bound_aggregate(
    *,
    repository: str,
    token: str,
) -> dict[str, Any]:
    _assert_fixed_contract()
    receipts = _load_canonical_receipts(repository=repository, token=token)
    return _acquire_bound_aggregate(
        receipts,
        opener=_FIXED_OPEN,
        monotonic=_FIXED_MONOTONIC,
        aggregate=_FIXED_AGGREGATE,
    )


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "consumer_issue": CONSUMER_ISSUE,
        "receipt_issue": RECEIPT_ISSUE,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "dataset_id": DATASET_ID,
        "source_gsim_trt_compatibility_verified": False,
        "numerical_hazard_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _parse_result_object(body: object) -> dict[str, Any] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    return _parse_marked_json(
        body,
        marker=RESULT_MARKER,
        label="exact-51 TRT result",
    )


def parse_terminal_result(body: object, *, execution_sha: str) -> bool:
    result = _parse_result_object(body)
    if result is None:
        return False
    if set(result) != _RESULT_FIELDS:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 TRT result fields drifted"
        )
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"exact-51 TRT result drifted at {field}"
            )
    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("provider_file_bytes_read") is not True
            or result.get("raw_xml_returned") is not False
            or result.get("canonical_414_ledger_binding_verified") is not True
        ):
            raise Eshm20SourceModelTrtActionError(
                "exact-51 TRT PASS authority fields are invalid"
            )
        _validate_bound_aggregate(result.get("aggregate_profile"))
        return True
    if status == "blocked":
        if (
            result.get("failure_class") != "source_model_trt_profile_failure"
            or result.get("aggregate_profile") is not None
            or result.get("provider_file_bytes_read") is not False
            or result.get("raw_xml_returned") is not False
            or result.get("canonical_414_ledger_binding_verified") is not False
        ):
            raise Eshm20SourceModelTrtActionError(
                "exact-51 TRT blocked result widened evidence"
            )
        return True
    if status == "duplicate":
        if (
            result.get("failure_class") is not None
            or result.get("aggregate_profile") is not None
            or result.get("provider_file_bytes_read") is not False
            or result.get("raw_xml_returned") is not False
            or result.get("canonical_414_ledger_binding_verified") is not False
        ):
            raise Eshm20SourceModelTrtActionError(
                "exact-51 TRT duplicate result carries evidence"
            )
        return True
    raise Eshm20SourceModelTrtActionError(
        "exact-51 TRT result has non-terminal status"
    )


def _result_execution_sha(body: object) -> str | None:
    result = _parse_result_object(body)
    if result is None:
        return None
    fixed = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("consumer_issue", CONSUMER_ISSUE),
        ("receipt_issue", RECEIPT_ISSUE),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in fixed:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtActionError(
                f"historical exact-51 TRT result drifted at {field}"
            )
    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if (
        type(target_sha) is not str
        or _SHA_RE.fullmatch(target_sha) is None
        or type(execution_sha) is not str
        or _SHA_RE.fullmatch(execution_sha) is None
        or target_sha != execution_sha
    ):
        raise Eshm20SourceModelTrtActionError(
            "historical exact-51 TRT SHA binding is malformed"
        )
    return execution_sha


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
) -> bool:
    if repository != REPOSITORY:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 action repository is not canonical"
        )
    try:
        comments = _FIXED_FETCH_COMMENTS(
            repository,
            token,
            issue=SOURCE_ISSUE,
            max_pages=MAX_LEDGER_PAGES,
        )
    except LedgerError as exc:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 TRT result ledger is incomplete"
        ) from exc
    for comment in comments:
        if type(comment) is not dict:
            raise Eshm20SourceModelTrtActionError(
                "exact-51 TRT result ledger contains non-object"
            )
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        own_sha = _result_execution_sha(comment.get("body"))
        if own_sha is None:
            continue
        if not parse_terminal_result(comment.get("body"), execution_sha=own_sha):
            continue
        if own_sha == execution_sha:
            return True
    return False


def execute(
    *,
    repository: str,
    token: str,
    execution_sha: str,
) -> dict[str, Any]:
    _assert_fixed_contract()
    if repository != REPOSITORY:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 action repository is not canonical"
        )
    if not token:
        raise Eshm20SourceModelTrtActionError(
            "GitHub ledger token is absent"
        )
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Eshm20SourceModelTrtActionError("invalid execution SHA")
    if has_terminal_result(
        repository=repository,
        token=token,
        execution_sha=execution_sha,
    ):
        result = {
            **_base_result(execution_sha=execution_sha),
            "status": "duplicate",
            "failure_class": None,
            "aggregate_profile": None,
            "provider_file_bytes_read": False,
            "raw_xml_returned": False,
            "canonical_414_ledger_binding_verified": False,
        }
    else:
        try:
            aggregate_profile = acquire_bound_aggregate(
                repository=repository,
                token=token,
            )
            result = {
                **_base_result(execution_sha=execution_sha),
                "status": "pass",
                "failure_class": None,
                "aggregate_profile": aggregate_profile,
                "provider_file_bytes_read": True,
                "raw_xml_returned": False,
                "canonical_414_ledger_binding_verified": True,
            }
        except (
            Eshm20SourceModelTrtActionError,
            profiler.Eshm20SourceModelTrtProfileError,
            transport.EfehrAcquisitionError,
        ):
            result = {
                **_base_result(execution_sha=execution_sha),
                "status": "blocked",
                "failure_class": "source_model_trt_profile_failure",
                "aggregate_profile": None,
                "provider_file_bytes_read": False,
                "raw_xml_returned": False,
                "canonical_414_ledger_binding_verified": False,
            }

    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_UTF8_BYTES:
        raise Eshm20SourceModelTrtActionError(
            "exact-51 TRT result exceeds publication limit"
        )
    parse_terminal_result(
        RESULT_MARKER + "\n" + encoded.decode("utf-8"),
        execution_sha=execution_sha,
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--token-env")
    parser.add_argument("--output")
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.repository or not args.token_env or not args.output:
        parser.error(
            "--repository, --token-env and --output are required for execution"
        )
    token = os.environ.get(args.token_env)
    if not token:
        raise Eshm20SourceModelTrtActionError(
            "GitHub ledger token is absent"
        )
    result = execute(
        repository=args.repository,
        token=token,
        execution_sha=args.execution_sha,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
