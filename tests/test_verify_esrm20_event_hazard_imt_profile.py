# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import verify_esrm20_event_hazard_dependencies as subject


class EventHazardImtProfileTests(unittest.TestCase):
    def test_extracts_canonical_names_from_event_based_list(self) -> None:
        option, names = subject.extract_openquake_imt_names(
            "[calculation]\n"
            "intensity_measure_types = SA(1.0), PGA SA(0.3)\n"
        )
        self.assertEqual(option, "intensity_measure_types")
        self.assertEqual(names, ["PGA", "SA(0.3)", "SA(1.0)"])

    def test_extracts_only_mapping_keys_without_evaluating_levels(self) -> None:
        option, names = subject.extract_openquake_imt_names(
            "[calculation]\n"
            "intensity_measure_types_and_levels = "
            "{'SA(1.0)': logscale(0.01, 2, 20), "
            "'PGA': [0.1, 0.2], 'SA(0.3)': custom_unknown_expression(1)}\n"
        )
        self.assertEqual(option, "intensity_measure_types_and_levels")
        self.assertEqual(names, ["PGA", "SA(0.3)", "SA(1.0)"])

    def test_rejects_both_standard_imt_options(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "exactly one standard IMT option",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\n"
                "intensity_measure_types = PGA\n"
                "intensity_measure_types_and_levels = {'PGA': [0.1]}\n"
            )

    def test_rejects_duplicate_imt_names(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "contains duplicates",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\nintensity_measure_types = PGA, PGA\n"
            )

    def test_rejects_non_mapping_level_expression(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "is not a mapping",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\nintensity_measure_types_and_levels = ['PGA']\n"
            )

    def test_rejects_unsafe_mapping_key(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "not safely bounded",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\n"
                "intensity_measure_types_and_levels = {'PGA\\nunsafe': [0.1]}\n"
            )

    def test_verified_profile_fails_before_parsing_wrong_bytes(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "byte count mismatch",
        ):
            subject.extract_verified_event_hazard_imt_profile(
                1,
                b"[calculation]\nintensity_measure_types = PGA\n",
            )


if __name__ == "__main__":
    unittest.main()
