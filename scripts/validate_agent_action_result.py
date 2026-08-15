# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed validator for durable Agent Action Dispatch result receipts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

try:
    from scripts.agent_action_protocol import (
        DIGEST_RE,
        GIT_SHA_RE,
        REPOSITORY_RE,
        RESULT_SCHEMA_VERSION,
        SAFE_ID_RE,
        ProtocolError,
        semantic_request_id_from_result,
    )
    from scripts.acquire_dwd_extreme_wind_receipt import (
        DATASET_ID as ACQUISITION_DATASET_ID,
        EXPECTED_BEGIN_DATE,
        EXPECTED_END_DATE,
        EXPECTED_STATION_ID,
        FILENAME as ACQUISITION_FILENAME,
        MAX_ARCHIVE_MEMBERS,
        MAX_BYTES,
        MAX_UNCOMPRESSED_BYTES,
        SCHEMA_VERSION as ACQUISITION_SCHEMA_VERSION,
        SOURCE_URL as ACQUISITION_SOURCE_URL,
    )
    from scripts.acquire_dwd_metadata_receipt import (
        DATASET_ID as DWD_METADATA_DATASET_ID,
        EXPECTED_STATION_ID as DWD_METADATA_STATION_ID,
        FILENAME as DWD_METADATA_FILENAME,
        MAX_ARCHIVE_MEMBERS as DWD_METADATA_MAX_ARCHIVE_MEMBERS,
        MAX_BYTES as DWD_METADATA_MAX_BYTES,
        MAX_UNCOMPRESSED_BYTES as DWD_METADATA_MAX_UNCOMPRESSED_BYTES,
        REQUIRED_METADATA_FAMILIES,
        SCHEMA_VERSION as DWD_METADATA_SCHEMA_VERSION,
        SOURCE_ISSUE as DWD_METADATA_SOURCE_ISSUE,
        SOURCE_URL as DWD_METADATA_SOURCE_URL,
    )
    from scripts.acquire_efehr_gitlab_receipt import (
        DATASET_ID as EFEHR_README_DATASET_ID,
        MAX_CANARY_BYTES as EFEHR_README_MAX_BYTES,
        OPERATION_ID as EFEHR_README_OPERATION_ID,
        PROJECT_ID as EFEHR_README_PROJECT_ID,
        RELEASE_TAG as EFEHR_README_RELEASE_TAG,
        REPOSITORY_PATH as EFEHR_README_REPOSITORY_PATH,
        SCHEMA_VERSION as EFEHR_README_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_RECEIPT_SOURCE_ISSUE,
        TAG_API_URL as EFEHR_README_TAG_API_URL,
    )
    from scripts.acquire_efehr_eshm20_tree_metadata import (
        BRANCH as EFEHR_ESHM20_BRANCH,
        DATASET_ID as EFEHR_ESHM20_DATASET_ID,
        MAX_TOTAL_METADATA_BYTES as EFEHR_ESHM20_MAX_METADATA_BYTES,
        MAX_TREE_ENTRIES as EFEHR_ESHM20_MAX_TREE_ENTRIES,
        MAX_TREE_PAGES as EFEHR_ESHM20_MAX_TREE_PAGES,
        OPERATION_ID as EFEHR_ESHM20_OPERATION_ID,
        PROJECT_ID as EFEHR_ESHM20_PROJECT_ID,
        PROJECT_PATH as EFEHR_ESHM20_PROJECT_PATH,
        SCHEMA_VERSION as EFEHR_ESHM20_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_ESHM20_SOURCE_ISSUE,
        TREE_PREFIX as EFEHR_ESHM20_TREE_PREFIX,
    )
    from scripts.acquire_efehr_kosovo_receipt import (
        COMMIT_SHA as EFEHR_KOSOVO_COMMIT_SHA,
        DATASET_ID as EFEHR_KOSOVO_DATASET_ID,
        MAX_FILE_BYTES as EFEHR_KOSOVO_MAX_BYTES,
        OPERATION_ID as EFEHR_KOSOVO_OPERATION_ID,
        PROJECT_ID as EFEHR_KOSOVO_PROJECT_ID,
        REPOSITORY_PATH as EFEHR_KOSOVO_REPOSITORY_PATH,
        SCHEMA_VERSION as EFEHR_KOSOVO_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_KOSOVO_SOURCE_ISSUE,
    )
    from scripts.acquire_efehr_eshm20_root_config_receipt import (
        COMMIT_SHA as EFEHR_ESHM20_ROOT_CONFIG_COMMIT_SHA,
        DATASET_ID as EFEHR_ESHM20_ROOT_CONFIG_DATASET_ID,
        MAX_ROOT_CONFIG_BYTES as EFEHR_ESHM20_ROOT_CONFIG_MAX_BYTES,
        OPERATION_ID as EFEHR_ESHM20_ROOT_CONFIG_OPERATION_ID,
        PROJECT_ID as EFEHR_ESHM20_ROOT_CONFIG_PROJECT_ID,
        REPOSITORY_PATH as EFEHR_ESHM20_ROOT_CONFIG_REPOSITORY_PATH,
        SCHEMA_VERSION as EFEHR_ESHM20_ROOT_CONFIG_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_ESHM20_ROOT_CONFIG_SOURCE_ISSUE,
    )
    from scripts.efehr_gitlab_receipt import (
        PROJECTS as EFEHR_PROJECTS,
        PROVIDER_HOST as EFEHR_PROVIDER_HOST,
        EfehrReceiptError,
        raw_file_api_url as efehr_raw_file_api_url,
        validate_target as validate_efehr_target,
    )
    from scripts.validate_agent_action_request import (
        EFEHR_ESHM20_TREE_METADATA_ISSUE as EFEHR_ESHM20_ACTION_ISSUE,
        EFEHR_KOSOVO_EXPOSURE_RECEIPT_ISSUE as EFEHR_KOSOVO_ACTION_ISSUE,
        EFEHR_ESHM20_ROOT_CONFIG_RECEIPT_ISSUE as EFEHR_ESHM20_ROOT_CONFIG_ACTION_ISSUE,
        EFEHR_README_RECEIPT_ISSUE as EFEHR_ACTION_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from agent_action_protocol import (
        DIGEST_RE,
        GIT_SHA_RE,
        REPOSITORY_RE,
        RESULT_SCHEMA_VERSION,
        SAFE_ID_RE,
        ProtocolError,
        semantic_request_id_from_result,
    )
    from acquire_dwd_extreme_wind_receipt import (
        DATASET_ID as ACQUISITION_DATASET_ID,
        EXPECTED_BEGIN_DATE,
        EXPECTED_END_DATE,
        EXPECTED_STATION_ID,
        FILENAME as ACQUISITION_FILENAME,
        MAX_ARCHIVE_MEMBERS,
        MAX_BYTES,
        MAX_UNCOMPRESSED_BYTES,
        SCHEMA_VERSION as ACQUISITION_SCHEMA_VERSION,
        SOURCE_URL as ACQUISITION_SOURCE_URL,
    )
    from acquire_dwd_metadata_receipt import (
        DATASET_ID as DWD_METADATA_DATASET_ID,
        EXPECTED_STATION_ID as DWD_METADATA_STATION_ID,
        FILENAME as DWD_METADATA_FILENAME,
        MAX_ARCHIVE_MEMBERS as DWD_METADATA_MAX_ARCHIVE_MEMBERS,
        MAX_BYTES as DWD_METADATA_MAX_BYTES,
        MAX_UNCOMPRESSED_BYTES as DWD_METADATA_MAX_UNCOMPRESSED_BYTES,
        REQUIRED_METADATA_FAMILIES,
        SCHEMA_VERSION as DWD_METADATA_SCHEMA_VERSION,
        SOURCE_ISSUE as DWD_METADATA_SOURCE_ISSUE,
        SOURCE_URL as DWD_METADATA_SOURCE_URL,
    )
    from acquire_efehr_gitlab_receipt import (
        DATASET_ID as EFEHR_README_DATASET_ID,
        MAX_CANARY_BYTES as EFEHR_README_MAX_BYTES,
        OPERATION_ID as EFEHR_README_OPERATION_ID,
        PROJECT_ID as EFEHR_README_PROJECT_ID,
        RELEASE_TAG as EFEHR_README_RELEASE_TAG,
        REPOSITORY_PATH as EFEHR_README_REPOSITORY_PATH,
        SCHEMA_VERSION as EFEHR_README_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_RECEIPT_SOURCE_ISSUE,
        TAG_API_URL as EFEHR_README_TAG_API_URL,
    )
    from acquire_efehr_eshm20_tree_metadata import (
        BRANCH as EFEHR_ESHM20_BRANCH,
        DATASET_ID as EFEHR_ESHM20_DATASET_ID,
        MAX_TOTAL_METADATA_BYTES as EFEHR_ESHM20_MAX_METADATA_BYTES,
        MAX_TREE_ENTRIES as EFEHR_ESHM20_MAX_TREE_ENTRIES,
        MAX_TREE_PAGES as EFEHR_ESHM20_MAX_TREE_PAGES,
        OPERATION_ID as EFEHR_ESHM20_OPERATION_ID,
        PROJECT_ID as EFEHR_ESHM20_PROJECT_ID,
        PROJECT_PATH as EFEHR_ESHM20_PROJECT_PATH,
        SCHEMA_VERSION as EFEHR_ESHM20_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_ESHM20_SOURCE_ISSUE,
        TREE_PREFIX as EFEHR_ESHM20_TREE_PREFIX,
    )
    from acquire_efehr_kosovo_receipt import (
        COMMIT_SHA as EFEHR_KOSOVO_COMMIT_SHA,
        DATASET_ID as EFEHR_KOSOVO_DATASET_ID,
        MAX_FILE_BYTES as EFEHR_KOSOVO_MAX_BYTES,
        OPERATION_ID as EFEHR_KOSOVO_OPERATION_ID,
        PROJECT_ID as EFEHR_KOSOVO_PROJECT_ID,
        REPOSITORY_PATH as EFEHR_KOSOVO_REPOSITORY_PATH,
        SCHEMA_VERSION as EFEHR_KOSOVO_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_KOSOVO_SOURCE_ISSUE,
    )
    from acquire_efehr_eshm20_root_config_receipt import (
        COMMIT_SHA as EFEHR_ESHM20_ROOT_CONFIG_COMMIT_SHA,
        DATASET_ID as EFEHR_ESHM20_ROOT_CONFIG_DATASET_ID,
        MAX_ROOT_CONFIG_BYTES as EFEHR_ESHM20_ROOT_CONFIG_MAX_BYTES,
        OPERATION_ID as EFEHR_ESHM20_ROOT_CONFIG_OPERATION_ID,
        PROJECT_ID as EFEHR_ESHM20_ROOT_CONFIG_PROJECT_ID,
        REPOSITORY_PATH as EFEHR_ESHM20_ROOT_CONFIG_REPOSITORY_PATH,
        SCHEMA_VERSION as EFEHR_ESHM20_ROOT_CONFIG_SCHEMA_VERSION,
        SOURCE_ISSUE as EFEHR_ESHM20_ROOT_CONFIG_SOURCE_ISSUE,
    )
    from efehr_gitlab_receipt import (
        PROJECTS as EFEHR_PROJECTS,
        PROVIDER_HOST as EFEHR_PROVIDER_HOST,
        EfehrReceiptError,
        raw_file_api_url as efehr_raw_file_api_url,
        validate_target as validate_efehr_target,
    )
    from validate_agent_action_request import (
        EFEHR_ESHM20_TREE_METADATA_ISSUE as EFEHR_ESHM20_ACTION_ISSUE,
        EFEHR_KOSOVO_EXPOSURE_RECEIPT_ISSUE as EFEHR_KOSOVO_ACTION_ISSUE,
        EFEHR_ESHM20_ROOT_CONFIG_RECEIPT_ISSUE as EFEHR_ESHM20_ROOT_CONFIG_ACTION_ISSUE,
        EFEHR_README_RECEIPT_ISSUE as EFEHR_ACTION_ISSUE,
    )

REQUIRED_FIELDS = {
    "schema_version", "semantic_request_id", "repository", "action",
    "source_issue", "source_comment_id", "target_sha", "dataset_id", "execution_sha",
    "run_id", "run_attempt", "started_at", "finished_at", "phase", "status",
    "external_bytes_persisted", "evidence", "duplicate_result_comment_id", "failure_class",
}
REQUEST_EVIDENCE_FIELDS = {"request_validated", "ledger_scan_complete", "prior_result_reused"}
ACQUISITION_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {"acquisition_receipt"}
DWD_METADATA_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {"dwd_metadata_receipt"}
EFEHR_README_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {"efehr_readme_receipt"}
EFEHR_ESHM20_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {"efehr_eshm20_tree_metadata"}
EFEHR_KOSOVO_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {"efehr_kosovo_exposure_receipt"}
EFEHR_ESHM20_ROOT_CONFIG_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {
    "efehr_eshm20_root_config_receipt"
}
ACQUISITION_RECEIPT_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "requested_url", "final_url",
    "filename", "retrieved_at", "byte_count", "sha256", "content_type",
    "last_modified", "etag", "archive_member_count", "archive_uncompressed_bytes",
    "product_member", "product_station_id", "product_begin_date", "product_end_date",
    "product_row_count", "product_structure_validated", "external_bytes_persisted",
    "publication_authorized",
}
DWD_METADATA_RECEIPT_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "requested_url", "final_url",
    "filename", "retrieved_at", "byte_count", "sha256", "content_type",
    "last_modified", "etag", "archive_member_count", "archive_uncompressed_bytes",
    "station_id", "required_metadata_families", "metadata_members",
    "temporal_coverage_status", "external_bytes_persisted", "publication_authorized",
}
EFEHR_README_RECEIPT_FIELDS = {
    "schema_version", "operation_id", "release_tag", "tag_api_url", "source_issue",
    "dataset_id", "provider_host", "project_id", "project_path", "commit_sha",
    "repository_path", "requested_url", "final_url", "retrieved_at", "byte_count",
    "sha256", "content_type", "etag", "external_bytes_persisted", "publication_authorized",
}
EFEHR_ESHM20_RECEIPT_FIELDS = {
    "schema_version", "operation_id", "source_issue", "dataset_id",
    "provider_host", "project_id", "project_path", "branch",
    "resolved_commit_sha", "tree_prefix", "retrieved_at", "tree_page_count",
    "tree_entry_count", "metadata_byte_count", "entries",
    "external_bytes_persisted", "publication_authorized",
}
EFEHR_KOSOVO_RECEIPT_FIELDS = {
    "schema_version", "operation_id", "source_issue", "dataset_id",
    "provider_host", "project_id", "project_path", "commit_sha",
    "repository_path", "requested_url", "final_url", "retrieved_at",
    "byte_count", "sha256", "content_type", "etag",
    "external_bytes_persisted", "publication_authorized",
}
EFEHR_ESHM20_ROOT_CONFIG_RECEIPT_FIELDS = {
    "schema_version", "operation_id", "source_issue", "dataset_id", "provider_host",
    "project_id", "project_path", "commit_sha", "repository_path", "requested_url",
    "final_url", "retrieved_at", "byte_count", "sha256", "content_type", "etag",
    "external_bytes_persisted", "publication_authorized",
}
ALLOWED_ACTIONS = {
    "sample_audit", "acquisition_receipt", "dwd_metadata_receipt",
    "efehr_readme_receipt", "efehr_eshm20_tree_metadata",
    "efehr_kosovo_exposure_receipt", "efehr_eshm20_root_config_receipt",
}
ALLOWED_PHASES = {"request_validation", "acquisition_receipt"}
ALLOWED_STATUSES = {"pass", "duplicate", "blocked"}
ACQUISITION_FAILURE_CLASS = "acquisition_failed"
DWD_METADATA_PROVIDER_PREFIXES = {
    "equipment": "metadaten_geraete",
    "geography": "metadaten_geographie",
    "parameter": "metadaten_parameter",
}
DWD_METADATA_STATION_ID_RE = re.compile(r"(?<!\d)(\d{5})(?!\d)")


