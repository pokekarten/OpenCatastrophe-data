# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from decimal import Decimal

from research_runners import esrm20_aalr_shared_denominator_challenge as subject


def _row(index: int, *, shared: bool = False) -> dict[str, str]:
    return {
        "Name": f"Synthetic Country {index}",
        subject.AAL_COLUMNS[0]: "1",
        subject.AAL_COLUMNS[1]: "1",
        subject.AAL_COLUMNS[2]: "2",
        subject.AAL_COLUMNS[3]: "4",
        subject.AALR_COLUMNS[0]: "10.00",
        subject.AALR_COLUMNS[1]: "20.00",
        subject.AALR_COLUMNS[2]: "30.00",
        subject.AALR_COLUMNS[3]: "60.00" if shared else "22.00",
    }


class SharedDenominatorChallengeTests(unittest.TestCase):
    def test_all_rows_falsify_shared_denominator_under_rounding(self):
        rows = [_row(i) for i in range(subject.EXPECTED_ROWS)]
        result = subject.analyze_rows(rows)
        self.assertEqual(result["rows_analyzed"], subject.EXPECTED_ROWS)
        self.assertEqual(result["absolute_aal_additive_under_display_rounding"], 44)
        self.assertEqual(result["shared_denominator_sum_incompatible_under_display_rounding"], 44)
        self.assertEqual(result["shared_denominator_sum_compatible_under_display_rounding"], 0)
        self.assertTrue(result["shared_all_occupancy_denominator_hypothesis_rejected"])
        self.assertEqual(result["total_aalr_within_occupancy_range_under_rounding"], 44)
        self.assertEqual(result["total_aalr_outside_occupancy_range_under_rounding"], 0)
        self.assertEqual(
            result["implied_occupancy_replacement_costs_additive_under_rounding"], 44
        )
        self.assertEqual(
            result["implied_occupancy_replacement_costs_nonadditive_under_rounding"], 0
        )
        self.assertEqual(result["implied_occupancy_replacement_costs_unassessable"], 0)
        self.assertTrue(result["costs_from_aal_divided_by_aalr_are_hypothetical"])
        self.assertEqual(
            result["conclusion"],
            "SHARED_DENOMINATOR_NECESSARY_CONDITION_FALSIFIED_UNDER_ROUNDING",
        )
        for key in (
            "occupancy_specific_denominator_verified",
            "implied_costs_are_provider_verified",
            "provider_rounding_rule_verified",
            "provider_numeric_values_returned",
            "provider_rows_returned",
            "external_bytes_persisted",
            "reference_loss_agreement_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[key], False, key)
        encoded = json.dumps(result)
        self.assertNotIn("Synthetic Country", encoded)
        self.assertNotIn('"22.00"', encoded)

    def test_all_shared_denominator_components_are_compatible(self):
        rows = [_row(i, shared=True) for i in range(subject.EXPECTED_ROWS)]
        result = subject.analyze_rows(rows)
        self.assertFalse(result["shared_all_occupancy_denominator_hypothesis_rejected"])
        self.assertEqual(result["shared_denominator_sum_compatible_under_display_rounding"], 44)
        self.assertEqual(result["total_aalr_outside_occupancy_range_under_rounding"], 44)
        self.assertEqual(
            result["implied_occupancy_replacement_costs_nonadditive_under_rounding"], 44
        )

    def test_absolute_aal_nonadditivity_does_not_reject_denominator(self):
        rows = [_row(i, shared=True) for i in range(subject.EXPECTED_ROWS)]
        for row in rows:
            row[subject.AAL_COLUMNS[-1]] = "100"
            row[subject.AALR_COLUMNS[-1]] = "22.00"
        result = subject.analyze_rows(rows)
        self.assertEqual(result["absolute_aal_not_additive_under_display_rounding"], 44)
        self.assertEqual(result["shared_denominator_sum_incompatible_under_display_rounding"], 0)
        self.assertFalse(result["shared_all_occupancy_denominator_hypothesis_rejected"])

    def test_exact_positive_cost_denominators_recover_additive_portfolio(self):
        aal = tuple(subject._interval(x) for x in ("1.000", "1.000", "2.000", "4.000"))
        ratios = tuple(
            subject._interval(x) for x in ("10.000", "20.000", "30.000", "18.462")
        )
        self.assertTrue(subject._total_within_occupancy_ratio_range(ratios))
        self.assertIs(subject._cost_denominators_compatible(aal, ratios), True)
        self.assertIsInstance(
            subject._replacement_cost_interval(aal[0], ratios[0])[0], Decimal
        )

    def test_cost_sum_fails_for_inconsistent_total_ratio(self):
        aal = tuple(subject._interval(x) for x in ("1.000", "1.000", "2.000", "4.000"))
        ratios = tuple(
            subject._interval(x) for x in ("10.000", "20.000", "30.000", "50.000")
        )
        self.assertFalse(subject._total_within_occupancy_ratio_range(ratios))
        self.assertIs(subject._cost_denominators_compatible(aal, ratios), False)

    def test_zero_ratio_is_unassessable_not_falsified(self):
        rows = [_row(i) for i in range(subject.EXPECTED_ROWS)]
        for row in rows:
            row[subject.AALR_COLUMNS[0]] = "0.000"
        result = subject.analyze_rows(rows)
        self.assertEqual(result["implied_occupancy_replacement_costs_unassessable"], 44)
        self.assertEqual(result["implied_occupancy_replacement_costs_nonadditive_under_rounding"], 0)
        self.assertIsNone(
            subject._replacement_cost_interval(
                subject._interval("1.000"), subject._interval("0.000")
            )
        )

    def test_scientific_notation_preserves_half_display_unit(self):
        self.assertEqual(subject._interval("1E+3"), (Decimal("5E+2"), Decimal("1.5E+3")))
        self.assertEqual(subject._interval("1000"), (Decimal("999.5"), Decimal("1000.5")))
        self.assertEqual(subject._interval("1.00"), (Decimal("0.995"), Decimal("1.005")))

    def test_rounding_interval_overlap_is_not_false_rejection(self):
        parts = tuple(subject._interval("1.0") for _ in range(3))
        self.assertTrue(subject._intervals_overlap(parts, subject._interval("3.1")))
        self.assertFalse(subject._intervals_overlap(parts, subject._interval("4.0")))

    def test_row_count_and_identity_drift_fails_closed(self):
        rows = [_row(i) for i in range(subject.EXPECTED_ROWS)]
        with self.assertRaisesRegex(subject.SharedDenominatorChallengeError, "row count"):
            subject.analyze_rows(rows[:-1])
        rows[-1]["Name"] = rows[0]["Name"]
        with self.assertRaisesRegex(subject.SharedDenominatorChallengeError, "duplicated"):
            subject.analyze_rows(rows)

    def test_nonfinite_negative_padded_and_unbounded_values_fail(self):
        for literal in ("-1", "NaN", "Infinity", " 1.0 ", "1" * 90, "1e+60", ""):
            with self.subTest(literal=literal):
                with self.assertRaises(subject.SharedDenominatorChallengeError):
                    subject._interval(literal)

    def test_untrusted_frozen_bytes_rejected_before_any_value_interpretation(self):
        with self.assertRaisesRegex(subject.SharedDenominatorChallengeError, "identity"):
            subject.analyze_frozen_bytes(
                b"Name,AAL\nSynthetic,1\n",
                {
                    "project_id": 269,
                    "commit_sha": "0" * 40,
                    "sha256": "0" * 64,
                },
            )

    def test_one_occupancy_sum_rejection_is_not_independent_model_validation(self):
        rows = [_row(i, shared=True) for i in range(subject.EXPECTED_ROWS)]
        rows[0][subject.AALR_COLUMNS[-1]] = "22.00"
        result = subject.analyze_rows(rows)
        self.assertEqual(result["shared_denominator_sum_incompatible_under_display_rounding"], 1)
        self.assertTrue(result["shared_all_occupancy_denominator_hypothesis_rejected"])
        self.assertFalse(result["reference_loss_agreement_verified"])


if __name__ == "__main__":
    unittest.main()
