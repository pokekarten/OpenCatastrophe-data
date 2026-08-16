# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed validation contract for ESRM20 Group1/Group2 dependency profiles."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):  # pragma: no cover - direct script execution path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import acquire_esrm20_event_hazard_dependencies as worker
from scripts import openquake_config_dependencies as oqdeps
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
from scripts.acquire_efehr_gitlab_receipt import utc_now

REQUEST_MARKER = "<!-- oc-eq1-esrm20-event-hazard-dependency-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-event-hazard-dependency-profile-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-event-hazard-dependency-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-event-hazard-dependency-profile-result-v1"
CONTROL_ISSUE = 429
DATASET_ID = worker.bridge.DATASET_ID
ACTION_GROUP1 = "esrm20_event_hazard_group1_dependencies"
ACTION_GROUP2 = "esrm20_event_hazard_group2_dependencies"
ACTION_TO_GROUP = {ACTION_GROUP1: 1, ACTION_GROUP2: 2}
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_DEPENDENCIES = 128
MAX_TEXT_UTF8_BYTES = 2048
MAX_RESULT_UTF8_BYTES = 64_000

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_UTC_SECOND_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "control_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "group",
    "operation_id",
    "repository_path",
    "byte_count",
    "sha256",
    "receipt_comment_id",
    "parser",
    "dependencies",
    "dependency_inventory_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "profiled_at",
}
_DEPENDENCY_FIELDS = {"section", "option", "raw_path", "resolved_path"}
_RESULT_COMMON_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "status",
    "failure_class",
    "profile",
    "dependency_inventory_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}

_FETCH_COMMENTS = fetch_repository_comments
_ACQUIRE_GROUP1 = worker.acquire_event_hazard_group1_dependencies
_ACQUIRE_GROUP2 = worker.acquire_event_hazard_group2_dependencies
_NORMALIZE_REFERENCE = oqdeps.normalize_repository_reference
_UTC_NOW = utc_now