class ResultError(ValueError):
    """Raised when a result receipt is not exactly valid."""


def _strict_json(text: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ResultError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(ResultError(f"non-finite JSON value: {token}")),
        )
    except (json.JSONDecodeError, ResultError) as exc:
        raise ResultError(f"invalid result JSON: {exc}") from exc
    if type(value) is not dict:
        raise ResultError("result must be a JSON object")
    return value


def _utc_second(value: Any, field: str) -> datetime:
    if type(value) is not str or len(value) != 20 or not value.endswith("Z"):
        raise ResultError(f"{field} must be UTC second-precision text")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ResultError(f"{field} must be a real UTC timestamp") from exc
    return parsed


def _bounded_header(value: Any, field: str, *, prefix: str = "acquisition_receipt") -> None:
    if value is None:
        return
    if type(value) is not str or len(value) > 512:
        raise ResultError(f"{prefix}.{field} must be null or bounded text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ResultError(f"{prefix}.{field} contains control characters")


def _positive_bounded_int(value: Any, field: str, maximum: int, *, prefix: str = "acquisition_receipt") -> None:
    if type(value) is not int or not (1 <= value <= maximum):
        raise ResultError(f"{prefix}.{field} must be an integer in [1,{maximum}]")


def _validate_safe_text_path(value: Any, field: str) -> str:
    if type(value) is not str or not (1 <= len(value) <= 512):
        raise ResultError(f"{field} must be bounded text")
    if "\\" in value or "\x00" in value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ResultError(f"{field} must be a safe relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ResultError(f"{field} must be a safe relative POSIX path")
    return value


def _validate_product_member(value: Any) -> None:
    path = _validate_safe_text_path(value, "acquisition_receipt.product_member")
    if PurePosixPath(path).suffix.casefold() != ".txt":
        raise ResultError("acquisition_receipt.product_member must identify a text member")


def _validate_dwd_metadata_member_binding(path: str, family: str, prefix: str) -> None:
    basename = PurePosixPath(path).name.casefold()
    expected_prefix = DWD_METADATA_PROVIDER_PREFIXES[family]
    if not basename.startswith(expected_prefix):
        raise ResultError(f"{prefix}.metadata_members path does not match its provider-native family")
    suffix = basename[len(expected_prefix):]
    if suffix and suffix[0] not in "_.-":
        raise ResultError(f"{prefix}.metadata_members path does not match its provider-native family")
    station_ids = DWD_METADATA_STATION_ID_RE.findall(PurePosixPath(path).name)
    if station_ids != [DWD_METADATA_STATION_ID]:
        raise ResultError(f"{prefix}.metadata_members path is not bound exactly to station {DWD_METADATA_STATION_ID}")


def validate_acquisition_receipt(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise ResultError("acquisition_receipt must be a JSON object")
    keys = set(receipt)
    if keys != ACQUISITION_RECEIPT_FIELDS:
        raise ResultError(
            "acquisition_receipt fields mismatch; "
            f"missing={sorted(ACQUISITION_RECEIPT_FIELDS - keys)}, "
            f"unexpected={sorted(keys - ACQUISITION_RECEIPT_FIELDS)}"
        )
    exact_values = {
        "schema_version": ACQUISITION_SCHEMA_VERSION,
        "dataset_id": ACQUISITION_DATASET_ID,
        "source_issue": 162,
        "requested_url": ACQUISITION_SOURCE_URL,
        "final_url": ACQUISITION_SOURCE_URL,
        "filename": ACQUISITION_FILENAME,
        "product_station_id": EXPECTED_STATION_ID,
        "product_begin_date": EXPECTED_BEGIN_DATE,
        "product_end_date": EXPECTED_END_DATE,
        "product_structure_validated": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"acquisition_receipt.{field} does not match the frozen contract")
    _utc_second(receipt["retrieved_at"], "acquisition_receipt.retrieved_at")
    _positive_bounded_int(receipt["byte_count"], "byte_count", MAX_BYTES)
    if type(receipt["sha256"]) is not str or not DIGEST_RE.fullmatch(receipt["sha256"]):
        raise ResultError("acquisition_receipt.sha256 must be a lowercase SHA-256 digest")
    for field in ("content_type", "last_modified", "etag"):
        _bounded_header(receipt[field], field)
    _positive_bounded_int(receipt["archive_member_count"], "archive_member_count", MAX_ARCHIVE_MEMBERS)
    _positive_bounded_int(receipt["archive_uncompressed_bytes"], "archive_uncompressed_bytes", MAX_UNCOMPRESSED_BYTES)
    _validate_product_member(receipt["product_member"])
    _positive_bounded_int(receipt["product_row_count"], "product_row_count", 1_000_000)
    return receipt


def validate_dwd_metadata_receipt(receipt: Any) -> dict[str, Any]:
    prefix = "dwd_metadata_receipt"
    if type(receipt) is not dict:
        raise ResultError(f"{prefix} must be a JSON object")
    keys = set(receipt)
    if keys != DWD_METADATA_RECEIPT_FIELDS:
        raise ResultError(
            f"{prefix} fields mismatch; missing={sorted(DWD_METADATA_RECEIPT_FIELDS - keys)}, "
            f"unexpected={sorted(keys - DWD_METADATA_RECEIPT_FIELDS)}"
        )
    exact_values = {
        "schema_version": DWD_METADATA_SCHEMA_VERSION,
        "dataset_id": DWD_METADATA_DATASET_ID,
        "source_issue": DWD_METADATA_SOURCE_ISSUE,
        "requested_url": DWD_METADATA_SOURCE_URL,
        "final_url": DWD_METADATA_SOURCE_URL,
        "filename": DWD_METADATA_FILENAME,
        "station_id": DWD_METADATA_STATION_ID,
        "temporal_coverage_status": "unverified",
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen contract")
    _utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    _positive_bounded_int(receipt["byte_count"], "byte_count", DWD_METADATA_MAX_BYTES, prefix=prefix)
    if type(receipt["sha256"]) is not str or not DIGEST_RE.fullmatch(receipt["sha256"]):
        raise ResultError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")
    for field in ("content_type", "last_modified", "etag"):
        _bounded_header(receipt[field], field, prefix=prefix)
    _positive_bounded_int(receipt["archive_member_count"], "archive_member_count", DWD_METADATA_MAX_ARCHIVE_MEMBERS, prefix=prefix)
    _positive_bounded_int(receipt["archive_uncompressed_bytes"], "archive_uncompressed_bytes", DWD_METADATA_MAX_UNCOMPRESSED_BYTES, prefix=prefix)
    expected_families = sorted(REQUIRED_METADATA_FAMILIES)
    if receipt["required_metadata_families"] != expected_families:
        raise ResultError(f"{prefix}.required_metadata_families must equal the frozen provider-family set")
    members = receipt["metadata_members"]
    if type(members) is not list or not (3 <= len(members) <= DWD_METADATA_MAX_ARCHIVE_MEMBERS):
        raise ResultError(f"{prefix}.metadata_members must be a bounded evidence list")
    if len(members) > receipt["archive_member_count"]:
        raise ResultError(f"{prefix}.metadata_members cannot exceed archive_member_count")
    seen_paths: set[str] = set()
    seen_families: set[str] = set()
    previous_key: tuple[str, str] | None = None
    for member in members:
        if type(member) is not dict or set(member) != {"path", "family"}:
            raise ResultError(f"{prefix}.metadata_members items must contain exactly path and family")
        path = _validate_safe_text_path(member["path"], f"{prefix}.metadata_members.path")
        family = member["family"]
        if type(family) is not str or family not in REQUIRED_METADATA_FAMILIES:
            raise ResultError(f"{prefix}.metadata_members.family is outside the frozen family set")
        _validate_dwd_metadata_member_binding(path, family, prefix)
        if path in seen_paths:
            raise ResultError(f"{prefix}.metadata_members paths must be unique")
        seen_paths.add(path)
        seen_families.add(family)
        key = (family, path)
        if previous_key is not None and key <= previous_key:
            raise ResultError(f"{prefix}.metadata_members must be strictly sorted by family/path")
        previous_key = key
    if seen_families != REQUIRED_METADATA_FAMILIES:
        raise ResultError(f"{prefix}.metadata_members must prove every required provider family")
    return receipt


def validate_efehr_readme_receipt(receipt: Any) -> dict[str, Any]:
    prefix = "efehr_readme_receipt"
    if type(receipt) is not dict:
        raise ResultError(f"{prefix} must be a JSON object")
    keys = set(receipt)
    if keys != EFEHR_README_RECEIPT_FIELDS:
        raise ResultError(
            f"{prefix} fields mismatch; missing={sorted(EFEHR_README_RECEIPT_FIELDS - keys)}, "
            f"unexpected={sorted(keys - EFEHR_README_RECEIPT_FIELDS)}"
        )
    expected_project_path = str(EFEHR_PROJECTS[EFEHR_README_PROJECT_ID]["project_path"])
    exact_values = {
        "schema_version": EFEHR_README_SCHEMA_VERSION,
        "operation_id": EFEHR_README_OPERATION_ID,
        "release_tag": EFEHR_README_RELEASE_TAG,
        "tag_api_url": EFEHR_README_TAG_API_URL,
        "source_issue": EFEHR_RECEIPT_SOURCE_ISSUE,
        "dataset_id": EFEHR_README_DATASET_ID,
        "provider_host": EFEHR_PROVIDER_HOST,
        "project_id": EFEHR_README_PROJECT_ID,
        "project_path": expected_project_path,
        "repository_path": EFEHR_README_REPOSITORY_PATH,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen contract")
    commit_sha = receipt["commit_sha"]
    if type(commit_sha) is not str or not GIT_SHA_RE.fullmatch(commit_sha):
        raise ResultError(f"{prefix}.commit_sha must be a lowercase 40-character Git commit SHA")
    try:
        target = validate_efehr_target(
            source_issue=EFEHR_RECEIPT_SOURCE_ISSUE,
            dataset_id=EFEHR_README_DATASET_ID,
            project_id=EFEHR_README_PROJECT_ID,
            commit_sha=commit_sha,
            repository_path=EFEHR_README_REPOSITORY_PATH,
        )
        expected_url = efehr_raw_file_api_url(target)
    except EfehrReceiptError as exc:
        raise ResultError(f"{prefix} target binding is invalid: {exc}") from exc
    for field in ("requested_url", "final_url"):
        if type(receipt[field]) is not str or receipt[field] != expected_url:
            raise ResultError(f"{prefix}.{field} does not match the immutable resolved target")
    _utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    _positive_bounded_int(receipt["byte_count"], "byte_count", EFEHR_README_MAX_BYTES, prefix=prefix)
    if type(receipt["sha256"]) is not str or not DIGEST_RE.fullmatch(receipt["sha256"]):
        raise ResultError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")
    for field in ("content_type", "etag"):
        _bounded_header(receipt[field], field, prefix=prefix)
    return receipt


def validate_efehr_eshm20_tree_metadata(receipt: Any) -> dict[str, Any]:
    prefix = "efehr_eshm20_tree_metadata"
    if type(receipt) is not dict:
        raise ResultError(f"{prefix} must be a JSON object")
    keys = set(receipt)
    if keys != EFEHR_ESHM20_RECEIPT_FIELDS:
        raise ResultError(
            f"{prefix} fields mismatch; "
            f"missing={sorted(EFEHR_ESHM20_RECEIPT_FIELDS - keys)}, "
            f"unexpected={sorted(keys - EFEHR_ESHM20_RECEIPT_FIELDS)}"
        )
    exact_values = {
        "schema_version": EFEHR_ESHM20_SCHEMA_VERSION,
        "operation_id": EFEHR_ESHM20_OPERATION_ID,
        "source_issue": EFEHR_ESHM20_SOURCE_ISSUE,
        "dataset_id": EFEHR_ESHM20_DATASET_ID,
        "provider_host": EFEHR_PROVIDER_HOST,
        "project_id": EFEHR_ESHM20_PROJECT_ID,
        "project_path": EFEHR_ESHM20_PROJECT_PATH,
        "branch": EFEHR_ESHM20_BRANCH,
        "tree_prefix": EFEHR_ESHM20_TREE_PREFIX,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen contract")
    resolved_sha = receipt["resolved_commit_sha"]
    if type(resolved_sha) is not str or not GIT_SHA_RE.fullmatch(resolved_sha):
        raise ResultError(
            f"{prefix}.resolved_commit_sha must be a lowercase 40-character Git SHA"
        )
    _utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    _positive_bounded_int(
        receipt["tree_page_count"], "tree_page_count", EFEHR_ESHM20_MAX_TREE_PAGES, prefix=prefix
    )
    _positive_bounded_int(
        receipt["tree_entry_count"], "tree_entry_count", EFEHR_ESHM20_MAX_TREE_ENTRIES, prefix=prefix
    )
    _positive_bounded_int(
        receipt["metadata_byte_count"], "metadata_byte_count", EFEHR_ESHM20_MAX_METADATA_BYTES, prefix=prefix
    )
    entries = receipt["entries"]
    if type(entries) is not list or len(entries) != receipt["tree_entry_count"]:
        raise ResultError(f"{prefix}.entries must match tree_entry_count")
    previous_path: str | None = None
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"path", "type", "id", "mode"}:
            raise ResultError(f"{prefix}.entries items must contain exactly path/type/id/mode")
        path = entry["path"]
        if type(path) is not str or not (1 <= len(path) <= 1024):
            raise ResultError(f"{prefix}.entries path must be bounded text")
        if (
            "\\" in path
            or "\x00" in path
            or path.startswith("/")
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or not path.startswith(EFEHR_ESHM20_TREE_PREFIX)
        ):
            raise ResultError(f"{prefix}.entries path escaped the frozen tree prefix")
        if previous_path is not None and path <= previous_path:
            raise ResultError(f"{prefix}.entries paths must be unique and strictly sorted")
        previous_path = path
        if type(entry["type"]) is not str or entry["type"] not in {"blob", "tree"}:
            raise ResultError(f"{prefix}.entries type is outside the closed tree policy")
        if type(entry["id"]) is not str or not GIT_SHA_RE.fullmatch(entry["id"]):
            raise ResultError(f"{prefix}.entries id must be a lowercase 40-character Git SHA")
        if type(entry["mode"]) is not str or not re.fullmatch(r"[0-7]{6}", entry["mode"]):
            raise ResultError(f"{prefix}.entries mode is malformed")
    return receipt


def validate_efehr_kosovo_exposure_receipt(receipt: Any) -> dict[str, Any]:
    prefix = "efehr_kosovo_exposure_receipt"
    if type(receipt) is not dict:
        raise ResultError(f"{prefix} must be a JSON object")
    keys = set(receipt)
    if keys != EFEHR_KOSOVO_RECEIPT_FIELDS:
        raise ResultError(
            f"{prefix} fields mismatch; missing={sorted(EFEHR_KOSOVO_RECEIPT_FIELDS - keys)}, "
            f"unexpected={sorted(keys - EFEHR_KOSOVO_RECEIPT_FIELDS)}"
        )
    expected_project_path = str(EFEHR_PROJECTS[EFEHR_KOSOVO_PROJECT_ID]["project_path"])
    exact_values = {
        "schema_version": EFEHR_KOSOVO_SCHEMA_VERSION,
        "operation_id": EFEHR_KOSOVO_OPERATION_ID,
        "source_issue": EFEHR_KOSOVO_SOURCE_ISSUE,
        "dataset_id": EFEHR_KOSOVO_DATASET_ID,
        "provider_host": EFEHR_PROVIDER_HOST,
        "project_id": EFEHR_KOSOVO_PROJECT_ID,
        "project_path": expected_project_path,
        "commit_sha": EFEHR_KOSOVO_COMMIT_SHA,
        "repository_path": EFEHR_KOSOVO_REPOSITORY_PATH,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen contract")
    try:
        target = validate_efehr_target(
            source_issue=EFEHR_KOSOVO_SOURCE_ISSUE,
            dataset_id=EFEHR_KOSOVO_DATASET_ID,
            project_id=EFEHR_KOSOVO_PROJECT_ID,
            commit_sha=EFEHR_KOSOVO_COMMIT_SHA,
            repository_path=EFEHR_KOSOVO_REPOSITORY_PATH,
        )
        expected_url = efehr_raw_file_api_url(target)
    except EfehrReceiptError as exc:
        raise ResultError(f"{prefix} target binding is invalid: {exc}") from exc
    for field in ("requested_url", "final_url"):
        if type(receipt[field]) is not str or receipt[field] != expected_url:
            raise ResultError(f"{prefix}.{field} does not match the immutable frozen target")
    _utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    _positive_bounded_int(receipt["byte_count"], "byte_count", EFEHR_KOSOVO_MAX_BYTES, prefix=prefix)
    if type(receipt["sha256"]) is not str or not DIGEST_RE.fullmatch(receipt["sha256"]):
        raise ResultError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")
    for field in ("content_type", "etag"):
        _bounded_header(receipt[field], field, prefix=prefix)
    return receipt


def validate_efehr_eshm20_root_config_receipt(receipt: Any) -> dict[str, Any]:
    prefix = "efehr_eshm20_root_config_receipt"
    if type(receipt) is not dict:
        raise ResultError(f"{prefix} must be a JSON object")
    keys = set(receipt)
    if keys != EFEHR_ESHM20_ROOT_CONFIG_RECEIPT_FIELDS:
        raise ResultError(
            f"{prefix} fields mismatch; "
            f"missing={sorted(EFEHR_ESHM20_ROOT_CONFIG_RECEIPT_FIELDS - keys)}, "
            f"unexpected={sorted(keys - EFEHR_ESHM20_ROOT_CONFIG_RECEIPT_FIELDS)}"
        )
    expected_project_path = str(
        EFEHR_PROJECTS[EFEHR_ESHM20_ROOT_CONFIG_PROJECT_ID]["project_path"]
    )
    exact_values = {
        "schema_version": EFEHR_ESHM20_ROOT_CONFIG_SCHEMA_VERSION,
        "operation_id": EFEHR_ESHM20_ROOT_CONFIG_OPERATION_ID,
        "source_issue": EFEHR_ESHM20_ROOT_CONFIG_SOURCE_ISSUE,
        "dataset_id": EFEHR_ESHM20_ROOT_CONFIG_DATASET_ID,
        "provider_host": EFEHR_PROVIDER_HOST,
        "project_id": EFEHR_ESHM20_ROOT_CONFIG_PROJECT_ID,
        "project_path": expected_project_path,
        "commit_sha": EFEHR_ESHM20_ROOT_CONFIG_COMMIT_SHA,
        "repository_path": EFEHR_ESHM20_ROOT_CONFIG_REPOSITORY_PATH,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"{prefix}.{field} does not match the frozen contract")
    try:
        target = validate_efehr_target(
            source_issue=EFEHR_ESHM20_ROOT_CONFIG_SOURCE_ISSUE,
            dataset_id=EFEHR_ESHM20_ROOT_CONFIG_DATASET_ID,
            project_id=EFEHR_ESHM20_ROOT_CONFIG_PROJECT_ID,
            commit_sha=EFEHR_ESHM20_ROOT_CONFIG_COMMIT_SHA,
            repository_path=EFEHR_ESHM20_ROOT_CONFIG_REPOSITORY_PATH,
        )
        expected_url = efehr_raw_file_api_url(target)
    except EfehrReceiptError as exc:
        raise ResultError(f"{prefix} target binding is invalid: {exc}") from exc
    for field in ("requested_url", "final_url"):
        if type(receipt[field]) is not str or receipt[field] != expected_url:
            raise ResultError(f"{prefix}.{field} does not match the frozen immutable target")
    _utc_second(receipt["retrieved_at"], f"{prefix}.retrieved_at")
    _positive_bounded_int(
        receipt["byte_count"], "byte_count", EFEHR_ESHM20_ROOT_CONFIG_MAX_BYTES, prefix=prefix
    )
    if type(receipt["sha256"]) is not str or not DIGEST_RE.fullmatch(receipt["sha256"]):
        raise ResultError(f"{prefix}.sha256 must be a lowercase SHA-256 digest")
    for field in ("content_type", "etag"):
        _bounded_header(receipt[field], field, prefix=prefix)
    return receipt


def _validate_request_evidence(evidence: Any) -> dict[str, Any]:
    if type(evidence) is not dict or set(evidence) != REQUEST_EVIDENCE_FIELDS:
        raise ResultError("evidence must be a closed request-validation evidence object")
    for field in REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True:
        raise ResultError("result v1 requires request_validated=true")
    return evidence


def _validate_network_evidence(evidence: Any, *, receipt_field: str) -> dict[str, Any]:
    expected_by_field = {
        "acquisition_receipt": ACQUISITION_EVIDENCE_FIELDS,
        "dwd_metadata_receipt": DWD_METADATA_EVIDENCE_FIELDS,
        "efehr_readme_receipt": EFEHR_README_EVIDENCE_FIELDS,
        "efehr_eshm20_tree_metadata": EFEHR_ESHM20_EVIDENCE_FIELDS,
        "efehr_kosovo_exposure_receipt": EFEHR_KOSOVO_EVIDENCE_FIELDS,
        "efehr_eshm20_root_config_receipt": EFEHR_ESHM20_ROOT_CONFIG_EVIDENCE_FIELDS,
    }
    expected_fields = expected_by_field.get(receipt_field)
    if expected_fields is None:
        raise ResultError("unsupported closed acquisition receipt field")
    if type(evidence) is not dict or set(evidence) != expected_fields:
        raise ResultError(f"evidence must be a closed {receipt_field} evidence object")
    for field in REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True:
        raise ResultError("result v1 requires request_validated=true")
    return evidence


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict:
        raise ResultError("result must be a JSON object")
    keys = set(result)
    if keys != REQUIRED_FIELDS:
        raise ResultError(f"result fields mismatch; missing={sorted(REQUIRED_FIELDS - keys)}, unexpected={sorted(keys - REQUIRED_FIELDS)}")
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    if type(result["repository"]) is not str or not REPOSITORY_RE.fullmatch(result["repository"]):
        raise ResultError("repository must be canonical owner/name")
    if type(result["action"]) is not str or result["action"] not in ALLOWED_ACTIONS:
        raise ResultError("unsupported action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        if type(result[field]) is not str or not GIT_SHA_RE.fullmatch(result[field]):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    dataset_id = result["dataset_id"]
    if type(dataset_id) is not str or not (1 <= len(dataset_id) <= 160) or not SAFE_ID_RE.fullmatch(dataset_id):
        raise ResultError("dataset_id is not a safe bounded identifier")
    try:
        expected_semantic_id = semantic_request_id_from_result(result)
    except ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if result["semantic_request_id"] != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound repository/action/dataset/target/execution fields")
    started = _utc_second(result["started_at"], "started_at")
    finished = _utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase = result["phase"]
    if type(phase) is not str or phase not in ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    status = result["status"]
    if type(status) is not str or status not in ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if type(result["external_bytes_persisted"]) is not bool or result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false in result v1")
    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or a positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        evidence = _validate_request_evidence(result["evidence"])
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

    action = result["action"]
    if action == "acquisition_receipt":
        if result["source_issue"] != 162 or result["dataset_id"] != ACQUISITION_DATASET_ID:
            raise ResultError("acquisition_receipt result is outside the frozen DWD issue/dataset boundary")
        receipt_field = "acquisition_receipt"
        receipt_validator = validate_acquisition_receipt
    elif action == "dwd_metadata_receipt":
        if result["source_issue"] != DWD_METADATA_SOURCE_ISSUE or result["dataset_id"] != DWD_METADATA_DATASET_ID:
            raise ResultError("dwd_metadata_receipt result is outside the frozen DWD issue/dataset boundary")
        receipt_field = "dwd_metadata_receipt"
        receipt_validator = validate_dwd_metadata_receipt
    elif action == "efehr_readme_receipt":
        if result["source_issue"] != EFEHR_ACTION_ISSUE or result["dataset_id"] != EFEHR_README_DATASET_ID:
            raise ResultError("efehr_readme_receipt result is outside the frozen issue/dataset boundary")
        receipt_field = "efehr_readme_receipt"
        receipt_validator = validate_efehr_readme_receipt
    elif action == "efehr_eshm20_tree_metadata":
        if (
            result["source_issue"] != EFEHR_ESHM20_ACTION_ISSUE
            or result["dataset_id"] != EFEHR_ESHM20_DATASET_ID
        ):
            raise ResultError("efehr_eshm20_tree_metadata result is outside the frozen issue/dataset boundary")
        receipt_field = "efehr_eshm20_tree_metadata"
        receipt_validator = validate_efehr_eshm20_tree_metadata
    elif action == "efehr_kosovo_exposure_receipt":
        if (
            result["source_issue"] != EFEHR_KOSOVO_ACTION_ISSUE
            or result["dataset_id"] != EFEHR_KOSOVO_DATASET_ID
        ):
            raise ResultError(
                "efehr_kosovo_exposure_receipt result is outside the frozen issue/dataset boundary"
            )
        receipt_field = "efehr_kosovo_exposure_receipt"
        receipt_validator = validate_efehr_kosovo_exposure_receipt
    elif action == "efehr_eshm20_root_config_receipt":
        if (
            result["source_issue"] != EFEHR_ESHM20_ROOT_CONFIG_ACTION_ISSUE
            or result["dataset_id"] != EFEHR_ESHM20_ROOT_CONFIG_DATASET_ID
        ):
            raise ResultError(
                "efehr_eshm20_root_config_receipt result is outside the frozen issue/dataset boundary"
            )
        receipt_field = "efehr_eshm20_root_config_receipt"
        receipt_validator = validate_efehr_eshm20_root_config_receipt
    else:
        raise ResultError("acquisition_receipt phase requires a closed network acquisition action")
    evidence = _validate_network_evidence(result["evidence"], receipt_field=receipt_field)
    if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
        raise ResultError("acquisition_receipt phase requires complete ledger scan and no prior reuse")
    if duplicate_id is not None:
        raise ResultError("acquisition_receipt phase cannot carry duplicate_result_comment_id")
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful acquisition_receipt cannot carry failure_class")
        receipt = receipt_validator(evidence[receipt_field])
        retrieved = _utc_second(receipt["retrieved_at"], f"{receipt_field}.retrieved_at")
        if retrieved < started or retrieved > finished:
            raise ResultError(f"{receipt_field}.retrieved_at must fall within action start/finish bounds")
    elif status == "blocked":
        if failure_class != ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked acquisition_receipt must identify acquisition_failed")
        if evidence[receipt_field] is not None:
            raise ResultError("blocked acquisition_receipt cannot carry a receipt")
    else:
        raise ResultError("duplicate network acquisition must remain in request_validation phase")
    return result


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
