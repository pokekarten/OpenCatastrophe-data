# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Trusted-main native OpenQuake 3.12.1 acceptance gate for the fixed Greece rupture.

This action is deliberately narrower than a scenario hazard run.  It verifies the
exact OpenQuake v3.12.1 source checkout before any provider access, reacquires only
the already-receipted 666-byte Greece rupture, rechecks the merged bounded child
shape precondition, and then asks the model-era native
``openquake.commonlib.readinput.get_rupture`` reader to convert those exact bytes.

A PASS proves native reader/converter acceptance for this one exact rupture object
only.  It does not establish event selection, site/GSIM compatibility, numerical
hazard agreement, loss, validation/holdout status, publication permission, or
model-use authority.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import inspect
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

try:
    from scripts import run_esrm20_scenario_v10_greece_rupture_child_diagnostic_action as child
    from scripts import run_esrm20_scenario_v10_greece_rupture_profile_action as base
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    import run_esrm20_scenario_v10_greece_rupture_child_diagnostic_action as child
    import run_esrm20_scenario_v10_greece_rupture_profile_action as base

REQUEST_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-openquake3121-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-scenario-v10-greece-rupture-openquake3121-runtime-result-v1 -->"
REQUEST_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-openquake3121-runtime-request-v1"
RESULT_SCHEMA_VERSION = "oc-esrm20-scenario-v10-greece-rupture-openquake3121-runtime-result-v1"
ACTION = "esrm20_scenario_v10_greece_rupture_openquake3121_runtime"
TRUSTED_RESULT_LOGIN = "github-actions[bot]"
MAX_REQUEST_UTF8_BYTES = 4096
MAX_TERMINAL_UTF8_BYTES = 7000
MAX_LEDGER_PAGES = 20

_SOURCE_ISSUE = 285
_DATASET_ID = "efehr.esrm20.scenario-tests.v1.0"
_RECEIPT_BYTE_COUNT = 666
_RECEIPT_SHA256 = "bb2715a8ca2233dd27a77dbccf789ab023b742048805ce53df6dd2532a1b073b"
_OPENQUAKE_REPOSITORY = "gem/oq-engine"
_OPENQUAKE_TAG = "v3.12.1"
_OPENQUAKE_COMMIT = "0bb8441aa202cd6ec075bf2044dd4aaeb26919b9"
_OPENQUAKE_PARSER_PATH = "openquake.commonlib.readinput.get_rupture"
_OPENQUAKE_ROOT = Path("/oq-engine")
_OPENQUAKE_PACKAGE_ROOT = _OPENQUAKE_ROOT / "openquake"

# Upstream v3.12.1 RuptureConverterTestCase uses 1.5 km for its well-formed
# rupture conversion fixtures.  For singlePlaneRupture the converter constructs
# PlanarSurface directly, so this is an API/regression fixture only, not an EQ1
# scientific parameter conclusion.  ses_seed is used by get_rupture only to set
# rup_id; it is likewise a fixed API fixture, not scenario/RNG authority.
_API_RUPTURE_MESH_SPACING_KM = 1.5
_API_SES_SEED = 1

_EXPECTED_SHAPE = {
    "root_class": "nrml_root_legacy_04",
    "child_class": "single_plane_rupture",
    "child_namespace_class": "legacy_04_namespace",
    "required_structure_class": "oq3121_required_direct_children_present",
}
_OPENQUAKE_REFERENCE = {
    "repository": _OPENQUAKE_REPOSITORY,
    "tag": _OPENQUAKE_TAG,
    "commit": _OPENQUAKE_COMMIT,
    "parser_path": _OPENQUAKE_PARSER_PATH,
}

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
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
    "rupture_identity",
    "openquake_reference",
    "execution_container_image_digest",
    "status",
    "failure_stage",
    "failure_code",
    "runtime_source_commit_verified",
    "provider_file_bytes_read",
    "byte_identity_verified",
    "trusted_shape_precondition_verified",
    "native_conversion_attempted",
    "legacy_nrml_04_native_acceptance_verified",
    "single_plane_native_conversion_verified",
    "readinput_postconditions_verified",
    "rupture_class",
    "surface_class",
    "output_payload_bytes_read",
    "external_bytes_persisted",
    "historical_environment_verified",
    "event_location_inference_authorized",
    "scenario_selection_authorized",
    "site_model_compatibility_verified",
    "gsim_compatibility_verified",
    "numerical_hazard_agreement_verified",
    "vulnerability_compatibility_verified",
    "reference_run_verified",
    "scientific_validity_verified",
    "independent_validation_established",
    "holdout_status_established",
    "publication_authorized",
    "model_use_authorized",
}
_FAILURES = {
    "runtime_identity": "runtime_identity_rejected",
    "acquisition": "acquisition_failed",
    "byte_identity": "byte_identity_mismatch",
    "shape_precondition": "shape_precondition_rejected",
    "native_conversion": "native_conversion_rejected",
}


