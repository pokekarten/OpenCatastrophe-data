# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import project_esrm20_group1_risk_runtime_scalars as shared_runtime
from scripts import project_esrm20_group2_risk_runtime_scalars as subject


class Group2RiskRuntimeScalarTests(unittest.TestCase):
    def test_reuses_reviewed_runtime_parser_without_semantic_fork(self) -> None:
        self.assertIs(
            subject.project_runtime_scalars_from_verified_text,
            shared_runtime.project_runtime_scalars_from_verified_text,
        )
        self.assertIs(subject.RiskRuntimeScalarError, shared_runtime.RiskRuntimeScalarError)
        self.assertEqual(subject.OPENQUAKE_REPOSITORY, shared_runtime.OPENQUAKE_REPOSITORY)
        self.assertEqual(subject.OPENQUAKE_TAG, shared_runtime.OPENQUAKE_TAG)
        self.assertEqual(subject.OPENQUAKE_COMMIT, shared_runtime.OPENQUAKE_COMMIT)

    def test_group2_spec_is_exact_frozen_receipt(self) -> None:
        self.assertEqual(subject.GROUP2_KEY, "group2")
        self.assertEqual(
            subject.GROUP2_SPEC.repository_path,
            "Configuration_files/config_ebrisk_Group2.ini",
        )
        self.assertEqual(subject.GROUP2_SPEC.byte_count, 2832)
        self.assertEqual(
            subject.GROUP2_SPEC.sha256,
            "80cf566003cdb5e12dde820d5cba3db8ea5a6ba2db31e7089f3453f921852625",
        )

    def test_shared_projection_preserves_explicit_values_and_absence(self) -> None:
        result = subject.project_runtime_scalars_from_verified_text(
            "[general]\n"
            "calculation_mode = event_based_risk\n"
            "random_seed = 17\n"
            "minimum_asset_loss = {'structural': 2.500, 'contents': 0}\n"
            "unrelated_option = private-to-parser\n"
        )
        self.assertEqual(result["calculation_mode"], "event_based_risk")
        self.assertEqual(
            result["configured_seed_settings"],
            [
                {
                    "key": "random_seed",
                    "purpose": "logic_tree_sampling",
                    "section": "general",
                    "value": 17,
                }
            ],
        )
        self.assertIsNone(result["ignore_master_seed"])
        self.assertFalse(result["ignore_master_seed_present"])
        self.assertEqual(result["minimum_asset_loss_structural"], "2.5")
        self.assertFalse(result["defaults_inferred"])
        self.assertFalse(result["vulnerability_sampling_seed_semantics_verified"])
        self.assertNotIn("unrelated_option", repr(result))

    def test_shared_projection_keeps_fail_closed_alias_behavior(self) -> None:
        for option in ("Calculation_Mode", "minimum-asset-loss", "MasterSeed"):
            with self.subTest(option=option):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(
                        f"[general]\n{option} = 1\n"
                    )

    def test_wrapper_verifies_group2_identity_before_projection(self) -> None:
        config_text = (
            "[general]\n"
            "calculation_mode = event_based_risk\n"
            "master_seed = 321\n"
            "minimum_asset_loss = 0\n"
        )
        with (
            mock.patch.object(
                subject.risk_config,
                "_verify_payload_identity",
                return_value="b" * 64,
            ) as verify,
            mock.patch.object(
                subject.risk_config,
                "_decode_verified_payload",
                return_value=config_text,
            ) as decode,
        ):
            result = subject.project_group2_risk_runtime_scalars(b"synthetic")

        verify.assert_called_once_with(b"synthetic", subject.GROUP2_SPEC)
        decode.assert_called_once_with(b"synthetic")
        self.assertEqual(result["schema_version"], subject.SCHEMA_VERSION)
        self.assertEqual(result["control_issue"], subject.CONTROL_ISSUE)
        self.assertEqual(result["source_issue"], subject.SOURCE_ISSUE)
        self.assertEqual(result["candidate_key"], "group2")
        self.assertEqual(result["repository_path"], subject.GROUP2_SPEC.repository_path)
        self.assertEqual(result["byte_count"], len(b"synthetic"))
        self.assertEqual(result["sha256"], "b" * 64)
        self.assertEqual(
            result["openquake_reference"]["commit_sha"], subject.OPENQUAKE_COMMIT
        )
        self.assertEqual(result["runtime_scalars"]["minimum_asset_loss_structural"], "0")
        self.assertFalse(result["raw_config_returned"])
        self.assertFalse(result["historical_group_assignment_verified"])
        self.assertFalse(result["runtime_compatibility_verified"])
        self.assertFalse(result["numerical_loss_reproduction_verified"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_identity_failure_stops_before_decode(self) -> None:
        with (
            mock.patch.object(
                subject.risk_config,
                "_verify_payload_identity",
                side_effect=subject.risk_config.VerifiedEbriskConfigError("bad bytes"),
            ),
            mock.patch.object(subject.risk_config, "_decode_verified_payload") as decode,
        ):
            with self.assertRaises(subject.risk_config.VerifiedEbriskConfigError):
                subject.project_group2_risk_runtime_scalars(b"wrong")
        decode.assert_not_called()


if __name__ == "__main__":
    unittest.main()
