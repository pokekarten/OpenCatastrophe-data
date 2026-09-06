# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate durable Agent Action results for fixed CEMS companion-mask receipts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts import acquire_cems_europe_mask_receipts as _masks
    from scripts import agent_action_protocol_cems_masks as _protocol
    from scripts import validate_agent_action_result_cems_rp10_profile as _legacy
    from scripts.validate_agent_action_request_cems_masks import (
        CEMS_MASK_RECEIPTS_ACTION,
        CEMS_MASK_RECEIPTS_DATASET_ID,
        CEMS_MASK_RECEIPTS_ISSUE,
    )
except ModuleNotFoundError:  # pragma: no cover
    import acquire_cems_europe_mask_receipts as _masks
    import agent_action_protocol_cems_masks as _protocol
    import validate_agent_action_result_cems_rp10_profile as _legacy
    from validate_agent_action_request_cems_masks import (
        CEMS_MASK_RECEIPTS_ACTION,
        CEMS_MASK_RECEIPTS_DATASET_ID,
        CEMS_MASK_RECEIPTS_ISSUE,
    )

for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_legacy, _name)

_base = _legacy._base
ALLOWED_ACTIONS = _legacy.ALLOWED_ACTIONS | {CEMS_MASK_RECEIPTS_ACTION}
_CEMS_MASK_FIELD = "cems_europe_mask_receipts"
_CEMS_MASK_EVIDENCE_FIELDS = _legacy._CEMS_PROFILE_EVIDENCE_FIELDS - {
    _legacy._CEMS_PROFILE_FIELD
} | {_CEMS_MASK_FIELD}
_AGGREGATE_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "release", "receipts",
    "external_bytes_persisted", "geotiff_semantics_verified", "mask_values_inspected",
    "benchmark_use_authorized", "publication_authorized", "model_use_authorized",
}
_RECEIPT_FIELDS = {
    "schema_version", "dataset_id", "source_issue", "release", "release_date", "doi",
    "mask_kind", "filename", "requested_url", "final_url", "retrieved_at", "http_status",
    "media_type", "content_length_header", "byte_count", "sha256",
    "external_bytes_persisted", "geotiff_semantics_verified", "mask_values_inspected",
    "benchmark_use_authorized", "publication_authorized", "model_use_authorized",
}


