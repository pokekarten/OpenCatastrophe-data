# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Compare bounded runtime scalars from exact ESRM20 Group1 and Group2 bytes.

The two existing projectors remain the byte-identity and parsing authorities. This
module only compares their already-bounded outputs. Equality is a source-config
diagnostic, not evidence of historical group assignment, runtime compatibility,
vulnerability compatibility, or numerical loss reproduction.
"""

from __future__ import annotations

from typing import Any

from scripts import project_esrm20_group1_risk_runtime_scalars as group1_runtime
from scripts import project_esrm20_group2_risk_runtime_scalars as group2_runtime

SCHEMA_VERSION = "oc-esrm20-group-risk-runtime-scalar-comparison-v1"
CONTROL_ISSUE = 281

_FIELD_SPECS = (
    ("calculation_mode", "calculation_mode_present"),
    ("configured_seed_settings", "seed_setting_present"),
    ("ignore_master_seed", "ignore_master_seed_present"),
    ("minimum_asset_loss_structural", "minimum_asset_loss_structural_present"),
)
_EXPECTED_RUNTIME_KEYS = frozenset(
    {
        "calculation_mode",
        "calculation_mode_present",
        "configured_seed_settings",
        "seed_setting_present",
        "ignore_master_seed",
        "ignore_master_seed_present",
        "minimum_asset_loss_structural",
        "minimum_asset_loss_structural_present",
        "defaults_inferred",
        "vulnerability_sampling_seed_semantics_verified",
    }
)
_REQUIRED_FALSE_CEILINGS = (
    "raw_config_returned",
    "historical_group_assignment_verified",
    "runtime_compatibility_verified",
    "numerical_loss_reproduction_verified",
    "external_bytes_persisted",
    "publication_authorized",
    "model_use_authorized",
)


class RiskRuntimeScalarComparisonError(ValueError):
    """Raised when the two bounded runtime profiles cannot be compared safely."""


def _require_exact_false(value: object, field: str) -> None:
    if value is not False:
        raise RiskRuntimeScalarComparisonError(f"{field} must remain exactly false")


def _validate_profile(
    profile: dict[str, Any],
    *,
    candidate_key: str,
    expected_repository_path: str,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    if type(profile) is not dict:
        raise RiskRuntimeScalarComparisonError(f"{candidate_key} profile must be an object")
    if profile.get("candidate_key") != candidate_key:
        raise RiskRuntimeScalarComparisonError(f"{candidate_key} candidate identity drift")
    if profile.get("repository_path") != expected_repository_path:
        raise RiskRuntimeScalarComparisonError(f"{candidate_key} repository path drift")
    if profile.get("byte_count") != expected_byte_count:
        raise RiskRuntimeScalarComparisonError(f"{candidate_key} byte-count drift")
    if profile.get("sha256") != expected_sha256:
        raise RiskRuntimeScalarComparisonError(f"{candidate_key} SHA-256 drift")

    for field in _REQUIRED_FALSE_CEILINGS:
        _require_exact_false(profile.get(field), f"{candidate_key}.{field}")

    runtime_scalars = profile.get("runtime_scalars")
    if type(runtime_scalars) is not dict:
        raise RiskRuntimeScalarComparisonError(
            f"{candidate_key}.runtime_scalars must be an object"
        )
    if frozenset(runtime_scalars) != _EXPECTED_RUNTIME_KEYS:
        raise RiskRuntimeScalarComparisonError(
            f"{candidate_key}.runtime_scalars schema drift"
        )
    _require_exact_false(
        runtime_scalars.get("defaults_inferred"),
        f"{candidate_key}.runtime_scalars.defaults_inferred",
    )
    _require_exact_false(
        runtime_scalars.get("vulnerability_sampling_seed_semantics_verified"),
        f"{candidate_key}.runtime_scalars.vulnerability_sampling_seed_semantics_verified",
    )
    for _, present_field in _FIELD_SPECS:
        if type(runtime_scalars.get(present_field)) is not bool:
            raise RiskRuntimeScalarComparisonError(
                f"{candidate_key}.runtime_scalars.{present_field} must be boolean"
            )

    return runtime_scalars


def _relation(
    *,
    group1_present: bool,
    group1_value: object,
    group2_present: bool,
    group2_value: object,
) -> str:
    if not group1_present and not group2_present:
        return "absent_both"
    if group1_present != group2_present:
        return "present_in_one_group_only"
    if group1_value == group2_value:
        return "equal_explicit"
    return "different_explicit"


def compare_group_risk_runtime_scalars(
    group1_payload: bytes,
    group2_payload: bytes,
) -> dict[str, Any]:
    """Verify both exact config byte objects and compare only bounded scalars."""

    group1_profile = group1_runtime.project_group1_risk_runtime_scalars(group1_payload)
    group2_profile = group2_runtime.project_group2_risk_runtime_scalars(group2_payload)

    group1_scalars = _validate_profile(
        group1_profile,
        candidate_key=group1_runtime.GROUP1_KEY,
        expected_repository_path=group1_runtime.GROUP1_SPEC.repository_path,
        expected_byte_count=group1_runtime.GROUP1_SPEC.byte_count,
        expected_sha256=group1_runtime.GROUP1_SPEC.sha256,
    )
    group2_scalars = _validate_profile(
        group2_profile,
        candidate_key=group2_runtime.GROUP2_KEY,
        expected_repository_path=group2_runtime.GROUP2_SPEC.repository_path,
        expected_byte_count=group2_runtime.GROUP2_SPEC.byte_count,
        expected_sha256=group2_runtime.GROUP2_SPEC.sha256,
    )

    if group1_profile.get("dataset_id") != group2_profile.get("dataset_id"):
        raise RiskRuntimeScalarComparisonError("dataset identity differs across groups")
    if group1_profile.get("project_id") != group2_profile.get("project_id"):
        raise RiskRuntimeScalarComparisonError("provider project identity differs across groups")
    if group1_profile.get("project_path") != group2_profile.get("project_path"):
        raise RiskRuntimeScalarComparisonError("provider project path differs across groups")
    if group1_profile.get("commit_sha") != group2_profile.get("commit_sha"):
        raise RiskRuntimeScalarComparisonError("provider commit identity differs across groups")
    if group1_profile.get("openquake_reference") != group2_profile.get(
        "openquake_reference"
    ):
        raise RiskRuntimeScalarComparisonError("OpenQuake reference differs across groups")

    comparisons = []
    for value_field, present_field in _FIELD_SPECS:
        group1_present = group1_scalars[present_field]
        group2_present = group2_scalars[present_field]
        group1_value = group1_scalars[value_field]
        group2_value = group2_scalars[value_field]
        comparisons.append(
            {
                "field": value_field,
                "group1_present": group1_present,
                "group1_value": group1_value if group1_present else None,
                "group2_present": group2_present,
                "group2_value": group2_value if group2_present else None,
                "relation": _relation(
                    group1_present=group1_present,
                    group1_value=group1_value,
                    group2_present=group2_present,
                    group2_value=group2_value,
                ),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": group1_profile["dataset_id"],
        "project_id": group1_profile["project_id"],
        "project_path": group1_profile["project_path"],
        "commit_sha": group1_profile["commit_sha"],
        "openquake_reference": group1_profile["openquake_reference"],
        "group1_receipt": {
            "repository_path": group1_profile["repository_path"],
            "byte_count": group1_profile["byte_count"],
            "sha256": group1_profile["sha256"],
            "receipt_comment_id": group1_profile["receipt_comment_id"],
        },
        "group2_receipt": {
            "repository_path": group2_profile["repository_path"],
            "byte_count": group2_profile["byte_count"],
            "sha256": group2_profile["sha256"],
            "receipt_comment_id": group2_profile["receipt_comment_id"],
        },
        "comparisons": comparisons,
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
