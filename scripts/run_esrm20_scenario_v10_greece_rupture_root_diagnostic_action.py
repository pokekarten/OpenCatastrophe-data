# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Closed trusted-main root-shape diagnostic for the fixed ESRM20 Greece rupture.

This action classifies only the XML root shape of the exact already-receipted
rupture bytes after the earlier profiler stopped at ``unexpected_nrml_root``.
A successful diagnostic is not parser acceptance, event-locality evidence,
validation, publication permission, or model-use authority.
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
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import profile_esrm20_scenario_v10_greece_rupture as profile
    import run_esrm20_scenario_v10_greece_rupture_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-root-diagnostic-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-root-diagnostic-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-root-diagnostic-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-root-diagnostic-result-v1"
ACTION = "esrm20_scenario_v10_greece_rupture_root_diagnostic"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 6000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_RECEIPT_SHA256 = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
_RECEIPT_BYTE_COUNT = 666
_EXPECTED_NAMESPACE = "http://openquake.org/xmlns/nrml/0.5"
_LEGACY_NAMESPACE_04 = "http://openquake.org/xmlns/nrml/0.4"

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")

ROOT_CLASSES = frozenset(
    {
        "nrml_root_expected_namespace",
        "nrml_root_legacy_04",
        "nrml_root_unrecognized_namespace",
        "direct_rupture_root_expected_namespace",
        "direct_rupture_root_legacy_04",
        "direct_rupture_root_unrecognized_namespace",
        "unrecognized_root_local_name",
    }
)
FAILURE_STAGES = frozenset({"acquisition", "byte_identity", "root"})
ROOT_FAILURE_CODES = frozenset({"root_parse_rejected"})

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
    "provider_file_bytes_read",
    "byte_identity_verified",
    "root_classified",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}


class RuptureRootDiagnosticError(RuntimeError):
    """The root-diagnostic request/result contract or authority drifted."""