def _validate_one(receipt: Any, *, kind: str, filename: str) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _RECEIPT_FIELDS:
        raise ResultError("CEMS mask receipt fields drifted")
    url = _masks.BASE_URL + filename
    exact = {
        "schema_version": _masks.RECEIPT_SCHEMA_VERSION,
        "dataset_id": _masks.DATASET_ID,
        "source_issue": _masks.SOURCE_ISSUE,
        "release": _masks.RELEASE,
        "release_date": _masks.RELEASE_DATE,
        "doi": _masks.DOI,
        "mask_kind": kind,
        "filename": filename,
        "requested_url": url,
        "final_url": url,
        "http_status": 200,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "mask_values_inspected": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS mask receipt {field} drifted from frozen authority")
    _base._utc_second(receipt["retrieved_at"], f"{_CEMS_MASK_FIELD}.{kind}.retrieved_at")
    media = receipt["media_type"]
    if type(media) is not str or media not in _masks._base.ALLOWED_MEDIA_TYPES:
        raise ResultError("CEMS mask receipt media_type is outside fixed contract")
    byte_count = receipt["byte_count"]
    if type(byte_count) is not int or isinstance(byte_count, bool) or not (
        1 <= byte_count <= _masks._base.MAX_BYTES
    ):
        raise ResultError("CEMS mask receipt byte_count is outside bounded policy")
    declared = receipt["content_length_header"]
    if declared is not None:
        if type(declared) is not int or isinstance(declared, bool) or declared != byte_count:
            raise ResultError("CEMS mask receipt Content-Length does not match byte_count")
    digest = receipt["sha256"]
    if type(digest) is not str or not _legacy.DIGEST_RE.fullmatch(digest):
        raise ResultError("CEMS mask receipt sha256 is invalid")
    return receipt


def validate_cems_mask_receipts(receipt: Any) -> dict[str, Any]:
    if type(receipt) is not dict or set(receipt) != _AGGREGATE_FIELDS:
        raise ResultError("CEMS mask aggregate receipt fields drifted")
    exact = {
        "schema_version": _masks.SCHEMA_VERSION,
        "dataset_id": _masks.DATASET_ID,
        "source_issue": _masks.SOURCE_ISSUE,
        "release": _masks.RELEASE,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "mask_values_inspected": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    for field, expected in exact.items():
        if type(receipt[field]) is not type(expected) or receipt[field] != expected:
            raise ResultError(f"CEMS mask aggregate {field} drifted from frozen authority")
    items = receipt["receipts"]
    if type(items) is not list or len(items) != len(_masks.ASSETS):
        raise ResultError("CEMS mask aggregate receipt count drifted")
    for item, (kind, filename) in zip(items, _masks.ASSETS, strict=True):
        _validate_one(item, kind=kind, filename=filename)
    return receipt


def _validate_mask_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict or set(result) != _legacy.REQUIRED_FIELDS:
        raise ResultError("CEMS mask result fields drifted")
    if result["schema_version"] != _legacy.RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    semantic_id = result["semantic_request_id"]
    if type(semantic_id) is not str or not _legacy.DIGEST_RE.fullmatch(semantic_id):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
    repository = result["repository"]
    if type(repository) is not str or not _legacy.REPOSITORY_RE.fullmatch(repository):
        raise ResultError("repository must be canonical owner/name")
    if result["action"] != CEMS_MASK_RECEIPTS_ACTION:
        raise ResultError("unsupported CEMS mask action")
    for field in ("source_issue", "source_comment_id", "run_id", "run_attempt"):
        if type(result[field]) is not int or isinstance(result[field], bool) or result[field] < 1:
            raise ResultError(f"{field} must be a positive integer")
    for field in ("target_sha", "execution_sha"):
        value = result[field]
        if type(value) is not str or not _legacy.GIT_SHA_RE.fullmatch(value):
            raise ResultError(f"{field} must be a lowercase 40-character Git commit SHA")
    if result["target_sha"] != result["execution_sha"]:
        raise ResultError("CEMS mask network result requires target_sha == execution_sha")
    if result["source_issue"] != CEMS_MASK_RECEIPTS_ISSUE:
        raise ResultError("CEMS mask result is outside control issue 809")
    if result["dataset_id"] != CEMS_MASK_RECEIPTS_DATASET_ID:
        raise ResultError("CEMS mask result is outside frozen dataset")
    try:
        expected_id = _protocol.semantic_request_id_from_result(result)
    except _protocol.ProtocolError as exc:
        raise ResultError(f"semantic request binding is invalid: {exc}") from exc
    if semantic_id != expected_id:
        raise ResultError("semantic_request_id does not match bound result fields")

    started = _base._utc_second(result["started_at"], "started_at")
    finished = _base._utc_second(result["finished_at"], "finished_at")
    if finished < started:
        raise ResultError("finished_at must not precede started_at")
    phase, status = result["phase"], result["status"]
    if phase not in _legacy.ALLOWED_PHASES or status not in _legacy.ALLOWED_STATUSES:
        raise ResultError("unsupported CEMS mask result state")
    if result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false")
    duplicate_id, failure_class = result["duplicate_result_comment_id"], result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

    if phase == "request_validation":
        return _legacy._legacy._validate_request_validation_state(
            result, status=status, duplicate_id=duplicate_id, failure_class=failure_class
        )
    if phase != "acquisition_receipt":
        raise ResultError("CEMS mask network result requires acquisition_receipt phase")
    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != _CEMS_MASK_EVIDENCE_FIELDS:
        raise ResultError("CEMS mask evidence fields drifted")
    for field in _legacy.REQUEST_EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if (
        evidence["request_validated"] is not True
        or evidence["ledger_scan_complete"] is not True
        or evidence["prior_result_reused"] is not False
        or duplicate_id is not None
    ):
        raise ResultError("CEMS mask acquisition requires complete non-reused ledger state")

    aggregate = evidence[_CEMS_MASK_FIELD]
    if status == "pass":
        if failure_class is not None:
            raise ResultError("successful CEMS mask acquisition cannot carry failure_class")
        aggregate = validate_cems_mask_receipts(aggregate)
        for item in aggregate["receipts"]:
            retrieved = _base._utc_second(item["retrieved_at"], f"{_CEMS_MASK_FIELD}.retrieved_at")
            if retrieved < started or retrieved > finished:
                raise ResultError("CEMS mask retrieved_at must fall within action bounds")
    elif status == "blocked":
        if failure_class != _legacy.ACQUISITION_FAILURE_CLASS:
            raise ResultError("blocked CEMS mask acquisition failure class is invalid")
        if aggregate is not None:
            raise ResultError("blocked CEMS mask acquisition cannot publish receipts")
    else:
        raise ResultError("duplicate CEMS mask result must remain request_validation")
    return result


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is dict and result.get("action") == CEMS_MASK_RECEIPTS_ACTION:
        return _validate_mask_result(result)
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
