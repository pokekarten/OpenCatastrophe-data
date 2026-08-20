# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import project_esrm20_group1_risk_runtime_scalars as subject


class Group1RiskRuntimeScalarTests(unittest.TestCase):
    def test_projects_only_explicit_runtime_scalars(self) -> None:
        result = subject.project_runtime_scalars_from_verified_text(
            "[general]\n"
            "calculation_mode = event_based_risk\n"
            "master_seed = 42\n"
            "ignore_master_seed = false\n"
            "minimum_asset_loss = {'structural': 12.500, 'contents': 0}\n"
            "unrelated_option = should_not_escape\n"
        )
        self.assertEqual(result["calculation_mode"], "event_based_risk")
        self.assertTrue(result["calculation_mode_present"])
        self.assertEqual(
            result["configured_seed_settings"],
            [
                {
                    "key": "master_seed",
                    "purpose": "vulnerability_epsilon_sampling",
                    "section": "general",
                    "value": 42,
                }
            ],
        )
        self.assertTrue(result["seed_setting_present"])
        self.assertFalse(result["ignore_master_seed"])
        self.assertTrue(result["ignore_master_seed_present"])
        self.assertEqual(result["minimum_asset_loss_structural"], "12.5")
        self.assertTrue(result["minimum_asset_loss_structural_present"])
        self.assertFalse(result["defaults_inferred"])
        self.assertFalse(result["vulnerability_sampling_seed_semantics_verified"])
        self.assertNotIn("unrelated_option", repr(result))

    def test_seed_purposes_remain_distinct(self) -> None:
        result = subject.project_runtime_scalars_from_verified_text(
            "[general]\n"
            "master_seed = 11\n"
            "random_seed = 22\n"
            "ses_seed = 33\n"
        )
        self.assertEqual(
            [(row["key"], row["purpose"], row["value"]) for row in result["configured_seed_settings"]],
            [
                ("master_seed", "vulnerability_epsilon_sampling", 11),
                ("random_seed", "logic_tree_sampling", 22),
                ("ses_seed", "ground_motion_field_generation", 33),
            ],
        )

    def test_seed_values_match_frozen_openquake_positiveint_forms(self) -> None:
        forms = (
            ("0", 0),
            ("00", 0),
            ("01", 1),
            ("+1", 1),
            ("true", 1),
            ("TRUE", 1),
            ("false", 0),
            ("FALSE", 0),
            ("9223372036854775808", 9223372036854775808),
        )
        for key in ("master_seed", "random_seed", "ses_seed"):
            for value, expected in forms:
                with self.subTest(key=key, value=value):
                    result = subject.project_runtime_scalars_from_verified_text(
                        f"[general]\n{key} = {value}\n"
                    )
                    self.assertEqual(
                        result["configured_seed_settings"][0]["value"], expected
                    )
                    self.assertTrue(result["seed_setting_present"])
                    self.assertFalse(result["defaults_inferred"])

    def test_absence_is_preserved_without_defaults(self) -> None:
        result = subject.project_runtime_scalars_from_verified_text(
            "[general]\nexposure_file = Exposure/example.xml\n"
        )
        self.assertIsNone(result["calculation_mode"])
        self.assertFalse(result["calculation_mode_present"])
        self.assertEqual(result["configured_seed_settings"], [])
        self.assertFalse(result["seed_setting_present"])
        self.assertIsNone(result["ignore_master_seed"])
        self.assertFalse(result["ignore_master_seed_present"])
        self.assertIsNone(result["minimum_asset_loss_structural"])
        self.assertFalse(result["minimum_asset_loss_structural_present"])
        self.assertFalse(result["defaults_inferred"])

    def test_duplicate_or_inherited_runtime_options_fail_closed(self) -> None:
        cases = (
            "[a]\ncalculation_mode = event_based_risk\n[b]\ncalculation_mode = scenario_risk\n",
            "[DEFAULT]\nmaster_seed = 7\n[a]\nvalue = 1\n",
            "[a]\ncalculation_mode = event_based_risk\ncalculation_mode = scenario_risk\n",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(text)

    def test_alias_case_and_unknown_seed_drift_fail_closed(self) -> None:
        for option in (
            "Calculation_Mode",
            "calculation-mode",
            "minimum-asset-loss",
            "MasterSeed",
            "vulnerability_seed",
        ):
            with self.subTest(option=option):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(
                        f"[general]\n{option} = 1\n"
                    )

    def test_calculation_mode_matches_all_frozen_openquake_choices(self) -> None:
        expected_modes = {
            "classical_risk",
            "classical_damage",
            "classical",
            "event_based",
            "scenario",
            "post_risk",
            "ebrisk",
            "scenario_risk",
            "event_based_risk",
            "disaggregation",
            "multi_risk",
            "classical_bcr",
            "preclassical",
            "conditional_spectrum",
            "event_based_damage",
            "scenario_damage",
        }
        self.assertEqual(subject._CALCULATION_MODES, expected_modes)
        for mode in sorted(expected_modes):
            with self.subTest(mode=mode):
                result = subject.project_runtime_scalars_from_verified_text(
                    f"[general]\ncalculation_mode = {mode}\n"
                )
                self.assertEqual(result["calculation_mode"], mode)
                self.assertTrue(result["calculation_mode_present"])

        with self.assertRaises(subject.RiskRuntimeScalarError):
            subject.project_runtime_scalars_from_verified_text(
                "[general]\ncalculation_mode = event_based_magic\n"
            )

    def test_invalid_seed_values_fail_closed(self) -> None:
        for value in ("-1", "1.5", "nan", "yes", "no"):
            with self.subTest(value=value):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(
                        f"[general]\nmaster_seed = {value}\n"
                    )

    def test_ignore_master_seed_accepts_frozen_openquake_boolean_forms(self) -> None:
        for value, expected in (
            ("", False),
            ("0", False),
            ("1", True),
            ("false", False),
            ("true", True),
            ("FALSE", False),
            ("TRUE", True),
        ):
            with self.subTest(value=value):
                result = subject.project_runtime_scalars_from_verified_text(
                    f"[general]\nignore_master_seed = {value}\n"
                )
                self.assertIs(result["ignore_master_seed"], expected)
                self.assertTrue(result["ignore_master_seed_present"])
                self.assertFalse(result["defaults_inferred"])

        absent = subject.project_runtime_scalars_from_verified_text(
            "[general]\nexposure_file = Exposure/example.xml\n"
        )
        self.assertIsNone(absent["ignore_master_seed"])
        self.assertFalse(absent["ignore_master_seed_present"])

    def test_empty_values_remain_forbidden_for_other_runtime_options(self) -> None:
        for option in (
            "calculation_mode",
            "master_seed",
            "random_seed",
            "ses_seed",
            "minimum_asset_loss",
        ):
            with self.subTest(option=option):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(
                        f"[general]\n{option} =\n"
                    )

    def test_invalid_ignore_master_seed_fails_closed(self) -> None:
        for value in ("yes", "no", "vulnerability", "none", "2", "-1"):
            with self.subTest(value=value):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(
                        f"[general]\nignore_master_seed = {value}\n"
                    )

    def test_minimum_asset_loss_explicit_default_matches_scalar(self) -> None:
        scalar = subject.project_runtime_scalars_from_verified_text(
            "[general]\nminimum_asset_loss = 12.5\n"
        )
        explicit_default = subject.project_runtime_scalars_from_verified_text(
            "[general]\nminimum_asset_loss = {'default': 12.5}\n"
        )
        self.assertEqual(scalar["minimum_asset_loss_structural"], "12.5")
        self.assertEqual(
            explicit_default["minimum_asset_loss_structural"],
            scalar["minimum_asset_loss_structural"],
        )
        self.assertTrue(explicit_default["minimum_asset_loss_structural_present"])
        self.assertFalse(explicit_default["defaults_inferred"])

    def test_minimum_asset_loss_structural_overrides_explicit_default(self) -> None:
        result = subject.project_runtime_scalars_from_verified_text(
            "[general]\n"
            "minimum_asset_loss = {'default': 12.5, 'structural': 7.25}\n"
        )
        self.assertEqual(result["minimum_asset_loss_structural"], "7.25")
        self.assertTrue(result["minimum_asset_loss_structural_present"])
        self.assertFalse(result["defaults_inferred"])

    def test_invalid_minimum_asset_loss_values_fail_closed(self) -> None:
        cases = (
            "-1",
            "NaN",
            "Infinity",
            "{'contents': 1}",
            "{'default': -1}",
            "{'structural': -1}",
            "{'structural': float('nan')}",
            "{'structural': 1, 'structural': 2}",
            "{'default': 1, 'default': 2}",
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(subject.RiskRuntimeScalarError):
                    subject.project_runtime_scalars_from_verified_text(
                        f"[general]\nminimum_asset_loss = {value}\n"
                    )

    def test_wrapper_verifies_group1_identity_before_projection(self) -> None:
        config_text = (
            "[general]\n"
            "calculation_mode = event_based_risk\n"
            "master_seed = 123\n"
            "minimum_asset_loss = 0\n"
        )
        with (
            mock.patch.object(
                subject.risk_config,
                "_verify_payload_identity",
                return_value="a" * 64,
            ) as verify,
            mock.patch.object(
                subject.risk_config,
                "_decode_verified_payload",
                return_value=config_text,
            ) as decode,
        ):
            result = subject.project_group1_risk_runtime_scalars(b"synthetic")

        verify.assert_called_once_with(b"synthetic", subject.GROUP1_SPEC)
        decode.assert_called_once_with(b"synthetic")
        self.assertEqual(result["repository_path"], subject.GROUP1_SPEC.repository_path)
        self.assertEqual(result["sha256"], "a" * 64)
        self.assertEqual(
            result["openquake_reference"]["commit_sha"], subject.OPENQUAKE_COMMIT
        )
        self.assertEqual(result["runtime_scalars"]["minimum_asset_loss_structural"], "0")
        self.assertFalse(result["raw_config_returned"])
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
                subject.project_group1_risk_runtime_scalars(b"wrong")
        decode.assert_not_called()


if __name__ == "__main__":
    unittest.main()
