# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend Agent Action result validation for the fixed ESRM20 country-risk receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import PurePosixPath
import sys
from typing import Any

try:
    from scripts import acquire_efehr_esrm20_country_risk_receipt as _country
    from scripts import profile_esrm20_risk_v10_tree as _risk_tree
    from scripts import validate_agent_action_result as _legacy
    from scripts.efehr_gitlab_receipt import PROVIDER_HOST, raw_file_api_url, validate_target
    from scripts.validate_agent_action_request_country_risk import (
        ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
        ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
        ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_efehr_esrm20_country_risk_receipt as _country
    import profile_esrm20_risk_v10_tree as _risk_tree
    import validate_agent_action_result as _legacy
    from efehr_gitlab_receipt import PROVIDER_HOST, raw_file_api_url, validate_target
    from validate_agent_action_request_country_risk import (
        ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
        ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
        ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {ESRM20_COUNTRY_RISK_RECEIPT_ACTION}
_TREE_FIELD = "esrm20_risk_v10_tree_profile"
_COUNTRY_FIELD = "esrm20_country_risk_receipt"
_COUNTRY_EVIDENCE_FIELDS = _legacy.REQUEST_EVIDENCE_FIELDS | {
    _TREE_FIELD,
    _COUNTRY_FIELD,
}
_TREE_PROFILE_FIELDS = {
    "schema_version",
    "source_issue",
    "dataset_id",
    "project_id",
    "project_path",
    "release_tag",
    "commit_sha",
    "subtree_path",
    "pages_read",
    "entry_count",
    "blob_count",
    "tree_count",
    "tree_identity_sha256",
    "risk_inventory",
    "country_risk_path",
    "country_risk_path_status",
    "country_risk_path_entry",
    "country_risk_blob_candidate_present",
    "provider_file_bytes_read",
    "external_bytes_persisted",
    "country_risk_bytes_verified",
    "country_risk_schema_verified",
    "reference_loss_agreement_verified",
    "publication_authorized",
    "model_use_authorized",
}
_TREE_ENTRY_FIELDS = {"mode", "object_sha1", "path", "type"}
_COUNTRY_RECEIPT_FIELDS = {
    "schema_version",
    "operation_id",
    "source_issue",
    "dataset_id",
    "provider_host",
    "project_id",
    "project_path",
    "commit_sha",
    "repository_path",
    "requested_url",
    "final_url",
    "retrieved_at",
    "byte_count",
    "sha256",
    "content_type",
    "etag",
    "external_bytes_persisted",
    "provider_rows_exposed",
    "reference_loss_agreement_verified",
    "publication_authorized",
    "model_use_authorized",
}


def _bounded_nullable_header(value: Any, field: str) -> None:
    if value is None:
        return
    if type(value) is not str or len(value) > 1024:
        raise ResultError(f"{field} must be null or bounded text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ResultError(f"{field} contains control characters")


def _validate_tree_inventory_entry(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != _TREE_ENTRY_FIELDS:
        raise ResultError("risk-tree inventory entry fields drifted")
    entry_type = value["type"]
    if entry_type not in {"blob", "tree"}:
        raise ResultError("risk-tree inventory entry type is unsupported")
    mode = value["mode"]
    expected_mode = "100644" if entry_type == "blob" else "040000"
    if mode != expected_mode:
        raise ResultError("risk-tree inventory type/mode identity drifted")
    object_sha1 = value["object_sha1"]
    if type(object_sha1) is not str or not _legacy.GIT_SHA_RE.fullmatch(object_sha1):
        raise ResultError("risk-tree inventory object_sha1 is invalid")
    path = value["path"]
    if type(path) is not str or not path:
        raise ResultError("risk-tree inventory path is not text")
    try:
        encoded = path.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ResultError("risk-tree inventory path is not UTF-8") from exc
    if len(encoded) > _risk_tree.MAX_PATH_UTF8_BYTES:
        raise ResultError("risk-tree inventory path exceeds bounded policy")
    if any(ord(character) < 32 or ord(character) == 127 for character in path):
        raise ResultError("risk-tree inventory path contains control characters")
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or str(pure) != path
        or any(part in ("", ".", "..") for part in pure.parts)
        or "\\" in path
        or not path.startswith(_risk_tree.SUBTREE_PATH + "/")
    ):
        raise ResultError("risk-tree inventory path is not canonical fixed-subtree POSIX")
    return value


def validate_esrm20_risk_v10_tree_profile(profile: Any) -> dict[str, Any]:
    """Revalidate the complete bounded metadata precondition before publication."""
    if type(profile) is not dict or set(profile) != _TREE_PROFILE_FIELDS:
        raise ResultError("ESRM20 Risk tree profile fields drifted")
    exact_values = {
        "schema_version": _risk_tree.SCHEMA_VERSION,
        "source_issue": _risk_tree.SOURCE_ISSUE,
        "dataset_id": _risk_tree.DATASET_ID,
        "project_id": _risk_tree.PROJECT_ID,
        "project_path": _risk_tree.PROJECT_PATH,
        "release_tag": _risk_tree.RELEASE_TAG,
        "commit_sha": _risk_tree.EXPECTED_COMMIT_SHA,
        "subtree_path": _risk_tree.SUBTREE_PATH,
        "country_risk_path": _risk_tree.COUNTRY_RISK_PATH,
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "country_risk_bytes_verified": False,
        "country_risk_schema_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(profile[field]) is not type(expected) or profile[field] != expected:
            raise ResultError(f"risk-tree profile {field} drifted from frozen authority")

    pages_read = profile["pages_read"]
    if type(pages_read) is not int or isinstance(pages_read, bool) or not (
        1 <= pages_read <= _risk_tree.MAX_TREE_PAGES
    ):
        raise ResultError("risk-tree profile pages_read is outside bounded policy")
    entry_count = profile["entry_count"]
    blob_count = profile["blob_count"]
    tree_count = profile["tree_count"]
    for field, value in (
        ("entry_count", entry_count),
        ("blob_count", blob_count),
        ("tree_count", tree_count),
    ):
        if type(value) is not int or isinstance(value, bool) or value < 0:
            raise ResultError(f"risk-tree profile {field} is invalid")
    if not (1 <= entry_count <= _risk_tree.MAX_TREE_ENTRIES):
        raise ResultError("risk-tree profile entry_count is outside bounded policy")
    if blob_count + tree_count != entry_count:
        raise ResultError("risk-tree profile type counts do not equal entry_count")

    inventory = profile["risk_inventory"]
    if type(inventory) is not list or len(inventory) != entry_count:
        raise ResultError("risk-tree inventory length does not match entry_count")
    entries = [_validate_tree_inventory_entry(value) for value in inventory]
    paths = [entry["path"] for entry in entries]
    if paths != sorted(paths) or len(set(paths)) != len(paths):
        raise ResultError("risk-tree inventory paths are not sorted and unique")
    if sum(entry["type"] == "blob" for entry in entries) != blob_count:
        raise ResultError("risk-tree inventory blob count drifted")
    if sum(entry["type"] == "tree" for entry in entries) != tree_count:
        raise ResultError("risk-tree inventory tree count drifted")

    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['object_sha1']}\t{entry['path']}\n"
        for entry in entries
    ).encode("utf-8")
    expected_identity = hashlib.sha256(canonical).hexdigest()
    if profile["tree_identity_sha256"] != expected_identity:
        raise ResultError("risk-tree profile tree identity SHA-256 drifted")

    status = profile["country_risk_path_status"]
    if status not in {"absent", "tree", "blob"}:
        raise ResultError("risk-tree country path status is invalid")
    matching = [
        entry for entry in entries if entry["path"] == _risk_tree.COUNTRY_RISK_PATH
    ]
    if len(matching) > 1:
        raise ResultError("risk-tree country path appears more than once")
    country_entry = profile["country_risk_path_entry"]
    candidate_present = profile["country_risk_blob_candidate_present"]
    if type(candidate_present) is not bool:
        raise ResultError("risk-tree blob-candidate flag must be boolean")
    if not matching:
        if status != "absent" or country_entry is not None or candidate_present:
            raise ResultError("risk-tree absent country path state is inconsistent")
    else:
        entry = matching[0]
        expected_status = "blob" if entry["type"] == "blob" else "tree"
        if status != expected_status or country_entry != entry:
            raise ResultError("risk-tree country path evidence is inconsistent")
        if candidate_present is not (status == "blob"):
            raise ResultError("risk-tree blob-candidate flag is inconsistent")
    return profile


def validate_esrm20_country_risk_receipt(receipt: Any) -> dict[str, Any]:
    prefix = _COUNTRY_FIELD
    if type(receipt) is not dict or set(receipt) != _COUNTRY_RECEIPT_FIELDS:
        missing = (
            sorted(_COUNTRY_RECEIPT_FIELDS - set(receipt))
            if type(receipt) is dict
            else sorted(_COUNTRY_RECEIPT_FIELDS)
        )
        unexpected = (
            sorted(set(receipt) - _COUNTRY_RECEIPT_FIELDS)
            if type(receipt) is dict
            else []
        )
        raise ResultError(
            f"{prefix} fields mismatch; missing={missing}, unexpected={unexpected}"
        )

    target = validate_target(
        source_issue=_country.SOURCE_ISSUE,
        dataset_id=_country.DATASET_ID,
        project_id=_country.PROJECT_ID,
        commit_sha=_country.COMMIT_SHA,
        repository_path=_country.REPOSITORY_PATH,
    )
    expected_url = raw_file_api_url(target)
    exact_values = {
        "schema_version": _country.SCHEMA_VERSION,
        "operation_id": _country.OPERATION_ID,
        "source_issue": _country.SOURCE_ISSUE,
        "dataset_id": _country.DATASET_ID,
        "provider_host": PROVIDER_HOST,
        "project_id": _country.PROJECT_ID,
        "project_path": _country.PROJECT_PATH,
        "commit_sha": _country.COMMIT_SHA,
        "repository_path": _country.REPOSITORY_PATH,
        "requested_url": expected_url,
        "final_url": expected_url,
        "external_bytes_persisted": False,
        "provider_rows_exposed": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(
                f"{prefix}.{field} does not match the frozen country-risk receipt contract"
            )

    _legacy._utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    byte_count = receipt["byte_count"]
    if type(byte_count) is not int or isinstance(byte_count, bool) or not (
        1 <= byte_count <= _country.MAX_COUNTRY_RISK_BYTES
    ):
        raise ResultError(f"{prefix}.byte_count is outside bounded policy")
    sha256 = receipt["sha256"]
    if type(sha256) is not str or not _legacy.DIGEST_RE.fullmatch(sha256):
        raise ResultError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")
    _bounded_nullable_header(receipt["content_type"], f"{prefix}.content_type")
    _bounded_nullable_header(receipt["etag"], f"{prefix}.etag")
    return receipt


def _validate_country_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("country-risk result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not _legacy.DIGEST_RE.fullmatch(
        result["semantic_request_id"]
    ):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not _legacy.REPOSITORY_RE.fullmatch(
        result["repository"]
    ):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        raise ResultError("unsupported country-risk action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not _legacy.GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("country-risk network result requires target_sha == execution_sha")
    if result["source_issue"] != ESRM20_COUNTRY_RISK_RECEIPT_ISSUE:
        raise ResultError("country-risk result is outside frozen control issue 778")
    if result["dataset_id"] != ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID:
        raise ResultError("country-risk result is outside the frozen ESRM20 risk-input dataset")

    try:
        expected_semantic_id = _legacy.semantic_request_id_from_result(result)
    except _legacy.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if result["semantic_request_id"] != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = _legacy._utc_second(result["started_at"], "started_at")
    finished = _legacy._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase, status = result["phase"], result["status"]
    if type(phase) is not str or phase not in _legacy.ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    if type(status) is not str or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id, failure_class = (
        result["duplicate_result_comment_id"],
        result["failure_class"],
    )
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        evidence = _legacy._validate_request_evidence(result["evidence"])
        if status == "pass":
            if (
                duplicate_id is not None
                or failure_class is not None
                or evidence["ledger_scan_complete"] is not True
                or evidence["prior_result_reused"] is not False
            ):
                raise ResultError("pass request-validation state is invalid")
        elif status == "duplicate":
            if (
                duplicate_id is None
                or failure_class != "duplicate_request"
                or evidence["ledger_scan_complete"] is not True
                or evidence["prior_result_reused"] is not True
            ):
                raise ResultError("duplicate request-validation state is invalid")
        else:
            if (
                duplicate_id is not None
                or failure_class != "ledger_incomplete"
                or evidence["ledger_scan_complete"] is not False
                or evidence["prior_result_reused"] is not False
            ):
                raise ResultError("blocked request-validation state is invalid")
        return result

    if phase != "acquisition_receipt":
        raise ResultError("country-risk network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _COUNTRY_EVIDENCE_FIELDS:
        raise ResultError("country-risk evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError(
            "country-risk acquisition requires validated complete non-reused ledger state"
        )

    tree_profile = evidence[_TREE_FIELD]
    receipt = evidence[_COUNTRY_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful country-risk acquisition cannot carry failure_class")
        tree_profile = validate_esrm20_risk_v10_tree_profile(tree_profile)
        if tree_profile["country_risk_path_status"] != "blob":
            raise ResultError("successful country-risk acquisition requires blob precondition")
        receipt = validate_esrm20_country_risk_receipt(receipt)
        retrieved = _legacy._utc_second(
            receipt["retrieved_at"], f"{_COUNTRY_FIELD}.retrieved_at"
        )
        if retrieved < started or retrieved > finished:
            raise ResultError(
                f"{_COUNTRY_FIELD}.retrieved_at must fall within action start/finish bounds"
            )
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS or receipt is not None:
            raise ResultError("blocked country-risk acquisition state is invalid")
        if tree_profile is not None:
            validate_esrm20_risk_v10_tree_profile(tree_profile)
    else:
        raise ResultError("duplicate country-risk network result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == ESRM20_COUNTRY_RISK_RECEIPT_ACTION:
        return _validate_country_result(result)
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
        result = validate_result(_legacy._strict_json(os.environ[args.result_env]))
    except ResultError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
