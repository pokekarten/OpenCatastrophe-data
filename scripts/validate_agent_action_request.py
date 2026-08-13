# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate one bounded agent-action request embedded in a GitHub comment."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

MARKER = "<!-- oc-action-request-v1 -->"
SCHEMA_VERSION = "oc-action-request-v1"
SAMPLE_AUDIT_ACTION = "sample_audit"
ACQUISITION_RECEIPT_ACTION = "acquisition_receipt"
DWD_METADATA_RECEIPT_ACTION = "dwd_metadata_receipt"
EFEHR_README_RECEIPT_ACTION = "efehr_readme_receipt"
ACQUISITION_RECEIPT_ISSUE = 162
DWD_METADATA_RECEIPT_ISSUE = 211
EFEHR_README_RECEIPT_ISSUE = 298
ACQUISITION_RECEIPT_DATASET_ID = "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03"
DWD_METADATA_RECEIPT_DATASET_ID = ACQUISITION_RECEIPT_DATASET_ID
EFEHR_README_RECEIPT_DATASET_ID = "efehr.esrm20.european-exposure-model.v1.0"
ALLOWED_ACTIONS = {
    SAMPLE_AUDIT_ACTION,
    ACQUISITION_RECEIPT_ACTION,
    DWD_METADATA_RECEIPT_ACTION,
    EFEHR_README_RECEIPT_ACTION,
}
REQUIRED_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SHA256_HEX = re.compile(r"^[a-f0-9]{40}$")


class RequestError(ValueError):
    """Raised when an action request is not exactly valid."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RequestError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_strict_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                RequestError(f"non-finite JSON value: {token}")
            ),
        )
    except (json.JSONDecodeError, RequestError) as exc:
        raise RequestError(f"invalid request JSON: {exc}") from exc
    if type(value) is not dict:
        raise RequestError("request must be a JSON object")
    return value


def extract_request(comment_body: str) -> dict[str, Any]:
    """Extract exactly one marker followed by exactly one JSON object."""
    if comment_body.count(MARKER) != 1:
        raise RequestError("comment must contain exactly one action-request marker")
    prefix, payload = comment_body.split(MARKER, 1)
    if prefix.strip():
        raise RequestError("action-request marker must be the first non-whitespace content")
    payload = payload.strip()
    if not payload:
        raise RequestError("action-request payload is missing")
    decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicate_keys)
    try:
        value, end = decoder.raw_decode(payload)
    except (json.JSONDecodeError, RequestError) as exc:
        raise RequestError(f"invalid request JSON: {exc}") from exc
    if payload[end:].strip():
        raise RequestError("unexpected content after action-request JSON")
    if type(value) is not dict:
        raise RequestError("request must be a JSON object")
    return _load_strict_json(payload)


def validate_request(request: dict[str, Any], *, expected_issue: int | None = None) -> dict[str, Any]:
    keys = set(request)
    if keys != REQUIRED_FIELDS:
        missing = sorted(REQUIRED_FIELDS - keys)
        unexpected = sorted(keys - REQUIRED_FIELDS)
        raise RequestError(f"request fields mismatch; missing={missing}, unexpected={unexpected}")

    if request["schema_version"] != SCHEMA_VERSION:
        raise RequestError("unsupported schema_version")
    if type(request["action"]) is not str or request["action"] not in ALLOWED_ACTIONS:
        raise RequestError("unsupported action")
    if type(request["issue"]) is not int or request["issue"] < 1:
        raise RequestError("issue must be a positive integer")
    if expected_issue is not None and request["issue"] != expected_issue:
        raise RequestError("request issue does not match triggering GitHub issue/PR")
    if type(request["target_sha"]) is not str or not SHA256_HEX.fullmatch(request["target_sha"]):
        raise RequestError("target_sha must be a lowercase 40-character commit SHA")

    for field, limit in (("dataset_id", 160), ("requester", 128)):
        value = request[field]
        if type(value) is not str or not (1 <= len(value) <= limit) or not SAFE_ID.fullmatch(value):
            raise RequestError(f"{field} is not a safe bounded identifier")

    if request["action"] == ACQUISITION_RECEIPT_ACTION:
        if request["issue"] != ACQUISITION_RECEIPT_ISSUE:
            raise RequestError("acquisition_receipt is restricted to issue 162")
        if request["dataset_id"] != ACQUISITION_RECEIPT_DATASET_ID:
            raise RequestError("acquisition_receipt is restricted to the frozen DWD dataset")
    elif request["action"] == DWD_METADATA_RECEIPT_ACTION:
        if request["issue"] != DWD_METADATA_RECEIPT_ISSUE:
            raise RequestError("dwd_metadata_receipt is restricted to issue 211")
        if request["dataset_id"] != DWD_METADATA_RECEIPT_DATASET_ID:
            raise RequestError("dwd_metadata_receipt is restricted to the frozen DWD dataset")
    elif request["action"] == EFEHR_README_RECEIPT_ACTION:
        if request["issue"] != EFEHR_README_RECEIPT_ISSUE:
            raise RequestError("efehr_readme_receipt is restricted to issue 298")
        if request["dataset_id"] != EFEHR_README_RECEIPT_DATASET_ID:
            raise RequestError("efehr_readme_receipt is restricted to the frozen ESRM20 exposure dataset")

    return request


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.comment_body_env not in os.environ:
        print("invalid request: comment body environment variable is absent", file=sys.stderr)
        return 2
    try:
        request = extract_request(os.environ[args.comment_body_env])
        validate_request(request, expected_issue=args.expected_issue)
    except RequestError as exc:
        print(f"invalid request: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(request, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
