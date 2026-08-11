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

REQUIRED_FIELDS = {
    "schema_version", "semantic_request_id", "repository", "action",
    "source_issue", "source_comment_id", "target_sha", "dataset_id", "execution_sha",
    "run_id", "run_attempt", "started_at", "finished_at", "phase", "status",
    "external_bytes_persisted", "evidence", "duplicate_result_comment_id", "failure_class",
}
REQUEST_EVIDENCE_FIELDS = {"request_validated", "ledger_scan_complete", "prior_result_reused"}
ACQUISITION_EVIDENCE_FIELDS = REQUEST_EVIDENCE_FIELDS | {"acquisition_receipt"}
ACQUISITION_RECEIPT_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "requested_url", "final_url",
    "filename", "retrieved_at", "byte_count", "sha256", "content_type",
    "last_modified", "etag", "archive_member_count", "archive_uncompressed_bytes",
    "product_member", "product_station_id", "product_begin_date", "product_end_date",
    "product_row_count", "product_structure_validated", "external_bytes_persisted",
    "publication_authorized",
}
ALLOWED_ACTIONS = {"sample_audit", "acquisition_receipt"}
ALLOWED_PHASES = {"request_validation", "acquisition_receipt"}
ALLOWED_STATUSES = {"pass", "duplicate", "blocked"}
ACQUISITION_FAILURE_CLASS = "acquisition_failed"
PRODUCT_MEMBER_RE = re.compile(r"(^|/)produkt_extrema_wind_[^/]+\.txt$")


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


def _bounded_header(value: Any, field: str) -> None:
    if value is None:
        return
    if type(value) is not str or len(value) > 512:
        raise ResultError(f"acquisition_receipt.{field} must be null or bounded text")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ResultError(f"acquisition_receipt.{field} contains control characters")


def _positive_bounded_int(value: Any, field: str, maximum: int) -> None:
    if type(value) is not int or not (1 <= value <= maximum):
        raise ResultError(f"acquisition_receipt.{field} must be an integer in [1,{maximum}]")


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
    _positive_bounded_int(
        receipt["archive_uncompressed_bytes"],
        "archive_uncompressed_bytes",
        MAX_UNCOMPRESSED_BYTES,
    )
    member = receipt["product_member"]
    if type(member) is not str or not (1 <= len(member) <= 512) or not PRODUCT_MEMBER_RE.fullmatch(member):
        raise ResultError("acquisition_receipt.product_member does not match the frozen product contract")
    _positive_bounded_int(receipt["product_row_count"], "product_row_count", 1_000_000)
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


def _validate_acquisition_evidence(evidence: Any) -> dict[str, Any]:
    if type(evidence) is not dict or set(evidence) != ACQUISITION_EVIDENCE_FIELDS:
        raise ResultError("evidence must be a closed acquisition-receipt evidence object")
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
        raise ResultError(
            f"result fields mismatch; missing={sorted(REQUIRED_FIELDS - keys)}, "
            f"unexpected={sorted(keys - REQUIRED_FIELDS)}"
        )
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

    if result["action"] != "acquisition_receipt":
        raise ResultError("acquisition_receipt phase requires acquisition_receipt action")
    if result["source_issue"] != 162 or result["dataset_id"] != ACQUISITION_DATASET_ID:
        raise ResultError("acquisition_receipt result is outside the frozen DWD issue/dataset boundary")
    evidence = _validate_acquisition_evidence(result["evidence"])
    if evidence["ledger_scan_complete"] is not True or evidence["prior_result_reused"] is not False:
        raise ResultError("acquisition_receipt phase requires complete ledger scan and no prior reuse")
    if duplicate_id is not None:
        raise ResultError("acquisition_receipt phase cannot carry duplicate_result_comment_id")
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful acquisition_receipt cannot carry failure_class")
        receipt = validate_acquisition_receipt(evidence["acquisition_receipt"])
        retrieved = _utc_second(receipt["retrieved_at"], "acquisition_receipt.retrieved_at")
        if retrieved < started or retrieved > finished:
            raise ResultError("acquisition_receipt.retrieved_at must fall within action start/finish bounds")
    elif status == "blocked":
        if failure_class != ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked acquisition_receipt must identify acquisition_failed")
        if evidence["acquisition_receipt"] is not None:
            raise ResultError("blocked acquisition_receipt cannot carry a receipt")
    else:
        raise ResultError("duplicate acquisition_receipt must remain in request_validation phase")
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-env", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    text = os.environ.get(args.result_env)
    if text is None:
        print("invalid result: environment variable is absent", file=sys.stderr)
        return 2
    try:
        result = validate_result(_strict_json(text))
    except (ResultError, ProtocolError) as exc:
        print(f"invalid result: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
