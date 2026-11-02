# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-source independent offline synthetic ACT/Overture IoU tests."""
import struct
import unittest
from shapely.geometry import Point, Polygon, box
from research_runners.luxembourg_act_overture_original_city_pair_v0 import (
    _gpkg_polygon, geometric_candidates, GeoBaseError, main
)


def square(x=77240, y=75040, size=10):
    return box(x, y, x+size, y+size)


def gpkg(geom):
    return b"GP" + bytes([0, 1]) + struct.pack("<i", 2169) + geom.wkb


class OriginalACTOvertureComparisonTests(unittest.TestCase):
    def test_original_gpkg_polygon_header(self):
        self.assertEqual(_gpkg_polygon(gpkg(square())).area, 100)

    def test_bad_original_crs_rejected(self):
        b = b"GP" + bytes([0, 1]) + struct.pack("<i", 4326) + square().wkb
        with self.assertRaises(GeoBaseError):
            _gpkg_polygon(b)

    def test_invalid_gpkg_magic_rejected(self):
        with self.assertRaises(GeoBaseError):
            _gpkg_polygon(b"ZZ" + gpkg(square())[2:])

    def test_equal_source_polygons_one_candidate(self):
        result = geometric_candidates([square()], [square()])
        self.assertEqual(result["reciprocal_one_to_one_geometric_candidates"], 1)
        self.assertEqual(result["overlap_pairs_above_iou_0_75"], 1)
        self.assertNotIn("77240", str(result))

    def test_40percent_geometric_shift_is_not_a_match(self):
        result = geometric_candidates([square()], [square(77244)])
        self.assertEqual(result["reciprocal_one_to_one_geometric_candidates"], 0)

    def test_best_iou_histogram_catches_partial_overlap(self):
        result = geometric_candidates([square()], [square(77244)])
        self.assertEqual(result["positive_area_original_source_overlap_pairs"], 1)
        self.assertEqual(
            result["Overture_best_geometric_iou_distribution"]["iou_0_25_to_0_50"], 1)
        self.assertEqual(
            result["Overture_best_geometric_iou_distribution"]["iou_at_least_0_75"], 0)

    def test_zero_overlap_histogram_is_distinct_from_low_iou(self):
        result = geometric_candidates([square()], [square(77300)])
        self.assertEqual(result["positive_area_original_source_overlap_pairs"], 0)
        self.assertEqual(
            result["Overture_best_geometric_iou_distribution"]["no_positive_area_overlap"], 1)

    def test_two_overture_same_act_is_quarantined(self):
        result = geometric_candidates([square()], [square(), square()])
        self.assertEqual(result["act_features_with_ambiguous_many_to_many_candidates"], 1)
        self.assertEqual(result["reciprocal_one_to_one_geometric_candidates"], 0)

    def test_two_act_same_overture_is_quarantined(self):
        result = geometric_candidates([square(), square()], [square()])
        self.assertEqual(result["act_features_with_ambiguous_many_to_many_candidates"], 2)
        self.assertEqual(result["reciprocal_one_to_one_geometric_candidates"], 0)

    def test_reciprocal_candidate_source_family_is_aggregated(self):
        result = geometric_candidates([square()], [square()],
            overture_source_families=["OpenStreetMap"])
        self.assertEqual(
            result["reciprocal_candidate_overture_source_family_counts"]["OpenStreetMap"], 1)
        self.assertEqual(
            result["reciprocal_candidate_overture_source_family_counts"]["Microsoft ML Buildings"], 0)

    def test_microsoft_label_can_be_attributed_without_source_ids(self):
        result = geometric_candidates([square()], [square()],
            overture_source_families=["Microsoft ML Buildings"])
        self.assertEqual(
            result["reciprocal_candidate_overture_source_family_counts"]["Microsoft ML Buildings"], 1)
        self.assertNotIn("record_id", str(result))

    def test_missing_parallel_source_family_is_rejected(self):
        with self.assertRaises(GeoBaseError):
            geometric_candidates([square()], [square()], overture_source_families=[])

    def test_boundary_touch_does_not_match(self):
        result = geometric_candidates([square()], [square(77250)])
        self.assertEqual(result["overlap_pairs_above_iou_0_75"], 0)

    def test_no_pair_on_empty_slices(self):
        result = geometric_candidates([], [])
        self.assertEqual(result["overlap_pairs_above_iou_0_75"], 0)

    def test_large_batch_fails_closed(self):
        with self.assertRaises(GeoBaseError):
            geometric_candidates([square()]*501, [square()])

    def test_invalid_act_and_overture_polygons_never_form_false_matches(self):
        # A self-intersecting original footprint must not be silently
        # repaired or dropped: dropping it might fake a reciprocal match.
        bowtie = Polygon([
            (77240, 75040), (77250, 75050), (77240, 75050),
            (77250, 75040), (77240, 75040)
        ])
        self.assertFalse(bowtie.is_valid)
        for act, overture in (([bowtie], [square()]),
                              ([square()], [bowtie])):
            with self.subTest(side="act" if act[0] is bowtie else "overture"):
                with self.assertRaises(GeoBaseError):
                    geometric_candidates(act, overture)

    def test_reject_nonpolygon_source_geometry_before_iou(self):
        for act, overture in (([Point(77240, 75040)], [square()]),
                              ([square()], [Point(77240, 75040)])):
            with self.assertRaisesRegex(GeoBaseError, "non-polygon"):
                geometric_candidates(act, overture)

    def test_reject_infinite_projected_area_on_either_source(self):
        unbounded = box(0, 0, 1e200, 1e200)
        self.assertFalse(__import__("math").isfinite(unbounded.area))
        for act, overture in (([unbounded], [square()]),
                              ([square()], [unbounded])):
            with self.assertRaisesRegex(GeoBaseError, "non-finite"):
                geometric_candidates(act, overture)

    def test_threshold_sensitivity_exposes_75_to_90_percent_instability(self):
        # Shift by 1m yields IoU 90/110 ~= .818: a 75% candidate
        # is NOT a 90% candidate and cannot be labelled 'certain'.
        out = geometric_candidates([square()], [square(77241)])
        sweep = out["geometric_threshold_sensitivity_research_only"]
        self.assertEqual(
            [sweep[k]["reciprocal_one_to_one_geometric_candidates"]
             for k in ("iou_0_50", "iou_0_75", "iou_0_90")],
            [1, 1, 0],
        )
        self.assertEqual(out["reciprocal_one_to_one_geometric_candidates"], 1)
        self.assertIs(out["threshold_sensitivity_is_identity_confidence"], False)
        self.assertNotIn("77241", str(out))

    def test_lower_cutoff_can_create_ambiguity_without_changing_frozen_75_gate(self):
        # An exact overlap plus a 3m-shifted polygon produce 2 qualifying
        # links at 50%, but only the original strict 75% link remains.
        out = geometric_candidates([square()], [square(), square(77243)])
        sweep = out["geometric_threshold_sensitivity_research_only"]
        self.assertEqual(sweep["iou_0_50"]["overlap_pairs_at_or_above_threshold"], 2)
        self.assertEqual(sweep["iou_0_50"]["reciprocal_one_to_one_geometric_candidates"], 0)
        self.assertEqual(sweep["iou_0_50"]["act_features_with_ambiguous_geometric_candidates"], 1)
        self.assertEqual(sweep["iou_0_75"]["reciprocal_one_to_one_geometric_candidates"], 1)
        self.assertEqual(sweep["iou_0_90"]["reciprocal_one_to_one_geometric_candidates"], 1)
        self.assertEqual(out["reciprocal_one_to_one_geometric_candidates"], 1)

    def test_exact_geometry_stays_reciprocal_at_all_three_thresholds(self):
        sweep = geometric_candidates([square()], [square()])[
            "geometric_threshold_sensitivity_research_only"
        ]
        for result in sweep.values():
            self.assertEqual(result["overlap_pairs_at_or_above_threshold"], 1)
            self.assertEqual(result["reciprocal_one_to_one_geometric_candidates"], 1)
            self.assertEqual(result["act_features_with_ambiguous_geometric_candidates"], 0)

    def test_default_has_no_source_access(self):
        self.assertEqual(main(["--source-zip", "/tmp/nonexistent-act-original.zip"]), 2)


if __name__ == "__main__":
    unittest.main()
