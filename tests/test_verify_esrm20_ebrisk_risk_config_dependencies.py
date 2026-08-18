# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.verify_esrm20_ebrisk_risk_config_dependencies import (
    CONFIG_SPECS,
    RECEIPT_COMMENT_ID,
    VerifiedEbriskConfigError,
    _verify_payload_identity,
    config_spec,
    extract_dependencies_from_verified_text,
)


class EbriskReceiptBoundVerifierTests(unittest.TestCase):
    def test_frozen_specs_match_trusted_main_receipts(self) -> None:
        self.assertEqual(RECEIPT_COMMENT_ID, 5328119673)
        self.assertEqual(
            [(s.key, s.repository_path, s.byte_count, s.sha256) for s in CONFIG_SPECS],
            [
                (
                    "group1",
                    "Configuration_files/config_ebrisk_Group1.ini",
                    3052,
                    "be5f787954ca7e4060e4362d12efcf7cba5e50740930f3de7d7a521ebc580146",
                ),
                (
                    "group2",
                    "Configuration_files/config_ebrisk_Group2.ini",
                    2832,
                    "80cf566003cdb5e12dde820d5cba3db8ea5a6ba2db31e7089f3453f921852625",
                ),
                (
                    "iceland",
                    "Configuration_files/config_ebrisk_Iceland.ini",
                    1345,
                    "7d1f23170462a4f1b6b514518d4d35564a0ec2255072f6df38e5a5c6518b849c",
                ),
            ],
        )

    def test_unknown_candidate_fails_closed(self) -> None:
        with self.assertRaises(VerifiedEbriskConfigError):
            config_spec("kosovo")

    def test_identity_check_rejects_wrong_bytes_before_parsing(self) -> None:
        spec = config_spec("group1")
        with self.assertRaisesRegex(VerifiedEbriskConfigError, "byte count mismatch"):
            _verify_payload_identity(b"[general]\n", spec)

    def test_reviewed_parser_extracts_only_first_order_file_dependencies(self) -> None:
        dependencies = extract_dependencies_from_verified_text(
            """
[general]
calculation_mode = scenario_damage

[input]
exposure_file = ../Exposure/exposure_model.xml
structural_vulnerability_file = ../Vulnerability/structural.xml
ordinary_setting = not-a-file
""",
            repository_path="Configuration_files/config_ebrisk_Group1.ini",
        )
        self.assertEqual(
            [(row["option"], row["resolved_path"]) for row in dependencies],
            [
                ("exposure_file", "Exposure/exposure_model.xml"),
                ("structural_vulnerability_file", "Vulnerability/structural.xml"),
            ],
        )

    def test_repository_escape_from_verified_config_is_rejected(self) -> None:
        with self.assertRaises(VerifiedEbriskConfigError):
            extract_dependencies_from_verified_text(
                "[input]\nexposure_file = ../../outside.xml\n",
                repository_path="Configuration_files/config_ebrisk_Group1.ini",
            )


if __name__ == "__main__":
    unittest.main()
