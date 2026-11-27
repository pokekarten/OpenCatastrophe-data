# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-only and synthetic regression tests; never download source data."""
from __future__ import annotations

import copy
import tomllib
import unittest

from research_runners import swiss_crop_hail_verification_support_v0 as subject


class SwissHailVerificationSupportTests(unittest.TestCase):
    def test_paper_skill_contingency_metrics(self):
        values = subject.contingency_metrics(tp=2, fp=1, fn=1, tn=6)
        self.assertEqual((values["hits"], values["misses"]), (2, 1))
        self.assertAlmostEqual(values["pod"], 2 / 3, places=7)
        self.assertAlmostEqual(values["far"], 1 / 3, places=7)
        self.assertEqual(values["frequency_bias"], 1)
        self.assertEqual(values["critical_success_index"], 0.5)
        self.assertAlmostEqual(values["heidke_skill_score"], 22 / 42, places=7)

    def test_undefined_denominator_is_null_not_invented_zero(self):
        values = subject.contingency_metrics(0, 0, 0, 0)
        self.assertIsNone(values["pod"])
        self.assertIsNone(values["far"])
        self.assertIsNone(values["heidke_skill_score"])

    def test_reproduce_paper_scope_but_keep_missing_positives(self):
        # 3 crop-exposed cells (one hit, one false alarm, one correct negative);
        # 2 cells outside crop support, one with positive observed damage.
        x = subject.compare_verification_support(
            [True, True, False, False, False],
            [True, False, False, True, False],
            [True, True, True, False, False],
        )
        assert x["paper_conditional_support"] == subject.contingency_metrics(1, 1, 0, 1)
        assert x["diagnostic_counts_missing_positives_as_misses"] == subject.contingency_metrics(1, 1, 1, 1)
        self.assertEqual(x["outside_exposure_positive_observation_cells"], 1)
        self.assertEqual(x["outside_exposure_negative_observation_cells_not_scored"], 1)
        self.assertEqual(x["reference_exposure_cell_count"], 3)
        self.assertFalse(x["model_annual_frequency_admitted"])

    def test_cannot_claim_binary_crop_prediction_outside_crop_exposure(self):
        with self.assertRaisesRegex(subject.Blocked, "cannot predict"):
            subject.compare_verification_support([True, True], [False, True], [True, False])

    def test_forecast_mismatched_or_non_bool_or_empty_blocks(self):
        for a, b, c in [
            ([], [], []),
            ([True], [False, False], [True]),
            ([True], [1], [True]),
            ([True], [False], [0]),
        ]:
            with self.subTest(values=(a, b, c)):
                with self.assertRaises(subject.Blocked):
                    subject.compare_verification_support(a, b, c)
        with self.assertRaisesRegex(subject.Blocked, "no source crop exposure"):
            subject.compare_verification_support([False], [True], [False])

    def test_no_negative_noninteger_or_boolean_contingency(self):
        for bad in (-1, True, 3.5):
            with self.assertRaises(subject.Blocked):
                subject.contingency_metrics(bad, 0, 0, 0)

    def test_pinned_original_24_pair_source_proof(self):
        with subject.SOURCE_PROOF.open("rb") as handle:
            source = tomllib.load(handle)
        report = subject.source_proof_report(source)
        self.assertEqual(report["crop_resolution_pairs"], 24)
        self.assertEqual(report["fully_covered_pairs"], 19)
        self.assertEqual(report["outside_exposure_positions_across_pairs"], 1003)
        self.assertEqual(report["outside_exposure_positions_with_positive_impact_across_pairs"], 461)
        self.assertEqual(report["outside_exposure_positive_matrix_cells_across_pairs"], 550)
        self.assertEqual(report["observed_positive_matrix_cells_across_pairs"], 28674)
        self.assertAlmostEqual(report["fraction_of_observed_positive_cells_outside_source_exposure"],
                               550 / 28674, places=7)
        cases = {(d["crop"], d["resolution_km"]): d
                 for d in report["per_pair_coverage_only_not_skill"]}
        self.assertEqual(cases["maize", 2]["outside_2021_exposure_positive_impact_cells"], 247)
        self.assertEqual(cases["rapeseed", 2]["outside_2021_exposure_positive_impact_cells"], 133)
        self.assertEqual(cases["wheat", 2]["outside_2021_exposure_positive_impact_cells"], 170)
        self.assertFalse(report["paper_pod_far_hss_reproduced_from_original_hazard"])

    def test_tampered_research_receipts_or_admission_flag_block(self):
        with subject.SOURCE_PROOF.open("rb") as handle:
            original = tomllib.load(handle)
        for field, value in [
            ("positive_impact_matrix_entries_on_unmatched_positions", 549),
            ("full_damage_coordinate_coverage_pairs", 20),
            ("yearly_oep_aep_ready", True),
        ]:
            source = copy.deepcopy(original)
            source[field] = value
            with self.subTest(field=field):
                with self.assertRaises(subject.Blocked):
                    subject.source_proof_report(source)
        source = copy.deepcopy(original)
        source["crop_resolution"].pop()
        with self.assertRaises(subject.Blocked):
            subject.source_proof_report(source)

    def test_duplicate_crop_or_impossible_positive_counts_block(self):
        with subject.SOURCE_PROOF.open("rb") as handle:
            original = tomllib.load(handle)
        source = copy.deepcopy(original)
        source["crop_resolution"][0] = copy.deepcopy(source["crop_resolution"][1])
        with self.assertRaises(subject.Blocked):
            subject.source_proof_report(source)
        source = copy.deepcopy(original)
        source["crop_resolution"][1]["positive_impact_matrix_cells_on_unmatched_positions"] = 9999
        with self.assertRaises(subject.Blocked):
            subject.source_proof_report(source)


if __name__ == "__main__":
    unittest.main()
