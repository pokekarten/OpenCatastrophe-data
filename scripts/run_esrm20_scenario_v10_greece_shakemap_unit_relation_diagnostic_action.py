# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main classifier for one Greece ShakeMap field-unit rejection.

This successor does not widen the merged ShakeMap parser. It can only classify
the already-observed ``unsupported_grid_field_units`` boundary into a finite
member/field/relation tuple. Raw provider unit tokens and XML are never returned.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Mapping

try:
    from scripts import profile_esrm20_scenario_v10_greece_shakemap as profiler
    from scripts import run_esrm20_scenario_v10_greece_shakemap_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import profile_esrm20_scenario_v10_greece_shakemap as profiler
    import run_esrm20_scenario_v10_greece_shakemap_profile_action as base

REQUEST_MARKER = (
    "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-unit-relation-diagnostic-request-v1 -->"
)
RESULT_MARKER = (
    "<!-- oc-eq1-esrm20-scenario-v10-greece-shakemap-unit-relation-diagnostic-result-v1 -->"
)
REQUEST_SCHEMA_VERSION = (
    "oc-esrm20-scenario-v10-greece-shakemap-unit-relation-diagnostic-request-v1"
)
RESULT_SCHEMA_VERSION = (
    "oc-esrm20-scenario-v10-greece-shakemap-unit-relation-diagnostic-result-v1"
)
ACTION = "esrm20_scenario_v10_greece_shakemap_unit_relation_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 7600
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_GRID_SHA256 = "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f"
_UNCERTAINTY_SHA256 = "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417"
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_EXPECTED_GRID_FIELD_UNITS = {
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
_EXPECTED_UNCERTAINTY_FIELD_UNITS = {
    "LON": frozenset({"dd"}),
    "LAT": frozenset({"dd"}),
    "STDPGA": frozenset({"ln(pctg)"}),
    "STDPGV": frozenset({"ln(cms)"}),
    "STDMMI": frozenset({"mmi", "intensity"}),
    "STDPSA03": frozenset({"ln(pctg)"}),
    "STDPSA10": frozenset({"ln(pctg)"}),
    "STDPSA30": frozenset({"ln(pctg)"}),
}
_FROZEN_USGS_UNIT_VOCABULARY = frozenset(
    {"", "dd", "pctg", "cms", "mmi", "intensity", "ms", "ln(pctg)", "ln(cms)"}
)
_UNIT_RELATIONS = frozenset(
    {
        "blank_unexpected",
        "documented_global_unit_wrong_for_field",
        "outside_frozen_usgs_unit_vocabulary",
    }
)
_FAILURE_CODES = frozenset(
    {
        "acquisition_failed",
        "byte_identity_mismatch",
        "profile_rejection_changed",
        "profile_rejection_not_reproduced",
        "unsupported_grid_field_units",
    }
)
_FAILURE_STAGES = frozenset({"acquisition", "byte_identity", "profile"})

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
    "unit_failure_member",
    "unit_failure_field",
    "unit_relation",
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


class ShakeMapUnitRelationDiagnosticError(RuntimeError):
    """The diagnostic contract or frozen scientific boundary drifted."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ShakeMapUnitRelationDiagnosticError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise ShakeMapUnitRelationDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except ShakeMapUnitRelationDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ShakeMapUnitRelationDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise ShakeMapUnitRelationDiagnosticError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    base._require_canonical_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.GRID_SHA256, _GRID_SHA256, "grid receipt sha256"),
        (base.UNCERTAINTY_SHA256, _UNCERTAINTY_SHA256, "uncertainty receipt sha256"),
        (profiler._GRID_FIELD_UNITS, _EXPECTED_GRID_FIELD_UNITS, "grid unit map"),
        (
            profiler._UNCERTAINTY_FIELD_UNITS,
            _EXPECTED_UNCERTAINTY_FIELD_UNITS,
            "uncertainty unit map",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapUnitRelationDiagnosticError(f"diagnostic {label} drifted")


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise ShakeMapUnitRelationDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapUnitRelationDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise ShakeMapUnitRelationDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise ShakeMapUnitRelationDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise ShakeMapUnitRelationDiagnosticError("request fields drifted")
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
            raise ShakeMapUnitRelationDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise ShakeMapUnitRelationDiagnosticError("invalid requester")
    return request


def _relation_for_unit(units: str) -> str:
    if units == "":
        return "blank_unexpected"
    if units in _FROZEN_USGS_UNIT_VOCABULARY:
        return "documented_global_unit_wrong_for_field"
    return "outside_frozen_usgs_unit_vocabulary"


def _classify_member_unit_mismatch(
    data: bytes,
    *,
    member: str,
    allowed_units: Mapping[str, frozenset[str]],
) -> dict[str, str] | None:
    if type(member) is not str or member not in {"grid", "uncertainty"}:
        raise ShakeMapUnitRelationDiagnosticError("invalid unit classifier member")
    try:
        text = profiler._decode_xml(data, maximum=profiler.MAX_XML_BYTES)
        root = ET.fromstring(text)
    except (profiler.ShakeMapProfileError, ET.ParseError):
        raise ShakeMapUnitRelationDiagnosticError("unit classifier XML boundary drifted") from None

    try:
        namespace, local = profiler._split_tag(root.tag)
    except profiler.ShakeMapProfileError:
        raise ShakeMapUnitRelationDiagnosticError("unit classifier root drifted") from None
    if local != "shakemap_grid":
        raise ShakeMapUnitRelationDiagnosticError("unit classifier root drifted")

    for child in root:
        try:
            child_namespace, child_local = profiler._split_tag(child.tag)
        except profiler.ShakeMapProfileError:
            raise ShakeMapUnitRelationDiagnosticError("unit classifier child drifted") from None
        if child_namespace != namespace:
            raise ShakeMapUnitRelationDiagnosticError("unit classifier namespace drifted")
        if child_local != "grid_field":
            continue
        name = child.attrib.get("name", "")
        units = child.attrib.get("units", "")
        if name not in allowed_units:
            raise ShakeMapUnitRelationDiagnosticError("unit classifier field drifted")
        if units not in allowed_units[name]:
            return {
                "unit_failure_member": member,
                "unit_failure_field": name,
                "unit_relation": _relation_for_unit(units),
            }
    return None


def classify_unit_rejection(grid_raw: bytes, uncertainty_raw: bytes) -> dict[str, str]:
    """Classify the first unit mismatch without returning the raw unit token."""
    _require_authority()
    for data, member, allowed_units in (
        (grid_raw, "grid", _EXPECTED_GRID_FIELD_UNITS),
        (uncertainty_raw, "uncertainty", _EXPECTED_UNCERTAINTY_FIELD_UNITS),
    ):
        classified = _classify_member_unit_mismatch(
            data,
            member=member,
            allowed_units=allowed_units,
        )
        if classified is not None:
            return classified
    raise ShakeMapUnitRelationDiagnosticError("unit rejection was not reproduced")


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
        "unit_failure_member": None,
        "unit_failure_field": None,
        "unit_relation": None,
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
        raise ShakeMapUnitRelationDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapUnitRelationDiagnosticError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("shakemap_identity", base._identity()),
        ("status", "blocked"),
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
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapUnitRelationDiagnosticError(f"result {field} drifted")

    stage = result.get("failure_stage")
    code = result.get("failure_code")
    bytes_read = result.get("provider_file_bytes_read")
    profiled = result.get("provider_file_content_profiled")
    identity_verified = result.get("byte_identity_verified")
    member = result.get("unit_failure_member")
    field = result.get("unit_failure_field")
    relation = result.get("unit_relation")

    if (
        type(stage) is not str
        or stage not in _FAILURE_STAGES
        or type(code) is not str
        or code not in _FAILURE_CODES
    ):
        raise ShakeMapUnitRelationDiagnosticError("invalid failure state")
    if type(bytes_read) is not bool or type(profiled) is not bool or type(identity_verified) is not bool:
        raise ShakeMapUnitRelationDiagnosticError("invalid result boolean state")

    if stage == "acquisition":
        if code != "acquisition_failed" or identity_verified or profiled:
            raise ShakeMapUnitRelationDiagnosticError("invalid acquisition state")
    elif stage == "byte_identity":
        if code != "byte_identity_mismatch" or not bytes_read or identity_verified or profiled:
            raise ShakeMapUnitRelationDiagnosticError("invalid byte-identity state")
    else:
        if not bytes_read or not identity_verified:
            raise ShakeMapUnitRelationDiagnosticError("invalid profile byte state")
        if code == "profile_rejection_not_reproduced":
            if not profiled:
                raise ShakeMapUnitRelationDiagnosticError("invalid reproduced-profile state")
        elif profiled:
            raise ShakeMapUnitRelationDiagnosticError("invalid rejected-profile state")

    classified = code == "unsupported_grid_field_units"
    if classified:
        if (
            type(member) is not str
            or member not in {"grid", "uncertainty"}
            or type(relation) is not str
            or relation not in _UNIT_RELATIONS
        ):
            raise ShakeMapUnitRelationDiagnosticError("invalid unit classification")
        allowed_fields = (
            _EXPECTED_GRID_FIELD_UNITS if member == "grid" else _EXPECTED_UNCERTAINTY_FIELD_UNITS
        )
        if type(field) is not str or field not in allowed_fields:
            raise ShakeMapUnitRelationDiagnosticError("invalid unit field")
    elif member is not None or field is not None or relation is not None:
        raise ShakeMapUnitRelationDiagnosticError("unexpected unit classification")

    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise ShakeMapUnitRelationDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise ShakeMapUnitRelationDiagnosticError("non-canonical result envelope")
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
        raise ShakeMapUnitRelationDiagnosticError("issue ledger is incomplete") from exc
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
    profile_pair: Callable[[bytes, bytes], dict[str, object]],
    unit_classifier: Callable[[bytes, bytes], dict[str, str]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise ShakeMapUnitRelationDiagnosticError("invalid execution SHA")
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
            profile = profile_pair(grid_raw, uncertainty_raw)
        except base.ShakeMapProfileError as exc:
            result["failure_stage"] = "profile"
            if type(exc) is base.ShakeMapProfileError and str(exc) == "unsupported_grid_field_units":
                classified = unit_classifier(grid_raw, uncertainty_raw)
                if type(classified) is not dict or set(classified) != {
                    "unit_failure_member",
                    "unit_failure_field",
                    "unit_relation",
                }:
                    raise ShakeMapUnitRelationDiagnosticError("unit classifier fields drifted")
                result["failure_code"] = "unsupported_grid_field_units"
                result.update(classified)
            else:
                result["failure_code"] = "profile_rejection_changed"
        else:
            base._validate_profile(profile)
            result.update(
                {
                    "failure_stage": "profile",
                    "failure_code": "profile_rejection_not_reproduced",
                    "provider_file_content_profiled": True,
                }
            )
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_diagnostic_with(
        execution_sha=execution_sha,
        fetcher=base._acquire_fixed_shakemap_pair,
        profile_pair=base.profile_fixed_greece_shakemap_pair,
        unit_classifier=classify_unit_rejection,
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
        raise ShakeMapUnitRelationDiagnosticError("output path is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
