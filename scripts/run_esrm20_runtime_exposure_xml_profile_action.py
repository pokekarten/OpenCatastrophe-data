# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed issue-comment action for exact ESRM20 Kosovo runtime exposure XML profiling."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments
    from scripts.profile_esrm20_runtime_exposure_xml import (
        ACCEPTED_NRML_NAMESPACES,
        COMMIT_SHA,
        DATASET_ID,
        EXPECTED_BYTE_COUNT,
        EXPECTED_SHA256,
        PROJECT_ID,
        PROJECT_PATH,
        REPOSITORY_PATH,
        SOURCE_ISSUE,
        ByteIdentityMismatch,
        RuntimeExposureXmlProfileError,
        XmlSemanticProfileError,
        profile_runtime_exposure_xml,
    )
except ModuleNotFoundError:  # pragma: no cover
    from acquire_efehr_gitlab_receipt import EfehrAcquisitionError
    from prepare_agent_action_result import LedgerError, fetch_repository_comments
    from profile_esrm20_runtime_exposure_xml import (
        ACCEPTED_NRML_NAMESPACES,
        COMMIT_SHA,
        DATASET_ID,
        EXPECTED_BYTE_COUNT,
        EXPECTED_SHA256,
        PROJECT_ID,
        PROJECT_PATH,
        REPOSITORY_PATH,
        SOURCE_ISSUE,
        ByteIdentityMismatch,
        RuntimeExposureXmlProfileError,
        XmlSemanticProfileError,
        profile_runtime_exposure_xml,
    )

REQUEST_MARKER = "<!-- oc-eq1-esrm20-runtime-exposure-xml-profile-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-runtime-exposure-xml-profile-result-v5 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-runtime-exposure-xml-profile-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-runtime-exposure-xml-profile-result-v5"
ACTION = "esrm20_runtime_exposure_xml_profile"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_LEDGER_PAGES = 20
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 30000

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
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
    "runtime_exposure_identity",
    "status",
    "failure_class",
    "failure_code",
    "receipt",
    "profile",
    "xml_content_interpreted",
    "exact_kosovo_exposure_selected",
    "value_structural_wiring_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
}
_PROFILE_FIELDS = {
    "nrml_namespace",
    "exposure_model",
    "asset_references",
    "cost_types",
    "area",
    "occupancy_periods",
    "tag_names",
    "exposure_fields",
    "structural_cost_type_declared",
    "structural_value_inputs",
}

# Public diagnostic codes are intentionally derived only from static parser-owned
# messages. Provider bytes, text, attributes and values are never copied into the
# terminal result. Unknown/new parser messages collapse to one bounded code.
_XML_FAILURE_CODE_BY_MESSAGE = {
    "runtime exposure payload is empty or not bytes": "empty_or_nonbytes_payload",
    "runtime exposure payload exceeds profile bound": "payload_exceeds_profile_bound",
    "DTD/entity declarations are forbidden": "dtd_or_entity_forbidden",
    "runtime exposure XML is malformed": "malformed_xml",
    "runtime exposure NRML root local name drifted": "nrml_root_local_name_drifted",
    "runtime exposure NRML root namespace is unrecognized": (
        "nrml_root_namespace_unrecognized"
    ),
    "runtime exposure NRML root attributes present": "nrml_root_attributes_present",
    "expected exactly one exposureModel": "exposure_model_cardinality_drifted",
    "exposureModel attributes drifted": "exposure_model_attributes_drifted",
    "foreign exposureModel child namespace": "exposure_model_child_namespace_drifted",
    "unknown or duplicate exposureModel child": "exposure_model_child_set_drifted",
    "required exposure metadata is missing": "required_exposure_metadata_missing",
    "description unexpectedly contains child elements": "description_shape_drifted",
    "description is empty": "description_empty",
    "unsafe asset reference": "unsafe_asset_reference",
    "runtime exposure asset is not CSV": "asset_reference_not_csv",
    "assets declaration drifted": "assets_declaration_drifted",
    "asset references are empty or duplicated": "asset_reference_set_drifted",
    "conversions envelope drifted": "conversions_envelope_drifted",
    "foreign conversions namespace": "conversions_child_namespace_drifted",
    "unknown or duplicate conversions child": "conversions_child_set_drifted",
    "area declaration drifted": "area_declaration_drifted",
    "costTypes envelope drifted": "cost_types_envelope_drifted",
    "costType declaration drifted": "cost_type_declaration_drifted",
    "costType attributes drifted": "cost_type_attributes_drifted",
    "duplicate costType name": "duplicate_cost_type_name",
    "occupancyPeriods declaration drifted": "occupancy_periods_declaration_drifted",
    "tagNames declaration drifted": "tag_names_declaration_drifted",
    "exposureFields envelope drifted": "exposure_fields_envelope_drifted",
    "exposure field declaration drifted": "exposure_field_declaration_drifted",
    "exposure field attributes drifted": "exposure_field_attributes_drifted",
}
_XML_FAILURE_CODES = frozenset(_XML_FAILURE_CODE_BY_MESSAGE.values()) | {
    "unclassified_xml_profile_failure"
}


