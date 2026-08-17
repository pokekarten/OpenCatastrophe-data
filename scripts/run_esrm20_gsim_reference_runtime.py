# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Adapt the reviewed ESHM20 OpenQuake-3.14 GSIM runtime gate to exact ESRM20 bytes.

The module reuses the existing acquisition, GSIM request parser, OpenQuake
source verification, alias/registry/constructor and reconstructed runtime recipe.
Immutable ESRM20 identities are applied only inside a temporary execution
context and are restored afterwards so the existing ESHM20 path is untouched.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterator, Mapping

from scripts import acquire_eshm20_gsim_resource_profile as _gmm
from scripts import profile_eshm20_gsim_identities as _profiler
from scripts import run_eshm20_gsim_reference_runtime as _runtime
from scripts import validate_eshm20_gsim_openquake_runtime as _gate

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
# Trusted #481 PASS 5310194089 returned key names only, never argument values.
EXPECTED_SOURCE_ARGUMENT_KEYS = (
    "a",
    "b",
    "c3_epsilon",
    "epsilon",
    "faba_taper_model",
    "sigma_mu_epsilon",
    "site_epsilon",
    "theta_6_adjustment",
)
CANONICAL_PROFILE_RESULT_COMMENT_ID = 5310194089
# Trusted #476 request/result pair and successful main-only workflow execution.
CANONICAL_RECEIPT_REQUEST_COMMENT_ID = 5310055297
CANONICAL_RECEIPT_RESULT_COMMENT_ID = 5310057117
CANONICAL_RECEIPT_RUN_ID = 31977222858
CANONICAL_RECEIPT_EXECUTION_SHA = "ea6d723d7b4dc333a21c0d1015981b75c530cc9a"
CANONICAL_RECEIPT_RETRIEVED_AT = "2026-08-16T22:45:52Z"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
_SAFE_CLASS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
_SAFE_PARAMETER_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SAFE_ARGUMENT_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_EXTERNAL_RESOURCE_SUFFIXES = ("_file", "_table")

_BASE_RUN_REFERENCE_RUNTIME = _runtime.run_reference_runtime


class Esrm20GsimReferenceRuntimeError(RuntimeError):
    """Raised when the narrow ESRM20 adapter or site-requirement evidence drifts."""


def _bindings() -> tuple[tuple[Any, str, Any], ...]:
    return (
        (_gmm, "SOURCE_ISSUE", HANDOFF_ISSUE),
        (_gmm, "CONTROL_ISSUE", SOURCE_ISSUE),
        (_gmm, "DATASET_ID", DATASET_ID),
        (_gmm, "PROJECT_ID", PROJECT_ID),
        (_gmm, "PROJECT_PATH", PROJECT_PATH),
        (_gmm, "COMMIT_SHA", COMMIT_SHA),
        (_gmm, "REPOSITORY_PATH", REPOSITORY_PATH),
        (_gmm, "EXPECTED_BYTE_COUNT", EXPECTED_BYTE_COUNT),
        (_gmm, "EXPECTED_SHA256", EXPECTED_SHA256),
        (_profiler, "SOURCE_ISSUE", HANDOFF_ISSUE),
        (_profiler, "CONTROL_ISSUE", SOURCE_ISSUE),
        (_profiler, "DATASET_ID", DATASET_ID),
        (_profiler, "PROJECT_ID", PROJECT_ID),
        (_profiler, "PROJECT_PATH", PROJECT_PATH),
        (_profiler, "COMMIT_SHA", COMMIT_SHA),
        (_profiler, "REPOSITORY_PATH", REPOSITORY_PATH),
        (_profiler, "EXPECTED_BYTE_COUNT", EXPECTED_BYTE_COUNT),
        (_profiler, "EXPECTED_SHA256", EXPECTED_SHA256),
        (_profiler, "EXPECTED_BRANCH_SET_COUNT", EXPECTED_BRANCH_SET_COUNT),
        (_profiler, "EXPECTED_BRANCH_COUNT", EXPECTED_BRANCH_COUNT),
        (
            _profiler,
            "FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID",
            CANONICAL_RECEIPT_RESULT_COMMENT_ID,
        ),
        (_profiler, "FIRST_ORDER_RECEIPT_RUN_ID", CANONICAL_RECEIPT_RUN_ID),
        (
            _profiler,
            "FIRST_ORDER_RECEIPT_EXECUTION_SHA",
            CANONICAL_RECEIPT_EXECUTION_SHA,
        ),
        (_gate, "SOURCE_ISSUE", SOURCE_ISSUE),
        (_gate, "HANDOFF_ISSUE", HANDOFF_ISSUE),
        (_gate, "DATASET_ID", DATASET_ID),
        (_runtime, "SCHEMA_VERSION", SCHEMA_VERSION),
        (_runtime, "REQUEST_SCHEMA_VERSION", REQUEST_SCHEMA_VERSION),
        (_runtime, "REQUEST_MARKER", REQUEST_MARKER),
        (_runtime, "RESULT_MARKER", RESULT_MARKER),
        (_runtime, "SOURCE_ISSUE", SOURCE_ISSUE),
        (_runtime, "_PROJECT_ID", PROJECT_ID),
        (_runtime, "_PROJECT_PATH", PROJECT_PATH),
        (_runtime, "_COMMIT_SHA", COMMIT_SHA),
        (_runtime, "_REPOSITORY_PATH", REPOSITORY_PATH),
        (_runtime, "_EXPECTED_BYTES", EXPECTED_BYTE_COUNT),
        (_runtime, "_EXPECTED_SHA256", EXPECTED_SHA256),
    )


