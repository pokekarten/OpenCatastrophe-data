# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline 10k synthetic hazard/curve/GUL parity vs separately pinned SQL receipts."""

import unittest
from decimal import Decimal

from research_runners.synthetic_ci_curve_catxl_bridge_v0 import (
    SyntheticCurveBridgeError,
    fictional_event_loss_cells,
)
from research_runners.synthetic_neon_10k_curve_gul_bridge_v0 import (
    ASSETS,
    TOY_HAZARD_UNIT,
    _percentile_disc,
    replay_synthetic_curve_10k,
    synthetic_curve_for_factor,
)

# Pinned published **fictional** read-only SQL validation-branch receipts.
# Equality demonstrates mathematical toy parity, not original dataset rights.
EXPECTED_RECEIPTS = {
    "annual": "6aebdda0c542f06a882ec16a4fcaa667",
    "event": "e0b6b2414c0a12459c47785a7de53777",
    "event_asset": "8cba885a6e1aab7d43e2fe1087fe0d95",
    "event_intensity": "2f11da6a6e1fb752cc410f50bfeffbc6",
}


class SyntheticNeon10kCurveGULTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = replay_synthetic_curve_10k()

    def test_all_four_sql_row_receipts_match_independently(self):
        self.assertEqual(self.result["receipts_md5"], EXPECTED_RECEIPTS)

    def test_10k_years_12_positions_and_exact_toy_event_counts(self):
        self.assertEqual(self.result["worlds"], 10_000)
        self.assertEqual(self.result["assets"], 12)
        self.assertEqual(self.result["invented_exposure_value_eur"], 3_150_000)
        self.assertEqual(self.result["events"], 1_541)
        self.assertEqual(self.result["zero_event_years"], 8_509)
        self.assertEqual(self.result["peril_event_counts"],
                         {"flood": 533, "windstorm": 1008})

    def test_exact_ground_up_annual_totals_and_peril_conservation(self):
        self.assertEqual(self.result["gross_loss_total_eur"], 285_494_000)
        self.assertEqual(self.result["aal_eur"], "28549.4")
        self.assertEqual(
            self.result["peril_loss_totals_eur"],
            {"flood": 97_473_000, "windstorm": 188_021_000},
        )
        self.assertEqual(
            sum(self.result["peril_loss_totals_eur"].values()),
            self.result["gross_loss_total_eur"],
        )

    def test_aep_oep_are_year_based_and_distinct(self):
        self.assertEqual((self.result["aep99_eur"], self.result["aep995_eur"]),
                         (342_500, 366_250))
        self.assertEqual((self.result["oep99_eur"], self.result["oep995_eur"]),
                         (333_750, 351_250))
        self.assertEqual(self.result["max_annual_eur"], 638_750)

    def test_more_than_one_peril_in_one_year_is_preserved(self):
        self.assertGreater(self.result["years_with_both_perils"], 0)
        self.assertEqual(
            self.result["events"],
            10_000 - self.result["zero_event_years"] + self.result["years_with_both_perils"],
        )

    def test_single_asset_curve_replaces_invented_multiplier_exactly(self):
        cells = fictional_event_loss_cells(
            positions_eur={"SYNTH-01": 125_000},
            intensities={"SYNTH-01": 3},
            curve_points=synthetic_curve_for_factor(2),
            source_curve_id="SYNTH-NEON-GUL-FACTOR-2",
            asset_class="SYNTH-GENERIC-PROPERTY",
            curve_unit=TOY_HAZARD_UNIT,
            event_unit=TOY_HAZARD_UNIT,
            output_metric="fractional_damage_ratio",
        )
        self.assertEqual(cells, {"SYNTH-01": 7_500})
        self.assertEqual(synthetic_curve_for_factor(3)[1][1], Decimal("0.15"))

    def test_unsupported_curve_factor_fails(self):
        for value in (0, 4, True, 1.0, "1", -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                synthetic_curve_for_factor(value)

    def test_reject_repair_output_and_wrong_intensity_unit(self):
        common = dict(
            positions_eur={"SYNTH-01": 125_000},
            intensities={"SYNTH-01": 3},
            curve_points=synthetic_curve_for_factor(2),
            source_curve_id="SYNTH-NEON-GUL-FACTOR-2",
            asset_class="SYNTH-GENERIC-PROPERTY",
            curve_unit=TOY_HAZARD_UNIT,
            event_unit=TOY_HAZARD_UNIT,
            output_metric="fractional_damage_ratio",
        )
        for field, value in (("output_metric", "repair_rate"), ("event_unit", "mm")):
            with self.subTest(field=field), self.assertRaises(SyntheticCurveBridgeError):
                fictional_event_loss_cells(**{**common, field: value})

    def test_percentile_disc_matches_sql_discrete_rank(self):
        self.assertEqual(_percentile_disc([10, 30, 20, 40], 1, 2), 20)
        self.assertEqual(_percentile_disc([10, 30, 20, 40], 1, 1), 40)
        for args in (([], 1, 2), ([1], 0, 1), ([1], 2, 1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                _percentile_disc(*args)

    def test_no_source_admission_or_treaty_result_claim(self):
        result = self.result
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["real_insurer"])
        self.assertFalse(result["real_hazard_or_vulnerability"])
        self.assertFalse(result["neon_query_executed"])
        self.assertFalse(result["treaty_or_retro_executed"])
        self.assertEqual(result["external_source_rows_used"], 0)
        self.assertEqual(len(ASSETS), len(set(k for k, _ in ASSETS)))


if __name__ == "__main__":
    unittest.main()
