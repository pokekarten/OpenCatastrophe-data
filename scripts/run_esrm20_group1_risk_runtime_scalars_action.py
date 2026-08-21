# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for exact Group1 risk-runtime scalar evidence."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import acquire_esrm20_ebrisk_risk_config_dependencies as worker
from scripts import project_esrm20_group1_risk_runtime_scalars as projector
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

REQUEST_MARKER = "<!-- oc-eq1-esrm20-group1-risk-runtime-scalars-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-group1-risk-runtime-scalars-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-group1-risk-runtime-scalars-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-group1-risk-runtime-scalars-result-v1"
ACTION = "esrm20_group1_risk_runtime_scalars"
CONTROL_ISSUE = 287
DATASET_ID = projector.DATASET_ID
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 32_000
MAX_TEXT_UTF8_BYTES = 2048
MAX_SEED_SETTINGS = 3

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version", "action", "issue", "target_sha", "dataset_id", "requester"
}
_RESULT_FIELDS = {
    "schema_version", "action", "source_issue", "dataset_id", "target_sha",
    "execution_sha", "status", "failure_class", "evidence", "raw_config_returned",
    "historical_group_assignment_verified", "runtime_compatibility_verified",
    "numerical_loss_reproduction_verified", "external_bytes_persisted",
    "publication_authorized", "model_use_authorized"
}
_EVIDENCE_FIELDS = {
    "schema_version", "control_issue", "source_issue", "dataset_id", "project_id",
    "project_path", "commit_sha", "candidate_key", "repository_path", "byte_count",
    "sha256", "receipt_comment_id", "openquake_reference", "runtime_scalars",
    "raw_config_returned", "historical_group_assignment_verified",
    "runtime_compatibility_verified", "numerical_loss_reproduction_verified",
    "external_bytes_persisted", "publication_authorized", "model_use_authorized"
}
_RUNTIME_FIELDS = {
    "calculation_mode", "calculation_mode_present", "configured_seed_settings",
    "seed_setting_present", "ignore_master_seed", "ignore_master_seed_present",
    "minimum_asset_loss_structural", "minimum_asset_loss_structural_present",
    "defaults_inferred", "vulnerability_sampling_seed_semantics_verified"
}
_SEED_FIELDS = {"key", "purpose", "section", "value"}
_OPENQUAKE_FIELDS = {"repository", "tag", "commit_sha"}

_CANONICAL_FETCH_COMMENTS = fetch_repository_comments
_CANONICAL_ACQUIRE_PAYLOAD = worker._CANONICAL_ACQUIRE_EXACT_PAYLOAD  # noqa: SLF001
_CANONICAL_OPEN_FIXED = worker._CANONICAL_OPEN_FIXED  # noqa: SLF001
_CANONICAL_MONOTONIC = worker._CANONICAL_MONOTONIC  # noqa: SLF001
_CANONICAL_REQUIRE_WORKER_IDENTITY = worker._require_production_identity  # noqa: SLF001
_CANONICAL_PROJECT = projector.project_group1_risk_runtime_scalars
_CANONICAL_GROUP1_SPEC = projector.GROUP1_SPEC
_CANONICAL_FIXED_AUTHORITY = (
    projector.SCHEMA_VERSION,
    projector.CONTROL_ISSUE,
    projector.SOURCE_ISSUE,
    projector.DATASET_ID,
    projector.PROJECT_ID,
    projector.PROJECT_PATH,
    projector.COMMIT_SHA,
    projector.GROUP1_KEY,
    projector.GROUP1_SPEC.repository_path,
    projector.GROUP1_SPEC.byte_count,
    projector.GROUP1_SPEC.sha256,
    projector.OPENQUAKE_REPOSITORY,
    projector.OPENQUAKE_TAG,
    projector.OPENQUAKE_COMMIT,
)


