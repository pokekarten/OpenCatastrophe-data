# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for Natural Earth exact-source topology diagnostics."""

from __future__ import annotations

import copy
import json
import unittest

from research_runners.naturalearth_admin0_topology_v0 import (
    NaturalEarthTopologyError,
    _reason_family,
    inspect_topology,
)

FIRST_RING = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]


def payload(second_ring=None) -> dict:
    if second_ring is None:
        second_ring = [[3, 0], [4, 0], [4, 2], [3, 2], [3, 0]]
    def feature(identifier: str, iso2: str, ring):
        return {
            "type": "Feature",
            "properties": {"ADM0_A3": identifier, "ISO_A2": iso2},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        }
    return {
        "type": "FeatureCollection",
        "features": [
            feature("AAA", "AA", copy.deepcopy(FIRST_RING)),
            feature("BBB", "-99", copy.deepcopy(second_ring)),
        ],
    }


def raw(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


class NaturalEarthTopologyResearchTests(unittest.TestCase):
    def inspect(self, obj: dict) -> dict:
        return inspect_topology(raw(obj), require_pinned_identity=False)

    def test_nonoverlapping_two_original_shaped_polygons(self):
        got = self.inspect(payload())
        self.assertEqual(got["feature_count"], 2)
        self.assertEqual(got["ogc_valid_features"], 2)
        self.assertEqual(got["ogc_invalid_features"], 0)
        self.assertEqual(got["planar_crs84_material_overlap_pairs"], 0)
        self.assertEqual(got["invalid_reason_families"], {})
        self.assertTrue(got["topology_qa_pass"])
        self.assertEqual(got["excluded_original_feature_positions"], [])
        self.assertEqual(got["remaining_candidate_feature_positions"], [0, 1])
        self.assertEqual(got["remaining_candidate_feature_count"], 2)
        self.assertFalse(got["country_join_global_uniqueness_proven"])
        self.assertFalse(got["country_join_scientifically_admitted"])
        self.assertFalse(got["CAT_model_input_approved"])
        self.assertFalse(got["original_or_modified_geometries_persisted"])

    def test_shared_boundary_does_not_count_as_overlap(self):
        doc = payload([[2, 0], [3, 0], [3, 2], [2, 2], [2, 0]])
        got = self.inspect(doc)
        self.assertEqual(got["planar_crs84_material_overlap_pairs"], 0)
        self.assertEqual(got["planar_crs84_touching_pairs"], 1)
        self.assertEqual(got["excluded_original_feature_positions"], [])
        self.assertEqual(got["remaining_candidate_feature_count"], 2)

    def test_material_interior_overlap_count_is_symmetric_once(self):
        doc = payload([[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]])
        got = self.inspect(doc)
        self.assertEqual(got["planar_crs84_material_overlap_pairs"], 1)
        self.assertEqual(got["planar_crs84_touching_pairs"], 0)
        self.assertEqual(got["excluded_any_positive_overlap_positions"], 2)
        self.assertEqual(got["excluded_original_feature_positions"], [0, 1])
        self.assertEqual(got["remaining_candidate_feature_count"], 0)
        self.assertTrue(got["topology_qa_pass"])
        self.assertFalse(got["country_code_alignment_verified"])
        self.assertFalse(got["precise_border_or_cadastral_use_approved"])

    def test_bowtie_is_invalid_even_when_planar_area_zero(self):
        doc = payload()
        doc["features"][0]["geometry"]["coordinates"] = [
            [[0, 0], [2, 2], [0, 2], [2, 0], [0, 0]]
        ]
        got = self.inspect(doc)
        self.assertEqual(got["ogc_invalid_features"], 1)
        self.assertEqual(got["ogc_valid_features"], 1)
        self.assertEqual(got["empty_or_zero_area_features"], 0)
        self.assertEqual(got["invalid_reason_families"], {"self_intersection": 1})
        self.assertEqual(got["excluded_invalid_or_empty_positions"], 1)
        self.assertEqual(got["excluded_original_feature_positions"], [0])
        self.assertEqual(got["remaining_candidate_feature_positions"], [1])
        self.assertFalse(got["topology_qa_pass"])
        self.assertFalse(got["automatic_repairs_performed"])
        self.assertNotIn("coordinates", json.dumps(got))
        self.assertNotIn("AAA", json.dumps(got))

    def test_hole_outside_shell_fails_source_topology(self):
        doc = payload()
        doc["features"][0]["geometry"]["coordinates"] = [
            copy.deepcopy(FIRST_RING),
            [[7, 7], [8, 7], [8, 8], [7, 8], [7, 7]],
        ]
        got = self.inspect(doc)
        self.assertEqual(got["ogc_invalid_features"], 1)
        self.assertFalse(got["topology_qa_pass"])
        self.assertTrue(sum(got["invalid_reason_families"].values()) == 1)

    def test_antimeridian_wrap_suspect_is_excluded_not_normalized(self):
        doc = payload()
        doc["features"][0]["geometry"]["coordinates"] = [
            [[-179, 0], [179, 0], [179, 2], [-179, 2], [-179, 0]]
        ]
        got = self.inspect(doc)
        self.assertEqual(got["ogc_valid_features"], 2)
        self.assertEqual(
            got["antimeridian_width_gt_180_features_excluded_from_overlap"], 1
        )
        self.assertEqual(got["excluded_antimeridian_positions"], 1)
        self.assertEqual(got["excluded_original_feature_positions"], [0])
        self.assertEqual(got["remaining_candidate_feature_positions"], [1])
        self.assertFalse(got["independent_national_boundary_completeness_verified"])

    def test_tiny_positive_intersection_blocks_both_join_candidates(self):
        # Planar overlap below a reporting threshold is still real ambiguity.
        doc = payload([[2 - 1e-13, 0], [3, 0], [3, 2],
                       [2 - 1e-13, 2], [2 - 1e-13, 0]])
        got = self.inspect(doc)
        self.assertEqual(got["planar_crs84_material_overlap_pairs"], 0)
        self.assertEqual(got["planar_crs84_sub_epsilon_positive_overlap_pairs"], 1)
        self.assertEqual(got["excluded_original_feature_positions"], [0, 1])
        self.assertEqual(got["remaining_candidate_feature_count"], 0)
        self.assertFalse(got["country_join_global_uniqueness_proven"])

    def test_join_mask_reports_only_original_positions_no_country_identity(self):
        # Third synthetic feature remains a candidate when the first two
        # overlap; exclude only proven ambiguous geometry positions.
        doc = payload([[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]])
        doc["features"].append({
            "type": "Feature",
            "properties": {"ADM0_A3": "CCC", "ISO_A2": "CC"},
            "geometry": {"type": "Polygon", "coordinates": [
                [[10, 10], [11, 10], [11, 11], [10, 11], [10, 10]]
            ]},
        })
        got = self.inspect(doc)
        self.assertEqual(got["excluded_original_feature_positions"], [0, 1])
        self.assertEqual(got["remaining_candidate_feature_positions"], [2])
        self.assertEqual(got["remaining_candidate_feature_count"], 1)
        self.assertEqual(
            got["remaining_candidate_feature_count"]
            + len(got["excluded_original_feature_positions"]),
            got["feature_count"],
        )
        self.assertNotIn("AAA", json.dumps(got))
        self.assertNotIn("BBB", json.dumps(got))
        self.assertNotIn("CCC", json.dumps(got))
        self.assertNotIn("coordinates", json.dumps(got))
        self.assertFalse(got["CAT_model_input_approved"])

    def test_multipolygon_is_safely_counted_and_not_modified(self):
        doc = payload()
        doc["features"][0]["geometry"] = {
            "type": "MultiPolygon",
            "coordinates": [[copy.deepcopy(FIRST_RING)]],
        }
        got = self.inspect(doc)
        self.assertEqual(got["source_geometry_types"], {"MultiPolygon": 1, "Polygon": 1})
        self.assertFalse(got["original_or_modified_geometries_persisted"])

    def test_trusted_source_hash_cannot_be_claimed_from_synthetic(self):
        with self.assertRaisesRegex(NaturalEarthTopologyError, "structural/identity"):
            inspect_topology(raw(payload()))
        with self.assertRaisesRegex(NaturalEarthTopologyError, "oversized"):
            inspect_topology(b"x" * (1_048_576 + 1), require_pinned_identity=False)

    def test_source_level_country_identity_still_fails_closed(self):
        doc = payload()
        doc["features"][1]["properties"]["ADM0_A3"] = "AAA"
        with self.assertRaisesRegex(NaturalEarthTopologyError, "structural/identity"):
            self.inspect(doc)
        doc = payload()
        doc["features"][1]["properties"]["ISO_A2"] = "UKX"
        with self.assertRaisesRegex(NaturalEarthTopologyError, "structural/identity"):
            self.inspect(doc)

    def test_geos_reason_output_is_coarse_not_coordinate_bearing(self):
        self.assertEqual(
            _reason_family("Self-intersection[2.457 51.120]"),
            "self_intersection",
        )
        self.assertEqual(_reason_family("Unexpected error[1 2]"), "other_invalid_geos_reason")


if __name__ == "__main__":
    unittest.main()
