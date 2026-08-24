# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main diagnosis for the exact Athens ESRM20 v1.0 GMPE profile.

The normal trusted-main lane intentionally collapses profiler exceptions to a
generic profile_failure. This diagnostic only classifies that already-observed
failure into a closed static code. It never returns provider XML, GSIM/model
strings, exception text, or scientific/model-use authority.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from scripts import profile_esrm20_scenario_v10_greece_gmpe_logic_tree as profile
from scripts import run_esrm20_athens_gmpe_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-diagnostic-result-v1"
ACTION = "esrm20_athens_gmpe_logic_tree_profile_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 6000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_RECEIPT_SHA256 = "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_PROFILE_ERROR_CODE_BY_MESSAGE = {
    "non_text_xml_tag": "non_text_xml_tag",
    "malformed_expanded_xml_name": "malformed_expanded_xml_name",
    "unsafe_xml_local_name": "unsafe_xml_local_name",
    "non_utf8_xml_encoding": "non_utf8_xml_encoding",
    "invalid_utf8_xml": "invalid_utf8_xml",
    "nul_character_forbidden": "nul_character_forbidden",
    "dtd_or_entity_forbidden": "dtd_or_entity_forbidden",
    "byte_count_mismatch": "profiler_byte_count_mismatch",
    "sha256_mismatch": "profiler_sha256_mismatch",
    "invalid_xml": "invalid_xml",
    "unexpected_nrml_root": "unexpected_nrml_root",
    "unexpected_logic_tree_root": "unexpected_logic_tree_root",
    "xml_element_limit_exceeded": "xml_element_limit_exceeded",
    "xml_depth_limit_exceeded": "xml_depth_limit_exceeded",
    "foreign_xml_namespace": "foreign_xml_namespace",
    "branch_direct_child_cardinality_mismatch": "branch_direct_child_cardinality_mismatch",
    "namespaced_attribute_forbidden": "namespaced_attribute_forbidden",
    "attribute_value_too_large": "attribute_value_too_large",
    "element_text_too_large": "element_text_too_large",
    "non_whitespace_tail_text_forbidden": "non_whitespace_tail_text_forbidden",
    "branch_model_cardinality_mismatch": "branch_model_cardinality_mismatch",
    "branch_weight_cardinality_mismatch": "branch_weight_cardinality_mismatch",
}
_PROFILE_ERROR_CODE_BY_PREFIX = {
    "missing_direct_child:": "missing_direct_child",
    "unexpected_direct_child:": "unexpected_direct_child",
    "unexpected_leaf_child:": "unexpected_leaf_child",
    "non_whitespace_container_text_forbidden:": "non_whitespace_container_text_forbidden",
    "missing_required_element:": "missing_required_element",
}
PROFILE_FAILURE_CODES = frozenset(
    {
        *_PROFILE_ERROR_CODE_BY_MESSAGE.values(),
        *_PROFILE_ERROR_CODE_BY_PREFIX.values(),
        "unclassified_profile_rejection",
    }
)
BYTE_IDENTITY_CODES = frozenset({"profiler_byte_count_mismatch", "profiler_sha256_mismatch"})

_REQUEST_FIELDS = {
    "schema_version", "action", "issue", "target_sha", "dataset_id",
    "receipt_sha256", "requester",
}
_RESULT_FIELDS = {
    "schema_version", "action", "source_issue", "dataset_id", "target_sha",
    "execution_sha", "gmpe_identity", "status", "failure_stage", "failure_code",
    "provider_file_bytes_read", "provider_file_content_profiled",
    "byte_identity_verified", "output_payload_bytes_read", "external_bytes_persisted",
    "gmpe_semantics_verified", "gmpe_applicability_verified",
    "numerical_equivalence_verified", "scenario_selection_authorized",
    "independent_validation_established", "publication_authorized", "model_use_authorized",
}


