# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Trusted-main-only OpenQuake 3.12.1 native acceptance gate for the fixed Greece rupture.

This gate proves only that the exact already-receipted ESRM20 v1.0 Greece rupture
can be ingested by the model-era OpenQuake 3.12.1 ``readinput.get_rupture`` path
as a single-plane rupture. It does not establish event selection, hazard
agreement, validation, vulnerability compatibility, publication permission, or
model-use authority.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

try:
    from scripts import run_esrm20_scenario_v10_greece_rupture_child_diagnostic_action as childdiag
    from scripts import run_esrm20_scenario_v10_greece_rupture_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import run_esrm20_scenario_v10_greece_rupture_child_diagnostic_action as childdiag
    import run_esrm20_scenario_v10_greece_rupture_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-oq3121-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-oq3121-runtime-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-oq3121-runtime-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-oq3121-runtime-result-v1"
ACTION = "esrm20_scenario_v10_greece_rupture_oq3121_runtime"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"

SOURCE_ISSUE = 285
DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
RECEIPT_SHA256 = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
OPENQUAKE_TAG = "v3.12.1"
OPENQUAKE_COMMIT = "0bb8441aa202cd6ec075bf2044dd4aaeb26919b9"
OPENQUAKE_IMAGE = "openquake/engine:3.12.1"
PARSER_PATH = "openquake.commonlib.readinput.get_rupture"
RUPTURE_CLASS = "BaseRupture"
SURFACE_CLASS = "PlanarSurface"
API_RUPTURE_MESH_SPACING = 1.0
API_SES_SEED = 0
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 7000
MAX_LEDGER_PAGES = 20

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUESTER_RE = re.compile(r"^[A-Za-z0-9_.:@/+ -]{1,96}$")
_IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUEST_FIELDS = {
    "schema_version",
    "action",
    "issue",
    "target_sha",
    "dataset_id",
    "receipt_sha256",
    "openquake_tag",
    "openquake_commit",
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
    "byte_identity_verified",
    "openquake_tag",
    "openquake_commit",
    "openquake_image",
    "runtime_image_digest",
    "parser_path",
    "openquake_version",
    "openquake_source_path_verified",
    "legacy_nrml_04_native_acceptance_verified",
    "single_plane_native_conversion_verified",
    "rupture_class",
    "surface_class",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "site_gsim_compatibility_established",
    "numerical_hazard_agreement_established",
    "vulnerability_compatibility_established",
    "reference_run_established",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}


