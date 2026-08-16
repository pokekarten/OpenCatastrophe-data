# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Adapt the reviewed ESHM20 OpenQuake-3.14 GSIM runtime gate to exact ESRM20 bytes.

The module intentionally reuses the existing acquisition, request-token parser,
OpenQuake source verification, alias/registry/constructor and reconstructed
runtime-recipe machinery. Only immutable ESRM20 source identities and outer
request/result identities are rebound here. After the reviewed gate succeeds,
site-parameter names are read from the already-resolved OpenQuake classes.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from scripts import acquire_eshm20_gsim_resource_profile as _gmm
from scripts import profile_eshm20_gsim_identities as _profiler

SCHEMA_VERSION = "oc-esrm20-gsim-reference-runtime-result-v1"
REQUEST_SCHEMA_VERSION = "oc-esrm20-gsim-reference-runtime-request-v1"
REQUEST_MARKER = "<!-- oc-eq1-esrm20-gsim-reference-runtime-request-v1 -->"
RESULT_MARKER = "<!-- oc-eq1-esrm20-gsim-reference-runtime-result-v1 -->"
SOURCE_ISSUE = 493
HANDOFF_ISSUE = 281
DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
PROJECT_ID = 269
PROJECT_PATH = "efehr/esrm20"
COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
REPOSITORY_PATH = "Hazard/gmpe_logic_tree_5br_slope_geology.xml"
EXPECTED_BYTE_COUNT = 34_018
EXPECTED_SHA256 = "f3efd16d56189c7804824d94b20ed75d6ceefc879144d8bd697c1f9b47cf17b4"
EXPECTED_BRANCH_SET_COUNT = 6
EXPECTED_BRANCH_COUNT = 80
EXPECTED_REQUESTED_TOKENS = (
    "BCHydroESHM20SInter",
    "BCHydroESHM20SSlab",
    "ESHM20Craton",
    "KothaEtAl2020ESHM20SlopeGeology",
    "LanzanoLuzi2019shallow",
)
CANONICAL_PROFILE_RESULT_COMMENT_ID = 5310201828
CANONICAL_RECEIPT_RESULT_COMMENT_ID = 5310057117
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
_SAFE_CLASS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_SAFE_PARAMETER_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")

# Bind immutable ESRM20 source identity before importing the reviewed runtime
# modules, whose constants are intentionally read from these provider modules.
_gmm.SOURCE_ISSUE = HANDOFF_ISSUE
_gmm.CONTROL_ISSUE = SOURCE_ISSUE
_gmm.DATASET_ID = DATASET_ID
_gmm.PROJECT_ID = PROJECT_ID
_gmm.PROJECT_PATH = PROJECT_PATH
_gmm.COMMIT_SHA = COMMIT_SHA
_gmm.REPOSITORY_PATH = REPOSITORY_PATH
_gmm.EXPECTED_BYTE_COUNT = EXPECTED_BYTE_COUNT
_gmm.EXPECTED_SHA256 = EXPECTED_SHA256

_profiler.SOURCE_ISSUE = HANDOFF_ISSUE
_profiler.CONTROL_ISSUE = SOURCE_ISSUE
_profiler.DATASET_ID = DATASET_ID
_profiler.PROJECT_ID = PROJECT_ID
_profiler.PROJECT_PATH = PROJECT_PATH
_profiler.COMMIT_SHA = COMMIT_SHA
_profiler.REPOSITORY_PATH = REPOSITORY_PATH
_profiler.EXPECTED_BYTE_COUNT = EXPECTED_BYTE_COUNT
_profiler.EXPECTED_SHA256 = EXPECTED_SHA256
_profiler.EXPECTED_BRANCH_SET_COUNT = EXPECTED_BRANCH_SET_COUNT
_profiler.EXPECTED_BRANCH_COUNT = EXPECTED_BRANCH_COUNT
_profiler.RECEIPT_RESULT_COMMENT_ID = CANONICAL_RECEIPT_RESULT_COMMENT_ID

from scripts import validate_eshm20_gsim_openquake_runtime as _gate  # noqa: E402

_gate.SOURCE_ISSUE = SOURCE_ISSUE
_gate.HANDOFF_ISSUE = HANDOFF_ISSUE
_gate.DATASET_ID = DATASET_ID

from scripts import run_eshm20_gsim_reference_runtime as _runtime  # noqa: E402

_runtime.SCHEMA_VERSION = SCHEMA_VERSION
_runtime.REQUEST_SCHEMA_VERSION = REQUEST_SCHEMA_VERSION
_runtime.REQUEST_MARKER = REQUEST_MARKER
_runtime.RESULT_MARKER = RESULT_MARKER
_runtime.SOURCE_ISSUE = SOURCE_ISSUE
_BASE_RUN_REFERENCE_RUNTIME = _runtime.run_reference_runtime


class Esrm20GsimReferenceRuntimeError(RuntimeError):
    """Raised when the narrow ESRM20 adapter or site-requirement evidence drifts."""