class AthensGmpeProfileDiagnosticError(RuntimeError):
    """The closed diagnostic request/result contract drifted."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AthensGmpeProfileDiagnosticError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise AthensGmpeProfileDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except AthensGmpeProfileDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AthensGmpeProfileDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise AthensGmpeProfileDiagnosticError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    exact = (
        (base.CONTROL_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.EXPECTED_SHA256, _RECEIPT_SHA256, "receipt sha256"),
        (base.EXPECTED_BYTE_COUNT, 6490, "byte count"),
        (base.PROJECT_ID, 273, "project id"),
        (base.COMMIT_SHA, "041f90d950d6ff84180b2faa11319a42c66c74cc", "commit sha"),
        (base.REPOSITORY_PATH, "ruptures/ground-motion-models/gmpe_logic_tree_5br_shallow_default.xml", "repository path"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileDiagnosticError(f"diagnostic authority drifted at {label}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise AthensGmpeProfileDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise AthensGmpeProfileDiagnosticError("invalid execution SHA")
    if type(body) is not str or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES or body.count(REQUEST_MARKER) != 1:
        raise AthensGmpeProfileDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise AthensGmpeProfileDiagnosticError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION), ("action", ACTION),
        ("issue", _SOURCE_ISSUE), ("target_sha", execution_sha),
        ("dataset_id", _DATASET_ID), ("receipt_sha256", _RECEIPT_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if type(requester) is not str or requester != requester.strip() or _REQUESTER_RE.fullmatch(requester) is None:
        raise AthensGmpeProfileDiagnosticError("invalid requester")
    return request


def classify_profile_error(exc: BaseException | None) -> str:
    """Map only profiler-owned messages to a closed public code."""
    if type(exc) is not profile.GmpeLogicTreeProfileError:
        return "unclassified_profile_rejection"
    message = str(exc)
    exact = _PROFILE_ERROR_CODE_BY_MESSAGE.get(message)
    if exact is not None:
        return exact
    for prefix, code in _PROFILE_ERROR_CODE_BY_PREFIX.items():
        if message.startswith(prefix):
            return code
    return "unclassified_profile_rejection"


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION, "action": ACTION,
        "source_issue": _SOURCE_ISSUE, "dataset_id": _DATASET_ID,
        "target_sha": execution_sha, "execution_sha": execution_sha,
        "gmpe_identity": base._identity(), "status": "blocked",
        "failure_stage": "acquisition", "failure_code": "acquisition_failed",
        "provider_file_bytes_read": None, "provider_file_content_profiled": False,
        "byte_identity_verified": False, "output_payload_bytes_read": False,
        "external_bytes_persisted": False, "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False, "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False, "independent_validation_established": False,
        "publication_authorized": False, "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    _require_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise AthensGmpeProfileDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise AthensGmpeProfileDiagnosticError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION), ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE), ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha), ("gmpe_identity", base._identity()),
        ("output_payload_bytes_read", False), ("external_bytes_persisted", False),
        ("gmpe_semantics_verified", False), ("gmpe_applicability_verified", False),
        ("numerical_equivalence_verified", False), ("scenario_selection_authorized", False),
        ("independent_validation_established", False), ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise AthensGmpeProfileDiagnosticError(f"result {field} drifted")
    status, stage, code = result.get("status"), result.get("failure_stage"), result.get("failure_code")
    bytes_read = result.get("provider_file_bytes_read")
    profiled = result.get("provider_file_content_profiled")
    identity = result.get("byte_identity_verified")
    if status == "pass":
        if stage is not None or code is not None or bytes_read is not True or profiled is not True or identity is not True:
            raise AthensGmpeProfileDiagnosticError("invalid PASS state")
    elif status == "blocked":
        if profiled is not False:
            raise AthensGmpeProfileDiagnosticError("blocked result profiled content")
        if stage == "acquisition":
            if code != "acquisition_failed" or bytes_read is not None or identity is not False:
                raise AthensGmpeProfileDiagnosticError("invalid acquisition state")
        elif stage == "byte_identity":
            if code not in BYTE_IDENTITY_CODES or bytes_read is not True or identity is not False:
                raise AthensGmpeProfileDiagnosticError("invalid byte identity state")
        elif stage == "profile":
            if code not in PROFILE_FAILURE_CODES or code in BYTE_IDENTITY_CODES or bytes_read is not True or identity is not True:
                raise AthensGmpeProfileDiagnosticError("invalid profile failure state")
        else:
            raise AthensGmpeProfileDiagnosticError("invalid blocked failure stage")
    else:
        raise AthensGmpeProfileDiagnosticError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise AthensGmpeProfileDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileDiagnosticError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(*, repository: str, token: str, execution_sha: str, opener: Any | None = None) -> bool:
    kwargs: dict[str, Any] = {"issue": _SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = base.fetch_repository_comments(repository, token, **kwargs)
    except base.LedgerError as exc:
        raise AthensGmpeProfileDiagnosticError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
        if type(comment) is not dict:
            raise AthensGmpeProfileDiagnosticError("diagnostic ledger contains non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body")) == execution_sha:
            found = True
    return found


def _run_diagnostic_with(*, execution_sha: str, acquirer: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise AthensGmpeProfileDiagnosticError("invalid execution SHA")
    _require_authority()
    result = _base_result(execution_sha)
    try:
        evidence = acquirer()
    except base.AthensGmpeProfileAcquisitionError:
        pass
    except base.AthensGmpeProfileContentError as exc:
        code = classify_profile_error(exc.__cause__)
        if code in BYTE_IDENTITY_CODES:
            result.update({"failure_stage": "byte_identity", "failure_code": code, "provider_file_bytes_read": True, "byte_identity_verified": False})
        else:
            result.update({"failure_stage": "profile", "failure_code": code, "provider_file_bytes_read": True, "byte_identity_verified": True})
    else:
        base._validate_evidence(evidence)
        result.update({"status": "pass", "failure_stage": None, "failure_code": None, "provider_file_bytes_read": True, "provider_file_content_profiled": True, "byte_identity_verified": True})
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_diagnostic_with(execution_sha=execution_sha, acquirer=base.acquire_and_profile_athens_gmpe)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(os.environ.get(args.comment_body_env), expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output:
        parser.error("--output is required for execution")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
