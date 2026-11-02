# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only full AGE HQ10/HQext original-geometry conservation gates."""
from __future__ import annotations

from copy import deepcopy
import unittest

try:
    import pyproj  # noqa: F401
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False

from research_runners.luxembourg_age_hq2021_sibling_full_geometry_quality_v0 import (
    _finalize, EXPECTED_SHA256,
)
from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    HQ100GeometryError,
)


def fixtures(scenario: str):
    meta = {
        "observed_sha256": EXPECTED_SHA256[scenario],
        "publisher_sha1_match": True,
        "source_polygon_records": 1,
        "original_source_ring_parts": 3,
        "source_coordinates_skipped_without_reading": 15,
    }
    coords = {
        "original_polygon_records": 1,
        "source_polygon_ring_parts": 3,
        "original_coordinate_pairs_read_and_aggregated": 15,
        "closed_ring_parts": 3,
        "open_ring_parts": 0,
        "zero_or_near_zero_signed_area_ring_parts": 0,
        "positive_signed_orientation_ring_parts": 1,
        "negative_signed_orientation_ring_parts": 2,
        "file_bbox_matches_all_original_vertices": True,
        "record_bbox_matches_all_original_vertices": True,
        "all_original_coordinates_finite": True,
        "aggregate_original_projected_bbox_rounded_m": [49000., 60000., 105000., 135000.],
    }
    topology = {
        "source_rings_examined_total": 3,
        "individually_valid_nonzero_area_rings": 2,
        "individually_invalid_rings": 1,
        "complex_ring_geometry_test_skipped": 0,
        "geos_ring_test_errors": 0,
        "full_multipart_polygon_ogc_validity_verified": False,
        "model_input_admitted": False,
    }
    crs = {
        "crs_epsg_match_at_min90_confidence": 2169,
        "original_crs_is_projected": True,
        "original_crs_axis_unit_names": ["metre"],
    }
    return meta, coords, topology, crs


@unittest.skipUnless(HAS_PYPROJ, "Pinned pyproj required for original axis-envelope hypothesis")
class SiblingFullGeometryQualityTests(unittest.TestCase):
    def test_both_source_names_are_distinct_and_no_scientific_approval(self):
        for scenario in EXPECTED_SHA256:
            with self.subTest(scenario=scenario):
                report = _finalize(scenario, *fixtures(scenario))
                self.assertEqual(report["scenario"], scenario)
                self.assertEqual(report["closed_rings"], 3)
                self.assertEqual(report["individual_ring_topology"]["individually_invalid_rings"], 1)
                self.assertEqual(report["source_crs_epsg_90_confidence"], 2169)
                self.assertFalse(report["full_multipart_record_validated"])
                self.assertFalse(report["original_hq10_hq100_hqext_flood_areas_ordered_and_proven"])
                self.assertFalse(report["numeric_water_depth_observed"])
                self.assertFalse(report["CAT_model_input_admitted"])
                self.assertFalse(report["source_geometries_or_identifiers_exported"])

    def test_cross_scenario_checksum_and_population_mismatch_rejected(self):
        for scenario in EXPECTED_SHA256:
            m,c,t,p = fixtures(scenario)
            other = "hqext" if scenario == "hq10" else "hq10"
            m["observed_sha256"] = EXPECTED_SHA256[other]
            with self.assertRaises(HQ100GeometryError):
                _finalize(scenario,m,c,t,p)
            m,c,t,p = fixtures(scenario)
            t["source_rings_examined_total"] = 2
            with self.assertRaises(HQ100GeometryError):
                _finalize(scenario,m,c,t,p)
            m,c,t,p = fixtures(scenario)
            c["original_coordinate_pairs_read_and_aggregated"] = 14
            with self.assertRaises(HQ100GeometryError):
                _finalize(scenario,m,c,t,p)

    def test_bad_crs_and_invalid_ring_structures_fail(self):
        m,c,t,p = fixtures("hq10")
        p["crs_epsg_match_at_min90_confidence"] = 4326
        with self.assertRaises(HQ100GeometryError):
            _finalize("hq10",m,c,t,p)
        m,c,t,p = fixtures("hq10")
        c["open_ring_parts"] = 1
        with self.assertRaises(HQ100GeometryError):
            _finalize("hq10",m,c,t,p)
        m,c,t,p = fixtures("hq10")
        c["record_bbox_matches_all_original_vertices"] = False
        with self.assertRaises(HQ100GeometryError):
            _finalize("hq10",m,c,t,p)
        m,c,t,p = fixtures("hq10")
        m["publisher_sha1_match"] = False
        with self.assertRaises(HQ100GeometryError):
            _finalize("hq10",m,c,t,p)
        m,c,t,p = fixtures("hq10")
        with self.assertRaises(HQ100GeometryError):
            _finalize("hq100",m,c,t,p)


if __name__ == "__main__":
    unittest.main()