class RuntimeExposureXmlProfileActionError(RuntimeError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeExposureXmlProfileActionError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise RuntimeExposureXmlProfileActionError(f"non-finite JSON constant: {value}")


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise RuntimeExposureXmlProfileActionError("non-finite JSON float")
    return parsed


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
            parse_float=_parse_float,
        )
    except RuntimeExposureXmlProfileActionError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeExposureXmlProfileActionError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RuntimeExposureXmlProfileActionError("text is not UTF-8 encodable") from exc


def _xml_failure_code(exc: XmlSemanticProfileError) -> str:
    return _XML_FAILURE_CODE_BY_MESSAGE.get(
        str(exc), "unclassified_xml_profile_failure"
    )


def validate_request(
    body: object, *, expected_issue: int, execution_sha: str
) -> dict[str, Any]:
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise RuntimeExposureXmlProfileActionError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureXmlProfileActionError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise RuntimeExposureXmlProfileActionError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuntimeExposureXmlProfileActionError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise RuntimeExposureXmlProfileActionError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
        ("receipt_sha256", EXPECTED_SHA256),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise RuntimeExposureXmlProfileActionError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise RuntimeExposureXmlProfileActionError("invalid requester")
    return request


def _identity() -> dict[str, Any]:
    return {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "receipt_byte_count": EXPECTED_BYTE_COUNT,
        "receipt_sha256": EXPECTED_SHA256,
    }


