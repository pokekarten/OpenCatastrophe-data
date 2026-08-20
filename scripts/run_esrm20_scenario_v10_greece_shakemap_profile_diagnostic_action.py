# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main diagnostic for the fixed ESRM20 Greece ShakeMap profiler.

This runner only classifies an already-observed fail-closed profiler rejection.
It reuses the merged fixed acquisition and profiling boundaries and publishes a
closed static code. Provider XML and exception text are never published.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import run_esrm20_scenario_v10_greece_shakemap_profile_action as base

REQUEST_MARKER = (
    "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-profile-diagnostic-request-v1 -->"
)
RESULT_MARKER = (
    "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-profile-diagnostic-result-v1 -->"
)
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-profile-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-profile-diagnostic-result-v1"
ACTION = "esrm20_scenario_v10_greece_shakemap_profile_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 7000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_GRID_SHA256 = "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f"
_UNCERTAINTY_SHA256 = "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417"
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_PROFILE_ERROR_CODE_BY_MESSAGE = {
    "production_authority_drift:grid_byte_count": "authority_grid_byte_count_drift",
    "production_authority_drift:grid_sha256": "authority_grid_sha256_drift",
    "production_authority_drift:uncertainty_byte_count": "authority_uncertainty_byte_count_drift",
    "production_authority_drift:uncertainty_sha256": "authority_uncertainty_sha256_drift",
    "production_authority_drift:event_id": "authority_event_id_drift",
    "production_authority_drift:max_fields": "authority_max_fields_drift",
    "production_authority_drift:max_rows": "authority_max_rows_drift",
    "production_authority_drift:max_columns": "authority_max_columns_drift",
    "production_authority_drift:max_xml_bytes": "authority_max_xml_bytes_drift",
    "non_text_xml_tag": "non_text_xml_tag",
    "malformed_expanded_xml_name": "malformed_expanded_xml_name",
    "unsafe_xml_local_name": "unsafe_xml_local_name",
    "non_ascii_utf8_xml_encoding": "non_ascii_utf8_xml_encoding",
    "invalid_ascii_utf8_xml": "invalid_ascii_utf8_xml",
    "xml_encoding_declaration_mismatch": "xml_encoding_declaration_mismatch",
    "dtd_or_entity_forbidden": "dtd_or_entity_forbidden",
    "foreign_xml_namespace": "foreign_xml_namespace",
    "invalid_grid_field_index": "invalid_grid_field_index",
    "grid_field_limit_exceeded": "grid_field_limit_exceeded",
    "unsupported_grid_field_name": "unsupported_grid_field_name",
    "unsupported_grid_field_units": "unsupported_grid_field_units",
    "duplicate_grid_field_index": "duplicate_grid_field_index",
    "duplicate_grid_field_name": "duplicate_grid_field_name",
    "insufficient_grid_fields": "insufficient_grid_fields",
    "gapped_grid_field_indexes": "gapped_grid_field_indexes",
    "coordinate_fields_not_first": "coordinate_fields_not_first",
    "grid_specification_cardinality": "grid_specification_cardinality",
    "invalid_nlon": "invalid_nlon",
    "invalid_nlat": "invalid_nlat",
    "missing_lon_min": "missing_lon_min",
    "missing_lat_min": "missing_lat_min",
    "missing_lon_max": "missing_lon_max",
    "missing_lat_max": "missing_lat_max",
    "missing_nominal_lon_spacing": "missing_nominal_lon_spacing",
    "missing_nominal_lat_spacing": "missing_nominal_lat_spacing",
    "invalid_lon_min": "invalid_lon_min",
    "invalid_lat_min": "invalid_lat_min",
    "invalid_lon_max": "invalid_lon_max",
    "invalid_lat_max": "invalid_lat_max",
    "invalid_nominal_lon_spacing": "invalid_nominal_lon_spacing",
    "invalid_nominal_lat_spacing": "invalid_nominal_lat_spacing",
    "non_finite_lon_min": "non_finite_lon_min",
    "non_finite_lat_min": "non_finite_lat_min",
    "non_finite_lon_max": "non_finite_lon_max",
    "non_finite_lat_max": "non_finite_lat_max",
    "non_finite_nominal_lon_spacing": "non_finite_nominal_lon_spacing",
    "non_finite_nominal_lat_spacing": "non_finite_nominal_lat_spacing",
    "grid_cardinality_limit_exceeded": "grid_cardinality_limit_exceeded",
    "invalid_grid_bounds": "invalid_grid_bounds",
    "invalid_grid_spacing": "invalid_grid_spacing",
    "grid_column_limit_exceeded": "grid_column_limit_exceeded",
    "grid_data_cardinality": "grid_data_cardinality",
    "grid_data_must_be_text_only": "grid_data_must_be_text_only",
    "grid_row_count_exceeded": "grid_row_count_exceeded",
    "grid_row_width_mismatch": "grid_row_width_mismatch",
    "invalid_grid_numeric_token": "invalid_grid_numeric_token",
    "non_finite_grid_numeric_token": "non_finite_grid_numeric_token",
    "grid_row_count_mismatch": "grid_row_count_mismatch",
    "byte_count_mismatch": "profiler_byte_count_mismatch",
    "sha256_mismatch": "profiler_sha256_mismatch",
    "invalid_xml": "invalid_xml",
    "unexpected_shakemap_root": "unexpected_shakemap_root",
    "unsafe_event_id": "unsafe_event_id",
    "unsafe_shakemap_id": "unsafe_shakemap_id",
    "unsafe_shakemap_version": "unsafe_shakemap_version",
    "unsafe_code_version": "unsafe_code_version",
    "unsafe_shakemap_originator": "unsafe_shakemap_originator",
    "unsafe_map_status": "unsafe_map_status",
    "unsafe_shakemap_event_type": "unsafe_shakemap_event_type",
    "shakemap_namespace_mismatch": "shakemap_namespace_mismatch",
    "shakemap_event_id_pair_mismatch": "shakemap_event_id_pair_mismatch",
    "grid_specification_mismatch": "grid_specification_mismatch",
    "grid_row_count_pair_mismatch": "grid_row_count_pair_mismatch",
    "coordinate_grid_mismatch": "coordinate_grid_mismatch",
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
    "grid_receipt_sha256",
    "uncertainty_receipt_sha256",
    "requester",
}
_RESULT_FIELDS = {
    "schema_version",
    "action",
    "source_issue",
    "dataset_id",
    "target_sha",
    "execution_sha",
    "shakemap_identity",
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


class ShakeMapProfileDiagnosticError(RuntimeError):
    """The diagnostic request/result contract drifted."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ShakeMapProfileDiagnosticError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise ShakeMapProfileDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except ShakeMapProfileDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ShakeMapProfileDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise ShakeMapProfileDiagnosticError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    base._require_canonical_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.GRID_SHA256, _GRID_SHA256, "grid receipt sha256"),
        (base.UNCERTAINTY_SHA256, _UNCERTAINTY_SHA256, "uncertainty receipt sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapProfileDiagnosticError(f"diagnostic {label} drifted")


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise ShakeMapProfileDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapProfileDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise ShakeMapProfileDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ShakeMapProfileDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ShakeMapProfileDiagnosticError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", _SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", _DATASET_ID),
        ("grid_receipt_sha256", _GRID_SHA256),
        ("uncertainty_receipt_sha256", _UNCERTAINTY_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapProfileDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ShakeMapProfileDiagnosticError("invalid requester")
    return request


def classify_profile_error(exc: base.ShakeMapProfileError) -> str:
    """Map only exact profiler-owned messages to a closed public code."""
    if type(exc) is not base.ShakeMapProfileError:
        return "unclassified_profile_rejection"
    return _PROFILE_ERROR_CODE_BY_MESSAGE.get(str(exc), "unclassified_profile_rejection")


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": _SOURCE_ISSUE,
        "dataset_id": _DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "shakemap_identity": base._identity(),
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
        raise ShakeMapProfileDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapProfileDiagnosticError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("shakemap_identity", base._identity()),
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
            raise ShakeMapProfileDiagnosticError(f"result {field} drifted")

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
            raise ShakeMapProfileDiagnosticError("invalid PASS state")
    elif status == "blocked":
        if stage not in FAILURE_STAGES or type(code) is not str:
            raise ShakeMapProfileDiagnosticError("invalid blocked failure state")
        if stage == "acquisition":
            if code != "acquisition_failed" or identity_verified is not False:
                raise ShakeMapProfileDiagnosticError("invalid acquisition state")
            if type(bytes_read) is not bool:
                raise ShakeMapProfileDiagnosticError("invalid acquisition byte state")
        elif stage == "byte_identity":
            if code != "byte_identity_mismatch" or bytes_read is not True or identity_verified is not False:
                raise ShakeMapProfileDiagnosticError("invalid byte-identity state")
        else:
            if code not in PROFILE_FAILURE_CODES or bytes_read is not True or identity_verified is not True:
                raise ShakeMapProfileDiagnosticError("invalid profile failure state")
        if profiled is not False:
            raise ShakeMapProfileDiagnosticError("blocked result profiled content")
    else:
        raise ShakeMapProfileDiagnosticError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise ShakeMapProfileDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ShakeMapProfileDiagnosticError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


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
        raise ShakeMapProfileDiagnosticError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body")) == execution_sha:
            found = True
    return found


def _run_diagnostic_with(
    *,
    execution_sha: str,
    fetcher: Callable[[], tuple[tuple[bytes, bytes], dict[str, Any]]],
    profiler: Callable[[bytes, bytes], dict[str, object]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapProfileDiagnosticError("invalid execution SHA")
    _require_authority()
    result = _base_result(execution_sha)
    try:
        (grid_raw, uncertainty_raw), receipts = fetcher()
    except base.ShakeMapAcquisitionError as exc:
        result["provider_file_bytes_read"] = exc.completed_files > 0
    except base.ShakeMapByteIdentityError:
        result.update(
            {
                "failure_stage": "byte_identity",
                "failure_code": "byte_identity_mismatch",
                "provider_file_bytes_read": True,
            }
        )
    else:
        base._validate_receipts(receipts)
        result["provider_file_bytes_read"] = True
        result["byte_identity_verified"] = True
        try:
            profile = profiler(grid_raw, uncertainty_raw)
        except base.ShakeMapProfileError as exc:
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
        fetcher=base._acquire_fixed_shakemap_pair,
        profiler=base.profile_fixed_greece_shakemap_pair,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(
        os.environ.get(args.comment_body_env),
        expected_issue=args.expected_issue,
        execution_sha=args.execution_sha,
    )
    if args.validate_request_only:
        return 0
    if not args.output:
        raise ShakeMapProfileDiagnosticError("output path is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
