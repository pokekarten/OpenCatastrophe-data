# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Dependency-free synthetic tests of source polygon overlap decision semantics."""
from __future__ import annotations

import math
import unittest

from research_runners.materialcities_bkg_gadm_geometry_overlap_v0 import (
    GeometryOverlapError,
    MANUAL_REVIEW_IOU_THRESHOLD,
    overlap_metrics,
    summarize_scores,
    validate_bkg_geofactors,
    compare_land_water_scores,
    audit_manual_case_inventory,
    directed_neighbor_support,
    ORIGINAL_GF4_REVIEW_AGS,
)


def example_scores():
    source = {
        "01001": overlap_metrics(100.0, 98.0, 97.0),
        "03159": overlap_metrics(100.0, 100.0, 99.9),
        "16063": overlap_metrics(100.0, 101.0, 99.0),
        "16054": overlap_metrics(100.0, 70.0, 69.8),
        "09162": overlap_metrics(100.0, 100.0, 99.7),
    }
    return source


class SourceGeometryResearchGateTests(unittest.TestCase):
    def test_same_polygon_is_100pct_iou(self):
        x = overlap_metrics(100.0, 100.0, 100.0)
        self.assertEqual(x["iou"], 1.0)
        self.assertEqual(x["official_bkg_covered_fraction"], 1.0)
        self.assertEqual(x["gadm_covered_fraction"], 1.0)
        self.assertEqual(x["area_difference_gadm_minus_bkg_km2"], 0.0)

    def test_disjoint_polygon_is_zero_overlap_not_fake_match(self):
        x = overlap_metrics(100.0, 100.0, 0.0)
        self.assertEqual(x["iou"], 0.0)
        self.assertEqual(x["official_bkg_covered_fraction"], 0.0)

    def test_coverage_directions_are_not_interchangeable(self):
        x = overlap_metrics(100.0, 75.0, 75.0)
        self.assertAlmostEqual(x["iou"], 0.75)
        self.assertAlmostEqual(x["official_bkg_covered_fraction"], 0.75)
        self.assertAlmostEqual(x["gadm_covered_fraction"], 1.0)

    def test_imbalanced_source_areas_are_flaggable(self):
        x = overlap_metrics(142.0, 103.0, 101.0)
        self.assertLess(x["iou"], MANUAL_REVIEW_IOU_THRESHOLD)
        self.assertLess(x["official_bkg_covered_fraction"], 0.75)

    def test_empty_or_negative_area_rejected(self):
        for values in ((0, 1, 0), (1, 0, 0), (-1, 1, 0), (1, -1, 0), (1, 1, -1)):
            with self.subTest(values=values), self.assertRaises(GeometryOverlapError):
                overlap_metrics(*values)

    def test_source_nan_or_infinity_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaisesRegex(GeometryOverlapError, "finite"):
                overlap_metrics(value, 1, 0)

    def test_fake_intersection_larger_than_source_rejected(self):
        with self.assertRaisesRegex(GeometryOverlapError, "larger"):
            overlap_metrics(100, 80, 90)

    def test_floating_inputs_only(self):
        with self.assertRaisesRegex(GeometryOverlapError, "finite"):
            overlap_metrics("100", 80, 50)
        with self.assertRaisesRegex(GeometryOverlapError, "finite"):
            overlap_metrics(True, 80, 50)

    def test_summary_retains_manual_review_and_research_no_go(self):
        r = summarize_scores(example_scores(), exact_original=False)
        self.assertEqual(r["unique_2022_ags_with_geometry_compared"], 5)
        self.assertEqual(r["count_manual_review_iou_below_0_95"], 1)
        self.assertEqual(r["manual_review_AGS_source_keys"], ["16054"])
        self.assertEqual(r["count_iou_at_least_0_95"], 4)
        self.assertEqual(r["worst_ags"], "16054")
        self.assertIn("03159", r["source_identity_exceptions_focus"])
        self.assertIn("16063", r["source_identity_exceptions_focus"])
        self.assertTrue(r["research_only"])
        for key in ("full_per_region_geometry_exported",
                    "bkg_gadm_area_join_suitable_for_rva_exposure",
                    "gadm_redistribution_or_commercial_rights_granted",
                    "materialcities_gfa_reallocated",
                    "zensus_2022_2025_insurer_vintage_equivalence_proven",
                    "actual_insured_building_geocoding_proven",
                    "cat_model_input_admitted"):
            self.assertFalse(r[key])

    def test_missing_400_count_fails_original_gate(self):
        with self.assertRaisesRegex(GeometryOverlapError, "400-Kreis"):
            summarize_scores(example_scores())

    def test_original_400_count_still_requires_all_research_focus_regions(self):
        toy = {f"{i:05d}": overlap_metrics(100, 100, 100) for i in range(400)}
        with self.assertRaisesRegex(GeometryOverlapError, "original 400-Kreis"):
            summarize_scores(toy)

    def test_corrupt_iou_fraction_is_blocked(self):
        scores = example_scores()
        scores["16054"]["iou"] = float("nan")
        with self.assertRaisesRegex(GeometryOverlapError, "invalid geometry IoU"):
            summarize_scores(scores, exact_original=False)

    def test_empty_source_scores_blocked(self):
        with self.assertRaisesRegex(GeometryOverlapError, "complete AGS"):
            summarize_scores({}, exact_original=False)

    def test_geographic_area_units_are_explicit_m2_to_km2(self):
        x = overlap_metrics(2_000_000, 2_000_000, 1_500_000)
        self.assertEqual(x["bkg_area_km2"], 2.0)
        self.assertAlmostEqual(x["iou"], 0.6)

    def test_precision_tolerance_keeps_iou_in_unit_interval(self):
        x = overlap_metrics(100, 100, 100 + 1e-7)
        self.assertLessEqual(x["iou"], 1.0)