def _base_result(execution_sha: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "runtime_exposure_identity": _identity(),
        "status": "blocked",
        "failure_class": "profile_failure",
        "failure_code": None,
        "receipt": None,
        "profile": None,
        "xml_content_interpreted": False,
        "exact_kosovo_exposure_selected": False,
        "value_structural_wiring_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_profile(profile: object) -> dict[str, Any]:
    if type(profile) is not dict or set(profile) != _PROFILE_FIELDS:
        raise RuntimeExposureXmlProfileActionError("profile fields drifted")
    namespace = profile.get("nrml_namespace")
    if type(namespace) is not str or namespace not in ACCEPTED_NRML_NAMESPACES:
        raise RuntimeExposureXmlProfileActionError("NRML namespace drifted")
    model = profile.get("exposure_model")
    if type(model) is not dict or set(model) != {
        "id",
        "category",
        "taxonomy_source",
        "description",
    }:
        raise RuntimeExposureXmlProfileActionError("exposure model profile drifted")
    for key in ("id", "description"):
        if type(model.get(key)) is not str or not model[key]:
            raise RuntimeExposureXmlProfileActionError("invalid exposure model text")
    for key in ("category", "taxonomy_source"):
        if model.get(key) is not None and type(model[key]) is not str:
            raise RuntimeExposureXmlProfileActionError("invalid exposure model metadata")
    assets = profile.get("asset_references")
    if (
        type(assets) is not list
        or not assets
        or any(type(item) is not str or not item for item in assets)
    ):
        raise RuntimeExposureXmlProfileActionError("invalid asset references")
    for key in (
        "cost_types",
        "occupancy_periods",
        "tag_names",
        "exposure_fields",
        "structural_value_inputs",
    ):
        if type(profile.get(key)) is not list:
            raise RuntimeExposureXmlProfileActionError(f"invalid profile list: {key}")
    if profile.get("area") is not None and type(profile["area"]) is not dict:
        raise RuntimeExposureXmlProfileActionError("invalid area declaration")
    if type(profile.get("structural_cost_type_declared")) is not bool:
        raise RuntimeExposureXmlProfileActionError(
            "invalid structural declaration flag"
        )
    return profile


def _validate_terminal_result(result: object) -> str:
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise RuntimeExposureXmlProfileActionError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureXmlProfileActionError("invalid result SHA")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("runtime_exposure_identity", _identity()),
        ("exact_kosovo_exposure_selected", False),
        ("value_structural_wiring_verified", False),
        ("external_bytes_persisted", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        if result.get(field) != expected:
            raise RuntimeExposureXmlProfileActionError(f"result {field} drifted")
    status = result.get("status")
    if status == "pass":
        if (
            result.get("failure_class") is not None
            or result.get("failure_code") is not None
            or result.get("xml_content_interpreted") is not True
        ):
            raise RuntimeExposureXmlProfileActionError("invalid PASS state")
        receipt = result.get("receipt")
        if type(receipt) is not dict or set(receipt) != {
            "retrieved_at",
            "byte_count",
            "sha256",
            "content_type",
            "etag",
        }:
            raise RuntimeExposureXmlProfileActionError("PASS receipt drifted")
        if (
            receipt.get("byte_count") != EXPECTED_BYTE_COUNT
            or receipt.get("sha256") != EXPECTED_SHA256
        ):
            raise RuntimeExposureXmlProfileActionError("PASS byte identity drifted")
        if type(receipt.get("retrieved_at")) is not str or not receipt["retrieved_at"]:
            raise RuntimeExposureXmlProfileActionError("PASS retrieval time invalid")
        _validate_profile(result.get("profile"))
    elif status == "blocked":
        failure_class = result.get("failure_class")
        if failure_class not in {
            "acquisition_failure",
            "byte_identity_mismatch",
            "xml_profile_failure",
            "profile_failure",
        }:
            raise RuntimeExposureXmlProfileActionError(
                "invalid blocked failure class"
            )
        failure_code = result.get("failure_code")
        if failure_class == "xml_profile_failure":
            if type(failure_code) is not str or failure_code not in _XML_FAILURE_CODES:
                raise RuntimeExposureXmlProfileActionError("invalid XML failure code")
        elif failure_code is not None:
            raise RuntimeExposureXmlProfileActionError(
                "non-XML failure carries diagnostic code"
            )
        if (
            result.get("receipt") is not None
            or result.get("profile") is not None
            or result.get("xml_content_interpreted") is not False
        ):
            raise RuntimeExposureXmlProfileActionError("blocked result widened evidence")
    else:
        raise RuntimeExposureXmlProfileActionError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if (
        _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES
        or body.count(RESULT_MARKER) != 1
    ):
        raise RuntimeExposureXmlProfileActionError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuntimeExposureXmlProfileActionError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    kwargs: dict[str, Any] = {
        "issue": SOURCE_ISSUE,
        "max_pages": MAX_LEDGER_PAGES,
    }
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise RuntimeExposureXmlProfileActionError("issue ledger is incomplete") from exc
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


def run_profile(*, execution_sha: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuntimeExposureXmlProfileActionError("invalid execution SHA")
    result = _base_result(execution_sha)
    try:
        evidence = profile_runtime_exposure_xml()
    except ByteIdentityMismatch:
        result["failure_class"] = "byte_identity_mismatch"
    except XmlSemanticProfileError as exc:
        result["failure_class"] = "xml_profile_failure"
        result["failure_code"] = _xml_failure_code(exc)
    except EfehrAcquisitionError:
        result["failure_class"] = "acquisition_failure"
    except RuntimeExposureXmlProfileError:
        result["failure_class"] = "profile_failure"
    else:
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "failure_code": None,
                "receipt": evidence["receipt"],
                "profile": evidence["profile"],
                "xml_content_interpreted": True,
            }
        )
    _validate_terminal_result(result)
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
    result = run_profile(execution_sha=args.execution_sha)
    if not args.output:
        raise RuntimeExposureXmlProfileActionError("output path is required")
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())