# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main direct-child diagnostic for the fixed ESRM20 Greece rupture.

The upstream trusted-main root diagnostic proved that the exact already-receipted
666-byte rupture has an NRML 0.4 ``nrml`` root. Model-era OpenQuake 3.12.1 source
and tests show that this root namespace alone is not a generic rupture-reader
blocker. This action therefore classifies only the single direct rupture child
and a small whitelist-derived direct-child structural class. It never persists
provider bytes or publishes raw XML values.

A PASS is diagnostic classification only. It is not OpenQuake runtime acceptance,
event selection, validation, publication permission, or model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

try:
    from scripts import profile_esrm20_scenario_v10_greece_rupture as profile
    from scripts import run_esrm20_scenario_v10_greece_rupture_profile_action as base
    from scripts import run_esrm20_scenario_v10_greece_rupture_root_diagnostic_action as rootdiag
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import profile_esrm20_scenario_v10_greece_rupture as profile
    import run_esrm20_scenario_v10_greece_rupture_profile_action as base
    import run_esrm20_scenario_v10_greece_rupture_root_diagnostic_action as rootdiag

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-child-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-child-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-child-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-child-diagnostic-result-v1"
ACTION = "esrm20_scenario_v10_greece_rupture_child_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 6000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_RECEIPT_SHA256 = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
_RECEIPT_BYTE_COUNT = 666
_EXPECTED_ROOT_NAMESPACE = "http://openquake.org/xmlns/nrml/0.4"
_EXPECTED_05_NAMESPACE = "http://openquake.org/xmlns/nrml/0.5"

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

_CHILD_CLASS_BY_LOCAL = {
    "simpleFaultRupture": "simple_fault_rupture",
    "complexFaultRupture": "complex_fault_rupture",
    "singlePlaneRupture": "single_plane_rupture",
    "multiPlanesRupture": "multi_planes_rupture",
    "griddedRupture": "gridded_rupture",
}
CHILD_CLASSES = frozenset(
    set(_CHILD_CLASS_BY_LOCAL.values())
    | {"unsupported_rupture_child", "top_level_cardinality_not_one"}
)
CHILD_NAMESPACE_CLASSES = frozenset(
    {"legacy_04_namespace", "expected_05_namespace", "unrecognized_namespace"}
)
STRUCTURE_CLASSES = frozenset(
    {
        "oq3121_required_direct_children_present",
        "oq3121_required_direct_children_missing_or_ambiguous",
        "not_assessed",
    }
)
FAILURE_STAGES = frozenset({"acquisition", "byte_identity", "child_shape"})
CHILD_FAILURE_CODES = frozenset({"child_shape_parse_rejected"})

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
    "root_class",
    "child_class",
    "child_namespace_class",
    "required_structure_class",
    "provider_file_bytes_read",
    "byte_identity_verified",
    "child_shape_classified",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}


class RuptureChildDiagnosticError(RuntimeError):
    """The child-diagnostic request/result contract or authority drifted."""