@contextlib.contextmanager
def esrm20_binding() -> Iterator[None]:
    """Temporarily bind reviewed generic/ESHM20 modules to exact ESRM20 identity."""
    bindings = _bindings()
    missing = [name for module, name, _ in bindings if not hasattr(module, name)]
    if missing:
        raise Esrm20GsimReferenceRuntimeError(
            "ESRM20 runtime adapter binding surface drifted: " + ", ".join(missing)
        )
    original: list[tuple[Any, str, Any]] = []
    for module, name, value in bindings:
        original.append((module, name, getattr(module, name)))
        setattr(module, name, value)
    try:
        assert_esrm20_binding()
        yield
    finally:
        for module, name, value in reversed(original):
            setattr(module, name, value)


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
        (
            _profiler.FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
            CANONICAL_RECEIPT_RESULT_COMMENT_ID,
        ),
        (_profiler.FIRST_ORDER_RECEIPT_RUN_ID, CANONICAL_RECEIPT_RUN_ID),
        (
            _profiler.FIRST_ORDER_RECEIPT_EXECUTION_SHA,
            CANONICAL_RECEIPT_EXECUTION_SHA,
        ),
        (_runtime.SOURCE_ISSUE, SOURCE_ISSUE),
        (_runtime._PROJECT_ID, PROJECT_ID),
        (_runtime._EXPECTED_BYTES, EXPECTED_BYTE_COUNT),
        (_runtime._EXPECTED_SHA256, EXPECTED_SHA256),
        (_runtime.REQUEST_MARKER, REQUEST_MARKER),
        (_runtime.RESULT_MARKER, RESULT_MARKER),
        (_gate.OPENQUAKE_COMMIT, OPENQUAKE_COMMIT),
    )
    for observed, expected in exact:
        if type(observed) is not type(expected) or observed != expected:
            raise Esrm20GsimReferenceRuntimeError("ESRM20 runtime adapter identity drifted")


def _argument_keys(value: object, *, field: str) -> list[str]:
    if type(value) is not list or value != sorted(set(value)):
        raise Esrm20GsimReferenceRuntimeError(f"{field} are not a canonical key list")
    for key in value:
        if type(key) is not str or _SAFE_ARGUMENT_RE.fullmatch(key) is None:
            raise Esrm20GsimReferenceRuntimeError(f"{field} contain an invalid key")
    return value


def _gsim_argument_evidence(branches: object) -> dict[str, Any]:
    """Validate source-derived GSIM argument names without returning values."""
    if type(branches) is not list or len(branches) != EXPECTED_BRANCH_COUNT:
        raise Esrm20GsimReferenceRuntimeError("verified runtime branch inventory is invalid")

    source_keys: set[str] = set()
    runtime_keys: set[str] = set()
    for branch in branches:
        if type(branch) is not dict:
            raise Esrm20GsimReferenceRuntimeError("verified runtime branch is not an object")
        source = _argument_keys(branch.get("argument_keys"), field="source GSIM argument keys")
        runtime = _argument_keys(
            branch.get("runtime_argument_keys_after_alias"),
            field="post-alias GSIM argument keys",
        )
        source_keys.update(source)
        runtime_keys.update(runtime)

    source = sorted(source_keys)
    runtime = sorted(runtime_keys)
    if source != list(EXPECTED_SOURCE_ARGUMENT_KEYS):
        raise Esrm20GsimReferenceRuntimeError(
            "verified ESRM20 source GSIM argument-key set drifted"
        )
    external = sorted(
        {
            key
            for key in (*source, *runtime)
            if key.endswith(_EXTERNAL_RESOURCE_SUFFIXES)
        }
    )
    if external:
        raise Esrm20GsimReferenceRuntimeError(
            "verified ESRM20 GSIM arguments require external resources"
        )
    if not runtime:
        raise Esrm20GsimReferenceRuntimeError(
            "verified ESRM20 post-alias argument evidence is unexpectedly empty"
        )
    return {
        "source_argument_keys": source,
        "runtime_argument_keys_after_alias": runtime,
        "external_resource_argument_keys": [],
        "argument_values_returned": False,
        "source_profile_result_comment_id": CANONICAL_PROFILE_RESULT_COMMENT_ID,
    }


