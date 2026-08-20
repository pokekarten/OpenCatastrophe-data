# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main diagnostic for the fixed ESRM20 Greece rupture profiler.

This action exists only to classify the already-observed fail-closed profiler
rejection for #285. It reuses the merged fixed acquisition and profiler
boundaries, publishes only a closed static code, and never publishes provider
XML, exception text, event-locality inference, or model-use authority.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import run_esrm20_scenario_v10_greece_rupture_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import run_esrm20_scenario_v10_greece_rupture_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-profile-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-profile-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-profile-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-profile-diagnostic-result-v1"
ACTION = "esrm20_scenario_v10_greece_rupture_profile_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 6000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_RECEIPT_SHA256 = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_PROFILE_ERROR_CODE_BY_MESSAGE = {
    "production_authority_drift:byte_count": "authority_byte_count_drift",
    "production_authority_drift:sha256": "authority_sha256_drift",
    "production_authority_drift:nrml_namespace": "authority_nrml_namespace_drift",
    "production_authority_drift:rupture_elements": "authority_rupture_elements_drift",
    "production_authority_drift:max_elements": "authority_max_elements_drift",
    "production_authority_drift:max_depth": "authority_max_depth_drift",
    "non_text_xml_tag": "non_text_xml_tag",
    "malformed_expanded_xml_name": "malformed_expanded_xml_name",
    "unsafe_xml_local_name": "unsafe_xml_local_name",
    "non_utf8_xml_encoding": "non_utf8_xml_encoding",
    "invalid_utf8_xml": "invalid_utf8_xml",
    "xml_encoding_declaration_mismatch": "xml_encoding_declaration_mismatch",
    "dtd_or_entity_forbidden": "dtd_or_entity_forbidden",
    "xml_element_limit_exceeded": "xml_element_limit_exceeded",
    "xml_depth_limit_exceeded": "xml_depth_limit_exceeded",
    "foreign_xml_namespace": "foreign_xml_namespace",
    "byte_count_mismatch": "profiler_byte_count_mismatch",
    "sha256_mismatch": "profiler_sha256_mismatch",
    "invalid_xml": "invalid_xml",
    "unexpected_nrml_root": "unexpected_nrml_root",
    "rupture_top_level_cardinality": "rupture_top_level_cardinality",
    "foreign_rupture_namespace": "foreign_rupture_namespace",
    "unsupported_rupture_element": "unsupported_rupture_element",
}
PROFILE_FAILURE_CODES = frozenset(
    {*_PROFILE_ERROR_CODE_BY_MESSAGE.values(), "unclassified_profile_rejection"}
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
    "dataset_id",
    "target_sha",
    "execution_sha",
    "rupture_identity",
    "status",
    "failure_stage",
    "failure_code",
    "provider_file_bytes_read",
    "provider_file_content_profiled",
    "byte_identity_verified",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}


class RuptureProfileDiagnosticError(RuntimeError):
    """The diagnostic request/result contract drifted."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RuptureProfileDiagnosticError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise RuptureProfileDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except RuptureProfileDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuptureProfileDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RuptureProfileDiagnosticError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    base._require_canonical_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.EXPECTED_SHA256, _RECEIPT_SHA256, "receipt sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise RuptureProfileDiagnosticError(f"diagnostic {label} drifted")


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise RuptureProfileDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureProfileDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise RuptureProfileDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuptureProfileDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise RuptureProfileDiagnosticError("request fields drifted")
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
            raise RuptureProfileDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise RuptureProfileDiagnosticError("invalid requester")
    return request


def classify_profile_error(exc: base.RuptureProfileError) -> str:
    """Map only exact parser-owned messages to public closed codes."""
    if type(exc) is not base.RuptureProfileError:
        return "unclassified_profile_rejection"
    return _PROFILE_ERROR_CODE_BY_MESSAGE.get(
        str(exc),
        "unclassified_profile_rejection",
    )


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": _SOURCE_ISSUE,
        "dataset_id": _DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "rupture_identity": base._identity(),
        "status": "blocked",
        "failure_stage": "acquisition",
        "failure_code": "acquisition_failed",
        "provider_file_bytes_read": False,
        "provider_file_content_profiled": False,
        "byte_identity_verified": False,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    _require_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise RuptureProfileDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureProfileDiagnosticError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("rupture_identity", base._identity()),
        ("output_payload_bytes_read", False),
        ("external_bytes_persisted", False),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise RuptureProfileDiagnosticError(f"result {field} drifted")

    status = result.get("status")
    stage = result.get("failure_stage")
    code = result.get("failure_code")
    bytes_read = result.get("provider_file_bytes_read")
    profiled = result.get("provider_file_content_profiled")
    identity_verified = result.get("byte_identity_verified")
    if status == "pass":
        if (
            stage is not None
            or code is not None
            or bytes_read is not True
            or profiled is not True
            or identity_verified is not True
        ):
            raise RuptureProfileDiagnosticError("invalid PASS state")
    elif status == "blocked":
        if stage not in FAILURE_STAGES or type(code) is not str:
            raise RuptureProfileDiagnosticError("invalid blocked failure state")
        if stage == "acquisition":
            expected = ("acquisition_failed", False, False)
        elif stage == "byte_identity":
            expected = ("byte_identity_mismatch", True, False)
        else:
            if code not in PROFILE_FAILURE_CODES:
                raise RuptureProfileDiagnosticError("invalid profile failure code")
            expected = (code, True, True)
        if (code, bytes_read, identity_verified) != expected:
            raise RuptureProfileDiagnosticError("blocked byte/identity state drifted")
        if profiled is not False:
            raise RuptureProfileDiagnosticError("blocked result profiled content")
    else:
        raise RuptureProfileDiagnosticError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if (
        _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES
        or body.count(RESULT_MARKER) != 1
    ):
        raise RuptureProfileDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuptureProfileDiagnosticError("non-canonical result envelope")
    result = _strict_loads(after.strip(), label="result")
    return _validate_terminal_result(result)


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    kwargs: dict[str, Any] = {"issue": _SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = base.fetch_repository_comments(repository, token, **kwargs)
    except base.LedgerError as exc:
        raise RuptureProfileDiagnosticError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
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
    fetcher: Callable[[], tuple[bytes, dict[str, Any]]],
    profiler: Callable[[bytes], dict[str, object]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureProfileDiagnosticError("invalid execution SHA")
    _require_authority()
    result = _base_result(execution_sha)
    try:
        raw, receipt = fetcher()
    except base.RuptureByteIdentityError:
        result.update(
            {
                "failure_stage": "byte_identity",
                "failure_code": "byte_identity_mismatch",
                "provider_file_bytes_read": True,
            }
        )
    except base.EfehrAcquisitionError:
        pass
    else:
        base._validate_receipt(receipt)
        result["provider_file_bytes_read"] = True
        result["byte_identity_verified"] = True
        try:
            profile = profiler(raw)
        except base.RuptureProfileError as exc:
            result.update(
                {
                    "failure_stage": "profile",
                    "failure_code": classify_profile_error(exc),
                }
            )
        else:
            base._validate_profile(profile)
            result.update(
                {
                    "status": "pass",
                    "failure_stage": None,
                    "failure_code": None,
                    "provider_file_content_profiled": True,
                }
            )
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_diagnostic_with(
        execution_sha=execution_sha,
        fetcher=base._acquire_fixed_rupture,
        profiler=base.profile_fixed_greece_rupture,
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
        raise RuptureProfileDiagnosticError("output path is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
