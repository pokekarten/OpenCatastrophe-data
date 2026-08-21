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
_SHARED_SOURCE_LINEAGE_FIELDS = (
    "dataset_id",
    "project_id",
    "project_path",
    "commit_sha",
    "openquake_reference",
)


class RiskRuntimeScalarComparisonError(ValueError):
    """Raised when the two bounded runtime profiles cannot be compared safely."""


def _require_exact_false(value: object, field: str) -> None:
    if value is not False:
        raise RiskRuntimeScalarComparisonError(f"{field} must remain exactly false")


def _validate_presence_consistency(
    runtime_scalars: dict[str, Any], *, candidate_key: str
) -> None:
    for value_field, present_field in _FIELD_SPECS:
        present = runtime_scalars[present_field]
        value = runtime_scalars[value_field]
        field_name = f"{candidate_key}.runtime_scalars.{value_field}"
        if value_field == "configured_seed_settings":
            if type(value) is not list:
                raise RiskRuntimeScalarComparisonError(f"{field_name} must be a list")
            if present is not bool(value):
                raise RiskRuntimeScalarComparisonError(
                    f"{field_name} presence flag contradicts its value"
                )
            continue
        if not present:
            if value is not None:
                raise RiskRuntimeScalarComparisonError(
                    f"{field_name} must be null when absent"
                )
            continue
        if value_field == "ignore_master_seed":
            if type(value) is not bool:
                raise RiskRuntimeScalarComparisonError(
                    f"{field_name} must be boolean when present"
                )
        elif type(value) is not str or not value:
            raise RiskRuntimeScalarComparisonError(
                f"{field_name} must be non-empty text when present"
            )


def _expected_openquake_reference(runtime_module: Any) -> dict[str, str]:
    return {
        "repository": runtime_module.OPENQUAKE_REPOSITORY,
        "tag": runtime_module.OPENQUAKE_TAG,
        "commit_sha": runtime_module.OPENQUAKE_COMMIT,
    }


def _validate_profile(
    profile: dict[str, Any],
    *,
    runtime_module: Any,
    candidate_key: str,
    expected_repository_path: str,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, Any]:
    if type(profile) is not dict:
        raise RiskRuntimeScalarComparisonError(f"{candidate_key} profile must be an object")

    expected = {
        "schema_version": runtime_module.SCHEMA_VERSION,
        "control_issue": runtime_module.CONTROL_ISSUE,
        "source_issue": runtime_module.SOURCE_ISSUE,
        "dataset_id": runtime_module.DATASET_ID,
        "project_id": runtime_module.PROJECT_ID,
        "project_path": runtime_module.PROJECT_PATH,
        "commit_sha": runtime_module.COMMIT_SHA,
        "candidate_key": candidate_key,
        "repository_path": expected_repository_path,
        "byte_count": expected_byte_count,
        "sha256": expected_sha256,
        "receipt_comment_id": runtime_module.risk_config.RECEIPT_COMMENT_ID,
        "openquake_reference": _expected_openquake_reference(runtime_module),
    }
    for field, expected_value in expected.items():
        if profile.get(field) != expected_value:
            raise RiskRuntimeScalarComparisonError(
                f"{candidate_key}.{field} drifted from frozen projector authority"
            )

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
    _validate_presence_consistency(runtime_scalars, candidate_key=candidate_key)
    return runtime_scalars


def _validate_shared_source_lineage(
    group1_profile: dict[str, Any], group2_profile: dict[str, Any]
) -> None:
    """Reject comparisons whose two individually valid projectors changed lineage."""

    for field in _SHARED_SOURCE_LINEAGE_FIELDS:
        if group1_profile[field] != group2_profile[field]:
            raise RiskRuntimeScalarComparisonError(
                f"group source lineage diverged at {field}"
            )


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
    group1_payload: bytes, group2_payload: bytes
) -> dict[str, Any]:
    """Verify both exact config byte objects and compare only bounded scalars."""

    group1_profile = group1_runtime.project_group1_risk_runtime_scalars(group1_payload)
    group2_profile = group2_runtime.project_group2_risk_runtime_scalars(group2_payload)

    group1_scalars = _validate_profile(
        group1_profile,
        runtime_module=group1_runtime,
        candidate_key=group1_runtime.GROUP1_KEY,
        expected_repository_path=group1_runtime.GROUP1_SPEC.repository_path,
        expected_byte_count=group1_runtime.GROUP1_SPEC.byte_count,
        expected_sha256=group1_runtime.GROUP1_SPEC.sha256,
    )
    group2_scalars = _validate_profile(
        group2_profile,
        runtime_module=group2_runtime,
        candidate_key=group2_runtime.GROUP2_KEY,
        expected_repository_path=group2_runtime.GROUP2_SPEC.repository_path,
        expected_byte_count=group2_runtime.GROUP2_SPEC.byte_count,
        expected_sha256=group2_runtime.GROUP2_SPEC.sha256,
    )
    _validate_shared_source_lineage(group1_profile, group2_profile)

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