def assert_esrm20_binding() -> None:
    exact = (
        (_gmm.DATASET_ID, DATASET_ID),
        (_gmm.PROJECT_ID, PROJECT_ID),
        (_gmm.COMMIT_SHA, COMMIT_SHA),
        (_gmm.REPOSITORY_PATH, REPOSITORY_PATH),
        (_gmm.EXPECTED_BYTE_COUNT, EXPECTED_BYTE_COUNT),
        (_gmm.EXPECTED_SHA256, EXPECTED_SHA256),
        (_profiler.EXPECTED_BRANCH_SET_COUNT, EXPECTED_BRANCH_SET_COUNT),
        (_profiler.EXPECTED_BRANCH_COUNT, EXPECTED_BRANCH_COUNT),
        (_runtime.SOURCE_ISSUE, SOURCE_ISSUE),
        (_runtime.REQUEST_MARKER, REQUEST_MARKER),
        (_runtime.RESULT_MARKER, RESULT_MARKER),
        (_gate.OPENQUAKE_COMMIT, OPENQUAKE_COMMIT),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20GsimReferenceRuntimeError("ESRM20 runtime adapter identity drifted")


def _site_parameter_evidence(
    runtime_result: Mapping[str, Any], registry: Mapping[str, Any]
) -> dict[str, Any]:
    """Derive only public class-level site parameter names from verified classes."""
    classes = runtime_result.get("unique_resolved_gsim_classes")
    branches = runtime_result.get("branches")
    if (
        type(classes) is not list
        or not classes
        or classes != sorted(set(classes))
        or type(branches) is not list
        or len(branches) != EXPECTED_BRANCH_COUNT
    ):
        raise Esrm20GsimReferenceRuntimeError("verified runtime class inventory is invalid")

    requested = sorted({branch.get("requested_gsim_token") for branch in branches})
    if requested != list(EXPECTED_REQUESTED_TOKENS):
        raise Esrm20GsimReferenceRuntimeError("verified ESRM20 requested-token set drifted")
    if any(branch.get("argument_keys") != [] for branch in branches):
        raise Esrm20GsimReferenceRuntimeError("ESRM20 source unexpectedly requires GSIM arguments")
    if any(branch.get("runtime_argument_keys_after_alias") != [] for branch in branches):
        raise Esrm20GsimReferenceRuntimeError(
            "ESRM20 alias expansion unexpectedly introduced GSIM arguments"
        )

    rows: list[dict[str, Any]] = []
    union: set[str] = set()
    for class_name in classes:
        if type(class_name) is not str or _SAFE_CLASS_RE.fullmatch(class_name) is None:
            raise Esrm20GsimReferenceRuntimeError("resolved GSIM class name is invalid")
        gsim_class = registry.get(class_name)
        if gsim_class is None:
            raise Esrm20GsimReferenceRuntimeError("resolved GSIM class is absent from verified registry")
        raw = getattr(gsim_class, "REQUIRES_SITES_PARAMETERS", None)
        if not isinstance(raw, (set, frozenset)):
            raise Esrm20GsimReferenceRuntimeError(
                "resolved GSIM class has invalid REQUIRES_SITES_PARAMETERS"
            )
        parameters = sorted(raw)
        if any(
            type(parameter) is not str
            or _SAFE_PARAMETER_RE.fullmatch(parameter) is None
            for parameter in parameters
        ):
            raise Esrm20GsimReferenceRuntimeError("resolved GSIM site parameter is invalid")
        union.update(parameters)
        rows.append({"resolved_gsim_class": class_name, "site_parameters": parameters})

    return {
        "per_resolved_gsim_class": rows,
        "required_site_parameters": sorted(union),
        "source": "OpenQuake-3.14-verified-class.REQUIRES_SITES_PARAMETERS",
    }


def run_reference_runtime(*, execution_sha: str, image_digest: str) -> dict[str, Any]:
    """Run the reviewed runtime gate and append bounded site-requirement evidence."""
    assert_esrm20_binding()
    result = _BASE_RUN_REFERENCE_RUNTIME(
        execution_sha=execution_sha,
        image_digest=image_digest,
    )
    identity = result.get("gmm_identity")
    if identity != {
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": EXPECTED_BYTE_COUNT,
        "sha256": EXPECTED_SHA256,
    }:
        raise Esrm20GsimReferenceRuntimeError("runtime result is not bound to canonical ESRM20 GSIM bytes")
    if result.get("branch_count") != EXPECTED_BRANCH_COUNT:
        raise Esrm20GsimReferenceRuntimeError("runtime result branch count drifted")
    if result.get("openquake_reference", {}).get("commit") != OPENQUAKE_COMMIT:
        raise Esrm20GsimReferenceRuntimeError("runtime result OpenQuake commit drifted")

    verified_runtime = _gate._load_verified_openquake_runtime()
    evidence = _site_parameter_evidence(result, verified_runtime.registry)
    result = dict(result)
    result["schema_version"] = SCHEMA_VERSION
    result["source_issue"] = SOURCE_ISSUE
    result["source_profile_result_comment_id"] = CANONICAL_PROFILE_RESULT_COMMENT_ID
    result["source_receipt_result_comment_id"] = CANONICAL_RECEIPT_RESULT_COMMENT_ID
    result["requested_gsim_tokens"] = list(EXPECTED_REQUESTED_TOKENS)
    result["site_parameter_requirements"] = evidence
    result["site_parameter_requirements_derived"] = True
    result["site_model_compatibility_verified"] = False
    result["imt_component_unit_compatibility_verified"] = False
    result["numerical_hazard_agreement_verified"] = False
    result["full_hazard_compatibility_verified"] = False
    result["model_use_authorized"] = False
    return result


validate_request = _runtime.validate_request
has_terminal_runtime_result = _runtime.has_terminal_runtime_result
collect_runtime_observation = _runtime.collect_runtime_observation


def main(argv: list[str] | None = None) -> int:
    # Reuse reviewed argument/request plumbing while routing only the execution
    # callable through the ESRM20 source-identity/site-requirement wrapper.
    original = _runtime.run_reference_runtime
    try:
        _runtime.run_reference_runtime = run_reference_runtime
        return _runtime.main(argv)
    finally:
        _runtime.run_reference_runtime = original


assert_esrm20_binding()

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
