# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from copy import deepcopy
import unittest
from unittest import mock

from scripts import compare_esrm20_group_risk_runtime_scalars as subject


def _profile(
    candidate: str,
    *,
    calculation_mode: str | None = "ebrisk",
    calculation_mode_present: bool = True,
    seeds: list[dict[str, object]] | None = None,
    seed_setting_present: bool | None = None,
    ignore_master_seed: bool | None = None,
    ignore_master_seed_present: bool = False,
    minimum_asset_loss: str | None = "0",
    minimum_asset_loss_present: bool = True,
) -> dict[str, object]:
    runtime_module = subject.group1_runtime if candidate == "group1" else subject.group2_runtime
    if seeds is None:
        seeds = []
    if seed_setting_present is None:
        seed_setting_present = bool(seeds)
    return {
        "schema_version": f"synthetic-{candidate}",
        "control_issue": 281,
        "source_issue": 281,
        "dataset_id": "efehr.esrm20.risk-inputs.v1.0",
        "project_id": 269,
        "project_path": "efehr/esrm20",
        "commit_sha": "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        "candidate_key": candidate,
        "repository_path": runtime_module.GROUP1_SPEC.repository_path
        if candidate == "group1"
        else runtime_module.GROUP2_SPEC.repository_path,
        "byte_count": runtime_module.GROUP1_SPEC.byte_count
        if candidate == "group1"
        else runtime_module.GROUP2_SPEC.byte_count,
        "sha256": runtime_module.GROUP1_SPEC.sha256
        if candidate == "group1"
        else runtime_module.GROUP2_SPEC.sha256,
        "receipt_comment_id": 123456789,
        "openquake_reference": {
            "repository": "gem/oq-engine",
            "tag": "v3.14.0",
            "commit_sha": "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
        },
        "runtime_scalars": {
            "calculation_mode": calculation_mode,
            "calculation_mode_present": calculation_mode_present,
            "configured_seed_settings": seeds,
            "seed_setting_present": seed_setting_present,
            "ignore_master_seed": ignore_master_seed,
            "ignore_master_seed_present": ignore_master_seed_present,
            "minimum_asset_loss_structural": minimum_asset_loss,
            "minimum_asset_loss_structural_present": minimum_asset_loss_present,
            "defaults_inferred": False,
            "vulnerability_sampling_seed_semantics_verified": False,
        },
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class GroupRiskRuntimeScalarComparisonTests(unittest.TestCase):
    def test_compares_exact_projector_outputs_without_widening_authority(self) -> None:
        group1_profile = _profile(
            "group1",
            seeds=[
                {
                    "key": "master_seed",
                    "purpose": "vulnerability_epsilon_sampling",
                    "section": "general",
                    "value": 7,
                }
            ],
            ignore_master_seed=False,
            ignore_master_seed_present=True,
            minimum_asset_loss="0.5",
        )
        group2_profile = _profile(
            "group2",
            seeds=[
                {
                    "key": "master_seed",
                    "purpose": "vulnerability_epsilon_sampling",
                    "section": "general",
                    "value": 7,
                }
            ],
            ignore_master_seed=False,
            ignore_master_seed_present=True,
            minimum_asset_loss="1",
        )
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ) as project1,
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ) as project2,
        ):
            result = subject.compare_group_risk_runtime_scalars(b"group1", b"group2")

        project1.assert_called_once_with(b"group1")
        project2.assert_called_once_with(b"group2")
        relations = {entry["field"]: entry["relation"] for entry in result["comparisons"]}
        self.assertEqual(relations["calculation_mode"], "equal_explicit")
        self.assertEqual(relations["configured_seed_settings"], "equal_explicit")
        self.assertEqual(relations["ignore_master_seed"], "equal_explicit")
        self.assertEqual(relations["minimum_asset_loss_structural"], "different_explicit")
        self.assertEqual(
            result["group1_receipt"]["sha256"], subject.group1_runtime.GROUP1_SPEC.sha256
        )
        self.assertEqual(
            result["group2_receipt"]["sha256"], subject.group2_runtime.GROUP2_SPEC.sha256
        )
        self.assertFalse(result["raw_config_returned"])
        self.assertFalse(result["historical_group_assignment_verified"])
        self.assertFalse(result["runtime_compatibility_verified"])
        self.assertFalse(result["vulnerability_compatibility_verified"])
        self.assertFalse(result["numerical_loss_reproduction_verified"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_distinguishes_absent_both_and_one_sided_presence(self) -> None:
        group1_profile = _profile(
            "group1",
            calculation_mode=None,
            calculation_mode_present=False,
            minimum_asset_loss=None,
            minimum_asset_loss_present=False,
        )
        group2_profile = _profile(
            "group2",
            calculation_mode=None,
            calculation_mode_present=False,
            ignore_master_seed=True,
            ignore_master_seed_present=True,
            minimum_asset_loss=None,
            minimum_asset_loss_present=False,
        )
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ),
        ):
            result = subject.compare_group_risk_runtime_scalars(b"a", b"b")

        comparison = {entry["field"]: entry for entry in result["comparisons"]}
        self.assertEqual(comparison["calculation_mode"]["relation"], "absent_both")
        self.assertEqual(
            comparison["minimum_asset_loss_structural"]["relation"], "absent_both"
        )
        self.assertEqual(
            comparison["ignore_master_seed"]["relation"],
            "present_in_one_group_only",
        )
        self.assertIsNone(comparison["ignore_master_seed"]["group1_value"])
        self.assertIs(comparison["ignore_master_seed"]["group2_value"], True)

    def test_rejects_projector_authority_ceiling_inflation(self) -> None:
        group1_profile = _profile("group1")
        group2_profile = _profile("group2")
        group2_profile["runtime_compatibility_verified"] = True
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ),
        ):
            with self.assertRaisesRegex(
                subject.RiskRuntimeScalarComparisonError,
                "runtime_compatibility_verified must remain exactly false",
            ):
                subject.compare_group_risk_runtime_scalars(b"a", b"b")

    def test_rejects_runtime_scalar_schema_drift(self) -> None:
        group1_profile = _profile("group1")
        group2_profile = _profile("group2")
        runtime_scalars = group1_profile["runtime_scalars"]
        self.assertIsInstance(runtime_scalars, dict)
        runtime_scalars["new_runtime_knob"] = "unsafe"  # type: ignore[index]
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ),
        ):
            with self.assertRaisesRegex(
                subject.RiskRuntimeScalarComparisonError,
                "runtime_scalars schema drift",
            ):
                subject.compare_group_risk_runtime_scalars(b"a", b"b")

    def test_rejects_cross_group_provider_identity_drift(self) -> None:
        group1_profile = _profile("group1")
        group2_profile = _profile("group2")
        group2_profile["commit_sha"] = "f" * 40
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ),
        ):
            with self.assertRaisesRegex(
                subject.RiskRuntimeScalarComparisonError,
                "provider commit identity differs across groups",
            ):
                subject.compare_group_risk_runtime_scalars(b"a", b"b")

    def test_rejects_presence_value_contradiction(self) -> None:
        group1_profile = _profile(
            "group1", calculation_mode="ebrisk", calculation_mode_present=False
        )
        group2_profile = _profile("group2")
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ),
        ):
            with self.assertRaisesRegex(
                subject.RiskRuntimeScalarComparisonError,
                "calculation_mode must be null when absent",
            ):
                subject.compare_group_risk_runtime_scalars(b"a", b"b")

    def test_group1_failure_stops_before_group2_projection(self) -> None:
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                side_effect=ValueError("wrong Group1 bytes"),
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
            ) as project2,
        ):
            with self.assertRaisesRegex(ValueError, "wrong Group1 bytes"):
                subject.compare_group_risk_runtime_scalars(b"wrong", b"group2")
        project2.assert_not_called()

    def test_does_not_mutate_projector_evidence(self) -> None:
        group1_profile = _profile("group1")
        group2_profile = _profile("group2")
        original1 = deepcopy(group1_profile)
        original2 = deepcopy(group2_profile)
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                return_value=group1_profile,
            ),
            mock.patch.object(
                subject.group2_runtime,
                "project_group2_risk_runtime_scalars",
                return_value=group2_profile,
            ),
        ):
            subject.compare_group_risk_runtime_scalars(b"a", b"b")
        self.assertEqual(group1_profile, original1)
        self.assertEqual(group2_profile, original2)


if __name__ == "__main__":
    unittest.main()
