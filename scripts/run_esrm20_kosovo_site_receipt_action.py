# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed trusted-main action for the frozen ESRM20 Kosovo site receipt.

This adapter deliberately does not add another caller-selectable EFEHR target.
It exposes only an owner-requested, exact-main execution of the already-reviewed
fixed worker from #339. A PASS proves byte identity only; XML/site semantics and
model-use authority remain separate review gates under #291/#284.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
from scripts.acquire_efehr_kosovo_site_receipt import acquire_kosovo_site_receipt

REQUEST_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-receipt-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-kosovo-site-receipt-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-kosovo-site-receipt-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-kosovo-site-receipt-result-v1"
ACTION = "esrm20_kosovo_site_model_receipt"
CONTROL_ISSUE = 342
SOURCE_SCIENCE_ISSUE = 284
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Vs30/Site_model_Kosovo.xml"
WORKER_OPERATION_ID = "esrm20-kosovo-site-model-v1"

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "requester",
}


class SiteReceiptActionError(RuntimeError):
    """Fail-closed trusted action error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise SiteReceiptActionError("duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value: str) -> Any:
    raise SiteReceiptActionError(f"non-finite JSON constant: {value}")


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != CONTROL_ISSUE:
        raise SiteReceiptActionError("wrong runtime issue")
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteReceiptActionError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise SiteReceiptActionError("invalid site receipt request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise SiteReceiptActionError("site receipt request envelope is not canonical")
    try:
        request = json.loads(
            after.strip(),
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except SiteReceiptActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SiteReceiptActionError("invalid site receipt request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise SiteReceiptActionError("site receipt request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", CONTROL_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteReceiptActionError(f"site receipt request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or not _SAFE_REQUESTER_RE.fullmatch(requester)
    ):
        raise SiteReceiptActionError("invalid requester identity")
    return request


def _validate_receipt(receipt: object) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise SiteReceiptActionError("site worker returned a non-object receipt")
    exact = (
        ("schema_version", "oc-efehr-trusted-acquisition-v1"),
        ("operation_id", WORKER_OPERATION_ID),
        ("source_issue", SOURCE_SCIENCE_ISSUE),
        ("dataset_id", DATASET_ID),
        ("provider_host", "gitlab.seismo.ethz.ch"),
        ("project_id", PROJECT_ID),
        ("project_path", PROJECT_PATH),
        ("commit_sha", COMMIT_SHA),
        ("repository_path", REPOSITORY_PATH),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
    )
    for field, expected in exact:
        observed = receipt.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise SiteReceiptActionError(f"site receipt identity drifted at {field}")
    byte_count = receipt.get("byte_count")
    if type(byte_count) is not int or isinstance(byte_count, bool) or byte_count <= 0:
        raise SiteReceiptActionError("site receipt byte count is invalid")
    digest = receipt.get("sha256")
    if type(digest) is not str or not _DIGEST_RE.fullmatch(digest):
        raise SiteReceiptActionError("site receipt SHA-256 is invalid")
    retrieved_at = receipt.get("retrieved_at")
    if type(retrieved_at) is not str or not retrieved_at:
        raise SiteReceiptActionError("site receipt retrieval time is invalid")
    for field, value in receipt.items():
        if field.endswith("_authorized") or field.endswith("_persisted"):
            if value is not False:
                raise SiteReceiptActionError(
                    f"site receipt widened authority at {field}"
                )
    return receipt


def _base_result(*, execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "source_science_issue": SOURCE_SCIENCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "site_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
            "worker_operation_id": WORKER_OPERATION_ID,
        },
        "site_xml_semantics_verified": False,
        "crs_coordinate_semantics_verified": False,
        "site_parameter_units_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def run_site_receipt(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or not _SHA_RE.fullmatch(execution_sha):
        raise SiteReceiptActionError("invalid execution SHA")
    result = _base_result(execution_sha=execution_sha)
    try:
        receipt = _validate_receipt(acquire_kosovo_site_receipt())
    except (EfehrAcquisitionError, SiteReceiptActionError):
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipt": None,
            }
        )
        return result
    result.update(
        {
            "status": "pass",
            "failure_class": None,
            "receipt": {
                "retrieved_at": receipt["retrieved_at"],
                "byte_count": receipt["byte_count"],
                "sha256": receipt["sha256"],
                "content_type": receipt.get("content_type"),
                "etag": receipt.get("etag"),
            },
        }
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(
        body,
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")
    result = run_site_receipt(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
