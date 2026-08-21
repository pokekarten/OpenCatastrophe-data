# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import configparser
import hashlib
import unittest
from unittest import mock

from scripts import build_esrm20_kosovo_residential_ebrisk_config as subject


def synthetic_group1() -> str:
    return """[general]
calculation_mode = ebrisk
random_seed = 113
ignore_master_seed = true
minimum_asset_loss = {'structural': 2000}

[logic_trees]
source_model_logic_tree_file = ../Hazard/source_model_logic_tree_eshm20_v12e_collapsed_risk_model.xml
gsim_logic_tree_file = ../Hazard/gmpe_logic_tree_5br_slope_geology.xml

[site_params]
site_model_file = ../Vs30/Site_model_Albania.xml
    ../Vs30/Site_model_Kosovo.xml

[exposure]
exposure_file = ../Exposure/OQ_Exposure_Input_Albania.xml
    ../Exposure/OQ_Exposure_Input_Kosovo.xml
taxonomy_mapping_csv = ../Vulnerability/esrm20_exposure_vulnerability_mapping.csv

[vulnerability]
occupants_vulnerability_file = ../Vulnerability/vulnerability_loss-of-life_ESRM20_VariousIM.xml
structural_vulnerability_file = ../Vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml
"""


class KosovoResidentialEbriskConfigTests(unittest.TestCase):
    def test_exact_identity_is_rejected_before_decode_or_parse(self) -> None:
        with (
            mock.patch.object(subject, "_decode_group1") as decode,
            self.assertRaisesRegex(
                subject.KosovoResidentialEbriskConfigError,
                "^source Group1 config byte identity mismatch$",
            ),
        ):
            subject.build_kosovo_residential_ebrisk_config(b"not Group1")
        decode.assert_not_called()

    def test_non_bytes_are_rejected_before_decode(self) -> None:
        with (
            mock.patch.object(subject, "_decode_group1") as decode,
            self.assertRaisesRegex(
                subject.KosovoResidentialEbriskConfigError,
                "^source Group1 config must be bytes$",
            ),
        ):
            subject._verify_group1_identity(bytearray(b"x"))  # type: ignore[arg-type]
        decode.assert_not_called()

    def test_verified_synthetic_config_changes_only_two_country_selectors(self) -> None:
        source = synthetic_group1()
        first, evidence = subject._derive_from_verified_text(source)
        second, repeated_evidence = subject._derive_from_verified_text(source)

        self.assertEqual(first, second)
        self.assertEqual(evidence, repeated_evidence)
        self.assertEqual(
            evidence["semantic_changes"],
            [
                {
                    "section": "exposure",
                    "option": "exposure_file",
                    "derived_value": (
                        "../Exposure/"
                        "OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml"
                    ),
                },
                {
                    "section": "site_params",
                    "option": "site_model_file",
                    "derived_value": "../Vs30/Site_model_Kosovo.xml",
                },
            ],
        )
        self.assertEqual(evidence["semantic_change_count"], 2)
        self.assertEqual(evidence["derived_dependency_count"], 7)
        self.assertIs(evidence["full_semantic_diff_verified"], True)
        self.assertIs(evidence["non_country_dependencies_preserved"], True)
        self.assertIs(evidence["runtime_settings_preserved"], True)
        self.assertEqual(evidence["output"]["byte_count"], len(first))
        self.assertEqual(
            evidence["output"]["sha256"],
            hashlib.sha256(first).hexdigest(),
        )
        text = first.decode("utf-8")
        self.assertNotIn("Albania.xml", text)
        self.assertIn(
            "exposure_file = "
            "../Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml",
            text,
        )
        self.assertIn(
            "site_model_file = ../Vs30/Site_model_Kosovo.xml",
            text,
        )

        dependencies = {
            (
                row["section"],
                row["option"],
                row["raw_path"],
                row["resolved_path"],
            )
            for row in evidence["derived_dependencies"]
        }
        self.assertIn(
            (
                "exposure",
                "exposure_file",
                "../Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml",
                "Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml",
            ),
            dependencies,
        )
        self.assertIn(
            (
                "site_params",
                "site_model_file",
                "../Vs30/Site_model_Kosovo.xml",
                "Vs30/Site_model_Kosovo.xml",
            ),
            dependencies,
        )
        for boundary in (
            "external_bytes_persisted",
            "historical_group_assignment_verified",
            "runtime_compatibility_verified",
            "vulnerability_horizontal_component_verified",
            "horizontal_component_conversion_authorized",
            "numerical_loss_reproduction_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(evidence[boundary], False)
        self.assertIs(evidence["derived_config_bytes_returned"], True)
        self.assertIs(evidence["source_config_bytes_returned"], False)

    def test_source_must_contain_exact_kosovo_pair(self) -> None:
        source = synthetic_group1().replace(
            "../Vs30/Site_model_Kosovo.xml",
            "../Vs30/Site_model_Italy.xml",
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialEbriskConfigError,
            "^source Group1 site selector does not contain Kosovo$",
        ):
            subject._derive_from_verified_text(source)

    def test_target_alias_or_default_is_rejected(self) -> None:
        alias = synthetic_group1().replace("site_model_file", "Site-Model-File", 1)
        with self.assertRaisesRegex(
            subject.KosovoResidentialEbriskConfigError,
            "^site_model_file alias/case drift is not allowed$",
        ):
            subject._derive_from_verified_text(alias)

        defaulted = (
            "[DEFAULT]\n"
            "site_model_file = ../Vs30/Site_model_Kosovo.xml\n\n"
            + synthetic_group1().replace(
                "site_model_file = ../Vs30/Site_model_Albania.xml\n"
                "    ../Vs30/Site_model_Kosovo.xml\n",
                "",
            )
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialEbriskConfigError,
            "^site_model_file must be an explicit canonical section option$",
        ):
            subject._derive_from_verified_text(defaulted)

    def test_target_duplicate_across_sections_is_rejected(self) -> None:
        source = synthetic_group1().replace(
            "[vulnerability]",
            "[extra]\nsite_model_file = ../Vs30/Site_model_Kosovo.xml\n\n"
            "[vulnerability]",
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialEbriskConfigError,
            "^site_model_file must appear exactly once as an explicit option$",
        ):
            subject._derive_from_verified_text(source)

    def test_shared_dependency_drift_fails_closed(self) -> None:
        source = synthetic_group1().replace(
            "../Hazard/gmpe_logic_tree_5br_slope_geology.xml",
            "../Hazard/other.xml",
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialEbriskConfigError,
            "^source Group1 shared dependency surface drifted$",
        ):
            subject._derive_from_verified_text(source)

    def test_third_option_change_after_serialization_fails_closed(self) -> None:
        original = subject._serialize_canonical

        def mutate(parser: configparser.ConfigParser) -> bytes:
            payload = original(parser)
            return payload.replace(b"random_seed = 113", b"random_seed = 114")

        with (
            mock.patch.object(subject, "_serialize_canonical", side_effect=mutate),
            self.assertRaisesRegex(
                subject.KosovoResidentialEbriskConfigError,
                "^derived config semantic diff is not exactly the two country selectors$",
            ),
        ):
            subject._derive_from_verified_text(synthetic_group1())

    def test_live_authority_drift_fails_before_identity(self) -> None:
        with (
            mock.patch.object(subject, "CONTROL_ISSUE", 999),
            mock.patch.object(subject, "_verify_group1_identity") as verify,
            self.assertRaisesRegex(
                subject.KosovoResidentialEbriskConfigError,
                "^control issue authority drifted$",
            ),
        ):
            subject.build_kosovo_residential_ebrisk_config(b"x")
        verify.assert_not_called()

    def test_upstream_wrapper_path_drift_fails_before_identity(self) -> None:
        with (
            mock.patch.object(
                subject.exposure_wrapper,
                "OUTPUT_LOGICAL_PATH",
                "Exposure/wrong.xml",
            ),
            mock.patch.object(subject, "_verify_group1_identity") as verify,
            self.assertRaisesRegex(
                subject.KosovoResidentialEbriskConfigError,
                "^residential wrapper output path authority drifted$",
            ),
        ):
            subject.build_kosovo_residential_ebrisk_config(b"x")
        verify.assert_not_called()

    def test_public_entry_verifies_identity_before_decode_and_derivation(self) -> None:
        source = b"x"
        with (
            mock.patch.object(subject, "_require_canonical_authority"),
            mock.patch.object(
                subject,
                "_verify_group1_identity",
                return_value="abc",
            ) as verify,
            mock.patch.object(
                subject,
                "_decode_group1",
                return_value=synthetic_group1(),
            ) as decode,
            mock.patch.object(
                subject,
                "_derive_from_verified_text",
                return_value=(b"derived", {}),
            ) as derive,
        ):
            self.assertEqual(
                subject.build_kosovo_residential_ebrisk_config(source),
                (b"derived", {}),
            )
        verify.assert_called_once_with(source)
        decode.assert_called_once_with(source)
        derive.assert_called_once_with(synthetic_group1(), source_digest="abc")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