class BKGExactLandMarineSemanticsTests(unittest.TestCase):
    def test_only_gf4_is_land_and_gf2_is_separate_marine(self):
        inventory = {"01001": [4, 2], "01002": [4, 2, 2], "16054": [4]}
        result = validate_bkg_geofactors(inventory, exact_original=False)
        self.assertEqual(result["source_GF4_land_shape_records"], 3)
        self.assertEqual(result["source_GF2_coastal_or_lake_shape_records"], 3)
        self.assertEqual(result["official_AGS_with_GF2_marine_parts"], 2)
        self.assertTrue(result["each_official_AGS_has_one_GF4_land_geometry"])
        self.assertTrue(result["GF2_marine_excluded_from_building_land_comparison"])

    def test_two_land_geometries_for_one_ags_block(self):
        with self.assertRaisesRegex(GeometryOverlapError, "exactly one GF=4"):
            validate_bkg_geofactors({"01001": [4, 4]}, exact_original=False)

    def test_marine_only_without_land_never_substitutes_for_building_land(self):
        with self.assertRaisesRegex(GeometryOverlapError, "exactly one GF=4"):
            validate_bkg_geofactors({"01001": [2]}, exact_original=False)

    def test_unknown_GF_and_implicit_bool_are_blocked(self):
        for value in (3, 1, 9, True, "4"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(GeometryOverlapError, "documented 2/4"):
                    validate_bkg_geofactors({"01001": [4, value]}, exact_original=False)

    def test_wrong_original_GFs_are_blocked_even_when_all_AGSes_exist(self):
        fake = {f"{i:05d}": [4] for i in range(400)}
        with self.assertRaisesRegex(GeometryOverlapError, "land/marine profile changed"):
            validate_bkg_geofactors(fake)

    def test_land_water_threshold_change_and_non_admission(self):
        # Wholly fabricated polygon areas; the official GF distinction is the
        # research purpose, not a claim about actual Flensburg or Suhl shapes.
        land = {
            "01001": overlap_metrics(100.0, 100.0, 99.0),
            "16054": overlap_metrics(100.0, 100.0, 75.0),
        }
        all_surfaces = {
            "01001": overlap_metrics(110.0, 100.0, 98.0),
            "16054": overlap_metrics(100.0, 100.0, 75.0),
        }
        diagnostic = compare_land_water_scores(land, all_surfaces)
        self.assertEqual(diagnostic["previous_all_BKG_pieces_to_GF4_land_only_passes"], 1)
        self.assertEqual(diagnostic["previous_all_BKG_pieces_to_GF4_land_only_fails"], 0)
        self.assertTrue(diagnostic["neither_mode_establishes_spatial_exposure_admission"])

    def test_mismatched_mode_source_rosters_block(self):
        with self.assertRaisesRegex(GeometryOverlapError, "geographic cohorts"):
            compare_land_water_scores(
                {"16054": overlap_metrics(100.0, 100.0, 90.0)},
                {"01001": overlap_metrics(100.0, 100.0, 90.0)})

    def test_invalid_diagnostic_score_is_never_allowed(self):
        land = {"01001": {"iou": float("nan")}}
        all_surfaces = {"01001": {"iou": 0.5}}
        with self.assertRaisesRegex(GeometryOverlapError, "invalid land/water"):
            compare_land_water_scores(land, all_surfaces)


class NineOriginalSourceCaseReviews(unittest.TestCase):
    def _synthetic_two_counties(self):
        land = {
            "01054": overlap_metrics(100, 100, 90),
            "16054": overlap_metrics(200, 160, 140),
        }
        all_shapes = {
            "01054": overlap_metrics(130, 100, 97),
            "16054": land["16054"],
        }
        gf = {"01054": [4, 2], "16054": [4]}
        water = {"01054": 30.0}
        return land, all_shapes, gf, water

    def test_nine_original_ags_are_version_pinned(self):
        self.assertEqual(ORIGINAL_GF4_REVIEW_AGS, (
            "01054", "03405", "04012", "08335", "13003", "13075",
            "16054", "16070", "16072"))

    def test_only_manual_review_cases_and_rights_no_go(self):
        land, all_shapes, gf, water = self._synthetic_two_counties()
        result = audit_manual_case_inventory(
            land, all_shapes, gf, water, exact_original=False)
        self.assertEqual(result["review_case_count"], 2)
        self.assertEqual(result["review_case_AGS"], ["01054", "16054"])
        self.assertFalse(result["full_400_AGS_source_geometry_table_exported"])
        self.assertTrue(result["scientific_vintage_and_rights_review_pending"])
        coast = result["manual_review_case_diagnostics"]["01054"]
        thuringia = result["manual_review_case_diagnostics"]["16054"]
        self.assertEqual(coast["bkg_GF2_water_shape_count"], 1)
        self.assertAlmostEqual(coast["bkg_GF2_water_area_km2"], 0.00003)
        self.assertEqual(coast["research_bucket_not_a_causal_conclusion"],
                         "coastal_boundary_or_water_semantics_unresolved")
        self.assertEqual(thuringia["research_bucket_not_a_causal_conclusion"],
                         "thuringia_2019_boundary_vintage_hypothesis")
        self.assertTrue(coast["manual_review_required"])
        self.assertFalse(coast["land_or_insurer_model_admission"])
        self.assertFalse(thuringia["land_or_insurer_model_admission"])

    def test_no_whole_400_region_geometry_table(self):
        land, all_shapes, gf, water = self._synthetic_two_counties()
        land["01001"] = overlap_metrics(100, 100, 100)
        all_shapes["01001"] = land["01001"]
        gf["01001"] = [4]
        result = audit_manual_case_inventory(
            land, all_shapes, gf, water, exact_original=False)
        self.assertEqual(result["review_case_AGS"], ["01054", "16054"])
        self.assertNotIn("01001", result["manual_review_case_diagnostics"])

    def test_exact_source_nine_case_inventory_refuses_synthetic(self):
        with self.assertRaisesRegex(GeometryOverlapError, "nine-case"):
            audit_manual_case_inventory(*self._synthetic_two_counties())

    def test_different_geo_source_keysets_refused(self):
        land, all_shapes, gf, water = self._synthetic_two_counties()
        gf.pop("16054")
        with self.assertRaisesRegex(GeometryOverlapError, "cohorts"):
            audit_manual_case_inventory(
                land, all_shapes, gf, water, exact_original=False)

    def test_GF2_marine_area_value_and_record_count_must_agree(self):
        land, all_shapes, gf, water = self._synthetic_two_counties()
        water["01054"] = 0.0
        with self.assertRaisesRegex(GeometryOverlapError, "area/count mismatch"):
            audit_manual_case_inventory(
                land, all_shapes, gf, water, exact_original=False)

    def test_invalid_GF2_source_record_and_wrong_marker(self):
        land, all_shapes, gf, water = self._synthetic_two_counties()
        gf["01054"] = [4, 3]
        with self.assertRaisesRegex(GeometryOverlapError, "source record"):
            audit_manual_case_inventory(
                land, all_shapes, gf, water, exact_original=False)

    def test_nonfinite_or_negative_GF2_area_rejected(self):
        for value in (float("nan"), float("inf"), -1):
            land, all_shapes, gf, water = self._synthetic_two_counties()
            water["01054"] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(GeometryOverlapError, "source-marine"):
                    audit_manual_case_inventory(
                        land, all_shapes, gf, water, exact_original=False)

    def test_independent_thuringia_neighbor_overlap_fraction(self):
        r = directed_neighbor_support(40_000_000.0, 38_000_000.0)
        self.assertEqual(r["source_exclusive_area_km2"], 40.0)
        self.assertEqual(r["other_source_neighbor_cover_km2"], 38.0)
        self.assertAlmostEqual(r["neighbor_covers_source_exclusive_fraction"], .95)
        for key in ("historical_vintage_transfer_proven",
                    "municipality_geometry_identity_proven",
                    "building_area_transfer_authorized"):
            self.assertFalse(r[key])

    def test_neighbor_fraction_never_accepts_impossible_support(self):
        for a,b in ((0,0), (1,2), (-1,0), (1,-1),
                    (float("nan"),0), (float("inf"),0)):
            with self.subTest(a=a,b=b):
                with self.assertRaisesRegex(GeometryOverlapError, "invalid source-exclusive"):
                    directed_neighbor_support(a,b)

    def test_original_nine_case_ids_cannot_be_replaced_silently(self):
        land, all_shapes, gf, water = self._synthetic_two_counties()
        for code in ORIGINAL_GF4_REVIEW_AGS:
            if code in land:
                continue
            land[code] = overlap_metrics(100, 95, 90)
            all_shapes[code] = overlap_metrics(100, 95, 90)
            gf[code] = [4] if code.startswith("16") else [4,2]
            if not code.startswith("16"):
                water[code] = 10.0
        result = audit_manual_case_inventory(
            land, all_shapes, gf, water, exact_original=True)
        self.assertEqual(result["review_case_AGS"], list(ORIGINAL_GF4_REVIEW_AGS))
        self.assertEqual(result["review_case_count"], 9)


if __name__ == "__main__":
    unittest.main()
