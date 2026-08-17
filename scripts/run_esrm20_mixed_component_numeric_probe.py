# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Run one RotD50 and one geometric-mean ESRM20 GSIM numerically in OQ 3.14.

This is a bounded mechanics probe, not a historical hazard comparison. It proves
that two exact provider-native branches numerically execute without activating
the known OpenQuake component-conversion wrapper/request. Stronger compatibility
and scientific-validity claims deliberately remain false.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

from scripts import profile_eshm20_gsim_identities as _profiler
from scripts import run_eshm20_gsim_reference_runtime as _base_runtime
from scripts import run_esrm20_gsim_reference_runtime as _esrm
from scripts import validate_eshm20_gsim_openquake_runtime as _gate

SCHEMA_VERSION = "oc-esrm20-mixed-component-numeric-probe-result-v1"
REQUEST_SCHEMA_VERSION = "oc-esrm20-mixed-component-numeric-probe-request-v1"
REQUEST_MARKER = "<!-- oc-eq1-esrm20-mixed-component-numeric-probe-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-mixed-component-numeric-probe-result-v1 -->"
SOURCE_ISSUE = 287
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SYNTHETIC_CONTEXT = {"mag": 4.5, "vs30": 760.0, "rrup_km": 20.0, "rhypo_km": 20.0}
SELECTED_BRANCHES = (
    {
        "branch_set_id": "CratonModel",
        "branch_id": "CRParamMidMidSite",
        "requested_gsim_token": "ESHM20Craton",
        "native_component": "RotD50",
        "distance_field": "rrup",
    },
    {
        "branch_set_id": "Volcanic",
        "branch_id": "b61",
        "requested_gsim_token": "LanzanoLuzi2019shallow",
        "native_component": "GEOMETRIC_MEAN",
        "distance_field": "rhypo",
    },
)