class GreeceRuptureOpenQuake3121RuntimeError(RuntimeError):
    """The native-runtime request, execution, or evidence contract drifted."""


class NativeConversionRejected(RuntimeError):
    """The exact bytes were not accepted under the bounded native contract."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GreeceRuptureOpenQuake3121RuntimeError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise GreeceRuptureOpenQuake3121RuntimeError(
        f"non-finite JSON constant: {value}"
    )


def _strict_loads(text: str, *, label: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except GreeceRuptureOpenQuake3121RuntimeError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            f"invalid {label} JSON"
        ) from exc


def _utf8_size(value: str) -> int:
    try:
        return len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "text is not UTF-8 encodable"
        ) from exc


def _require_authority() -> None:
    base._require_canonical_authority()
    child._require_authority()
    exact = (
        (base.SOURCE_ISSUE, _SOURCE_ISSUE, "source issue"),
        (base.DATASET_ID, _DATASET_ID, "dataset id"),
        (base.EXPECTED_BYTE_COUNT, _RECEIPT_BYTE_COUNT, "receipt byte count"),
        (base.EXPECTED_SHA256, _RECEIPT_SHA256, "receipt sha256"),
        (child._RECEIPT_BYTE_COUNT, _RECEIPT_BYTE_COUNT, "child receipt byte count"),
        (child._RECEIPT_SHA256, _RECEIPT_SHA256, "child receipt sha256"),
    )
    for observed, expected, label in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceRuptureOpenQuake3121RuntimeError(
                f"native runtime {label} drifted"
            )


def validate_request(
    body: object,
    *,
    expected_issue: int,
    execution_sha: str,
) -> dict[str, Any]:
    _require_authority()
    if type(expected_issue) is not int or expected_issue != _SOURCE_ISSUE:
        raise GreeceRuptureOpenQuake3121RuntimeError("wrong issue")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid execution SHA")
    if (
        type(body) is not str
        or _utf8_size(body) > MAX_REQUEST_UTF8_BYTES
        or body.count(REQUEST_MARKER) != 1
    ):
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid request envelope")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "non-canonical request envelope"
        )
    request = _strict_loads(after.strip(), label="request")
    if type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise GreeceRuptureOpenQuake3121RuntimeError("request fields drifted")
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
            raise GreeceRuptureOpenQuake3121RuntimeError(
                f"request {field} drifted"
            )
    requester = request["requester"]
    if (
        type(requester) is not str
        or requester != requester.strip()
        or _REQUESTER_RE.fullmatch(requester) is None
    ):
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid requester")
    return request


def _base_result(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "action": ACTION,
        "source_issue": _SOURCE_ISSUE,
        "dataset_id": _DATASET_ID,
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "rupture_identity": base._identity(),
        "openquake_reference": dict(_OPENQUAKE_REFERENCE),
        "execution_container_image_digest": image_digest,
        "status": "blocked",
        "failure_stage": "runtime_identity",
        "failure_code": _FAILURES["runtime_identity"],
        "runtime_source_commit_verified": False,
        "provider_file_bytes_read": False,
        "byte_identity_verified": False,
        "trusted_shape_precondition_verified": False,
        "native_conversion_attempted": False,
        "legacy_nrml_04_native_acceptance_verified": False,
        "single_plane_native_conversion_verified": False,
        "readinput_postconditions_verified": False,
        "rupture_class": None,
        "surface_class": None,
        "output_payload_bytes_read": False,
        "external_bytes_persisted": False,
        "historical_environment_verified": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "site_model_compatibility_verified": False,
        "gsim_compatibility_verified": False,
        "numerical_hazard_agreement_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _validate_terminal_result(result: object) -> str:
    _require_authority()
    if type(result) is not dict or set(result) != _RESULT_FIELDS:
        raise GreeceRuptureOpenQuake3121RuntimeError("result fields drifted")
    execution_sha = result.get("execution_sha")
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid result SHA")
    image_digest = result.get("execution_container_image_digest")
    if type(image_digest) is not str or _DIGEST_RE.fullmatch(image_digest) is None:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid image digest")
    exact = (
        ("schema_version", RESULT_SCHEMA_VERSION),
        ("action", ACTION),
        ("source_issue", _SOURCE_ISSUE),
        ("dataset_id", _DATASET_ID),
        ("target_sha", execution_sha),
        ("rupture_identity", base._identity()),
        ("openquake_reference", _OPENQUAKE_REFERENCE),
        ("output_payload_bytes_read", False),
        ("external_bytes_persisted", False),
        ("historical_environment_verified", False),
        ("event_location_inference_authorized", False),
        ("scenario_selection_authorized", False),
        ("site_model_compatibility_verified", False),
        ("gsim_compatibility_verified", False),
        ("numerical_hazard_agreement_verified", False),
        ("vulnerability_compatibility_verified", False),
        ("reference_run_verified", False),
        ("scientific_validity_verified", False),
        ("independent_validation_established", False),
        ("holdout_status_established", False),
        ("publication_authorized", False),
        ("model_use_authorized", False),
    )
    for field, expected in exact:
        observed = result.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise GreeceRuptureOpenQuake3121RuntimeError(
                f"result {field} drifted"
            )

    bool_fields = (
        "runtime_source_commit_verified",
        "provider_file_bytes_read",
        "byte_identity_verified",
        "trusted_shape_precondition_verified",
        "native_conversion_attempted",
        "legacy_nrml_04_native_acceptance_verified",
        "single_plane_native_conversion_verified",
        "readinput_postconditions_verified",
    )
    if any(type(result.get(field)) is not bool for field in bool_fields):
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "runtime result boolean evidence drifted"
        )

    status = result.get("status")
    stage = result.get("failure_stage")
    code = result.get("failure_code")
    rupture_class = result.get("rupture_class")
    surface_class = result.get("surface_class")
    if status == "pass":
        if (
            stage is not None
            or code is not None
            or result["runtime_source_commit_verified"] is not True
            or result["provider_file_bytes_read"] is not True
            or result["byte_identity_verified"] is not True
            or result["trusted_shape_precondition_verified"] is not True
            or result["native_conversion_attempted"] is not True
            or result["legacy_nrml_04_native_acceptance_verified"] is not True
            or result["single_plane_native_conversion_verified"] is not True
            or result["readinput_postconditions_verified"] is not True
            or rupture_class != "BaseRupture"
            or surface_class != "PlanarSurface"
        ):
            raise GreeceRuptureOpenQuake3121RuntimeError("invalid PASS state")
    elif status == "blocked":
        if stage not in _FAILURES or code != _FAILURES[stage]:
            raise GreeceRuptureOpenQuake3121RuntimeError(
                "invalid blocked failure state"
            )
        expected = {
            "runtime_identity": (False, False, False, False, False),
            "acquisition": (True, False, False, False, False),
            "byte_identity": (True, True, False, False, False),
            "shape_precondition": (True, True, True, False, False),
            "native_conversion": (True, True, True, True, True),
        }[stage]
        observed = (
            result["runtime_source_commit_verified"],
            result["provider_file_bytes_read"],
            result["byte_identity_verified"],
            result["trusted_shape_precondition_verified"],
            result["native_conversion_attempted"],
        )
        if observed != expected:
            raise GreeceRuptureOpenQuake3121RuntimeError(
                "blocked stage evidence drifted"
            )
        if (
            result["legacy_nrml_04_native_acceptance_verified"] is not False
            or result["single_plane_native_conversion_verified"] is not False
            or result["readinput_postconditions_verified"] is not False
            or rupture_class is not None
            or surface_class is not None
        ):
            raise GreeceRuptureOpenQuake3121RuntimeError(
                "blocked result widened native evidence"
            )
    else:
        raise GreeceRuptureOpenQuake3121RuntimeError("non-terminal status")
    return execution_sha


def parse_terminal_result(body: object) -> str | None:
    if type(body) is not str or RESULT_MARKER not in body:
        return None
    if _utf8_size(body) > MAX_TERMINAL_UTF8_BYTES or body.count(RESULT_MARKER) != 1:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid result envelope")
    before, after = body.split(RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "non-canonical result envelope"
        )
    result = _strict_loads(after.strip(), label="result")
    return _validate_terminal_result(result)


def has_terminal_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
) -> bool:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid execution SHA")
    kwargs: dict[str, Any] = {"issue": _SOURCE_ISSUE, "max_pages": MAX_LEDGER_PAGES}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = base.fetch_repository_comments(repository, token, **kwargs)
    except base.LedgerError as exc:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "runtime result ledger is incomplete"
        ) from exc
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


def _require_source_path(source_file: str | Path, *, package_root: Path) -> Path:
    source_path = Path(source_file).resolve()
    expected_root = package_root.resolve()
    try:
        source_path.relative_to(expected_root)
    except ValueError as exc:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "OpenQuake reader resolved outside exact checkout"
        ) from exc
    if not source_path.is_file():
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "OpenQuake reader source identity unavailable"
        )
    return source_path


def verify_runtime_source_identity(
    *,
    checkout_root: Path = _OPENQUAKE_ROOT,
) -> None:
    """Prove the executing native reader comes from the exact v3.12.1 checkout."""
    root = checkout_root.resolve()
    package_root = root / "openquake"
    if not package_root.is_dir():
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "exact OpenQuake package root unavailable"
        )
    try:
        observed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "OpenQuake source commit observation failed"
        ) from None
    if observed != _OPENQUAKE_COMMIT:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "OpenQuake source commit drifted"
        )
    try:
        from openquake.commonlib import readinput
    except Exception:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "OpenQuake 3.12.1 readinput unavailable"
        ) from None
    source_file = inspect.getsourcefile(readinput.get_rupture)
    if source_file is None:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "OpenQuake reader source identity unavailable"
        )
    _require_source_path(source_file, package_root=package_root)


def validate_fixed_bytes(data: bytes) -> None:
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    if len(data) != _RECEIPT_BYTE_COUNT:
        raise base.RuptureByteIdentityError("byte_count_mismatch")
    if hashlib.sha256(data).hexdigest() != _RECEIPT_SHA256:
        raise base.RuptureByteIdentityError("sha256_mismatch")


def _validate_shape(shape: object) -> None:
    if type(shape) is not dict or set(shape) != set(_EXPECTED_SHAPE):
        raise NativeConversionRejected("shape_precondition_rejected")
    for field, expected in _EXPECTED_SHAPE.items():
        observed = shape.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise NativeConversionRejected("shape_precondition_rejected")


def _native_convert_unbound(
    data: bytes,
    *,
    get_rupture: Callable[[Any], Any],
) -> dict[str, str]:
    """Exercise the native API over already-bound bytes without serializing values."""
    if type(data) is not bytes:
        raise TypeError("data must be bytes")
    try:
        with tempfile.TemporaryDirectory(prefix="oc-oq3121-rupture-") as directory:
            rupture_path = Path(directory) / "rupture.xml"
            rupture_path.write_bytes(data)
            oqparam = SimpleNamespace(
                inputs={"rupture_model": str(rupture_path)},
                rupture_mesh_spacing=_API_RUPTURE_MESH_SPACING_KM,
                ses_seed=_API_SES_SEED,
            )
            rupture = get_rupture(oqparam)
    except Exception:
        raise NativeConversionRejected("native_conversion_rejected") from None

    rupture_class = type(rupture).__name__
    surface = getattr(rupture, "surface", None)
    surface_class = type(surface).__name__ if surface is not None else None
    if (
        rupture_class != "BaseRupture"
        or surface_class != "PlanarSurface"
        or getattr(rupture, "tectonic_region_type", None) != "*"
        or getattr(rupture, "rup_id", None) != _API_SES_SEED
    ):
        raise NativeConversionRejected("native_conversion_rejected")
    return {
        "rupture_class": rupture_class,
        "surface_class": surface_class,
    }


def native_convert_fixed_bytes(data: bytes) -> dict[str, str]:
    """Run exact OQ v3.12.1 readinput.get_rupture over the fixed receipted bytes."""
    validate_fixed_bytes(data)
    try:
        from openquake.commonlib import readinput
    except Exception:
        raise NativeConversionRejected("native_conversion_rejected") from None
    source_file = inspect.getsourcefile(readinput.get_rupture)
    if source_file is None:
        raise NativeConversionRejected("native_conversion_rejected")
    try:
        _require_source_path(source_file, package_root=_OPENQUAKE_PACKAGE_ROOT)
    except GreeceRuptureOpenQuake3121RuntimeError:
        raise NativeConversionRejected("native_conversion_rejected") from None
    return _native_convert_unbound(data, get_rupture=readinput.get_rupture)


def _run_native_with(
    *,
    execution_sha: str,
    image_digest: str,
    runtime_verifier: Callable[[], None],
    fetcher: Callable[[], tuple[bytes, dict[str, Any]]],
    identity_checker: Callable[[bytes], None],
    shape_checker: Callable[[bytes], dict[str, Any]],
    converter: Callable[[bytes], dict[str, str]],
) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA1_RE.fullmatch(execution_sha) is None:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid execution SHA")
    if type(image_digest) is not str or _DIGEST_RE.fullmatch(image_digest) is None:
        raise GreeceRuptureOpenQuake3121RuntimeError("invalid image digest")
    _require_authority()
    result = _base_result(execution_sha=execution_sha, image_digest=image_digest)

    try:
        runtime_verifier()
    except GreeceRuptureOpenQuake3121RuntimeError:
        _validate_terminal_result(result)
        return result
    result["runtime_source_commit_verified"] = True
    result.update(
        {
            "failure_stage": "acquisition",
            "failure_code": _FAILURES["acquisition"],
        }
    )

    try:
        raw, receipt = fetcher()
    except base.RuptureByteIdentityError:
        result.update(
            {
                "failure_stage": "byte_identity",
                "failure_code": _FAILURES["byte_identity"],
                "provider_file_bytes_read": True,
            }
        )
        _validate_terminal_result(result)
        return result
    except (base.EfehrAcquisitionError, http.client.HTTPException):
        _validate_terminal_result(result)
        return result

    base._validate_receipt(receipt)
    result["provider_file_bytes_read"] = True
    try:
        identity_checker(raw)
    except base.RuptureByteIdentityError:
        result.update(
            {
                "failure_stage": "byte_identity",
                "failure_code": _FAILURES["byte_identity"],
            }
        )
        _validate_terminal_result(result)
        return result
    result["byte_identity_verified"] = True
    result.update(
        {
            "failure_stage": "shape_precondition",
            "failure_code": _FAILURES["shape_precondition"],
        }
    )

    try:
        shape = shape_checker(raw)
        _validate_shape(shape)
    except (child.ChildShapeParseError, base.RuptureByteIdentityError, NativeConversionRejected):
        _validate_terminal_result(result)
        return result
    result["trusted_shape_precondition_verified"] = True
    result.update(
        {
            "failure_stage": "native_conversion",
            "failure_code": _FAILURES["native_conversion"],
            "native_conversion_attempted": True,
        }
    )

    try:
        native = converter(raw)
    except (NativeConversionRejected, base.RuptureByteIdentityError):
        _validate_terminal_result(result)
        return result
    if type(native) is not dict or set(native) != {"rupture_class", "surface_class"}:
        raise GreeceRuptureOpenQuake3121RuntimeError(
            "native converter returned invalid fields"
        )
    if native != {"rupture_class": "BaseRupture", "surface_class": "PlanarSurface"}:
        _validate_terminal_result(result)
        return result

    result.update(
        {
            "status": "pass",
            "failure_stage": None,
            "failure_code": None,
            "legacy_nrml_04_native_acceptance_verified": True,
            "single_plane_native_conversion_verified": True,
            "readinput_postconditions_verified": True,
            **native,
        }
    )
    _validate_terminal_result(result)
    return result


def run_native_acceptance(
    *,
    execution_sha: str,
    image_digest: str,
) -> dict[str, Any]:
    return _run_native_with(
        execution_sha=execution_sha,
        image_digest=image_digest,
        runtime_verifier=verify_runtime_source_identity,
        fetcher=base._acquire_fixed_rupture,
        identity_checker=validate_fixed_bytes,
        shape_checker=child.classify_fixed_child_shape,
        converter=native_convert_fixed_bytes,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--image-digest")
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
    if not args.image_digest or not args.output:
        parser.error("--image-digest and --output are required for execution")

    result = run_native_acceptance(
        execution_sha=args.execution_sha,
        image_digest=args.image_digest,
    )
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
