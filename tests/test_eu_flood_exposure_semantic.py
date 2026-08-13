# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import eu_flood_exposure_semantic as mod


class FloodExposureSemanticTests(unittest.TestCase):
    def s(self, name, fraction, depth=None, **flags):
        return mod.HazardSupport(name, fraction, depth, **flags)

    def c(self, name, population, aoi, *supports):
        return mod.CensusCell(name, population, aoi, supports)

    def test_depth_boundaries(self):
        self.assertEqual(mod.classify_depth("0"), "dry_unexposed")
        self.assertEqual(mod.classify_depth("1"), "depth_gt_0_le_1m")
        self.assertEqual(mod.classify_depth("3"), "depth_gt_1_le_3m")
        self.assertEqual(mod.classify_depth("10"), "depth_gt_3_le_10m")
        self.assertEqual(mod.classify_depth("10.1"), "depth_gt_10m")

    def test_population_conservation_and_quality_buckets(self):
        result = mod.aggregate_cells([
            self.c(
                "A", "100", "0.8",
                self.s("wet", "0.2", "2"),
                self.s("nodata", "0.1", nodata=True),
                self.s("water", "0.1", permanent_water=True),
                self.s("spurious", "0.1", spurious_depth=True),
            )
        ])
        row = result["cells"][0]
        keys = (
            "dry_unexposed", "depth_gt_0_le_1m", "depth_gt_1_le_3m",
            "depth_gt_3_le_10m", "depth_gt_10m", "permanent_water_context",
            "spurious_depth_context", "nodata_unclassified", "hazard_support_missing",
            "excluded_by_aoi",
        )
        self.assertEqual(sum(Decimal(row[key]) for key in keys), Decimal("100"))
        self.assertEqual(row["dry_unexposed"], "0")
        self.assertEqual(row["hazard_support_missing"], "30")
        self.assertEqual(row["nodata_unclassified"], "10")

    def test_incomplete_support_is_not_dry(self):
        result = mod.aggregate_cells([
            self.c("A", "10", "1", self.s("wet", "0.4", "2"))
        ])
        row = result["cells"][0]
        self.assertEqual(row["dry_unexposed"], "0")
        self.assertEqual(row["hazard_support_missing"], "6")
        self.assertEqual(row["depth_gt_1_le_3m"], "4")

    def test_zero_and_nodata_remain_distinct(self):
        result = mod.aggregate_cells([
            self.c("A", "10", "1", self.s("dry", "0.5", "0"), self.s("missing", "0.5", nodata=True))
        ])
        row = result["cells"][0]
        self.assertEqual(row["dry_unexposed"], "5")
        self.assertEqual(row["nodata_unclassified"], "5")
        self.assertEqual(row["hazard_support_missing"], "0")

    def test_ambiguous_or_invalid_support_fails(self):
        cases = [
            self.c("A", "10", "0.5", self.s("x", "0.3", "1"), self.s("y", "0.3", "2")),
            self.c("A", "10", "1", self.s("x", "1", nodata=True, permanent_water=True)),
            self.c("A", "-1", "1"),
            self.c("A", "1", "NaN"),
        ]
        for cell in cases:
            with self.assertRaises(mod.SemanticError):
                mod.aggregate_cells([cell])

    def test_order_invariant_and_fixture_labelled(self):
        a = self.c("B", "20", "1", self.s("b2", "0.5", "4"), self.s("b1", "0.5", "0"))
        b = self.c("A", "10", "1", self.s("a1", "1", "11"))
        first = mod.aggregate_cells([a, b])
        second = mod.aggregate_cells([
            b,
            self.c("B", "20", "1", self.s("b1", "0.5", "0"), self.s("b2", "0.5", "4")),
        ])
        self.assertEqual(mod.canonical_json(first), mod.canonical_json(second))
        self.assertEqual(first["input_kind"], "fixture")
        self.assertEqual(first["scientific_role"], "test_fixture")


if __name__ == "__main__":
    unittest.main()