class NativeRuptureGateError(RuntimeError):
    """The request/result/runtime contract drifted or native conversion failed."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise NativeRuptureGateError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise NativeRuptureGateError(f"non-finite JSON constant: {value}")


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except NativeRuptureGateError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise NativeRuptureGateError(f"invalid {label} JSON") from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise NativeRuptureGateError("text is not UTF-8 encodable") from exc


def _require_authority() -> None:
    childdiag._require_authority()
    exact = (
        (base.SOURCE_ISSUE, SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, DATASET_ID, "dataset id"),
        (base.EXPECTED_SHA256, RECEIPT_SHA256, "receipt sha256"),
        (childdiag._RECEIPT_SHA256, RECEIPT_SHA256, "child receipt sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise NativeRuptureGateError(f"authority {label} drifted")
    if not _SHA1_RE.fullmatch(OPENQUAKE_COMMIT):
        raise NativeRuptureGateError("OpenQuake commit pin invalid")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != SOURCE_ISSUE:
        raise NativeRuptureGateError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise NativeRuptureGateError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise NativeRuptureGateError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise NativeRuptureGateError("non-canonical request envelope")
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise NativeRuptureGateError("request fields drifted")
    exact = (
        ("schema_version", REQUEST_SCHEMA_VERSION),
        ("action", ACTION),
        ("issue", SOURCE_ISSUE),
        ("target_sha", execution_sha),
        ("dataset_id", DATASET_ID),
        ("receipt_sha256", RECEIPT_SHA256),
        ("openquake_tag", OPENQUAKE_TAG),
        ("openquake_commit", OPENQUAKE_COMMIT),
    )
    for field, expected in exact:
        observed = request.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise NativeRuptureGateError(f"request {field} drifted")
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise NativeRuptureGateError("invalid requester")
    return request


def _base_result(execution_sha: str, image_digest: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": SOURCE_ISSUE,
        "dataset_id": DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "rupture_identity": base._identity(),
        "status": "blocked",
        "failure_stage": "acquisition",
        "failure_code": "acquisition_failed",
        "provider_file_bytes_read": False,
        "byte_identity_verified": False,
        "openquake_tag": OPENQUAKE_TAG,
        "openquake_commit": OPENQUAKE_COMMIT,
        "openquake_image": OPENQUAKE_IMAGE,
        "runtime_image_digest": image_digest,
        "parser_path": PARSER_PATH,
        "openquake_version": None,
        "openquake_source_path_verified": False,
        "legacy_nrml_04_native_acceptance_verified": False,
        "single_plane_native_conversion_verified": False,
        "rupture_class": None,
        "surface_class": None,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "site_gsim_compatibility_established": False,
        "numerical_hazard_agreement_established": False,
        "vulnerability_compatibility_established": False,
        "reference_run_established": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _native_convert(raw: bytes) -> dict[str, str]:
    """Run the exact model-era ingestion API and expose class metadata only."""
    if type(raw) is not bytes:
        raise TypeError("raw must be bytes")
    shape = childdiag.classify_fixed_child_shape(raw)
    if shape != {
        "root_class": "nrml_root_legacy_04",
        "child_class": "single_plane_rupture",
        "child_namespace_class": "legacy_04_namespace",
        "required_structure_class": "oq3121_required_direct_children_present",
    }:
        raise NativeRuptureGateError("trusted structural precondition drifted")

    try:
        from openquake import baselib
        from openquake.commonlib import readinput
    except Exception as exc:  # pragma: no cover - exact runtime only
        raise NativeRuptureGateError("OpenQuake import rejected") from exc

    version = getattr(baselib, "__version__", None)
    if type(version) is not str or not version.startswith("3.12.1"):
        raise NativeRuptureGateError("OpenQuake version drifted")

    source_path = Path(inspect.getfile(readinput)).resolve()
    expected_root = Path(os.environ.get("OC_OQ_CHECKOUT_ROOT", "/oq-engine")).resolve()
    try:
        source_path.relative_to(expected_root)
    except ValueError as exc:
        raise NativeRuptureGateError("OpenQuake source path escaped pinned checkout") from exc

    with tempfile.TemporaryDirectory(prefix="oc-oq3121-rupture-") as temp_dir:
        rupture_path = Path(temp_dir) / "rupture.xml"
        rupture_path.write_bytes(raw)
        oqparam = SimpleNamespace(
            inputs={"rupture_model": str(rupture_path)},
            rupture_mesh_spacing=API_RUPTURE_MESH_SPACING,
            ses_seed=API_SES_SEED,
        )
        try:
            rupture = readinput.get_rupture(oqparam)
        except Exception as exc:
            raise NativeRuptureGateError("readinput.get_rupture rejected fixed bytes") from exc

    rupture_class = type(rupture).__name__
    surface = getattr(rupture, "surface", None)
    surface_class = type(surface).__name__ if surface is not None else None
    if rupture_class != RUPTURE_CLASS or surface_class != SURFACE_CLASS:
        raise NativeRuptureGateError("native rupture/surface class drifted")
    return {
        "openquake_version": version,
        "rupture_class": rupture_class,
        "surface_class": surface_class,
    }


def _validate_terminal_result(result: object) -> str:
    _require_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise NativeRuptureGateError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise NativeRuptureGateError("invalid result SHA")
    image_digest = result.get("runtime_image_digest")
    if type(image_digest) is not str or _IMAGE_DIGEST_RE.fullmatch(image_digest) is None:
        raise NativeRuptureGateError("invalid runtime image digest")

    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", SOURCE_ISSUE),
        ("dataset_id", DATASET_ID),
        ("target_sha", execution_sha),
        ("rupture_identity", base._identity()),
        ("openquake_tag", OPENQUAKE_TAG),
        ("openquake_commit", OPENQUAKE_COMMIT),
        ("openquake_image", OPENQUAKE_IMAGE),
        ("parser_path", PARSER_PATH),
        ("output_payload_bytes_read", False),
        ("external_bytes_persisted", False),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("site_gsim_compatibility_established", False),
        ("numerical_hazard_agreement_established", False),
        ("vulnerability_compatibility_established", False),
        ("reference_run_established", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise NativeRuptureGateError(f"result {field} drifted")

    if result.get("status") == "pass":
        if (
            result.get("failure_stage") is not None
            or result.get("failure_code") is not None
            or result.get("provider_file_bytes_read") is not True
            or result.get("byte_identity_verified") is not True
            or result.get("openquake_source_path_verified") is not True
            or result.get("legacy_nrml_04_native_acceptance_verified") is not True
            or result.get("single_plane_native_conversion_verified") is not True
            or result.get("rupture_class") != RUPTURE_CLASS
            or result.get("surface_class") != SURFACE_CLASS
            or type(result.get("openquake_version")) is not str
            or not result["openquake_version"].startswith("3.12.1")
        ):
            raise NativeRuptureGateError("invalid PASS state")
    elif result.get("status") == "blocked":
        stage = result.get("failure_stage")
        code = result.get("failure_code")
        allowed = {
            ("acquisition", "acquisition_failed"),
            ("byte_identity", "byte_identity_mismatch"),
            ("openquake_runtime", "native_conversion_rejected"),
        }
        if (stage, code) not in allowed:
            raise NativeRuptureGateError("invalid blocked failure")
        if any(
            result.get(field) is not False
            for field in (
                "openquake_source_path_verified",
                "legacy_nrml_04_native_acceptance_verified",
                "single_plane_native_conversion_verified",
            )
        ):
            raise NativeRuptureGateError("blocked result widened native authority")
        if result.get("rupture_class") is not None or result.get("surface_class") is not None:
            raise NativeRuptureGateError("blocked result exposes native classes")
        if result.get("openquake_version") is not None:
            raise NativeRuptureGateError("blocked result exposes partial runtime version")
        expected_read = stage != "acquisition"
        if result.get("provider_file_bytes_read") is not expected_read:
            raise NativeRuptureGateError("blocked byte-read state drifted")
        expected_identity = stage == "openquake_runtime"
        if result.get("byte_identity_verified") is not expected_identity:
            raise NativeRuptureGateError("blocked identity state drifted")
    else:
        raise NativeRuptureGateError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise NativeRuptureGateError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise NativeRuptureGateError("non-canonical result envelope")
    return _validate_terminal_result(_strict_loads(after.strip(), label="result"))


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    kwargs: dict[str, Any] = {"issue": SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = base.fetch_repository_comments(repository, token, **kwargs)
    except base.LedgerError as exc:
        raise NativeRuptureGateError("issue ledger is incomplete") from exc
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
    image_digest: str,
    fetcher: Callable[[], tuple[bytes, dict[str, Any]]],
    converter: Callable[[bytes], dict[str, str]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise NativeRuptureGateError("invalid execution SHA")
    if type(image_digest) is not str or _IMAGE_DIGEST_RE.fullmatch(image_digest) is None:
        raise NativeRuptureGateError("invalid image digest")
    _require_authority()
    result = _base_result(execution_sha, image_digest)
    try:
        raw, _receipt = fetcher()
    except base.RuptureByteIdentityError:
        result.update(
            failure_stage="byte_identity",
            failure_code="byte_identity_mismatch",
            provider_file_bytes_read=True,
        )
    except base.EfehrAcquisitionError:
        pass
    else:
        result["provider_file_bytes_read"] = True
        result["byte_identity_verified"] = True
        try:
            metadata = converter(raw)
        except NativeRuptureGateError:
            result.update(
                failure_stage="openquake_runtime",
                failure_code="native_conversion_rejected",
            )
        else:
            if set(metadata) != {"openquake_version", "rupture_class", "surface_class"}:
                raise NativeRuptureGateError("converter metadata widened")
            result.update(
                status="pass",
                failure_stage=None,
                failure_code=None,
                openquake_version=metadata["openquake_version"],
                openquake_source_path_verified=True,
                legacy_nrml_04_native_acceptance_verified=True,
                single_plane_native_conversion_verified=True,
                rupture_class=metadata["rupture_class"],
                surface_class=metadata["surface_class"],
            )
    _validate_terminal_result(result)
    return result


def run_runtime(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    return _run_with(
        execution_sha=execution_sha,
        image_digest=image_digest,
        fetcher=base._acquire_fixed_rupture,
        converter=_native_convert,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--image-digest")
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.image_digest or not args.output:
        raise NativeRuptureGateError("image digest and output path are required")
    result = run_runtime(execution_sha=args.execution_sha, image_digest=args.image_digest)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