class RootShapeParseError(ValueError):
    """The bounded root shape could not be parsed safely."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RuptureRootDiagnosticError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise RuptureRootDiagnosticError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except RuptureRootDiagnosticError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuptureRootDiagnosticError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RuptureRootDiagnosticError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    base._require_canonical_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.EXPECTED_BYTE_COUNT, _RECEIPT_BYTE_COUNT, "receipt byte count"),
        (base.EXPECTED_SHA256, _RECEIPT_SHA256, "receipt sha256"),
        (base.EXPECTED_NRML_NAMESPACE, _EXPECTED_NAMESPACE, "expected NRML namespace"),
        (
            base.OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
            profile.OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS,
            "rupture element set",
        ),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise RuptureRootDiagnosticError(f"diagnostic {label} drifted")


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise RuptureRootDiagnosticError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureRootDiagnosticError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise RuptureRootDiagnosticError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuptureRootDiagnosticError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise RuptureRootDiagnosticError("request fields drifted")
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
            raise RuptureRootDiagnosticError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise RuptureRootDiagnosticError("invalid requester")
    return request


def _classify_root_shape_unbound(data: bytes) -> str:
    """Classify one synthetic/already-bound XML root without exposing source text."""
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    try:
        text = profile._decode_xml(data)
        root = ET.fromstring(text)
        namespace, local = profile._split_tag(root.tag)
    except (profile.RuptureProfileError, ET.ParseError) as exc:
        raise RootShapeParseError("root_parse_rejected") from exc

    if local == "nrml":
        if namespace == _EXPECTED_NAMESPACE:
            return "nrml_root_expected_namespace"
        if namespace == _LEGACY_NAMESPACE_04:
            return "nrml_root_legacy_04"
        return "nrml_root_unrecognized_namespace"

    if local in profile.OPENQUAKE_3_12_1_INDIVIDUAL_RUPTURE_ELEMENTS:
        if namespace == _EXPECTED_NAMESPACE:
            return "direct_rupture_root_expected_namespace"
        if namespace == _LEGACY_NAMESPACE_04:
            return "direct_rupture_root_legacy_04"
        return "direct_rupture_root_unrecognized_namespace"

    return "unrecognized_root_local_name"


def classify_fixed_root_shape(data: bytes) -> str:
    """Classify only the root shape of the exact receipted Greece rupture bytes."""
    _require_authority()
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if len(data) != _RECEIPT_BYTE_COUNT:
        raise base.RuptureByteIdentityError("byte_count_mismatch")
    if hashlib.sha256(data).hexdigest() != _RECEIPT_SHA256:
        raise base.RuptureByteIdentityError("sha256_mismatch")
    return _classify_root_shape_unbound(data)


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
        "provider_file_bytes_read": False,
        "byte_identity_verified": False,
        "root_classified": False,
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
        raise RuptureRootDiagnosticError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureRootDiagnosticError("invalid result SHA")
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
            raise RuptureRootDiagnosticError(f"result {field} drifted")

    status = result.get("status")
    stage = result.get("failure_stage")
    code = result.get("failure_code")
    root_class = result.get("root_class")
    bytes_read = result.get("provider_file_bytes_read")
    identity_verified = result.get("byte_identity_verified")
    root_classified = result.get("root_classified")

    if type(bytes_read) is not bool:
        raise RuptureRootDiagnosticError("invalid provider_file_bytes_read")
    if type(identity_verified) is not bool:
        raise RuptureRootDiagnosticError("invalid byte_identity_verified")
    if type(root_classified) is not bool:
        raise RuptureRootDiagnosticError("invalid root_classified")

    if status == "pass":
        if (
            stage is not None
            or code is not None
            or type(root_class) is not str
            or root_class not in ROOT_CLASSES
            or bytes_read is not True
            or identity_verified is not True
            or root_classified is not True
        ):
            raise RuptureRootDiagnosticError("invalid PASS state")
    elif status == "blocked":
        if stage not in FAILURE_STAGES or type(code) is not str or root_class is not None:
            raise RuptureRootDiagnosticError("invalid blocked failure state")
        if stage == "acquisition":
            expected = ("acquisition_failed", False, False, False)
        elif stage == "byte_identity":
            expected = ("byte_identity_mismatch", True, False, False)
        else:
            if code not in ROOT_FAILURE_CODES:
                raise RuptureRootDiagnosticError("invalid root failure code")
            expected = (code, True, True, False)
        if (code, bytes_read, identity_verified, root_classified) != expected:
            raise RuptureRootDiagnosticError("blocked identity/root state drifted")
    else:
        raise RuptureRootDiagnosticError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise RuptureRootDiagnosticError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise RuptureRootDiagnosticError("non-canonical result envelope")
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
        raise RuptureRootDiagnosticError("issue ledger is incomplete") from exc
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
    classifier: Callable[[bytes], str],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise RuptureRootDiagnosticError("invalid execution SHA")
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
            root_class = classifier(raw)
        except RootShapeParseError:
            result.update(
                {
                    "failure_stage": "root",
                    "failure_code": "root_parse_rejected",
                }
            )
        else:
            if type(root_class) is not str or root_class not in ROOT_CLASSES:
                raise RuptureRootDiagnosticError("classifier returned invalid root class")
            result.update(
                {
                    "status": "pass",
                    "failure_stage": None,
                    "failure_code": None,
                    "root_class": root_class,
                    "root_classified": True,
                }
            )
    _validate_terminal_result(result)
    return result


def run_diagnostic(*, execution_sha: str) -> dict[str, Any]:
    return _run_diagnostic_with(
        execution_sha=execution_sha,
        fetcher=base._acquire_fixed_rupture,
        classifier=classify_fixed_root_shape,
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
        raise RuptureRootDiagnosticError("output path is required")
    result = run_diagnostic(execution_sha=args.execution_sha)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
