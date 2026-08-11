# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed validator for durable Agent Action Dispatch result receipts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

try:
    from scripts.agent_action_protocol import DIGEST_RE, GIT_SHA_RE, RESULT_SCHEMA_VERSION, SAFE_ID_RE, ProtocolError
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from agent_action_protocol import DIGEST_RE, GIT_SHA_RE, RESULT_SCHEMA_VERSION, SAFE_ID_RE, ProtocolError

REQUIRED_FIELDS = {
    "schema_version",
    "semantic_request_id",
    "action",
    "source_issue",
    "source_comment_id",
    "target_sha",
    "dataset_id",
    "execution_sha",
    "run_id",
    "run_attempt",
    "phase",
    "status",
    "external_bytes_persisted",
    "duplicate_result_comment_id",
    "failure_class",
}
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
            parse_constant=lambda token: (_ for _ in ()).throw(
                ResultError(f"non-finite JSON value: {token}")
            ),
        )
    except (json.JSONDecodeError, ResultError) as exc:
        raise ResultError(f"invalid result JSON: {exc}") from exc
    if type(value) is not dict:
        raise ResultError("result must be a JSON object")
    return value


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    if type(result) is not dict:
        raise ResultError("result must be a JSON object")
    keys = set(result)
    if keys != REQUIRED_FIELDS:
        raise ResultError(
            f"result fields mismatch; missing={sorted(REQUIRED_FIELDS - keys)}, unexpected={sorted(keys - REQUIRED_FIELDS)}"
        )
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ResultError("unsupported schema_version")
    if type(result["semantic_request_id"]) is not str or not DIGEST_RE.fullmatch(result["semantic_request_id"]):
        raise ResultError("semantic_request_id must be a lowercase SHA-256 digest")
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
    if result["phase"] != "request_validation":
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
    if status == "pass" and (duplicate_id is not None or failure_class is not None):
        raise ResultError("pass result cannot carry duplicate/failure state")
    if status == "duplicate" and (duplicate_id is None or failure_class != "duplicate_request"):
        raise ResultError("duplicate result requires prior result comment identity")
    if status == "blocked" and (duplicate_id is not None or failure_class != "ledger_incomplete"):
        raise ResultError("blocked result must identify ledger_incomplete")
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
