# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts import verify_esrm20_event_hazard_dependencies as subject


class EventHazardImtProfileTests(unittest.TestCase):
    def test_extracts_canonical_names_from_event_based_list(self) -> None:
        option, names = subject.extract_openquake_imt_names(
            "[calculation]\n"
            "intensity_measure_types = SA(1.0), PGA, SA(0.3)\n"
        )
        self.assertEqual(option, "intensity_measure_types")
        self.assertEqual(names, ["PGA", "SA(0.3)", "SA(1.0)"])

    def test_normalizes_sa_period_like_frozen_openquake(self) -> None:
        option, names = subject.extract_openquake_imt_names(
            "[calculation]\n"
            "intensity_measure_types = PGA, SA(1.00), SA(0.30)\n"
        )
        self.assertEqual(option, "intensity_measure_types")
        self.assertEqual(names, ["PGA", "SA(0.3)", "SA(1.0)"])

    def test_rejects_duplicate_after_openquake_normalization(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "duplicates after OpenQuake normalization",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\nintensity_measure_types = SA(0.1), SA(0.10)\n"
            )

    def test_event_list_uses_openquake_comma_semantics(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "outside the bounded EQ1 PGA/SA subset",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\nintensity_measure_types = PGA SA(0.3)\n"
            )

    def test_extracts_only_mapping_keys_without_evaluating_levels(self) -> None:
        option, names = subject.extract_openquake_imt_names(
            "[calculation]\n"
            "intensity_measure_types_and_levels = "
            "{'SA(1.00)': logscale(0.01, 2, 20), "
            "'PGA': [0.1, 0.2], 'SA(0.30)': custom_unknown_expression(1)}\n"
        )
        self.assertEqual(option, "intensity_measure_types_and_levels")
        self.assertEqual(names, ["PGA", "SA(0.3)", "SA(1.0)"])

    def test_mapping_rejects_duplicate_after_normalization(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "duplicates after OpenQuake normalization",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\n"
                "intensity_measure_types_and_levels = "
                "{'SA(0.1)': [0.1], 'SA(0.10)': [0.2]}\n"
            )

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
            "duplicates after OpenQuake normalization",
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

    def test_rejects_unsupported_mapping_key(self) -> None:
        with self.assertRaisesRegex(
            subject.VerifiedEventHazardConfigError,
            "outside the bounded EQ1 PGA/SA subset",
        ):
            subject.extract_openquake_imt_names(
                "[calculation]\n"
                "intensity_measure_types_and_levels = {'PGV': [0.1]}\n"
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