def _site_parameter_evidence(
    runtime_result: Mapping[str, Any], registry: Mapping[str, Any]
) -> dict[str, Any]:
    """Derive only class-level site parameter names from verified OpenQuake classes."""
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
    with esrm20_binding():
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
            raise Esrm20GsimReferenceRuntimeError(
                "runtime result is not bound to canonical ESRM20 GSIM bytes"
            )
        if result.get("branch_count") != EXPECTED_BRANCH_COUNT:
            raise Esrm20GsimReferenceRuntimeError("runtime result branch count drifted")
        if result.get("openquake_reference", {}).get("commit") != OPENQUAKE_COMMIT:
            raise Esrm20GsimReferenceRuntimeError("runtime result OpenQuake commit drifted")

        argument_evidence = _gsim_argument_evidence(result.get("branches"))
        verified_runtime = _gate._load_verified_openquake_runtime()
        evidence = _site_parameter_evidence(result, verified_runtime.registry)
        result = dict(result)
        result["schema_version"] = SCHEMA_VERSION
        result["source_issue"] = SOURCE_ISSUE
        result["source_profile_result_comment_id"] = CANONICAL_PROFILE_RESULT_COMMENT_ID
        result["source_receipt_result_comment_id"] = CANONICAL_RECEIPT_RESULT_COMMENT_ID
        result["requested_gsim_tokens"] = list(EXPECTED_REQUESTED_TOKENS)
        result["gsim_argument_evidence"] = argument_evidence
        result["site_parameter_requirements"] = evidence
        result["site_parameter_requirements_derived"] = True
        result["site_model_compatibility_verified"] = False
        result["imt_component_unit_compatibility_verified"] = False
        result["numerical_hazard_agreement_verified"] = False
        result["full_hazard_compatibility_verified"] = False
        result["model_use_authorized"] = False
        return result


def validate_request(body: object, *, expected_issue: int, execution_sha: str) -> dict[str, Any]:
    with esrm20_binding():
        return _runtime.validate_request(
            body, expected_issue=expected_issue, execution_sha=execution_sha
        )


def has_terminal_runtime_result(
    *, repository: str, token: str, execution_sha: str, opener: Any | None = None, max_pages: int = 20
) -> bool:
    with esrm20_binding():
        return _runtime.has_terminal_runtime_result(
            repository=repository,
            token=token,
            execution_sha=execution_sha,
            opener=opener,
            max_pages=max_pages,
        )


def collect_runtime_observation(*, image_digest: str) -> dict[str, Any]:
    return _runtime.collect_runtime_observation(image_digest=image_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comment-body-env", required=True)
    parser.add_argument("--expected-issue", type=int, required=True)
    parser.add_argument("--execution-sha", required=True)
    parser.add_argument("--runtime-image-digest-env")
    parser.add_argument("--validate-request-only", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    body = os.environ.get(args.comment_body_env)
    validate_request(body, expected_issue=args.expected_issue, execution_sha=args.execution_sha)
    if args.validate_request_only:
        return 0
    if not args.output or not args.runtime_image_digest_env:
        raise Esrm20GsimReferenceRuntimeError(
            "--output and --runtime-image-digest-env are required for execution"
        )
    digest = os.environ.get(args.runtime_image_digest_env)
    if type(digest) is not str:
        raise Esrm20GsimReferenceRuntimeError("runtime image digest environment value is absent")
    # Preserve the reviewed digest syntax gate.
    digest = _runtime._validate_image_digest(digest)
    result = run_reference_runtime(execution_sha=args.execution_sha, image_digest=digest)
    Path(args.output).write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
