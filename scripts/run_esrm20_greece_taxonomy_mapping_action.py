# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main execution for the frozen Greece taxonomy mapping join.

The action acquires only four immutable ESRM20 v1.0 project-269 objects: the
three already-receipted Greece runtime exposure CSVs and the already-receipted
exposure-to-vulnerability mapping. Provider bytes remain in memory and are
passed to the existing receipt-first exact-literal join worker.

A passing result is component-compatibility evidence only. It does not assign
GEM taxonomy meaning, select vulnerability files or IMTs, establish hazard or
loss compatibility, authorize redistribution, or authorize model use.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from scripts import acquire_efehr_gitlab_receipt as transport
from scripts import join_esrm20_greece_taxonomy_mapping as join
from scripts import join_esrm20_kosovo_taxonomy_mapping as exact_join
from scripts import profile_efehr_esrm20_greece_exposure_csvs as exposure_source
from scripts.efehr_gitlab_receipt import PROVIDER_HOST, PROVIDER_ROOT
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-greece-taxonomy-mapping-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-greece-taxonomy-mapping-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-greece-taxonomy-mapping-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-greece-taxonomy-mapping-result-v1"
ACTION = "esrm20_greece_taxonomy_mapping"
CONTROL_ISSUE = 285
PARENT_CONSUMER_ISSUE = 287
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_TERMINAL_UTF8_BYTES = 55_000
TOTAL_DEADLINE_SECONDS = 60.0

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_FALSE_FIELDS = (
    "taxonomy_semantics_verified",
    "vulnerability_file_selection_authorized",
    "vulnerability_imt_selection_verified",
    "hazard_compatibility_verified",
    "ground_up_loss_executed",
    "benchmark_agreement_inspected",
    "independent_validation_established",
    "holdout_status_established",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)
_DERIVED_PRIVATE_FIELDS = (
    "classification_counts",
    "taxonomy_union_count",
    "all_taxonomies_resolved",
    "mapping_target_risk_ids",
)

# path, trusted byte count, trusted SHA-256
_CANONICAL_TARGETS = tuple(exposure_source.RECEIPTS) + (
    (
        exact_join._MAPPING_REPOSITORY_PATH,
        exact_join._MAPPING_BYTE_COUNT,
        exact_join._MAPPING_SHA256,
    ),
)
_CANONICAL_OPEN_FIXED = transport._open_fixed
_CANONICAL_REMAINING = transport._remaining
_CANONICAL_VALIDATE_EXACT_RESPONSE = transport._validate_exact_response
_CANONICAL_READ_BOUNDED = transport._read_bounded
_CANONICAL_REQUEST = urllib.request.Request
_CANONICAL_QUOTE = urllib.parse.quote
_CANONICAL_SHA256 = hashlib.sha256
_CANONICAL_MONOTONIC = time.monotonic