class Group1RuntimeScalarsActionError(RuntimeError):
    """Raised when trusted Group1 scalar evidence cannot be established safely."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Group1RuntimeScalarsActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise Group1RuntimeScalarsActionError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise Group1RuntimeScalarsActionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except Group1RuntimeScalarsActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise Group1RuntimeScalarsActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str, *, label: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise Group1RuntimeScalarsActionError(f"{label} is not UTF-8 encodable") from exc


def _bounded_text(value: object, *, label: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise Group1RuntimeScalarsActionError(f"{label} must be non-empty trimmed text")
    if len(value.encode("utf-8")) > MAX_TEXT_UTF8_BYTES:
        raise Group1RuntimeScalarsActionError(f"{label} exceeds bounded text policy")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Group1RuntimeScalarsActionError(f"{label} contains control characters")
    return value


def _require_production_authority() -> None:
    if fetch_repository_comments is not _CANONICAL_FETCH_COMMENTS:
        raise Group1RuntimeScalarsActionError("trusted ledger authority drifted")
    if worker._CANONICAL_ACQUIRE_EXACT_PAYLOAD is not _CANONICAL_ACQUIRE_PAYLOAD:  # noqa: SLF001
        raise Group1RuntimeScalarsActionError("trusted Group1 byte acquisition authority drifted")
    if worker._CANONICAL_OPEN_FIXED is not _CANONICAL_OPEN_FIXED:  # noqa: SLF001
        raise Group1RuntimeScalarsActionError("trusted Group1 transport authority drifted")
    if worker._CANONICAL_MONOTONIC is not _CANONICAL_MONOTONIC:  # noqa: SLF001
        raise Group1RuntimeScalarsActionError("trusted Group1 clock authority drifted")
    if worker._require_production_identity is not _CANONICAL_REQUIRE_WORKER_IDENTITY:  # noqa: SLF001
        raise Group1RuntimeScalarsActionError("trusted Group1 worker identity gate drifted")
    if projector.project_group1_risk_runtime_scalars is not _CANONICAL_PROJECT:
        raise Group1RuntimeScalarsActionError("trusted Group1 projector authority drifted")
    if projector.GROUP1_SPEC is not _CANONICAL_GROUP1_SPEC:
        raise Group1RuntimeScalarsActionError("trusted Group1 config spec object drifted")
    observed = (
        projector.SCHEMA_VERSION,
        projector.CONTROL_ISSUE,
        projector.SOURCE_ISSUE,
        projector.DATASET_ID,
        projector.PROJECT_ID,
        projector.PROJECT_PATH,
        projector.COMMIT_SHA,
        projector.GROUP1_KEY,
        projector.GROUP1_SPEC.repository_path,
        projector.GROUP1_SPEC.byte_count,
        projector.GROUP1_SPEC.sha256,
        projector.OPENQUAKE_REPOSITORY,
        projector.OPENQUAKE_TAG,
        projector.OPENQUAKE_COMMIT,
    )
    if observed != _CANONICAL_FIXED_AUTHORITY:
        raise Group1RuntimeScalarsActionError("trusted Group1 fixed authority drifted")
    try:
        _CANONICAL_REQUIRE_WORKER_IDENTITY()
    except worker.EbriskDependencyAcquisitionError as exc:
        raise Group1RuntimeScalarsActionError("trusted Group1 worker authority failed") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise Group1RuntimeScalarsActionError("wrong Group1 scalar issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group1RuntimeScalarsActionError("invalid execution SHA")
    if type(body) is not str:
        raise Group1RuntimeScalarsActionError("Group1 scalar request is not text")
    if _utf8_size(body, label="Group1 scalar request") > MAX_REQUEST_UTF8_BYTES:
        raise Group1RuntimeScalarsActionError("Group1 scalar request exceeds limit")
    if body.count(REQUEST_MARKER) != 1:
        raise Group1RuntimeScalarsActionError("invalid Group1 scalar request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise Group1RuntimeScalarsActionError("Group1 scalar request envelope is not canonical")
    request = _strict_loads(after.strip(), label="Group1 scalar request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise Group1RuntimeScalarsActionError("Group1 scalar request fields drifted")
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
            raise Group1RuntimeScalarsActionError(f"Group1 scalar request {field} drifted")
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise Group1RuntimeScalarsActionError("invalid requester identity")
    return request


def _validate_runtime_scalars(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _RUNTIME_FIELDS:
        raise Group1RuntimeScalarsActionError("runtime scalar fields drifted")
    for present_field in (
        "calculation_mode_present", "seed_setting_present", "ignore_master_seed_present",
        "minimum_asset_loss_structural_present", "defaults_inferred",
        "vulnerability_sampling_seed_semantics_verified",
    ):
        if type(value.get(present_field)) is not bool:
            raise Group1RuntimeScalarsActionError(f"runtime scalar {present_field} is not boolean")
    if value["defaults_inferred"] is not False or value["vulnerability_sampling_seed_semantics_verified"] is not False:
        raise Group1RuntimeScalarsActionError("runtime scalar authority widened")

    mode = value.get("calculation_mode")
    if value["calculation_mode_present"]:
        if type(mode) is not str or mode not in projector._CALCULATION_MODES:  # noqa: SLF001
            raise Group1RuntimeScalarsActionError("runtime calculation mode is invalid")
    elif mode is not None:
        raise Group1RuntimeScalarsActionError("absent calculation mode carries a value")

    seeds = value.get("configured_seed_settings")
    if type(seeds) is not list or len(seeds) > MAX_SEED_SETTINGS:
        raise Group1RuntimeScalarsActionError("runtime seed settings exceed bounded policy")
    if value["seed_setting_present"] is not bool(seeds):
        raise Group1RuntimeScalarsActionError("runtime seed presence flag drifted")
    seen: set[str] = set()
    for row in seeds:
        if type(row) is not dict or set(row) != _SEED_FIELDS:
            raise Group1RuntimeScalarsActionError("runtime seed row shape drifted")
        key = row.get("key")
        if type(key) is not str or key not in projector._SEED_PURPOSES or key in seen:  # noqa: SLF001
            raise Group1RuntimeScalarsActionError("runtime seed key is invalid")
        seen.add(key)
        if row.get("purpose") != projector._SEED_PURPOSES[key]:  # noqa: SLF001
            raise Group1RuntimeScalarsActionError("runtime seed purpose drifted")
        _bounded_text(row.get("section"), label="runtime seed section")
        seed_value = row.get("value")
        if type(seed_value) is not int or isinstance(seed_value, bool) or seed_value < 0:
            raise Group1RuntimeScalarsActionError("runtime seed value is invalid")

    ignore = value.get("ignore_master_seed")
    if value["ignore_master_seed_present"]:
        if type(ignore) is not bool:
            raise Group1RuntimeScalarsActionError("ignore_master_seed is invalid")
    elif ignore is not None:
        raise Group1RuntimeScalarsActionError("absent ignore_master_seed carries a value")

    minimum = value.get("minimum_asset_loss_structural")
    if value["minimum_asset_loss_structural_present"]:
        if type(minimum) is not str or not minimum or len(minimum.encode("utf-8")) > 128:
            raise Group1RuntimeScalarsActionError("minimum_asset_loss_structural is invalid")
    elif minimum is not None:
        raise Group1RuntimeScalarsActionError("absent minimum asset loss carries a value")
    return value


def validate_evidence(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _EVIDENCE_FIELDS:
        raise Group1RuntimeScalarsActionError("Group1 scalar evidence fields drifted")
    exact = (
        ("schema_version", _CANONICAL_FIXED_AUTHORITY[0]),
        ("control_issue", _CANONICAL_FIXED_AUTHORITY[1]),
        ("source_issue", _CANONICAL_FIXED_AUTHORITY[2]),
        ("dataset_id", _CANONICAL_FIXED_AUTHORITY[3]),
        ("project_id", _CANONICAL_FIXED_AUTHORITY[4]),
        ("project_path", _CANONICAL_FIXED_AUTHORITY[5]),
        ("commit_sha", _CANONICAL_FIXED_AUTHORITY[6]),
        ("candidate_key", _CANONICAL_FIXED_AUTHORITY[7]),
        ("repository_path", _CANONICAL_FIXED_AUTHORITY[8]),
        ("byte_count", _CANONICAL_FIXED_AUTHORITY[9]),
        ("sha256", _CANONICAL_FIXED_AUTHORITY[10]),
        ("receipt_comment_id", projector.risk_config.RECEIPT_COMMENT_ID),
        ("raw_config_returned", False),
        ("historical_group_assignment_verified", False),
        ("runtime_compatibility_verified", False),
        ("numerical_loss_reproduction_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Group1RuntimeScalarsActionError(f"Group1 scalar evidence drifted at {field}")
    if _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise Group1RuntimeScalarsActionError("Group1 scalar evidence SHA-256 is invalid")
    oq = value.get("openquake_reference")
    if type(oq) is not dict or set(oq) != _OPENQUAKE_FIELDS:
        raise Group1RuntimeScalarsActionError("OpenQuake reference shape drifted")
    expected_oq = {
        "repository": _CANONICAL_FIXED_AUTHORITY[11],
        "tag": _CANONICAL_FIXED_AUTHORITY[12],
        "commit_sha": _CANONICAL_FIXED_AUTHORITY[13],
    }
    if oq != expected_oq:
        raise Group1RuntimeScalarsActionError("OpenQuake reference drifted")
    _validate_runtime_scalars(value.get("runtime_scalars"))
    return value


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_terminal_result(result: object, *, execution_sha: str) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise Group1RuntimeScalarsActionError("trusted Group1 scalar result fields drifted")
    for field, expected in _base_result(execution_sha=execution_sha).items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise Group1RuntimeScalarsActionError(f"trusted Group1 scalar result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise Group1RuntimeScalarsActionError("PASS result carries failure_class")
        validate_evidence(result.get("evidence"))
        return result
    if status == "blocked":
        if result.get("failure_class") != "projection_failure" or result.get("evidence") is not None:
            raise Group1RuntimeScalarsActionError("blocked result widened or leaked evidence")
        return result
    raise Group1RuntimeScalarsActionError("trusted Group1 scalar result has non-terminal status")


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body, label="Group1 scalar result") > MAX_TERMINAL_UTF8_BYTES:
        raise Group1RuntimeScalarsActionError("trusted Group1 scalar result exceeds limit")
    if body.count(RESULT_MARKER) != 1:
        raise Group1RuntimeScalarsActionError("trusted Group1 scalar result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise Group1RuntimeScalarsActionError("trusted Group1 scalar result envelope is malformed")
    result = _strict_loads(after.strip(), label="Group1 scalar result")
    execution_sha = result.get("execution_sha") if type(result) is dict else None
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group1RuntimeScalarsActionError("trusted Group1 scalar result SHA is invalid")
    validate_terminal_result(result, execution_sha=execution_sha)
    return execution_sha


def has_terminal_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None,
    max_pages: int = MAX_LEDGER_PAGES,
) -> bool:
    _require_production_authority()
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise Group1RuntimeScalarsActionError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": CONTROL_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise Group1RuntimeScalarsActionError("Group1 scalar ledger is incomplete") from exc
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


def _execute_with(
    *, execution_sha: str, acquire_payload: Callable[[], bytes], project: Callable[[bytes], dict[str, Any]]
) -> dict[str, Any]:
    result = _base_result(execution_sha=execution_sha)
    try:
        payload = acquire_payload()
        if type(payload) is not bytes:
            raise Group1RuntimeScalarsActionError("trusted Group1 acquisition returned non-bytes")
        evidence = validate_evidence(project(payload))
    except (worker.EbriskDependencyAcquisitionError, projector.RiskRuntimeScalarError, Group1RuntimeScalarsActionError):
        result.update({"status": "blocked", "failure_class": "projection_failure", "evidence": None})
        return result
    result.update({"status": "pass", "failure_class": None, "evidence": evidence})
    validate_terminal_result(result, execution_sha=execution_sha)
    return result


def run_projection(*, execution_sha: str) -> dict[str, Any]:
    _require_production_authority()

    def acquire() -> bytes:
        return _CANONICAL_ACQUIRE_PAYLOAD(
            "group1", opener=_CANONICAL_OPEN_FIXED, monotonic=_CANONICAL_MONOTONIC
        )

    return _execute_with(execution_sha=execution_sha, acquire_payload=acquire, project=_CANONICAL_PROJECT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", required=True, type=int)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-request-only", action="store_true")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        if args.output is not None:
            parser.error("--output is not valid with --validate-request-only")
        return 0
    if args.output is None:
        parser.error("--output is required unless --validate-request-only is used")
    result = run_projection(execution_sha=args.execution_sha)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