class EventHazardDependencyActionError(RuntimeError):
    """Fail-closed error for the dedicated trusted-main action."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EventHazardDependencyActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise EventHazardDependencyActionError(f"non-finite JSON constant: {value}")


def _canonical_utc(value: object, *, field: str) -> str:
    if type(value) is not str or _UTC_SECOND_RE.fullmatch(value) is None:
        raise EventHazardDependencyActionError(f"{field} must be canonical UTC seconds")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise EventHazardDependencyActionError(f"{field} is not a valid UTC timestamp") from exc
    return value


def _bounded_text(value: object, *, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise EventHazardDependencyActionError(f"{field} must be a non-empty trimmed string")
    if len(value.encode("utf-8")) > MAX_TEXT_UTF8_BYTES:
        raise EventHazardDependencyActionError(f"{field} exceeds bounded text policy")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise EventHazardDependencyActionError(f"{field} contains control characters")
    return value


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise EventHazardDependencyActionError("wrong event-hazard dependency issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise EventHazardDependencyActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise EventHazardDependencyActionError("invalid event-hazard dependency request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise EventHazardDependencyActionError("request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EventHazardDependencyActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EventHazardDependencyActionError("invalid request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise EventHazardDependencyActionError("request fields drifted")
    if request.get("schema_version") != REQUEST_SCHEMA_VERSION:
        raise EventHazardDependencyActionError("request schema version drifted")
    action = request.get("action")
    if type(action) is not str or action not in ACTION_TO_GROUP:
        raise EventHazardDependencyActionError("request action is not one of the two closed operations")
    if type(request.get("issue")) is not int or request["issue"] != CONTROL_ISSUE:
        raise EventHazardDependencyActionError("request issue drifted")
    if type(request.get("target_sha")) is not str or request["target_sha"] != execution_sha:
        raise EventHazardDependencyActionError("request target SHA must equal trusted execution SHA")
    if type(request.get("dataset_id")) is not str or request["dataset_id"] != DATASET_ID:
        raise EventHazardDependencyActionError("request dataset drifted")
    requester = request.get("requester")
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _SAFE_REQUESTER_RE.fullmatch(requester) is None
    ):
        raise EventHazardDependencyActionError("requester identity is invalid")
    return request


def _validate_dependency(value: object, *, config_path: str) -> dict[str, str]:
    if type(value) is not dict or set(value) != _DEPENDENCY_FIELDS:
        raise EventHazardDependencyActionError("dependency row shape drifted")
    section = _bounded_text(value.get("section"), field="dependency section")
    option = _bounded_text(value.get("option"), field="dependency option")
    raw_path = _bounded_text(value.get("raw_path"), field="dependency raw path")
    resolved_path = _bounded_text(value.get("resolved_path"), field="dependency resolved path")
    try:
        expected = _NORMALIZE_REFERENCE(config_path, raw_path)
    except oqdeps.OpenQuakeConfigError as exc:
        raise EventHazardDependencyActionError("dependency path fails reviewed normalization") from exc
    if resolved_path != expected:
        raise EventHazardDependencyActionError("dependency resolved path drifted")
    return {
        "section": section,
        "option": option,
        "raw_path": raw_path,
        "resolved_path": resolved_path,
    }


def validate_profile(value: object, *, action: str) -> dict[str, Any]:
    if oqdeps.normalize_repository_reference is not _NORMALIZE_REFERENCE:
        raise EventHazardDependencyActionError("trusted path-normalization authority drifted")
    if type(value) is not dict or set(value) != _PROFILE_FIELDS:
        raise EventHazardDependencyActionError("dependency profile fields drifted")
    if action not in ACTION_TO_GROUP:
        raise EventHazardDependencyActionError("profile action is outside closed operations")
    group = ACTION_TO_GROUP[action]
    spec = worker.bridge.ROOT_SPECS[group]
    exact = (
        ("schema_version", worker.bridge.SCHEMA_VERSION),
        ("source_issue", worker.bridge.SOURCE_ISSUE),
        ("control_issue", worker.bridge.CONTROL_ISSUE),
        ("dataset_id", DATASET_ID),
        ("project_id", worker.bridge.PROJECT_ID),
        ("project_path", worker.bridge.PROJECT_PATH),
        ("commit_sha", worker.bridge.COMMIT_SHA),
        ("group", group),
        ("operation_id", spec.operation_id),
        ("repository_path", spec.repository_path),
        ("byte_count", spec.byte_count),
        ("sha256", spec.sha256),
        ("receipt_comment_id", spec.receipt_comment_id),
        ("parser", worker.bridge.PARSER_ID),
        ("dependency_inventory_authorized", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    )
    for field, expected in exact:
        observed = value.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EventHazardDependencyActionError(f"dependency profile drifted at {field}")
    if _SHA256_RE.fullmatch(value["sha256"]) is None:
        raise EventHazardDependencyActionError("dependency profile SHA-256 is invalid")
    _canonical_utc(value.get("profiled_at"), field="profiled_at")

    raw_dependencies = value.get("dependencies")
    if type(raw_dependencies) is not list or len(raw_dependencies) > MAX_DEPENDENCIES:
        raise EventHazardDependencyActionError("dependency list exceeds bounded policy")
    dependencies = [
        _validate_dependency(row, config_path=spec.repository_path) for row in raw_dependencies
    ]
    identities = [(row["section"], row["option"], row["resolved_path"]) for row in dependencies]
    if len(set(identities)) != len(identities):
        raise EventHazardDependencyActionError("dependency profile contains duplicates")
    if dependencies != sorted(
        dependencies,
        key=lambda row: (row["resolved_path"], row["section"], row["option"], row["raw_path"]),
    ):
        raise EventHazardDependencyActionError("dependency profile ordering drifted")
    return value


def _base_result(*, action: str, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": action,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def validate_terminal_result(body: object, *, action: str, execution_sha: str) -> bool:
    if type(body) is not str or RESULT_MARKER not in body:
        return False
    if body.count(RESULT_MARKER) != 1:
        raise EventHazardDependencyActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EventHazardDependencyActionError("trusted result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EventHazardDependencyActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EventHazardDependencyActionError("trusted result JSON is malformed") from exc
    if type(result) is not dict or set(result) != _RESULT_COMMON_FIELDS:
        raise EventHazardDependencyActionError("trusted result fields drifted")
    exact = _base_result(action=action, execution_sha=execution_sha)
    for field, expected in exact.items():
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise EventHazardDependencyActionError(f"trusted result drifted at {field}")
    status = result.get("status")
    if status == "pass":
        if result.get("failure_class") is not None:
            raise EventHazardDependencyActionError("PASS result carries a failure class")
        validate_profile(result.get("profile"), action=action)
        return True
    if status == "blocked":
        if result.get("failure_class") != "acquisition_failure" or result.get("profile") is not None:
            raise EventHazardDependencyActionError("blocked result widened or leaked evidence")
        return True
    if status == "duplicate":
        if result.get("failure_class") is not None or result.get("profile") is not None:
            raise EventHazardDependencyActionError("duplicate result must not carry evidence")
        return True
    raise EventHazardDependencyActionError("trusted result has non-terminal status")


def _peek_terminal_identity(body: object) -> tuple[str, str] | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if body.count(RESULT_MARKER) != 1:
        raise EventHazardDependencyActionError("trusted result marker is malformed")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise EventHazardDependencyActionError("trusted result envelope is malformed")
    try:
        result = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except EventHazardDependencyActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise EventHazardDependencyActionError("trusted result JSON is malformed") from exc
    if type(result) is not dict:
        raise EventHazardDependencyActionError("trusted result is not an object")
    observed_action = result.get("action")
    observed_sha = result.get("execution_sha")
    if type(observed_action) is not str or type(observed_sha) is not str:
        raise EventHazardDependencyActionError("trusted result lacks action/execution identity")
    return observed_action, observed_sha
