# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic numerical contract tests; no original vulnerability bytes."""

import unittest

from research_runners.ci_curve_semantics_v0 import (
    CurveSemanticsError,
    validate_curve_semantics,
)


class CurveSemanticsTests(unittest.TestCase):
    def base(self, *, metric="fractional_damage_ratio", source_unit="mm", model_unit="mm", points=None):
        if points is None:
            points = [(0, 0), (500, 0.2), (1200, 0.7)]
        return validate_curve_semantics(
            source_curve_id="synthetic-F-001",
            asset_class="synthetic-power-substation",
            source_intensity_unit=source_unit,
            model_intensity_unit=model_unit,
            output_metric=metric,
            points=points,
        )

    def test_valid_fractional_damage_ratio(self):
        self.assertEqual(len(self.base()), 3)

    def test_valid_repair_rate_above_one(self):
        self.assertEqual(self.base(metric="repair_rate", points=[(0, 0), (100, 2.1)])[1][1], 2.1)

    def test_valid_pipe_repairs_per_km_above_one(self):
        self.assertEqual(self.base(metric="pipe_repairs_per_km", points=[(0, 0), (100, 3)])[1][1], 3)

    def test_reject_repair_rate_interpreted_as_fraction(self):
        with self.assertRaises(CurveSemanticsError):
            self.base(points=[(0, 0), (100, 2.1)])

    def test_reject_unit_mismatch_without_named_conversion(self):
        with self.assertRaises(CurveSemanticsError):
            self.base(source_unit="mm", model_unit="m")

    def test_reject_ambiguous_metric(self):
        with self.assertRaises(CurveSemanticsError):
            self.base(metric="damage_factor_or_repair_rate")

    def test_reject_out_of_order_duplicate_and_nonfinite(self):
        for bad in (
            [(100, 0), (100, 0.1)],
            [(100, 0), (50, 0.1)],
            [(100, float("nan"))],
            [(100, float("inf"))],
        ):
            with self.subTest(bad=repr(bad)), self.assertRaises(CurveSemanticsError):
                self.base(points=bad)

    def test_reject_negative_fraction_and_boolean(self):
        for bad in ([(0, -0.1)], [(0, True)], [(True, 0.2)]):
            with self.subTest(bad=repr(bad)), self.assertRaises(CurveSemanticsError):
                self.base(points=bad)

    def test_returns_explicit_immutable_tuple_without_interpolation(self):
        self.assertEqual(self.base(points=[(100, 0.3)]), ((100.0, 0.3),))


if __name__ == "__main__":
    unittest.main()
