# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest

from research_runners import windstorm_europe_luisa_curve_mixture_sensitivity_v0 as model


class LuisaMixtureSensitivityTests(unittest.TestCase):
    def setUp(self):
        shares = {name: 0.0 for name in model.MATERIAL_COLUMNS}
        shares["weakest outbuilding"] = 0.5
        shares["outbuilding"] = 0.5
        curve_rows = []
        for speed in range(141):
            if speed <= 40:
                fraction = speed / 40
                weakest, regular, strong = 58 * fraction, 0.8 * fraction, 5.5 * fraction
            else:
                fraction = min((speed - 40) / 23, 1)
                weakest = 58 + 42 * fraction
                regular = 0.8 + 20.2 * fraction
                strong = 5.5 + 80.5 * fraction
            row = {name: 0.0 for name in model.CSV_COLUMNS}
            row.update({
                "wind speed": float(speed),
                "weakest outbuilding": weakest,
                "outbuilding": regular,
                "outbuilding strong": strong,
            })
            curve_rows.append(row)
        self.shares = shares
        self.result = model.compare({2110: {
            "description": "Non irrigated arable land",
            "shares": shares,
            "share_total": 1.0,
        }}, curve_rows)

    def test_full_source_grid_is_compared_under_both_mappings(self):
        self.assertEqual(self.result["class_count"], 1)
        self.assertEqual(self.result["wind_speed_knot_count"], 141)
        self.assertEqual(self.result["differing_class_count"], 1)
        self.assertEqual(
            self.result["global_maximum_difference"]["difference_pp"], 32.5
        )
        self.assertEqual(self.result["global_maximum_difference"]["wind_speed_m_s"], 63.0)

    def test_class_2110_total_mixture_includes_weakest_outbuilding(self):
        row = next(item for item in self.result["classes"] if item["landuse_code"] == 2110)
        self.assertEqual(row["regular_outbuilding_share"], 0.5)
        self.assertEqual(row["strong_outbuilding_share"], 0.0)
        self.assertAlmostEqual(row["semantic_percent_at_40m_s"], 29.4)
        self.assertAlmostEqual(row["legacy_percent_at_40m_s"], 31.75)
        self.assertAlmostEqual(row["difference_pp_at_40m_s"], -2.35)

    def test_strict_mapping_names_and_finite_loss_bounds(self):
        shares = {name: 0.0 for name in model.MATERIAL_COLUMNS}
        curves = {name: 0.0 for name in model.CSV_COLUMNS}
        shares["outbuilding"] = 0.5
        curves["outbuilding"] = 0.8
        curves["outbuilding strong"] = 5.5
        self.assertEqual(model.mix_one_curve(shares, curves, mapping="semantic_names"), 0.4)
        self.assertEqual(model.mix_one_curve(shares, curves, mapping="legacy_positional"), 2.75)
        with self.assertRaisesRegex(ValueError, "mapping must be"):
            model.mix_one_curve(shares, curves, mapping="guessed_alias")

    def test_material_share_labels_must_be_exact(self):
        with self.assertRaisesRegex(ValueError, "exactly match"):
            model.mix_one_curve({}, {}, mapping="semantic_names")


if __name__ == "__main__":
    unittest.main()
