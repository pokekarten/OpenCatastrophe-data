# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Exact-SHA dedup validator for the extended ESRM20 GSIM runtime receipt.

The ESRM20 adapter deliberately reuses the ESHM20 runtime implementation, but
its durable result adds ESRM20-specific provenance, argument, site and component
evidence.  This module validates that extended receipt directly instead of
feeding it back through the narrower ESHM20 terminal-result schema.
"""

from __future__ import annotations

import json
from typing import Any

from scripts import run_eshm20_gsim_reference_runtime as _base
from scripts import run_esrm20_gsim_reference_runtime as _runtime
from scripts.prepare_agent_action_result import LedgerError, fetch_repository_comments

TRUSTED_RESULT_LOGIN = "github-actions[bot]"
LEGACY_TERMINAL_COMMENT_ID = 5315069949
LEGACY_EXECUTION_SHA = "b3943491c1159464ae288583197b934f71c8e9f9"

_EXTRA_FIELDS = {
    "source_profile_result_comment_id",
    "source_receipt_result_comment_id",
    "requested_gsim_tokens",
    "gsim_argument_evidence",
    "site_parameter_requirements",
    "site_parameter_requirements_derived",
}
_COMPONENT_FIELDS = {"component_evidence", "component_evidence_derived"}
_BRANCH_FIELDS = set(_base._BRANCH_FIELDS)

_EXPECTED_SITE_ROWS = [
    {"resolved_gsim_class": "BCHydroESHM20SInter", "site_parameters": ["vs30", "xvf"]},
    {"resolved_gsim_class": "BCHydroESHM20SSlab", "site_parameters": ["vs30", "xvf"]},
    {"resolved_gsim_class": "ESHM20Craton", "site_parameters": ["vs30"]},
    {
        "resolved_gsim_class": "KothaEtAl2020ESHM20SlopeGeology",
        "site_parameters": ["geology", "region", "slope"],
    },
    {"resolved_gsim_class": "LanzanoLuzi2019shallow", "site_parameters": ["vs30"]},
]
_EXPECTED_SITE_REQUIREMENTS = ["geology", "region", "slope", "vs30", "xvf"]
_SITE_SOURCE = "OpenQuake-3.14-verified-class.REQUIRES_SITES_PARAMETERS"
_COMPONENT_SOURCE = (
    "OpenQuake-3.14-verified-class."
    "DEFINED_FOR_INTENSITY_MEASURE_COMPONENT+exact-direct-request-identity"
)


def _error(message: str) -> _runtime.Esrm20GsimReferenceRuntimeError:
    return _runtime.Esrm20GsimReferenceRuntimeError(message)


def _expected_branch_requests() -> dict[tuple[str, str], tuple[str, str, str, tuple[str, ...]]]:
    """Project the frozen ESHM20 request inventory onto exact ESRM20 request names."""

    expected: dict[tuple[str, str], tuple[str, str, str, tuple[str, ...]]] = {}
    for key, (trt, token, request_form, argument_keys) in _base._EXPECTED_BRANCH_REQUESTS.items():
        if token == "KothaEtAl2020ESHM20":
            token = "KothaEtAl2020ESHM20SlopeGeology"
        projected_keys = tuple(
            "theta_6_adjustment" if item == "theta6_adjustment" else item
            for item in argument_keys
        )
        expected[key] = (trt, token, request_form, projected_keys)
    if len(expected) != _runtime.EXPECTED_BRANCH_COUNT:
        raise _error("frozen ESRM20 branch projection drifted")
    return expected


def _validate_branches(result: dict[str, Any]) -> None:
    expected = _expected_branch_requests()
    branches = result.get("branches")
    if type(result.get("branch_count")) is not int or result["branch_count"] != _runtime.EXPECTED_BRANCH_COUNT:
        raise _error("trusted ESRM20 runtime branch count drifted")
    if type(branches) is not list or len(branches) != _runtime.EXPECTED_BRANCH_COUNT:
        raise _error("trusted ESRM20 runtime branch inventory drifted")

    observed_order: list[tuple[str, str]] = []
    resolved_classes: set[str] = set()
    for branch in branches:
        if type(branch) is not dict or set(branch) != _BRANCH_FIELDS:
            raise _error("trusted ESRM20 runtime branch fields drifted")
        branch_set_id = branch.get("branch_set_id")
        branch_id = branch.get("branch_id")
        if type(branch_set_id) is not str or type(branch_id) is not str:
            raise _error("trusted ESRM20 runtime branch identity drifted")
        key = (branch_set_id, branch_id)
        contract = expected.get(key)
        if contract is None:
            raise _error("trusted ESRM20 runtime branch identity drifted")
        trt, token, request_form, argument_keys = contract
        expected_keys = list(argument_keys)
        exact = (
            (branch.get("tectonic_region_type"), trt),
            (branch.get("requested_gsim_token"), token),
            (branch.get("resolved_gsim_class"), token),
            (branch.get("request_form"), request_form),
            (branch.get("argument_keys"), expected_keys),
            (branch.get("runtime_argument_keys_after_alias"), expected_keys),
            (branch.get("alias_definition_present"), False),
            (branch.get("alias_expansion_applied"), False),
            (branch.get("registry_alias_key_used"), False),
            (branch.get("constructor_accepted"), True),
        )
        for observed, wanted in exact:
            if type(observed) is not type(wanted) or observed != wanted:
                raise _error("trusted ESRM20 runtime branch contract drifted")
        observed_order.append(key)
        resolved_classes.add(token)

    if observed_order != sorted(expected):
        raise _error("trusted ESRM20 runtime branch order drifted")
    classes = sorted(resolved_classes)
    if classes != list(_runtime.EXPECTED_REQUESTED_TOKENS):
        raise _error("trusted ESRM20 runtime resolved-class inventory drifted")
    if result.get("unique_resolved_gsim_classes") != classes:
        raise _error("trusted ESRM20 runtime resolved-class summary drifted")
    if result.get("alias_requested_tokens") != []:
        raise _error("trusted ESRM20 runtime alias summary drifted")


def _validate_argument_evidence(result: dict[str, Any]) -> None:
    evidence = result.get("gsim_argument_evidence")
    fields = {
        "source_argument_keys",
        "runtime_argument_keys_after_alias",
        "external_resource_argument_keys",
        "argument_values_returned",
        "source_profile_result_comment_id",
    }
    if type(evidence) is not dict or set(evidence) != fields:
        raise _error("trusted ESRM20 GSIM argument evidence fields drifted")
    expected_keys = list(_runtime.EXPECTED_SOURCE_ARGUMENT_KEYS)
    exact = (
        (evidence.get("source_argument_keys"), expected_keys),
        (evidence.get("runtime_argument_keys_after_alias"), expected_keys),
        (evidence.get("external_resource_argument_keys"), []),
        (evidence.get("argument_values_returned"), False),
        (
            evidence.get("source_profile_result_comment_id"),
            _runtime.CANONICAL_PROFILE_RESULT_COMMENT_ID,
        ),
    )
    for observed, wanted in exact:
        if type(observed) is not type(wanted) or observed != wanted:
            raise _error("trusted ESRM20 GSIM argument evidence drifted")


def _validate_site_evidence(result: dict[str, Any]) -> None:
    if result.get("site_parameter_requirements_derived") is not True:
        raise _error("trusted ESRM20 site evidence derivation flag drifted")
    site = result.get("site_parameter_requirements")
    expected = {
        "per_resolved_gsim_class": _EXPECTED_SITE_ROWS,
        "required_site_parameters": _EXPECTED_SITE_REQUIREMENTS,
        "source": _SITE_SOURCE,
    }
    if type(site) is not dict or site != expected:
        raise _error("trusted ESRM20 site evidence drifted")


def _validate_component_evidence(result: dict[str, Any], *, legacy: bool) -> None:
    if legacy:
        if any(field in result for field in _COMPONENT_FIELDS):
            raise _error("legacy ESRM20 runtime component fields drifted")
        return
    if result.get("component_evidence_derived") is not True:
        raise _error("trusted ESRM20 component derivation flag drifted")
    component = result.get("component_evidence")
    rows = [
        {"resolved_gsim_class": name, "component": _runtime.EXPECTED_COMPONENTS_BY_GSIM[name]}
        for name in sorted(_runtime.EXPECTED_COMPONENTS_BY_GSIM)
    ]
    expected = {
        "per_resolved_gsim_class": rows,
        "unique_components": ["GEOMETRIC_MEAN", "RotD50"],
        "mixed_component_basis": True,
        "component_conversion_request_absent": True,
        "component_conversion_activated": False,
        "component_conversion_wrapper": _runtime.COMPONENT_CONVERSION_WRAPPER,
        "component_conversion_argument": _runtime.COMPONENT_CONVERSION_ARGUMENT,
        "reference_component_semantics": _runtime.REFERENCE_COMPONENT_SEMANTICS,
        "source": _COMPONENT_SOURCE,
    }
    if type(component) is not dict or component != expected:
        raise _error("trusted ESRM20 component evidence drifted")


def _parse_terminal(body: object, *, comment_id: object) -> str | None:
    if type(body) is not str or _runtime.RESULT_MARKER not in body:
        return None
    if body.count(_runtime.RESULT_MARKER) != 1:
        raise _error("trusted ESRM20 runtime result marker is malformed")
    before, after = body.split(_runtime.RESULT_MARKER, 1)
    if before.strip() or not after.strip():
        raise _error("trusted ESRM20 runtime result envelope is malformed")
    try:
        result = json.loads(
            after.strip(),
            object_pairs_hook=_base._pairs,
            parse_constant=_base._reject_constant,
        )
    except _base.ReferenceRuntimeExecutionError as exc:
        raise _error("trusted ESRM20 runtime result JSON is malformed") from exc
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise _error("trusted ESRM20 runtime result JSON is malformed") from exc
    if type(result) is not dict:
        raise _error("trusted ESRM20 runtime result is not an object")

    target_sha = result.get("target_sha")
    execution_sha = result.get("execution_sha")
    if (
        type(target_sha) is not str
        or _base._SHA_RE.fullmatch(target_sha) is None
        or execution_sha != target_sha
    ):
        raise _error("trusted ESRM20 runtime result SHA identity drifted")

    legacy = comment_id == LEGACY_TERMINAL_COMMENT_ID and target_sha == LEGACY_EXECUTION_SHA
    expected_fields = set(_base._TERMINAL_RESULT_FIELDS) | _EXTRA_FIELDS
    if not legacy:
        expected_fields |= _COMPONENT_FIELDS
    if set(result) != expected_fields:
        raise _error("trusted ESRM20 runtime result fields drifted")

    exact = (
        (result.get("schema_version"), _runtime.SCHEMA_VERSION),
        (result.get("source_issue"), _runtime.SOURCE_ISSUE),
        (result.get("dataset_id"), _runtime.DATASET_ID),
        (result.get("status"), "pass"),
        (result.get("same_process_runtime_observation_collected"), True),
        (result.get("executing_environment_matches_reconstructed_reference_recipe_fields"), True),
        (result.get("gsim_request_reference_recipe_runtime_compatibility_verified"), True),
        (result.get("historical_environment_verified"), False),
        (result.get("reference_base_image_byte_identity_verified"), False),
        (result.get("wheel_byte_identity_verified"), False),
        (result.get("numerical_hazard_agreement_verified"), False),
        (result.get("imt_component_unit_compatibility_verified"), False),
        (result.get("full_hazard_compatibility_verified"), False),
        (result.get("site_model_compatibility_verified"), False),
        (result.get("vulnerability_compatibility_verified"), False),
        (result.get("reference_run_verified"), False),
        (result.get("scientific_validity_verified"), False),
        (result.get("external_bytes_persisted"), False),
        (result.get("publication_authorized"), False),
        (result.get("model_use_authorized"), False),
        (
            result.get("source_profile_result_comment_id"),
            _runtime.CANONICAL_PROFILE_RESULT_COMMENT_ID,
        ),
        (
            result.get("source_receipt_result_comment_id"),
            _runtime.CANONICAL_RECEIPT_RESULT_COMMENT_ID,
        ),
        (result.get("requested_gsim_tokens"), list(_runtime.EXPECTED_REQUESTED_TOKENS)),
    )
    for observed, wanted in exact:
        if type(observed) is not type(wanted) or observed != wanted:
            raise _error("trusted ESRM20 runtime result contract drifted")

    digest = result.get("execution_container_image_digest")
    if type(digest) is not str or _base._DIGEST_RE.fullmatch(digest) is None:
        raise _error("trusted ESRM20 runtime image digest drifted")

    expected_gmm = {
        "project_id": _runtime.PROJECT_ID,
        "project_path": _runtime.PROJECT_PATH,
        "commit_sha": _runtime.COMMIT_SHA,
        "repository_path": _runtime.REPOSITORY_PATH,
        "byte_count": _runtime.EXPECTED_BYTE_COUNT,
        "sha256": _runtime.EXPECTED_SHA256,
    }
    if result.get("gmm_identity") != expected_gmm:
        raise _error("trusted ESRM20 GMM identity drifted")
    expected_oq = {
        "repository": _runtime._gate.OPENQUAKE_REPOSITORY,
        "tag": _runtime._gate.OPENQUAKE_TAG,
        "commit": _runtime.OPENQUAKE_COMMIT,
        "version": _runtime._gate.OPENQUAKE_VERSION,
    }
    if result.get("openquake_reference") != expected_oq:
        raise _error("trusted ESRM20 OpenQuake identity drifted")

    try:
        _base._validate_trusted_runtime_fingerprint(
            result.get("reference_runtime_fingerprint"), image_digest=digest
        )
    except _base.ReferenceRuntimeExecutionError as exc:
        raise _error("trusted ESRM20 runtime fingerprint drifted") from exc

    _validate_branches(result)
    _validate_argument_evidence(result)
    _validate_site_evidence(result)
    _validate_component_evidence(result, legacy=legacy)
    return target_sha


def has_terminal_runtime_result(
    *,
    repository: str,
    token: str,
    execution_sha: str,
    opener: Any | None = None,
    max_pages: int = 20,
) -> bool:
    """Fully validate trusted ESRM20 terminals, then deduplicate only exact SHA."""

    if type(execution_sha) is not str or _base._SHA_RE.fullmatch(execution_sha) is None:
        raise _error("invalid ESRM20 execution SHA")
    kwargs: dict[str, Any] = {"issue": _runtime.SOURCE_ISSUE, "max_pages": max_pages}
    if opener is not None:
        kwargs["opener"] = opener
    try:
        comments = fetch_repository_comments(repository, token, **kwargs)
    except LedgerError as exc:
        raise _error("ESRM20 runtime result ledger is incomplete") from exc

    for comment in comments:
        user = comment.get("user")
        login = user.get("login") if type(user) is dict else None
        if login != TRUSTED_RESULT_LOGIN:
            continue
        own_sha = _parse_terminal(comment.get("body"), comment_id=comment.get("id"))
        if own_sha is None:
            continue
        if own_sha == execution_sha:
            return True
    return False
