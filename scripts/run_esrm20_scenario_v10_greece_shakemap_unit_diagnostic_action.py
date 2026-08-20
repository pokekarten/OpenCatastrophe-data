# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed Trusted-Main diagnostic for the fixed Greece ShakeMap unit failure.

The merged profiler has already established the first structural rejection as
``unsupported_grid_field_units`` for an exact receipted grid/uncertainty pair.
This diagnostic does not widen accepted units.  It only classifies the failing
member, an already-known field name, and a closed relationship between the
observed unit token and the frozen documented unit vocabulary.  Raw provider
unit strings, XML, row values, and exception text are never serialized.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import profile_esrm20_scenario_v10_greece_shakemap as profiler
    from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_action as base
    from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_diagnostic_action as predecessor
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import profile_esrm20_scenario_v10_greece_shakemap as profiler
    import run_esrm20_scenario_v10_greece_shakemap_profile_action as base
    import run_esrm20_scenario_v10_greece_shakemap_profile_diagnostic_action as predecessor

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-unit-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-unit-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-unit-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-shakemap-unit-diagnostic-result-v1"
ACTION = "esrm20_scenario_v10_greece_shakemap_unit_diagnostic"
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

_EXPECTED_GRID_UNITS = {
    "LON": frozenset({"dd"}),
    "LAT": frozenset({"dd"}),
    "PGA": frozenset({"pctg"}),
    "PGV": frozenset({"cms"}),
    "MMI": frozenset({"mmi", "intensity"}),
    "PSA03": frozenset({"pctg"}),
    "PSA10": frozenset({"pctg"}),
    "PSA30": frozenset({"pctg"}),
    "STDPGA": frozenset({"ln(pctg)", "pctg"}),
    "URAT": frozenset({""}),
    "SVEL": frozenset({"ms"}),
}
_EXPECTED_UNCERTAINTY_UNITS = {
    "LON": frozenset({"dd"}),
    "LAT": frozenset({"dd"}),
    "STDPGA": frozenset({"ln(pctg)"}),
    "STDPGV": frozenset({"ln(cms)"}),
    "STDMMI": frozenset({"mmi", "intensity"}),
    "STDPSA03": frozenset({"ln(pctg)"}),
    "STDPSA10": frozenset({"ln(pctg)"}),
    "STDPSA30": frozenset({"ln(pctg)"}),
}
_KNOWN_FIELDS = frozenset({*_EXPECTED_GRID_UNITS, *_EXPECTED_UNCERTAINTY_UNITS})
_DOCUMENTED_UNITS = frozenset(
    unit
    for allowed in (*_EXPECTED_GRID_UNITS.values(), *_EXPECTED_UNCERTAINTY_UNITS.values())
    for unit in allowed
)
_MEMBERS = frozenset({"grid", "uncertainty"})
_UNIT_RELATIONS = frozenset(
    {
        "documented_global_unit_wrong_for_field",
        "blank_unexpected",
        "unrecognized_unit_token",
    }
)
_FAILURE_CODES = frozenset(
    {
        "acquisition_failed",
        "byte_identity_mismatch",
        "precondition_profile_failure_drift",
        "precondition_not_reproduced",
        "classifier_inconsistent",
        "unsupported_grid_field_units",
    }
)

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
    "unit_diagnostic",
    "provider_file_bytes_read",
    "byte_identity_verified",
    "profile_failure_reproduced",
    "provider_unit_metadata_classified",
    "provider_file_content_profiled",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}
_DIAGNOSTIC_FIELDS = {"member", "field_name", "unit_relation"}


class ShakeMapUnitDiagnosticError(RuntimeError):
    """The unit diagnostic envelope, authority, or closed result drifted."""