class ChildShapeParseError(ValueError):
    """The bounded direct-child shape could not be classified safely."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RuptureChildDiagnosticError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise RuptureChildDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except RuptureChildDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuptureChildDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RuptureChildDiagnosticError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    rootdiag._require_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.EXPECTED_BYTE_COUNT, _RECEIPT_BYTE_COUNT, "receipt byte count"),
        (base.EXPECTED_SHA256, _RECEIPT_SHA256, "receipt sha256"),
        (rootdiag._LEGACY_NAMESPACE_04, _EXPECTED_ROOT_NAMESPACE, "legacy root namespace"),
        (
            profile.OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
            frozenset(_CHILD_CLASS_BY_LOCAL),
            "rupture child set",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise RuptureChildDiagnosticError(f"diagnostic {label} drifted")


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise RuptureChildDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureChildDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise RuptureChildDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuptureChildDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise RuptureChildDiagnosticError("request fields drifted")
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
            raise RuptureChildDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise RuptureChildDiagnosticError("invalid requester")
    return request


def _namespace_class(namespace: str) -> str:
    if namespace == _EXPECTED_ROOT_NAMESPACE:
        return "legacy_04_namespace"
    if namespace == _EXPECTED_05_NAMESPACE:
        return "expected_05_namespace"
    return "unrecognized_namespace"


def _direct_local_counts(element: ET.Element) -> dict[str, int]:
    counts: dict[str, int] = {}
    for child in list(element):
        _, local = profile._split_tag(child.tag)
        counts[local] = counts.get(local, 0) + 1
    return counts


def _required_structure_class(child: ET.Element, rupture_local: str) -> str:
    counts = _direct_local_counts(child)
    core_ok = all(counts.get(name, 0) == 1 for name in ("magnitude", "rake", "hypocenter"))
    if rupture_local == "simpleFaultRupture":
        geometry_ok = counts.get("simpleFaultGeometry", 0) == 1
    elif rupture_local == "complexFaultRupture":
        geometry_ok = counts.get("complexFaultGeometry", 0) == 1
    elif rupture_local == "singlePlaneRupture":
        geometry_ok = counts.get("planarSurface", 0) == 1
    elif rupture_local == "multiPlanesRupture":
        planar = counts.get("planarSurface", 0)
        kite = counts.get("kiteSurface", 0)
        geometry_ok = (planar > 0) ^ (kite > 0)
    elif rupture_local == "griddedRupture":
        geometry_ok = counts.get("griddedSurface", 0) == 1
    else:  # pragma: no cover - caller guards supported local names
        return "not_assessed"
    if core_ok and geometry_ok:
        return "oq3121_required_direct_children_present"
    return "oq3121_required_direct_children_missing_or_ambiguous"


def _classify_child_shape_unbound(data: bytes) -> dict[str, str | None]:
    """Classify synthetic/already-bound XML without exposing provider values."""
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    try:
        text = profile._decode_xml(data)
        root = ET.fromstring(text)
        root_namespace, root_local = profile._split_tag(root.tag)
    except (profile.RuptureProfileError, ET.ParseError) as exc:
        raise ChildShapeParseError("child_shape_parse_rejected") from exc

    if root_local != "nrml" or root_namespace != _EXPECTED_ROOT_NAMESPACE:
        raise ChildShapeParseError("child_shape_parse_rejected")

    children = list(root)
    if len(children) != 1:
        return {
            "root_class": "nrml_root_legacy_04",
            "child_class": "top_level_cardinality_not_one",
            "child_namespace_class": None,
            "required_structure_class": "not_assessed",
        }

    child = children[0]
    try:
        child_namespace, child_local = profile._split_tag(child.tag)
        namespace_class = _namespace_class(child_namespace)
    except profile.RuptureProfileError as exc:
        raise ChildShapeParseError("child_shape_parse_rejected") from exc

    child_class = _CHILD_CLASS_BY_LOCAL.get(child_local)
    if child_class is None:
        return {
            "root_class": "nrml_root_legacy_04",
            "child_class": "unsupported_rupture_child",
            "child_namespace_class": namespace_class,
            "required_structure_class": "not_assessed",
        }

    try:
        structure_class = _required_structure_class(child, child_local)
    except profile.RuptureProfileError as exc:
        raise ChildShapeParseError("child_shape_parse_rejected") from exc
    return {
        "root_class": "nrml_root_legacy_04",
        "child_class": child_class,
        "child_namespace_class": namespace_class,
        "required_structure_class": structure_class,
    }


def classify_fixed_child_shape(data: bytes) -> dict[str, str | None]:
    """Classify only the direct-child shape of the exact receipted rupture bytes."""
    _require_authority()
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if len(data) != _RECEIPT_BYTE_COUNT:
        raise base.RuptureByteIdentityError("byte_count_mismatch")
    if hashlib.sha256(data).hexdigest() != _RECEIPT_SHA256:
        raise base.RuptureByteIdentityError("sha256_mismatch")
    return _classify_child_shape_unbound(data)


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
        "root_class": None,
        "child_class": None,
        "child_namespace_class": None,
        "required_structure_class": None,
        "provider_file_bytes_read": False,
        "byte_identity_verified": False,
        "child_shape_classified": False,
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
        raise RuptureChildDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureChildDiagnosticError("invalid result SHA")
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
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise RuptureChildDiagnosticError(f"result {field} drifted")

    status = result.get("status")
    stage = result.get("failure_stage")
    code = result.get("failure_code")
    root_class = result.get("root_class")
    child_class = result.get("child_class")
    ns_class = result.get("child_namespace_class")
    structure_class = result.get("required_structure_class")
    bytes_read = result.get("provider_file_bytes_read")
    identity_verified = result.get("byte_identity_verified")
    classified = result.get("child_shape_classified")

    if type(bytes_read) is not bool:
        raise RuptureChildDiagnosticError("invalid provider_file_bytes_read")
    if type(identity_verified) is not bool:
        raise RuptureChildDiagnosticError("invalid byte_identity_verified")
    if type(classified) is not bool:
        raise RuptureChildDiagnosticError("invalid child_shape_classified")

    if status == "pass":
        if (
            stage is not None
            or code is not None
            or root_class != "nrml_root_legacy_04"
            or child_class not in CHILD_CLASSES
            or structure_class not in STRUCTURE_CLASSES
            or bytes_read is not True
            or identity_verified is not True
            or classified is not True
        ):
            raise RuptureChildDiagnosticError("invalid PASS state")
        if child_class == "top_level_cardinality_not_one":
            if ns_class is not None or structure_class != "not_assessed":
                raise RuptureChildDiagnosticError("invalid cardinality classification")
        elif child_class == "unsupported_rupture_child":
            if ns_class not in CHILD_NAMESPACE_CLASSES or structure_class != "not_assessed":
                raise RuptureChildDiagnosticError("invalid unsupported-child classification")
        else:
            if (
                ns_class not in CHILD_NAMESPACE_CLASSES
                or structure_class
                not in {
                    "oq3121_required_direct_children_present",
                    "oq3121_required_direct_children_missing_or_ambiguous",
                }
            ):
                raise RuptureChildDiagnosticError("invalid supported-child classification")
    elif status == "blocked":
        if (
            stage not in FAILURE_STAGES
            or type(code) is not str
            or root_class is not None
            or child_class is not None
            or ns_class is not None
            or structure_class is not None
            or classified is not False
        ):
            raise RuptureChildDiagnosticError("invalid blocked failure state")
        if stage == "acquisition":
            expected = ("acquisition_failed", False, False)
        elif stage == "byte_identity":
            expected = ("byte_identity_mismatch", True, False)
        else:
            if code not in CHILD_FAILURE_CODES:
                raise RuptureChildDiagnosticError("invalid child-shape failure code")
            expected = (code, True, True)
        if (code, bytes_read, identity_verified) != expected:
            raise RuptureChildDiagnosticError("blocked identity/shape state drifted")
    else:
        raise RuptureChildDiagnosticError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise RuptureChildDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuptureChildDiagnosticError("non-canonical result envelope")
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
        raise RuptureChildDiagnosticError("issue ledger is incomplete") from exc
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
    classifier: Callable[[bytes], dict[str, str | None]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureChildDiagnosticError("invalid execution SHA")
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
            classification = classifier(raw)
        except ChildShapeParseError:
            result.update(
                {
                    "failure_stage": "child_shape",
                    "failure_code": "child_shape_parse_rejected",
                }
            )
        else:
            if type(classification) is not dict or set(classification) != {
                "root_class",
                "child_class",
                "child_namespace_class",
                "required_structure_class",
            }:
                raise RuptureChildDiagnosticError("classifier returned invalid fields")
            result.update(
                {
                    "status": "pass",
                    "failure_stage": None,
                    "failure_code": None,
                    **classification,
                    "child_shape_classified": True,
                }
            )
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_diagnostic_with(
        execution_sha=execution_sha,
        fetcher=base._acquire_fixed_rupture,
        classifier=classify_fixed_child_shape,
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
        raise RuptureChildDiagnosticError("output path is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
