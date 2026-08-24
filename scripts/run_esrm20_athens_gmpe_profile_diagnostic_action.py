# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main diagnostic for the fixed Athens ESRM20 GMPE profiler.

This action classifies only the already-observed fail-closed content rejection
for the exact receipted GMPE logic-tree bytes. It publishes one closed static
failure code and never publishes provider XML, model values, exception text, or
additional scientific/model-use authority.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import acquire_efehr_esrm20_athens_gmpe_profile as acquisition
    from scripts import profile_esrm20_scenario_v10_greece_gmpe_logic_tree as profile
    from scripts import run_esrm20_athens_gmpe_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import acquire_efehr_esrm20_athens_gmpe_profile as acquisition
    import profile_esrm20_scenario_v10_greece_gmpe_logic_tree as profile
    import run_esrm20_athens_gmpe_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-athens-gmpe-profile-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-athens-gmpe-profile-diagnostic-result-v1"
ACTION = "esrm20_athens_gmpe_logic_tree_structure_profile_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4_096
MAX_TERMINAL_UTF8_BYTES = 6_000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_PARENT_CONSUMER_ISSUE = 287
_CONTENT_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_RECEIPT_SHA256 = "3c6ff83efcac45cf75125e035060e84b910c45a9e531306d822b4566383d5b78"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_EXPECTED_IDENTITY = {
    "project_id": 273,
    "project_path": "efehr/esrm20_scenario_tests",
    "release_tag": "v1.0",
    "commit_sha": "041f90d950d6ff84180b2faa11319a42c66c74cc",
    "event_id": "Greece_07-9-1999",
    "repository_path": "ruptures/ground-motion-models/gmpe_logic_tree_5br_shallow_default.xml",
    "git_blob_sha1": "7f6ac690bf0f0538dabc4ef957db5b48e9fd35d3",
    "receipt_issue": 658,
    "receipt_comment_id": 5_389_061_280,
    "receipt_execution_sha": "991477641495363252764ad55e626fdfe23781d8",
    "receipt_retrieved_at": "2026-08-23T23:24:08Z",
    "byte_count": 6_490,
    "sha256": _RECEIPT_SHA256,
}

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
    "unexpected_direct_child:logicTree:logicTreeBranchSet": (
        "logic_tree_branch_set_direct_child"
    ),
    "branch_direct_child_cardinality_mismatch": "branch_direct_child_cardinality_mismatch",
    "namespaced_attribute_forbidden": "namespaced_attribute_forbidden",
    "attribute_value_too_large": "attribute_value_too_large",
    "element_text_too_large": "element_text_too_large",
    "non_whitespace_tail_text_forbidden": "non_whitespace_tail_text_forbidden",
    "branch_model_cardinality_mismatch": "branch_model_cardinality_mismatch",
    "branch_weight_cardinality_mismatch": "branch_weight_cardinality_mismatch",
}
_PROFILE_ERROR_CODE_BY_PREFIX = (
    ("missing_direct_child:", "missing_direct_child"),
    ("unexpected_direct_child:", "unexpected_direct_child"),
    ("unexpected_leaf_child:", "unexpected_leaf_child"),
    (
        "non_whitespace_container_text_forbidden:",
        "non_whitespace_container_text_forbidden",
    ),
    ("missing_required_element:", "missing_required_element"),
)
BYTE_IDENTITY_FAILURE_CODES = frozenset(
    {"profiler_byte_count_mismatch", "profiler_sha256_mismatch"}
)
PROFILE_FAILURE_CODES = frozenset(
    {
        *_PROFILE_ERROR_CODE_BY_MESSAGE.values(),
        *(code for _, code in _PROFILE_ERROR_CODE_BY_PREFIX),
        "unclassified_profile_rejection",
    }
)
STRUCTURAL_PROFILE_FAILURE_CODES = frozenset(
    PROFILE_FAILURE_CODES
    - BYTE_IDENTITY_FAILURE_CODES
    - {"unclassified_profile_rejection"}
)
FAILURE_STAGES = frozenset({"acquisition", "byte_identity", "profile"})

