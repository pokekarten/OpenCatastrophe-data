# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Diagnose which reviewed hazard parser rejects the exact receipted ESRM20 bytes.

This diagnostic intentionally publishes no provider content, paths beyond the
already-public receipt identities, parser exception text, model tokens, or
argument values. It exists only to distinguish source-tree versus GSIM-tree
parser incompatibility after the main #481 gate failed closed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from scripts import profile_eshm20_gsim_identities as gsim_identity
from scripts import run_esrm20_hazard_logic_tree_profile_action as subject
from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError, _open_fixed
from scripts.openquake_source_model_logic_tree_dependencies import (
    OpenQuakeLogicTreeError,
    extract_source_model_logic_tree_dependencies,
)

REQUEST_MARKER = "<!-- oc-eq1-esrm20-hazard-profile-stage-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-hazard-profile-stage-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-hazard-profile-stage-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-hazard-profile-stage-diagnostic-result-v1"
ACTION = "esrm20_hazard_profile_stage_diagnostic"
CONTROL_ISSUE = 481
DATASET_ID = subject.DATASET_ID
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_REQUEST_FIELDS = {"schema_version", "action", "issue", "target_sha", "dataset_id", "requester"}
_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_MONOTONIC = time.monotonic


class HazardProfileStageDiagnosticError(RuntimeError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise HazardProfileStageDiagnosticError("duplicate JSON key")
        out[key] = value
    return out


def _reject_constant(value: str) -> Any:
    raise HazardProfileStageDiagnosticError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if expected_issue != CONTROL_ISSUE or type(expected_issue) is not int:
        raise HazardProfileStageDiagnosticError("wrong runtime issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardProfileStageDiagnosticError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise HazardProfileStageDiagnosticError("invalid diagnostic request marker")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise HazardProfileStageDiagnosticError("diagnostic request envelope is not canonical")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except HazardProfileStageDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HazardProfileStageDiagnosticError("invalid diagnostic request JSON") from exc
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise HazardProfileStageDiagnosticError("diagnostic request fields drifted")
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
            raise HazardProfileStageDiagnosticError(f"diagnostic request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _SAFE_REQUESTER_RE.fullmatch(requester) is None:
        raise HazardProfileStageDiagnosticError("invalid requester identity")
    return request


def diagnose_texts(*, source_text: str, gsim_text: str) -> dict[str, Any]:
    """Pure stage diagnostic with no provider content in the returned object."""
    source_ok = True
    try:
        dependencies = extract_source_model_logic_tree_dependencies(
            source_text, logic_tree_path=subject.SOURCE_PATH
        )
        if not dependencies:
            source_ok = False
    except OpenQuakeLogicTreeError:
        source_ok = False

    gsim_ok = True
    try:
        profile = gsim_identity._profile_xml_text(gsim_text)
        if not profile.get("unique_requested_gsim_tokens"):
            gsim_ok = False
    except gsim_identity.Eshm20GsimIdentityProfileError:
        gsim_ok = False

    return {
        "source_parser_pass": source_ok,
        "gsim_parser_pass": gsim_ok,
        "source_parser": "scripts.openquake_source_model_logic_tree_dependencies.extract_source_model_logic_tree_dependencies",
        "gsim_parser": "scripts.profile_eshm20_gsim_identities._profile_xml_text",
        "provider_content_returned": False,
        "parser_error_text_returned": False,
    }


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise HazardProfileStageDiagnosticError("invalid execution SHA")
    base = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "gsim_byte_count": subject.GSIM_BYTE_COUNT,
        "gsim_sha256": subject.GSIM_SHA256,
        "source_byte_count": subject.SOURCE_BYTE_COUNT,
        "source_sha256": subject.SOURCE_SHA256,
        "provider_content_returned": False,
        "parser_error_text_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    if _open_fixed is not _CANONICAL_OPEN_FIXED or time.monotonic is not _CANONICAL_MONOTONIC:
        raise HazardProfileStageDiagnosticError("production transport identity drifted")
    try:
        gsim_raw = subject._acquire_exact_bytes(
            repository_path=subject.GSIM_PATH,
            expected_byte_count=subject.GSIM_BYTE_COUNT,
            expected_sha256=subject.GSIM_SHA256,
            opener=_CANONICAL_OPEN_FIXED,
            monotonic=_CANONICAL_MONOTONIC,
        )
        source_raw = subject._acquire_exact_bytes(
            repository_path=subject.SOURCE_PATH,
            expected_byte_count=subject.SOURCE_BYTE_COUNT,
            expected_sha256=subject.SOURCE_SHA256,
            opener=_CANONICAL_OPEN_FIXED,
            monotonic=_CANONICAL_MONOTONIC,
        )
    except EfehrAcquisitionError:
        return {**base, "status": "blocked", "failure_class": "acquisition_failure", "diagnostic": None}
    try:
        gsim_text = gsim_raw.decode("utf-8", errors="strict")
        source_text = source_raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {**base, "status": "blocked", "failure_class": "decode_failure", "diagnostic": None}
    diagnostic = diagnose_texts(source_text=source_text, gsim_text=gsim_text)
    if diagnostic["source_parser_pass"] and diagnostic["gsim_parser_pass"]:
        failure_class = "unexpected_composition_failure"
    elif not diagnostic["source_parser_pass"] and not diagnostic["gsim_parser_pass"]:
        failure_class = "both_parser_failure"
    elif not diagnostic["source_parser_pass"]:
        failure_class = "source_parser_failure"
    else:
        failure_class = "gsim_parser_failure"
    return {**base, "status": "pass", "failure_class": failure_class, "diagnostic": diagnostic}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        raise HazardProfileStageDiagnosticError("--output is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
