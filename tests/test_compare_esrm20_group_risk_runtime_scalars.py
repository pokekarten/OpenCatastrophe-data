# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from copy import deepcopy
import unittest
from unittest import mock

from scripts import compare_esrm20_group_risk_runtime_scalars as subject


def _module(candidate: str):
    return subject.group1_runtime if candidate == "group1" else subject.group2_runtime


def _spec(candidate: str):
    module = _module(candidate)
    return module.GROUP1_SPEC if candidate == "group1" else module.GROUP2_SPEC


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
    module = _module(candidate)
    spec = _spec(candidate)
    seeds = [] if seeds is None else seeds
    seed_setting_present = bool(seeds) if seed_setting_present is None else seed_setting_present
    return {
        "schema_version": module.SCHEMA_VERSION,
        "control_issue": module.CONTROL_ISSUE,
        "source_issue": module.SOURCE_ISSUE,
        "dataset_id": module.DATASET_ID,
        "project_id": module.PROJECT_ID,
        "project_path": module.PROJECT_PATH,
        "commit_sha": module.COMMIT_SHA,
        "candidate_key": candidate,
        "repository_path": spec.repository_path,
        "byte_count": spec.byte_count,
        "sha256": spec.sha256,
        "receipt_comment_id": module.risk_config.RECEIPT_COMMENT_ID,
        "openquake_reference": {
            "repository": module.OPENQUAKE_REPOSITORY,
            "tag": module.OPENQUAKE_TAG,
            "commit_sha": module.OPENQUAKE_COMMIT,
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


def _compare(group1_profile, group2_profile):
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
        return subject.compare_group_risk_runtime_scalars(b"group1", b"group2")


class GroupRiskRuntimeScalarComparisonTests(unittest.TestCase):
    def test_compares_exact_projector_outputs_without_widening_authority(self) -> None:
        group1 = _profile(
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
        group2 = _profile(
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
        result = _compare(group1, group2)
        relations = {entry["field"]: entry["relation"] for entry in result["comparisons"]}
        self.assertEqual(relations["calculation_mode"], "equal_explicit")
        self.assertEqual(relations["configured_seed_settings"], "equal_explicit")
        self.assertEqual(relations["ignore_master_seed"], "equal_explicit")
        self.assertEqual(relations["minimum_asset_loss_structural"], "different_explicit")
        self.assertEqual(
            result["group1_receipt"]["receipt_comment_id"],
            subject.group1_runtime.risk_config.RECEIPT_COMMENT_ID,
        )
        for field in (
            "raw_config_returned",
            "historical_group_assignment_verified",
            "runtime_compatibility_verified",
            "vulnerability_compatibility_verified",
            "numerical_loss_reproduction_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_distinguishes_absent_both_and_one_sided_presence(self) -> None:
        group1 = _profile(
            "group1",
            calculation_mode=None,
            calculation_mode_present=False,
            minimum_asset_loss=None,
            minimum_asset_loss_present=False,
        )
        group2 = _profile(
            "group2",
            calculation_mode=None,
            calculation_mode_present=False,
            ignore_master_seed=True,
            ignore_master_seed_present=True,
            minimum_asset_loss=None,
            minimum_asset_loss_present=False,
        )
        comparison = {
            entry["field"]: entry for entry in _compare(group1, group2)["comparisons"]
        }
        self.assertEqual(comparison["calculation_mode"]["relation"], "absent_both")
        self.assertEqual(
            comparison["minimum_asset_loss_structural"]["relation"], "absent_both"
        )
        self.assertEqual(
            comparison["ignore_master_seed"]["relation"], "present_in_one_group_only"
        )

    def test_rejects_projector_authority_ceiling_inflation(self) -> None:
        group1 = _profile("group1")
        group2 = _profile("group2")
        group2["runtime_compatibility_verified"] = True
        with self.assertRaisesRegex(
            subject.RiskRuntimeScalarComparisonError,
            "runtime_compatibility_verified must remain exactly false",
        ):
            _compare(group1, group2)

    def test_rejects_runtime_scalar_schema_drift(self) -> None:
        group1 = _profile("group1")
        scalars = group1["runtime_scalars"]
        self.assertIsInstance(scalars, dict)
        scalars["new_runtime_knob"] = "unsafe"  # type: ignore[index]
        with self.assertRaisesRegex(
            subject.RiskRuntimeScalarComparisonError, "runtime_scalars schema drift"
        ):
            _compare(group1, _profile("group2"))

    def test_rejects_presence_value_contradiction(self) -> None:
        group1 = _profile(
            "group1", calculation_mode="ebrisk", calculation_mode_present=False
        )
        with self.assertRaisesRegex(
            subject.RiskRuntimeScalarComparisonError,
            "calculation_mode must be null when absent",
        ):
            _compare(group1, _profile("group2"))

    def test_rejects_individual_top_level_schema_and_receipt_drift(self) -> None:
        mutations = (
            ("schema_version", "drifted-schema"),
            ("control_issue", 999),
            ("source_issue", 999),
            ("receipt_comment_id", 999),
            ("dataset_id", "wrong-dataset"),
            ("project_id", 999),
            ("project_path", "wrong/project"),
            ("commit_sha", "f" * 40),
            ("openquake_reference", {"repository": "wrong", "tag": "v0", "commit_sha": "f" * 40}),
        )
        for candidate in ("group1", "group2"):
            for field, value in mutations:
                with self.subTest(candidate=candidate, field=field):
                    group1 = _profile("group1")
                    group2 = _profile("group2")
                    target = group1 if candidate == "group1" else group2
                    target[field] = value
                    with self.assertRaisesRegex(
                        subject.RiskRuntimeScalarComparisonError,
                        f"{candidate}\\.{field} drifted",
                    ):
                        _compare(group1, group2)

    def test_rejects_joint_provenance_drift_that_preserves_cross_group_equality(self) -> None:
        for field, value in (
            ("dataset_id", "jointly-wrong-dataset"),
            ("project_id", 999),
            ("project_path", "joint/wrong"),
            ("commit_sha", "f" * 40),
            ("receipt_comment_id", 999),
        ):
            with self.subTest(field=field):
                group1 = _profile("group1")
                group2 = _profile("group2")
                group1[field] = value
                group2[field] = value
                with self.assertRaisesRegex(
                    subject.RiskRuntimeScalarComparisonError, "drifted from frozen projector authority"
                ):
                    _compare(group1, group2)

    def test_group1_failure_stops_before_group2_projection(self) -> None:
        with (
            mock.patch.object(
                subject.group1_runtime,
                "project_group1_risk_runtime_scalars",
                side_effect=ValueError("wrong Group1 bytes"),
            ),
            mock.patch.object(
                subject.group2_runtime, "project_group2_risk_runtime_scalars"
            ) as project2,
        ):
            with self.assertRaisesRegex(ValueError, "wrong Group1 bytes"):
                subject.compare_group_risk_runtime_scalars(b"wrong", b"group2")
        project2.assert_not_called()

    def test_does_not_mutate_projector_evidence(self) -> None:
        group1 = _profile("group1")
        group2 = _profile("group2")
        original1 = deepcopy(group1)
        original2 = deepcopy(group2)
        _compare(group1, group2)
        self.assertEqual(group1, original1)
        self.assertEqual(group2, original2)


if __name__ == "__main__":
    unittest.main()