def _require_authority() -> None:
    predecessor._require_authority()
    exact = (
        (profiler._GRID_FIELD_UNITS, _EXPECTED_GRID_UNITS, "grid unit vocabulary"),
        (profiler._UNCERTAINTY_FIELD_UNITS, _EXPECTED_UNCERTAINTY_UNITS, "uncertainty unit vocabulary"),
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.GRID_SHA256, _GRID_SHA256, "grid receipt sha256"),
        (base.UNCERTAINTY_SHA256, _UNCERTAINTY_SHA256, "uncertainty receipt sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapUnitDiagnosticError(f"diagnostic {label} drifted")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ShakeMapUnitDiagnosticError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ShakeMapUnitDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except ShakeMapUnitDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ShakeMapUnitDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise ShakeMapUnitDiagnosticError("text is not UTF-8 encodable") from exc


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise ShakeMapUnitDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapUnitDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise ShakeMapUnitDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ShakeMapUnitDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ShakeMapUnitDiagnosticError("request fields drifted")
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
            raise ShakeMapUnitDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ShakeMapUnitDiagnosticError("invalid requester")
    return request


def _unit_relation(unit: str, *, allowed: frozenset[str]) -> str:
    if unit == "":
        return "blank_unexpected"
    if unit in _DOCUMENTED_UNITS and unit not in allowed:
        return "documented_global_unit_wrong_for_field"
    return "unrecognized_unit_token"


def _classify_member(
    data: bytes,
    *,
    member: str,
    allowed_units: dict[str, frozenset[str]],
) -> dict[str, str] | None:
    """Classify the first unit mismatch without returning the observed token."""
    if member not in _MEMBERS:
        raise ShakeMapUnitDiagnosticError("unknown ShakeMap member")
    text = profiler._decode_xml(data, maximum=profiler.MAX_XML_BYTES)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ShakeMapUnitDiagnosticError("classifier XML precondition drifted") from exc
    namespace, local = profiler._split_tag(root.tag)
    if local != "shakemap_grid":
        raise ShakeMapUnitDiagnosticError("classifier root precondition drifted")
    for child in root:
        child_namespace, child_local = profiler._split_tag(child.tag)
        if child_namespace != namespace:
            raise ShakeMapUnitDiagnosticError("classifier namespace precondition drifted")
        if child_local != "grid_field":
            continue
        name = child.attrib.get("name", "")
        unit = child.attrib.get("units", "")
        if name not in allowed_units:
            raise ShakeMapUnitDiagnosticError("classifier field-name precondition drifted")
        if unit not in allowed_units[name]:
            relation = _unit_relation(unit, allowed=allowed_units[name])
            if name not in _KNOWN_FIELDS or relation not in _UNIT_RELATIONS:
                raise ShakeMapUnitDiagnosticError("classifier closed vocabulary drifted")
            return {"member": member, "field_name": name, "unit_relation": relation}
    return None


def classify_unit_failure(grid_raw: bytes, uncertainty_raw: bytes) -> dict[str, str]:
    grid = _classify_member(
        grid_raw,
        member="grid",
        allowed_units=_EXPECTED_GRID_UNITS,
    )
    if grid is not None:
        return grid
    uncertainty = _classify_member(
        uncertainty_raw,
        member="uncertainty",
        allowed_units=_EXPECTED_UNCERTAINTY_UNITS,
    )
    if uncertainty is None:
        raise ShakeMapUnitDiagnosticError("unit failure was not reproduced by classifier")
    return uncertainty


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
        "unit_diagnostic": None,
        "provider_file_bytes_read": False,
        "byte_identity_verified": False,
        "profile_failure_reproduced": False,
        "provider_unit_metadata_classified": False,
        "provider_file_content_profiled": False,
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
        raise ShakeMapUnitDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapUnitDiagnosticError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("shakemap_identity", base._identity()),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapUnitDiagnosticError(f"result {field} drifted")
    for field in (
        "provider_file_bytes_read",
        "byte_identity_verified",
        "profile_failure_reproduced",
        "provider_unit_metadata_classified",
        "provider_file_content_profiled",
        "output_payload_bytes_read",
        "external_bytes_persisted",
        "event_location_inference_authorized",
        "scenario_selection_authorized",
        "independent_validation_established",
        "holdout_status_established",
        "publication_authorized",
        "model_use_authorized",
    ):
        if type(result.get(field)) is not bool:
            raise ShakeMapUnitDiagnosticError(f"result {field} must be bool")
    for field in (
        "provider_file_content_profiled",
        "output_payload_bytes_read",
        "external_bytes_persisted",
        "event_location_inference_authorized",
        "scenario_selection_authorized",
        "independent_validation_established",
        "holdout_status_established",
        "publication_authorized",
        "model_use_authorized",
    ):
        if result[field] is not False:
            raise ShakeMapUnitDiagnosticError(f"result {field} widened authority")
    if result.get("status") != "blocked" or result.get("failure_code") not in _FAILURE_CODES:
        raise ShakeMapUnitDiagnosticError("invalid terminal status")
    if result.get("failure_stage") not in {"acquisition", "byte_identity", "profile"}:
        raise ShakeMapUnitDiagnosticError("invalid failure stage")

    diagnostic = result.get("unit_diagnostic")
    if result["failure_code"] == "unsupported_grid_field_units":
        if (
            result["failure_stage"] != "profile"
            or result["provider_file_bytes_read"] is not True
            or result["byte_identity_verified"] is not True
            or result["profile_failure_reproduced"] is not True
            or result["provider_unit_metadata_classified"] is not True
            or type(diagnostic) is not dict
            or set(diagnostic) != _DIAGNOSTIC_FIELDS
            or diagnostic.get("member") not in _MEMBERS
            or diagnostic.get("field_name") not in _KNOWN_FIELDS
            or diagnostic.get("unit_relation") not in _UNIT_RELATIONS
        ):
            raise ShakeMapUnitDiagnosticError("invalid classified unit failure")
    else:
        if diagnostic is not None or result["provider_unit_metadata_classified"] is not False:
            raise ShakeMapUnitDiagnosticError("unexpected unit diagnostic")
    if result["failure_stage"] == "acquisition":
        if result["failure_code"] != "acquisition_failed" or result["byte_identity_verified"] is not False:
            raise ShakeMapUnitDiagnosticError("invalid acquisition state")
    if result["failure_stage"] == "byte_identity":
        if (
            result["failure_code"] != "byte_identity_mismatch"
            or result["provider_file_bytes_read"] is not True
            or result["byte_identity_verified"] is not False
        ):
            raise ShakeMapUnitDiagnosticError("invalid byte-identity state")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise ShakeMapUnitDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ShakeMapUnitDiagnosticError("non-canonical result envelope")
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
        raise ShakeMapUnitDiagnosticError("issue ledger is incomplete") from exc
    found = False
    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        if parse_terminal_result(comment.get("body")) == execution_sha:
            found = True
    return found


def _run_with(
    *,
    execution_sha: str,
    fetcher: Callable[[], tuple[tuple[bytes, bytes], dict[str, Any]]],
    profile_func: Callable[[bytes, bytes], dict[str, object]],
    classifier: Callable[[bytes, bytes], dict[str, str]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapUnitDiagnosticError("invalid execution SHA")
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
            profile_func(grid_raw, uncertainty_raw)
        except base.ShakeMapProfileError as exc:
            if type(exc) is not base.ShakeMapProfileError or str(exc) != "unsupported_grid_field_units":
                result.update(
                    {
                        "failure_stage": "profile",
                        "failure_code": "precondition_profile_failure_drift",
                    }
                )
            else:
                result["profile_failure_reproduced"] = True
                try:
                    unit_diagnostic = classifier(grid_raw, uncertainty_raw)
                except (ShakeMapUnitDiagnosticError, base.ShakeMapProfileError):
                    result.update(
                        {
                            "failure_stage": "profile",
                            "failure_code": "classifier_inconsistent",
                        }
                    )
                else:
                    result.update(
                        {
                            "failure_stage": "profile",
                            "failure_code": "unsupported_grid_field_units",
                            "unit_diagnostic": unit_diagnostic,
                            "provider_unit_metadata_classified": True,
                        }
                    )
        else:
            result.update(
                {
                    "failure_stage": "profile",
                    "failure_code": "precondition_not_reproduced",
                }
            )
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_with(
        execution_sha=execution_sha,
        fetcher=base._acquire_fixed_shakemap_pair,
        profile_func=base.profile_fixed_greece_shakemap_pair,
        classifier=classify_unit_failure,
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
        raise ShakeMapUnitDiagnosticError("output path is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