_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "parent_consumer_issue",
    "content_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "gmpe_identity",
    "status",
    "failure_stage",
    "failure_code",
    "provider_file_bytes_read",
    "provider_file_content_profiled",
    "byte_identity_verified",
    "external_bytes_persisted",
    "gmpe_semantics_verified",
    "gmpe_applicability_verified",
    "numerical_equivalence_verified",
    "scenario_selection_authorized",
    "independent_validation_established",
    "publication_authorized",
    "model_use_authorized",
}


class AthensGmpeProfileDiagnosticError(RuntimeError):
    """The diagnostic request/result contract or authority drifted."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AthensGmpeProfileDiagnosticError("duplicate JSON key")
        value[key] = item
    return value


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
    acquisition._require_contract()
    exact = (
        (base.CONTROL_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.PARENT_CONSUMER_ISSUE, _PARENT_CONSUMER_ISSUE, "parent consumer"),
        (base.SOURCE_ISSUE, _CONTENT_ISSUE, "content issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.EXPECTED_SHA256, _RECEIPT_SHA256, "receipt sha256"),
        (base._identity(), _EXPECTED_IDENTITY, "fixed identity"),
        (acquisition.EXPECTED_BYTE_COUNT, 6_490, "byte count"),
        (profile.EXPECTED_BYTE_COUNT, 6_490, "profiler byte count"),
        (profile.EXPECTED_SHA256, _RECEIPT_SHA256, "profiler sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileDiagnosticError(
                f"Athens GMPE diagnostic {label} drifted"
            )


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise AthensGmpeProfileDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise AthensGmpeProfileDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise AthensGmpeProfileDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise AthensGmpeProfileDiagnosticError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", _SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", _DATASET_ID),
        ("receipt_sha256", _RECEIPT_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise AthensGmpeProfileDiagnosticError("invalid requester")
    return request


def classify_profile_error(exc: object) -> str:
    """Map only current profiler-owned messages/prefixes to closed public codes."""
    if type(exc) is not profile.GmpeLogicTreeProfileError:
        return "unclassified_profile_rejection"
    message = str(exc)
    exact = _PROFILE_ERROR_CODE_BY_MESSAGE.get(message)
    if exact is not None:
        return exact
    for prefix, code in _PROFILE_ERROR_CODE_BY_PREFIX:
        if message.startswith(prefix):
            return code
    return "unclassified_profile_rejection"


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": _SOURCE_ISSUE,
        "parent_consumer_issue": _PARENT_CONSUMER_ISSUE,
        "content_issue": _CONTENT_ISSUE,
        "dataset_id": _DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "gmpe_identity": dict(_EXPECTED_IDENTITY),
        "status": "blocked",
        "failure_stage": "acquisition",
        "failure_code": "acquisition_failed",
        "provider_file_bytes_read": None,
        "provider_file_content_profiled": False,
        "byte_identity_verified": False,
        "external_bytes_persisted": False,
        "gmpe_semantics_verified": False,
        "gmpe_applicability_verified": False,
        "numerical_equivalence_verified": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    _require_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise AthensGmpeProfileDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise AthensGmpeProfileDiagnosticError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("parent_consumer_issue", _PARENT_CONSUMER_ISSUE),
        ("content_issue", _CONTENT_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("gmpe_identity", _EXPECTED_IDENTITY),
        ("external_bytes_persisted", False),
        ("gmpe_semantics_verified", False),
        ("gmpe_applicability_verified", False),
        ("numerical_equivalence_verified", False),
        ("scenario_selection_authorized", False),
        ("independent_validation_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise AthensGmpeProfileDiagnosticError(f"result {field} drifted")

    status = result.get("status")
    stage = result.get("failure_stage")
    code = result.get("failure_code")
    bytes_read = result.get("provider_file_bytes_read")
    profiled = result.get("provider_file_content_profiled")
    identity_verified = result.get("byte_identity_verified")

    if type(profiled) is not bool or type(identity_verified) is not bool:
        raise AthensGmpeProfileDiagnosticError("invalid profile/identity booleans")
    if bytes_read is not None and type(bytes_read) is not bool:
        raise AthensGmpeProfileDiagnosticError("invalid provider_file_bytes_read")

    if status == "pass":
        if (
            stage is not None
            or code is not None
            or bytes_read is not True
            or profiled is not True
            or identity_verified is not True
        ):
            raise AthensGmpeProfileDiagnosticError("invalid PASS state")
    elif status == "blocked":
        if stage not in FAILURE_STAGES or type(code) is not str or profiled is not False:
            raise AthensGmpeProfileDiagnosticError("invalid blocked failure state")
        if stage == "acquisition":
            expected = ("acquisition_failed", None, False)
            if (code, bytes_read, identity_verified) != expected:
                raise AthensGmpeProfileDiagnosticError("blocked acquisition state drifted")
        elif stage == "byte_identity":
            if (
                code not in BYTE_IDENTITY_FAILURE_CODES
                or bytes_read is not True
                or identity_verified is not False
            ):
                raise AthensGmpeProfileDiagnosticError("blocked byte identity state drifted")
        else:
            if code not in PROFILE_FAILURE_CODES or code in BYTE_IDENTITY_FAILURE_CODES:
                raise AthensGmpeProfileDiagnosticError("invalid profile failure code")
            expected_identity = code in STRUCTURAL_PROFILE_FAILURE_CODES
            if bytes_read is not True or identity_verified is not expected_identity:
                raise AthensGmpeProfileDiagnosticError("blocked profile state drifted")
    else:
        raise AthensGmpeProfileDiagnosticError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if (
        _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES
        or body.count(RESULT_MARKER) != 1
    ):
        raise AthensGmpeProfileDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise AthensGmpeProfileDiagnosticError("non-canonical result envelope")
    result = _strict_loads(after.strip(), label="result")
    return _validate_terminal_result(result)


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    kwargs: dict[str, Any] = {
        "issue": _SOURCE_ISSUE,
        "max_pages": MAX_LEDGER_PAGES,
    }
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = base.fetch_repository_comments(repository, token, **kwargs)
    except base.LedgerError as exc:
        raise AthensGmpeProfileDiagnosticError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
        if type(comment) is not dict:
            raise AthensGmpeProfileDiagnosticError("ledger contains non-object comment")
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        terminal_sha = parse_terminal_result(comment.get("body"))
        if terminal_sha == execution_sha:
            found = True
    return found


def _run_diagnostic_with(
    *,
    execution_sha: str,
    acquirer: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise AthensGmpeProfileDiagnosticError("invalid execution SHA")
    _require_authority()
    result = _base_result(execution_sha)
    try:
        evidence = acquirer()
    except acquisition.AthensGmpeProfileAcquisitionError:
        pass
    except acquisition.AthensGmpeProfileContentError as exc:
        code = classify_profile_error(exc.__cause__)
        stage = "byte_identity" if code in BYTE_IDENTITY_FAILURE_CODES else "profile"
        result.update(
            {
                "failure_stage": stage,
                "failure_code": code,
                "provider_file_bytes_read": True,
                "byte_identity_verified": code in STRUCTURAL_PROFILE_FAILURE_CODES,
            }
        )
    else:
        base._validate_evidence(evidence)
        result.update(
            {
                "status": "pass",
                "failure_stage": None,
                "failure_code": None,
                "provider_file_bytes_read": True,
                "provider_file_content_profiled": True,
                "byte_identity_verified": True,
            }
        )
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_diagnostic_with(
        execution_sha=execution_sha,
        acquirer=acquisition.acquire_and_profile_athens_gmpe,
    )


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

    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