class MixedComponentNumericProbeError(RuntimeError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise MixedComponentNumericProbeError("duplicate JSON key")
        out[key] = value
    return out


def _reject_constant(value: str) -> None:
    raise MixedComponentNumericProbeError(f"non-finite JSON constant: {value}")


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    if expected_issue != SOURCE_ISSUE:
        raise MixedComponentNumericProbeError("unexpected source issue")
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise MixedComponentNumericProbeError("invalid execution SHA")
    if type(body) is not str or body.count(REQUEST_MARKER) != 1:
        raise MixedComponentNumericProbeError("request marker is missing or duplicated")
    before, after = body.split(REQUEST_MARKER, 1)
    if before.strip() or not after.strip():
        raise MixedComponentNumericProbeError("request envelope is malformed")
    try:
        request = json.loads(after.strip(), object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise MixedComponentNumericProbeError("request JSON is malformed") from exc
    if type(request) is not dict or set(request) != {"schema_version", "issue", "target_sha", "requester"}:
        raise MixedComponentNumericProbeError("request fields drifted")
    if request.get("schema_version") != REQUEST_SCHEMA_VERSION:
        raise MixedComponentNumericProbeError("request schema drifted")
    if type(request.get("issue")) is not int or request["issue"] != SOURCE_ISSUE:
        raise MixedComponentNumericProbeError("request issue drifted")
    if request.get("target_sha") != execution_sha:
        raise MixedComponentNumericProbeError("request target SHA drifted")
    if type(request.get("requester")) is not str or not request["requester"] or len(request["requester"]) > 128:
        raise MixedComponentNumericProbeError("requester is invalid")
    return request


def _finite(value: object, *, field: str) -> float:
    if type(value) is bool:
        raise MixedComponentNumericProbeError(f"{field} is not numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MixedComponentNumericProbeError(f"{field} is not numeric") from exc
    if not math.isfinite(result):
        raise MixedComponentNumericProbeError(f"{field} is non-finite")
    return result


def _selected_record(profile: dict[str, Any], branch: dict[str, str]) -> None:
    rows = [
        row for row in profile.get("branches", [])
        if type(row) is dict
        and row.get("branch_set_id") == branch["branch_set_id"]
        and row.get("branch_id") == branch["branch_id"]
    ]
    if len(rows) != 1:
        raise MixedComponentNumericProbeError("selected branch identity is not unique")
    if rows[0].get("requested_gsim_token") != branch["requested_gsim_token"] or rows[0].get("argument_keys") != []:
        raise MixedComponentNumericProbeError("selected branch request contract drifted")


def _compute_row(adapter: Any, model: object, branch: dict[str, str]) -> dict[str, Any]:
    try:
        import numpy as np
        from openquake.hazardlib.imt import PGA
    except Exception as exc:
        raise MixedComponentNumericProbeError("OpenQuake numerical runtime is unavailable") from exc

    if adapter.argument_keys_after_alias(model) != []:
        raise MixedComponentNumericProbeError("selected branch gained post-alias arguments")
    try:
        instance = adapter.instantiate(model)
    except Exception as exc:
        raise MixedComponentNumericProbeError("selected branch construction failed") from exc
    class_name = type(instance).__name__
    if class_name != branch["requested_gsim_token"] or class_name == _esrm.COMPONENT_CONVERSION_WRAPPER:
        raise MixedComponentNumericProbeError("selected branch resolved through an unexpected class/wrapper")
    component = getattr(getattr(instance, "DEFINED_FOR_INTENSITY_MEASURE_COMPONENT", None), "name", None)
    if component != branch["native_component"]:
        raise MixedComponentNumericProbeError("selected branch native component drifted")

    ctx = np.zeros(1, dtype=[("mag", float), ("vs30", float), ("rrup", float), ("rhypo", float)]).view(np.recarray)
    ctx.mag[:] = SYNTHETIC_CONTEXT["mag"]
    ctx.vs30[:] = SYNTHETIC_CONTEXT["vs30"]
    ctx.rrup[:] = SYNTHETIC_CONTEXT["rrup_km"]
    ctx.rhypo[:] = SYNTHETIC_CONTEXT["rhypo_km"]
    mean = np.zeros((1, 1)); sig = np.zeros((1, 1)); tau = np.zeros((1, 1)); phi = np.zeros((1, 1))
    try:
        instance.compute(ctx, [PGA()], mean, sig, tau, phi)
    except Exception as exc:
        raise MixedComponentNumericProbeError("selected branch numerical evaluation failed") from exc

    mean_ln_g = _finite(mean[0, 0], field="mean_ln_g")
    values = {
        "pga_g": _finite(math.exp(mean_ln_g), field="pga_g"),
        "sigma_ln": _finite(sig[0, 0], field="sigma_ln"),
        "tau_ln": _finite(tau[0, 0], field="tau_ln"),
        "phi_ln": _finite(phi[0, 0], field="phi_ln"),
    }
    if values["pga_g"] <= 0 or min(values["sigma_ln"], values["tau_ln"], values["phi_ln"]) < 0:
        raise MixedComponentNumericProbeError("selected branch output is outside basic numeric domain")
    distance = branch["distance_field"]
    return {
        "branch_set_id": branch["branch_set_id"], "branch_id": branch["branch_id"],
        "requested_gsim_token": branch["requested_gsim_token"], "resolved_gsim_class": class_name,
        "native_component": component, "argument_keys": [], "runtime_argument_keys_after_alias": [],
        "component_conversion_request_absent": True, "component_conversion_activated": False, "imt": "PGA",
        "input": {"mag": SYNTHETIC_CONTEXT["mag"], "vs30_m_per_s": SYNTHETIC_CONTEXT["vs30"],
                  "distance_name": distance, "distance_km": SYNTHETIC_CONTEXT[f"{distance}_km"]},
        "mean_ln_g": mean_ln_g, **values, "finite_numeric_output": True,
    }


def run_probe(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    if type(execution_sha) is not str or _SHA_RE.fullmatch(execution_sha) is None:
        raise MixedComponentNumericProbeError("invalid execution SHA")
    try:
        digest = _esrm._validate_image_digest(image_digest)
    except _esrm.Esrm20GsimReferenceRuntimeError as exc:
        raise MixedComponentNumericProbeError("invalid runtime image digest") from exc
    payload = b""
    try:
        with _esrm.esrm20_binding():
            payload = _base_runtime._acquire_exact_gmm()
            _base_runtime._pin_openquake_namespace()
            adapter = _gate._load_verified_openquake_runtime()
            profile = _profiler.profile_verified_gsim_identities(payload)
            models = _gate._model_elements_by_branch(payload)
            rows = []
            for branch in SELECTED_BRANCHES:
                _selected_record(profile, branch)
                model = models.get((branch["branch_set_id"], branch["branch_id"]))
                if model is None:
                    raise MixedComponentNumericProbeError("selected branch model is absent")
                rows.append(_compute_row(adapter, model, branch))
    except MixedComponentNumericProbeError:
        raise
    except Exception as exc:
        raise MixedComponentNumericProbeError("mixed-component numerical probe failed closed") from exc
    finally:
        payload = b""
    if [row["native_component"] for row in rows] != ["RotD50", "GEOMETRIC_MEAN"]:
        raise MixedComponentNumericProbeError("mixed native component pair drifted")
    return {
        "schema_version": SCHEMA_VERSION, "source_issue": SOURCE_ISSUE, "status": "pass",
        "target_sha": execution_sha, "execution_sha": execution_sha, "execution_container_image_digest": digest,
        "openquake_reference": {"repository": _gate.OPENQUAKE_REPOSITORY, "tag": _gate.OPENQUAKE_TAG,
                                "commit": _esrm.OPENQUAKE_COMMIT, "version": _gate.OPENQUAKE_VERSION},
        "gmm_identity": {"project_id": _esrm.PROJECT_ID, "project_path": _esrm.PROJECT_PATH,
                         "commit_sha": _esrm.COMMIT_SHA, "repository_path": _esrm.REPOSITORY_PATH,
                         "byte_count": _esrm.EXPECTED_BYTE_COUNT, "sha256": _esrm.EXPECTED_SHA256},
        "synthetic_mechanics_probe": True, "synthetic_context": dict(SYNTHETIC_CONTEXT), "probes": rows,
        "native_components": ["GEOMETRIC_MEAN", "RotD50"],
        "mixed_native_component_numeric_execution_verified": True,
        "component_conversion_request_absent": True, "component_conversion_activated": False,
        "component_conversion_wrapper": _esrm.COMPONENT_CONVERSION_WRAPPER,
        "component_conversion_argument": _esrm.COMPONENT_CONVERSION_ARGUMENT,
        "reference_component_semantics": _esrm.REFERENCE_COMPONENT_SEMANTICS,
        "historical_environment_verified": False, "numerical_hazard_agreement_verified": False,
        "imt_component_unit_compatibility_verified": False, "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False, "vulnerability_compatibility_verified": False,
        "reference_run_verified": False, "scientific_validity_verified": False,
        "external_bytes_persisted": False, "publication_authorized": False, "model_use_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--runtime-image-digest-env")
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    validate_request(os.environ.get(args.comment_body_env), expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.runtime_image_digest_env or not args.output:
        raise MixedComponentNumericProbeError("runtime digest environment and output are required")
    result = run_probe(execution_sha=args.execution_sha, image_digest=os.environ.get(args.runtime_image_digest_env))
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
