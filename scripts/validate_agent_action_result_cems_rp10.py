# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Extend Agent Action result validation for the fixed CEMS Europe RP10 receipt."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_europe_rp10_receipt as _cems
    from scripts import agent_action_protocol_cems_rp10 as _protocol
    from scripts import validate_agent_action_result_country_risk as _legacy
    from scripts.validate_agent_action_request_cems_rp10 import (
        CEMS_RP10_RECEIPT_ACTION,
        CEMS_RP10_RECEIPT_DATASET_ID,
        CEMS_RP10_RECEIPT_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    import acquire_cems_europe_rp10_receipt as _cems
    import agent_action_protocol_cems_rp10 as _protocol
    import validate_agent_action_result_country_risk as _legacy
    from validate_agent_action_request_cems_rp10 import (
        CEMS_RP10_RECEIPT_ACTION,
        CEMS_RP10_RECEIPT_DATASET_ID,
        CEMS_RP10_RECEIPT_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._legacy
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_RP10_RECEIPT_ACTION}
_CEMS_FIELD = "cems_europe_rp10_receipt"
_CEMS_EVIDENCE_FIELDS = _legacy.REQUEST_EVIDENCE_FIELDS | {_CEMS_FIELD}
_CEMS_RECEIPT_FIELDS = {
    "schema_version",
    "dataset_id",
    "source_issue",
    "release",
    "release_date",
    "doi",
    "return_period_years",
    "filename",
    "requested_url",
    "final_url",
    "retrieved_at",
    "http_status",
    "media_type",
    "content_length_header",
    "byte_count",
    "sha256",
    "external_bytes_persisted",
    "geotiff_semantics_verified",
    "benchmark_use_authorized",
    "publication_authorized",
    "model_use_authorized",
}


def validate_cems_rp10_receipt(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _CEMS_RECEIPT_FIELDS:
        raise ResultError("CEMS RP10 receipt fields drifted")
    exact_values = {
        "schema_version": _cems.SCHEMA_VERSION,
        "dataset_id": _cems.DATASET_ID,
        "source_issue": _cems.SOURCE_ISSUE,
        "release": _cems.RELEASE,
        "release_date": _cems.RELEASE_DATE,
        "doi": _cems.DOI,
        "return_period_years": _cems.RETURN_PERIOD_YEARS,
        "filename": _cems.FILENAME,
        "requested_url": _cems.SOURCE_URL,
        "final_url": _cems.SOURCE_URL,
        "http_status": 200,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact_values.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS RP10 receipt {field} drifted from frozen authority")

    _base._utc_second(receipt["retrieved_at"], "cems_europe_rp10_receipt.retrieved_at")
    media_type = receipt["media_type"]
    if type(media_type) is not str or media_type not in _cems.ALLOWED_MEDIA_TYPES:
        raise ResultError("CEMS RP10 receipt media_type is outside the fixed contract")
    byte_count = receipt["byte_count"]
    if type(byte_count) is not int or isinstance(byte_count, bool) or not (
        1 <= byte_count <= _cems.MAX_BYTES
    ):
        raise ResultError("CEMS RP10 receipt byte_count is outside bounded policy")
    declared = receipt["content_length_header"]
    if declared is not None:
        if type(declared) is not int or isinstance(declared, bool) or not (
            1 <= declared <= _cems.MAX_BYTES
        ):
            raise ResultError("CEMS RP10 receipt Content-Length is outside bounded policy")
        if declared != byte_count:
            raise ResultError("CEMS RP10 receipt Content-Length does not match byte_count")
    digest = receipt["sha256"]
    if type(digest) is not str or not _legacy.DIGEST_RE.fullmatch(digest):
        raise ResultError("CEMS RP10 receipt sha256 is invalid")
    return receipt


def _validate_request_validation_state(
    result: dict[str, Any], *, status: str, duplicate_id: Any, failure_class: Any
) -> dict[str, Any]:
    evidence = _base._validate_request_evidence(result["evidence"])
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


def _validate_cems_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("CEMS RP10 result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _legacy.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _legacy.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_RP10_RECEIPT_ACTION:
        raise ResultError("unsupported CEMS RP10 action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _legacy.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("CEMS RP10 network result requires target_sha == execution_sha")
    if result["source_issue"] != CEMS_RP10_RECEIPT_ISSUE:
        raise ResultError("CEMS RP10 result is outside frozen control issue 793")
    if result["dataset_id"] != CEMS_RP10_RECEIPT_DATASET_ID:
        raise ResultError("CEMS RP10 result is outside the frozen dataset")

    try:
        expected_semantic_id = _protocol.semantic_request_id_from_result(result)
    except _protocol.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if semantic_id != expected_semantic_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = _base._utc_second(result["started_at"], "started_at")
    finished = _base._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase = result["phase"]
    status = result["status"]
    if type(phase) is not str or phase not in _legacy.ALLOWED_PHASES:
        raise ResultError("unsupported result phase")
    if type(status) is not str or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        return _validate_request_validation_state(
            result,
            status=status,
            duplicate_id=duplicate_id,
            failure_class=failure_class,
        )
    if phase != "acquisition_receipt":
        raise ResultError("CEMS RP10 network result requires acquisition_receipt phase")

    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _CEMS_EVIDENCE_FIELDS:
        raise ResultError("CEMS RP10 evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError("CEMS RP10 acquisition requires complete non-reused ledger state")

    receipt = evidence[_CEMS_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful CEMS RP10 acquisition cannot carry failure_class")
        receipt = validate_cems_rp10_receipt(receipt)
        retrieved = _base._utc_second(receipt["retrieved_at"], f"{_CEMS_FIELD}.retrieved_at")
        if retrieved < started or retrieved > finished:
            raise ResultError("CEMS RP10 retrieved_at must fall within action bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS RP10 acquisition failure class is invalid")
        if receipt is not None:
            raise ResultError("blocked CEMS RP10 acquisition cannot publish a receipt")
    else:
        raise ResultError("duplicate CEMS RP10 result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == CEMS_RP10_RECEIPT_ACTION:
        return _validate_cems_result(result)
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
        result = validate_result(_base._strict_json(os.environ[args.result_env]))
    except ResultError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