class GreeceTaxonomyMappingActionError(RuntimeError):
    """Fail-closed trusted action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GreeceTaxonomyMappingActionError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise GreeceTaxonomyMappingActionError(f"non-finite JSON constant: {value}")


def _load_json(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceTaxonomyMappingActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceTaxonomyMappingActionError(f"invalid {label} JSON") from exc


def _require_frozen_authority() -> None:
    if PROVIDER_HOST != "gitlab.seismo.ethz.ch":
        raise GreeceTaxonomyMappingActionError("EFEHR provider host authority drifted")
    if PROVIDER_ROOT != "https://gitlab.seismo.ethz.ch":
        raise GreeceTaxonomyMappingActionError("EFEHR provider root authority drifted")
    exact = (
        (exposure_source.DATASET_ID, DATASET_ID, "exposure dataset"),
        (exposure_source.PROJECT_ID, PROJECT_ID, "exposure project"),
        (exposure_source.PROJECT_PATH, PROJECT_PATH, "exposure project path"),
        (exposure_source.COMMIT_SHA, COMMIT_SHA, "exposure commit"),
        (exact_join._MAPPING_DATASET_ID, DATASET_ID, "mapping dataset"),
        (exact_join._MAPPING_PROJECT_ID, PROJECT_ID, "mapping project"),
        (exact_join._MAPPING_PROJECT_PATH, PROJECT_PATH, "mapping project path"),
        (exact_join._MAPPING_COMMIT_SHA, COMMIT_SHA, "mapping commit"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceTaxonomyMappingActionError(f"frozen {label} authority drifted")
    expected_targets = tuple(exposure_source.RECEIPTS) + (
        (
            exact_join._MAPPING_REPOSITORY_PATH,
            exact_join._MAPPING_BYTE_COUNT,
            exact_join._MAPPING_SHA256,
        ),
    )
    if _CANONICAL_TARGETS != expected_targets or len(_CANONICAL_TARGETS) != 4:
        raise GreeceTaxonomyMappingActionError("frozen taxonomy input set drifted")
    if len({path for path, _, _ in _CANONICAL_TARGETS}) != 4:
        raise GreeceTaxonomyMappingActionError("frozen taxonomy input paths are not unique")
    for path, byte_count, sha256 in _CANONICAL_TARGETS:
        if type(path) is not str or not path or path.startswith("/") or ".." in path.split("/"):
            raise GreeceTaxonomyMappingActionError("invalid frozen taxonomy input path")
        if type(byte_count) is not int or isinstance(byte_count, bool) or byte_count < 1:
            raise GreeceTaxonomyMappingActionError("invalid frozen taxonomy input byte count")
        if type(sha256) is not str or _DIGEST_RE.fullmatch(sha256) is None:
            raise GreeceTaxonomyMappingActionError("invalid frozen taxonomy input digest")


def _require_production_transport_identity() -> None:
    identities = (
        (transport._open_fixed, _CANONICAL_OPEN_FIXED, "transport"),
        (transport._remaining, _CANONICAL_REMAINING, "deadline helper"),
        (
            transport._validate_exact_response,
            _CANONICAL_VALIDATE_EXACT_RESPONSE,
            "response validator",
        ),
        (transport._read_bounded, _CANONICAL_READ_BOUNDED, "response reader"),
        (urllib.request.Request, _CANONICAL_REQUEST, "request builder"),
        (urllib.parse.quote, _CANONICAL_QUOTE, "URL encoder"),
        (hashlib.sha256, _CANONICAL_SHA256, "SHA-256 hasher"),
        (time.monotonic, _CANONICAL_MONOTONIC, "monotonic clock"),
    )
    for observed, expected, label in identities:
        if observed is not expected:
            raise GreeceTaxonomyMappingActionError(
                f"frozen Greece taxonomy production {label} drifted"
            )


def _raw_file_url(repository_path: str) -> str:
    _require_frozen_authority()
    if repository_path not in {path for path, _, _ in _CANONICAL_TARGETS}:
        raise GreeceTaxonomyMappingActionError("taxonomy input path left frozen set")
    path = _CANONICAL_QUOTE(repository_path, safe="")
    commit = _CANONICAL_QUOTE(COMMIT_SHA, safe="")
    return (
        f"{PROVIDER_ROOT}/api/v4/projects/{PROJECT_ID}/repository/files/"
        f"{path}/raw?ref={commit}"
    )


def _acquire_inputs_for_test(*, opener: Any, monotonic: Any) -> dict[str, bytes]:
    _require_frozen_authority()
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    inputs: dict[str, bytes] = {}
    for repository_path, expected_byte_count, expected_sha256 in _CANONICAL_TARGETS:
        url = _raw_file_url(repository_path)
        request = _CANONICAL_REQUEST(
            url,
            headers={
                "Accept": "text/csv,application/octet-stream;q=0.5",
                "User-Agent": "OpenCatastrophe-EFEHR-Greece-taxonomy-mapping-v1",
            },
            method="GET",
        )
        try:
            with opener(
                request,
                timeout=_CANONICAL_REMAINING(deadline, monotonic),
            ) as response:
                _CANONICAL_VALIDATE_EXACT_RESPONSE(response, url)
                raw = _CANONICAL_READ_BOUNDED(
                    response,
                    deadline=deadline,
                    maximum=expected_byte_count,
                    monotonic=monotonic,
                )
        except (GreeceTaxonomyMappingActionError, transport.EfehrAcquisitionError):
            raise
        except (
            OSError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            http.client.HTTPException,
        ) as exc:
            raise transport.EfehrAcquisitionError(
                f"EFEHR Greece taxonomy input retrieval failed: {type(exc).__name__}"
            ) from exc
        if len(raw) != expected_byte_count:
            raise transport.EfehrAcquisitionError(
                "Greece taxonomy input byte count does not match trusted receipt"
            )
        if _CANONICAL_SHA256(raw).hexdigest() != expected_sha256:
            raise transport.EfehrAcquisitionError(
                "Greece taxonomy input SHA-256 does not match trusted receipt"
            )
        inputs[repository_path] = raw
    return inputs


def acquire_inputs() -> dict[str, bytes]:
    _require_frozen_authority()
    _require_production_transport_identity()
    return _acquire_inputs_for_test(
        opener=_CANONICAL_OPEN_FIXED,
        monotonic=_CANONICAL_MONOTONIC,
    )


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise GreeceTaxonomyMappingActionError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceTaxonomyMappingActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise GreeceTaxonomyMappingActionError("invalid Greece taxonomy request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceTaxonomyMappingActionError("Greece taxonomy request envelope is not canonical")
    request = _load_json(after.strip(), label="Greece taxonomy request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceTaxonomyMappingActionError("Greece taxonomy request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", CONTROL_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceTaxonomyMappingActionError(f"Greece taxonomy request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip():
        raise GreeceTaxonomyMappingActionError("invalid requester identity")
    if _SAFE_REQUESTER_RE.fullmatch(requester) is None:
        raise GreeceTaxonomyMappingActionError("invalid requester identity")
    return request


def _input_receipts() -> list[dict[str, Any]]:
    return [
        {"repository_path": path, "byte_count": byte_count, "sha256": sha256}
        for path, byte_count, sha256 in _CANONICAL_TARGETS
    ]


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "parent_consumer_issue": PARENT_CONSUMER_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "evidence_level": "component_compatibility",
        "input_receipts": _input_receipts(),
    }
    result.update({field: False for field in _FALSE_FIELDS})
    return result


def _validate_summary(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise GreeceTaxonomyMappingActionError("taxonomy mapping result is not an object")
    counts = result.get("classification_counts")
    if type(counts) is not dict or set(counts) != {"resolved", "unsupported", "ambiguous"}:
        raise GreeceTaxonomyMappingActionError("taxonomy mapping counts drifted")
    for value in counts.values():
        if type(value) is not int or isinstance(value, bool) or value < 0:
            raise GreeceTaxonomyMappingActionError("taxonomy mapping count is invalid")
    union_count = result.get("taxonomy_union_count")
    if type(union_count) is not int or isinstance(union_count, bool) or union_count < 1:
        raise GreeceTaxonomyMappingActionError("taxonomy union count is invalid")
    if sum(counts.values()) != union_count:
        raise GreeceTaxonomyMappingActionError("taxonomy mapping counts are not exhaustive")
    all_resolved = result.get("all_taxonomies_resolved")
    expected_all_resolved = counts["unsupported"] == 0 and counts["ambiguous"] == 0
    if type(all_resolved) is not bool or all_resolved is not expected_all_resolved:
        raise GreeceTaxonomyMappingActionError("all-taxonomies-resolved flag drifted")
    risk_ids = result.get("mapping_target_risk_ids")
    if type(risk_ids) is not list or risk_ids != sorted(set(risk_ids)):
        raise GreeceTaxonomyMappingActionError("mapping target risk-id set drifted")
    for risk_id in risk_ids:
        if (
            not exact_join._is_bounded_literal(
                risk_id,
                max_utf8_bytes=exact_join.MAX_RISK_ID_UTF8_BYTES,
            )
            or risk_id != risk_id.strip()
        ):
            raise GreeceTaxonomyMappingActionError("mapping target risk-id is invalid")
    return {
        "classification_counts": counts,
        "taxonomy_union_count": union_count,
        "all_taxonomies_resolved": all_resolved,
        "mapping_target_risk_ids": risk_ids,
    }


def _parse_trusted_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    try:
        encoded = body.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise GreeceTaxonomyMappingActionError("trusted taxonomy result is not UTF-8 encodable") from exc
    if len(encoded) > MAX_TERMINAL_UTF8_BYTES:
        raise GreeceTaxonomyMappingActionError("trusted taxonomy result exceeds byte bound")
    if body.count(RESULT_MARKER) != 1:
        raise GreeceTaxonomyMappingActionError("trusted taxonomy result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceTaxonomyMappingActionError("trusted taxonomy result envelope is malformed")
    result = _load_json(after.strip(), label="trusted taxonomy result")
    if type(result) is not dict:
        raise GreeceTaxonomyMappingActionError("trusted taxonomy result is not an object")
    terminal_sha = result.get("execution_sha")
    if type(terminal_sha) is not str or _SHA_RE.fullmatch(terminal_sha) is None:
        raise GreeceTaxonomyMappingActionError("trusted taxonomy execution SHA is malformed")
    base = _base_result(execution_sha=terminal_sha)
    expected_fields = set(base) | {"status", "failure_class", "component_compatibility_established"}
    if set(result) != expected_fields:
        raise GreeceTaxonomyMappingActionError("trusted taxonomy result fields drifted")
    for field, expected in base.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceTaxonomyMappingActionError(f"trusted taxonomy result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise GreeceTaxonomyMappingActionError("trusted taxonomy pass result has failure class")
        if result.get("component_compatibility_established") is not True:
            raise GreeceTaxonomyMappingActionError("trusted taxonomy pass result lacks compatibility gate")
        return terminal_sha
    if status == "blocked":
        if result.get("failure_class") not in {
            "acquisition_failure",
            "component_compatibility_failure",
        }:
            raise GreeceTaxonomyMappingActionError("trusted taxonomy blocked failure class drifted")
        if result.get("component_compatibility_established") is not False:
            raise GreeceTaxonomyMappingActionError("trusted taxonomy blocked result widened evidence")
        return terminal_sha
    raise GreeceTaxonomyMappingActionError("trusted taxonomy result has non-terminal status")


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceTaxonomyMappingActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise GreeceTaxonomyMappingActionError("taxonomy result ledger is incomplete") from exc
    match_seen = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        terminal_sha = _parse_trusted_terminal_result(comment.get("body"))
        if terminal_sha == execution_sha:
            match_seen = True
    return match_seen


def _blocked_result(
    result: dict[str, Any],
    *,
    failure_class: str,
) -> dict[str, Any]:
    result.update(
        {
            "status": "blocked",
            "failure_class": failure_class,
            "component_compatibility_established": False,
        }
    )
    return result


def run_mapping(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise GreeceTaxonomyMappingActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        raw_by_path = acquire_inputs()
    except (transport.EfehrAcquisitionError, GreeceTaxonomyMappingActionError):
        return _blocked_result(result, failure_class="acquisition_failure")

    mapping_path = exact_join._MAPPING_REPOSITORY_PATH
    mapping_raw = raw_by_path.pop(mapping_path, None)
    if mapping_raw is None:
        raise GreeceTaxonomyMappingActionError("trusted mapping input disappeared after acquisition")
    try:
        joined = join.join_verified_greece_taxonomy_mapping(raw_by_path, mapping_raw)
        summary = _validate_summary(joined)
    except (join.GreeceTaxonomyMappingJoinError, GreeceTaxonomyMappingActionError):
        return _blocked_result(result, failure_class="component_compatibility_failure")

    if summary["all_taxonomies_resolved"] is not True:
        return _blocked_result(result, failure_class="component_compatibility_failure")

    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "component_compatibility_established": True,
        }
    )
    for field in _DERIVED_PRIVATE_FIELDS:
        if field in result:
            raise GreeceTaxonomyMappingActionError("derived taxonomy detail entered durable result")
    return result


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
    result = run_mapping(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
