# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed validator for durable Agent Action Dispatch result receipts."""

from __future__ import annotations

import argparse
import json
import os
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

REQUIRED_FIELDS = {
    "schema_version", "semantic_request_id", "repository", "action",
    "source_issue", "source_comment_id", "target_sha", "dataset_id", "execution_sha",
    "run_id", "run_attempt", "started_at", "finished_at", "phase", "status",
    "external_bytes_persisted", "evidence", "duplicate_result_comment_id", "failure_class",
}
EVIDENCE_FIELDS = {"request_validated", "ledger_scan_complete", "prior_result_reused"}
ALLOWED_ACTIONS = {"sample_audit"}
ALLOWED_STATUSES = {"pass", "duplicate", "blocked"}


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
    if result["phase"] != "request_validation":
        raise ResultError("unsupported result phase")
    status = result["status"]
    if type(status) is not str or status not in ALLOWED_STATUSES:
        raise ResultError("unsupported result status")
    if type(result["external_bytes_persisted"]) is not bool or result["external_bytes_persisted"] is not False:
        raise ResultError("external_bytes_persisted must be exactly false in result v1")

    evidence = result["evidence"]
    if type(evidence) is not dict or set(evidence) != EVIDENCE_FIELDS:
        raise ResultError("evidence must be a closed request-validation evidence object")
    for field in EVIDENCE_FIELDS:
        if type(evidence[field]) is not bool:
            raise ResultError(f"evidence.{field} must be boolean")
    if evidence["request_validated"] is not True:
        raise ResultError("result v1 requires request_validated=true")

    duplicate_id = result["duplicate_result_comment_id"]
    failure_class = result["failure_class"]
    if duplicate_id is not None and (type(duplicate_id) is not int or duplicate_id < 1):
        raise ResultError("duplicate_result_comment_id must be null or a positive integer")
    if failure_class is not None and type(failure_class) is not str:
        raise ResultError("failure_class must be null or text")

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
            raise ResultError("blocked result must identify ledger_incomplete")
        if evidence["ledger_scan_complete"] is not False or evidence["prior_result_reused"] is not False:
            raise ResultError("blocked result requires incomplete ledger and no prior reuse")
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
