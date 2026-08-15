# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed Agent Action result validation with a bounded #376 extension.

All pre-existing actions delegate byte-for-byte to the legacy v1 validator.
Only the ESHM20 GMM external-resource profiling action is handled here so the
new trusted-main operation can participate in the same durable result ledger
without widening historical action semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from pathlib import PurePosixPath
from typing import Any

try:
    from scripts import acquire_eshm20_gsim_resource_profile as _gsim
    from scripts import validate_agent_action_result_legacy as _legacy
    from scripts.validate_agent_action_request import (
        EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ACTION,
        EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    import acquire_eshm20_gsim_resource_profile as _gsim
    import validate_agent_action_result_legacy as _legacy
    from validate_agent_action_request import (
        EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ACTION,
        EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ISSUE,
    )

# Preserve the historical validator surface for all existing imports/tests.
for _name in dir(_legacy):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_legacy, _name)

_strict_json = _legacy._strict_json
ResultError = _legacy.ResultError
ACQUISITION_FAILURE_CLASS = _legacy.ACQUISITION_FAILURE_CLASS
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ACTION}

_GSIM_RECEIPT_FIELD = "efehr_eshm20_gsim_resource_profile"
_GSIM_EVIDENCE_FIELDS = _legacy.REQUEST_EVIDENCE_FIELDS | {_GSIM_RECEIPT_FIELD}
_GSIM_RECEIPT_FIELDS = {
    "schema_version",
    "source_issue",
    "control_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "byte_count",
    "sha256",
    "openquake_reference",
    "inventory_receipt_comment_id",
    "root_dependency_result_comment_id",
    "root_dependency_section",
    "root_dependency_option",
    "first_order_receipt_request_comment_id",
    "first_order_receipt_result_comment_id",
    "first_order_receipt_run_id",
    "first_order_receipt_execution_sha",
    "first_order_receipt_retrieved_at",
    "branch_set_count",
    "branch_count",
    "resource_reference_count",
    "resources",
    "dependency_inventory_authorized",
    "dependency_receipt_authorized",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
    "profiled_at",
}
_RESOURCE_FIELDS = {
    "argument_key",
    "relative_path",
    "resolved_path",
    "selected_prefix_inventory_member",
    "comment_prefixed",
    "origins",
}
_ORIGIN_FIELDS = {"branch_set_id", "branch_id"}
_ARGUMENT_KEY_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _safe_xml_identity(value: Any, field: str) -> str:
    if type(value) is not str or not (1 <= len(value) <= 512) or value != value.strip():
        raise ResultError(f"{field} must be non-empty bounded already-trimmed text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ResultError(f"{field} contains control characters")
    return value


def _safe_relative_path(value: Any, field: str) -> str:
    if type(value) is not str or not (1 <= len(value) <= 512):
        raise ResultError(f"{field} must be bounded text")
    if (
        "\\" in value
        or "\x00" in value
        or "://" in value
        or "?" in value
        or "#" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ResultError(f"{field} must be a safe relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ResultError(f"{field} must be a canonical relative POSIX path")
    return value


def validate_efehr_eshm20_gsim_resource_profile(receipt: Any) -> dict[str, Any]:
    prefix = _GSIM_RECEIPT_FIELD
    if type(receipt) is not dict or set(receipt) != _GSIM_RECEIPT_FIELDS:
        missing = sorted(_GSIM_RECEIPT_FIELDS - set(receipt)) if type(receipt) is dict else sorted(_GSIM_RECEIPT_FIELDS)
        unexpected = sorted(set(receipt) - _GSIM_RECEIPT_FIELDS) if type(receipt) is dict else []
        raise ResultError(f"{prefix} fields mismatch; missing={missing}, unexpected={unexpected}")

    exact_values = {
        "schema_version": _gsim.SCHEMA_VERSION,
        "source_issue": _gsim.SOURCE_ISSUE,
        "control_issue": _gsim.CONTROL_ISSUE,
        "dataset_id": _gsim.DATASET_ID,
        "project_id": _gsim.PROJECT_ID,
        "project_path": _gsim.PROJECT_PATH,
        "commit_sha": _gsim.COMMIT_SHA,
        "repository_path": _gsim.REPOSITORY_PATH,
        "byte_count": _gsim.EXPECTED_BYTE_COUNT,
        "sha256": _gsim.EXPECTED_SHA256,
        "openquake_reference": _gsim.OPENQUAKE_REFERENCE,
        "inventory_receipt_comment_id": _gsim.INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": _gsim.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": _gsim.ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": _gsim.ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": _gsim.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_result_comment_id": _gsim.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
        "first_order_receipt_run_id": _gsim.FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": _gsim.FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "first_order_receipt_retrieved_at": _gsim.FIRST_ORDER_RECEIPT_RETRIEVED_AT,
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen contract")

    _legacy._utc_second(receipt["first_order_receipt_retrieved_at"], f"{prefix}.first_order_receipt_retrieved_at")
    _legacy._utc_second(receipt["profiled_at"], f"{prefix}.profiled_at")

    for field, maximum in (
        ("branch_set_count", _gsim.MAX_BRANCH_SETS),
        ("branch_count", _gsim.MAX_BRANCHES),
    ):
        value = receipt[field]
        if type(value) is not int or not (1 <= value <= maximum):
            raise ResultError(f"{prefix}.{field} is outside bounded policy")
    if receipt["branch_count"] < receipt["branch_set_count"]:
        raise ResultError(f"{prefix}.branch_count cannot be smaller than branch_set_count")

    resource_count = receipt["resource_reference_count"]
    if type(resource_count) is not int or not (0 <= resource_count <= _gsim.MAX_RESOURCE_REFERENCES):
        raise ResultError(f"{prefix}.resource_reference_count is outside bounded policy")
    resources = receipt["resources"]
    if type(resources) is not list or len(resources) != resource_count:
        raise ResultError(f"{prefix}.resources must match resource_reference_count")

    inventory = _gsim.root_bridge.FROZEN_INVENTORY_PATHS
    if type(inventory) is not frozenset or len(inventory) != 62 or _gsim.REPOSITORY_PATH not in inventory:
        raise ResultError(f"{prefix} frozen inventory authority is invalid")

    base = posixpath.dirname(_gsim.REPOSITORY_PATH)
    previous_resource_key: tuple[str, str, bool, bool] | None = None
    for index, resource in enumerate(resources):
        resource_prefix = f"{prefix}.resources[{index}]"
        if type(resource) is not dict or set(resource) != _RESOURCE_FIELDS:
            raise ResultError(f"{resource_prefix} must have the closed resource shape")

        argument_key = resource["argument_key"]
        if (
            type(argument_key) is not str
            or not (1 <= len(argument_key) <= 128)
            or not _ARGUMENT_KEY_RE.fullmatch(argument_key)
            or not argument_key.endswith(("_file", "_table"))
        ):
            raise ResultError(f"{resource_prefix}.argument_key is outside the closed OpenQuake key policy")

        relative = _safe_relative_path(resource["relative_path"], f"{resource_prefix}.relative_path")
        resolved = _safe_relative_path(resource["resolved_path"], f"{resource_prefix}.resolved_path")
        expected_resolved = posixpath.normpath(posixpath.join(base, relative))
        if expected_resolved != resolved or expected_resolved in {".", ".."} or expected_resolved.startswith("../"):
            raise ResultError(f"{resource_prefix} relative/resolved path binding is invalid")

        member = resource["selected_prefix_inventory_member"]
        if type(member) is not bool or member is not (resolved in inventory):
            raise ResultError(f"{resource_prefix}.selected_prefix_inventory_member is not independently reproduced")
        comment_prefixed = resource["comment_prefixed"]
        if type(comment_prefixed) is not bool:
            raise ResultError(f"{resource_prefix}.comment_prefixed must be boolean")

        origins = resource["origins"]
        if type(origins) is not list or not (1 <= len(origins) <= _gsim.MAX_BRANCHES):
            raise ResultError(f"{resource_prefix}.origins must be a non-empty bounded list")
        previous_origin: tuple[str, str] | None = None
        for origin_index, origin in enumerate(origins):
            origin_prefix = f"{resource_prefix}.origins[{origin_index}]"
            if type(origin) is not dict or set(origin) != _ORIGIN_FIELDS:
                raise ResultError(f"{origin_prefix} must contain exactly branch_set_id and branch_id")
            branch_set_id = _safe_xml_identity(origin["branch_set_id"], f"{origin_prefix}.branch_set_id")
            branch_id = _safe_xml_identity(origin["branch_id"], f"{origin_prefix}.branch_id")
            origin_key = (branch_set_id, branch_id)
            if previous_origin is not None and origin_key <= previous_origin:
                raise ResultError(f"{resource_prefix}.origins must be unique and strictly sorted")
            previous_origin = origin_key

        resource_key = (resolved, argument_key, comment_prefixed, member)
        if previous_resource_key is not None and resource_key <= previous_resource_key:
            raise ResultError(f"{prefix}.resources must be unique and strictly sorted")
        previous_resource_key = resource_key

    return receipt


def _validate_gsim_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict:
        raise ResultError("result must be a JSON object")
    keys = set(result)
    if keys != _legacy.REQUIRED_FIELDS:
        raise ResultError(
            f"result fields mismatch; missing={sorted(_legacy.REQUIRED_FIELDS - keys)}, "
            f"unexpected={sorted(keys - _legacy.REQUIRED_FIELDS)}"
        )
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not _legacy.DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not _legacy.REPOSITORY_RE.fullmatch(result["repository"]):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ACTION:
        raise ResultError("unsupported GMM resource profile action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not _legacy.GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    dataset_id = result["dataset_id"]
    if type(dataset_id) is not str or not (1 <= len(dataset_id) <= 160) or not _legacy.SAFE_ID_RE.fullmatch(dataset_id):
        raise ResultError("dataset_id is not a safe bounded identifier")
    try:
        expected_semantic_id = _legacy.semantic_request_id_from_result(result)
    except _legacy.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if result["semantic_request_id"] != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound repository/action/dataset/target/execution fields")

    started = _legacy._utc_second(result["started_at"], "started_at")
    finished = _legacy._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase = result["phase"]
    if type(phase) is not str or phase not in _legacy.ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    status = result["status"]
    if type(status) is not str or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if type(result["external_bytes_persisted"]) is not bool or result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false in result v1")
    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or a positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if result["source_issue"] != EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ISSUE:
        raise ResultError("GMM resource profile result is outside frozen issue 376")
    if result["dataset_id"] != _gsim.DATASET_ID:
        raise ResultError("GMM resource profile result is outside the frozen ESHM20 dataset")

    if phase == "request_validation":
        evidence = _legacy._validate_request_evidence(result["evidence"])
        if status == "pass":
            if duplicate_id is not None or failure_class is not None:
                raise ResultError("pass result cannot carry duplicate/failure state")
            if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
                raise ResultError("pass result requires complete ledger scan and no prior reuse")
        elif status == "duplicate":
            if duplicate_id is None or failure_class != "duplicate_request":
                raise ResultError("duplicate result requires prior result comment identity")
            if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not True:
                raise ResultError("duplicate result requires complete ledger scan and prior reuse")
        else:
            if duplicate_id is not None or failure_class != "ledger_incomplete":
                raise ResultError("blocked request-validation result must identify ledger_incomplete")
            if evidence["ledger_scan_complete"] is not False or evidence["prior_result_reused"] is not False:
                raise ResultError("blocked request-validation result requires incomplete ledger and no prior reuse")
        return result

    if phase != "acquisition_receipt":
        raise ResultError("GMM resource profile network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _GSIM_EVIDENCE_FIELDS:
        raise ResultError("evidence must be a closed ESHM20 GMM resource profile evidence object")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True:
        raise ResultError("result v1 requires request_validated=true")
    if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
        raise ResultError("acquisition_receipt phase requires complete ledger scan and no prior reuse")
    if duplicate_id is not None:
        raise ResultError("acquisition_receipt phase cannot carry duplicate_result_comment_id")

    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful acquisition_receipt cannot carry failure_class")
        receipt = validate_efehr_eshm20_gsim_resource_profile(evidence[_GSIM_RECEIPT_FIELD])
        profiled_at = _legacy._utc_second(receipt["profiled_at"], f"{_GSIM_RECEIPT_FIELD}.profiled_at")
        if profiled_at < started or profiled_at > finished:
            raise ResultError(f"{_GSIM_RECEIPT_FIELD}.profiled_at must fall within action start/finish bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked acquisition_receipt must identify acquisition_failed")
        if evidence[_GSIM_RECEIPT_FIELD] is not None:
            raise ResultError("blocked acquisition_receipt cannot carry a receipt")
    else:
        raise ResultError("duplicate network acquisition must remain in request_validation phase")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == EFEHR_ESHM20_GSIM_RESOURCE_PROFILE_ACTION:
        return _validate_gsim_result(result)
    return _legacy.validate_result(result)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.result_env not in os.environ:
        print("BLOCKED: result environment variable is absent", file=sys.stderr)
        return 2
    try:
        result = validate_result(_strict_json(os.environ[args.result_env]))
    except ResultError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
