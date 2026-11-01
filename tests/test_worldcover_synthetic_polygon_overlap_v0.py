# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only, completely synthetic footprint geometries and pixel fixtures."""
from __future__ import annotations

import unittest

from scripts.worldcover_synthetic_polygon_overlap_v0 import (
    SIDE, PolygonOverlapBlocked, _synthetic_lonlat,
    SYNTHETIC_FOOTPRINT_WGS84, evaluate_synthetic_polygon_in_block,
)


class SyntheticFootprintOverlapTests(unittest.TestCase):
    def test_single_uniform_class_is_not_an_invented_building(self):
        evidence=evaluate_synthetic_polygon_in_block(bytes([10])*(SIDE*SIDE))
        self.assertEqual(evidence["polygon_area_pixel_units"],14.08)
        self.assertEqual(evidence["intersected_pixel_cell_count"],24)
        self.assertEqual(evidence["area_weighted_class_fractions"],{"10":1.0})
        self.assertEqual(evidence["centroid_pixel_class_code"],10)
        self.assertFalse(evidence["polygon_class_heterogeneity_observed"])
        self.assertFalse(evidence["real_building_footprint_matched"])
        self.assertFalse(evidence["insured_tiv_inferred"])
        self.assertFalse(evidence["source_pixel_values_exported"])
        self.assertFalse(evidence["model_input_approved"])

    def test_exact_half_builtup_half_tree_cover_even_if_centroid_only_builtup(self):
        pixels=bytearray([10])*(SIDE*SIDE)
        for row in range(875,887):
            for col in range(880,889):
                pixels[row*SIDE+col]=50
        evidence=evaluate_synthetic_polygon_in_block(bytes(pixels))
        self.assertEqual(evidence["area_weighted_class_fractions"],{
            "10":0.5, "50":0.5,
        })
        self.assertTrue(evidence["polygon_class_heterogeneity_observed"])
        self.assertEqual(evidence["centroid_pixel_class_code"],50)
        self.assertEqual(evidence["intersected_pixel_cell_count"],24)

    def test_concave_polygon_clips_and_conserves_all_area(self):
        # 6x2 upper rectangle + 4x2 lower rectangle, non-self-intersecting.
        local=((876,878),(882,878),(882,880),(880,880),
               (880,882),(876,882))
        ring=tuple(_synthetic_lonlat(c,r) for c,r in local)
        evidence=evaluate_synthetic_polygon_in_block(
            bytes([30])*(SIDE*SIDE),ring=ring)
        self.assertEqual(evidence["polygon_area_pixel_units"],20.0)
        self.assertEqual(evidence["area_weighted_class_fractions"],{"30":1.0})
        self.assertEqual(evidence["intersected_pixel_cell_count"],20)

    def test_explicitly_reject_unknown_geographies_bad_shape_or_budget(self):
        malformed=[
            None,
            (),
            ((9.5,50.5),),
            ((True,50.5),(9.5,50.4999),(9.5001,50.5)),
            ((float("nan"),50.5),(9.5,50.4999),(9.5001,50.5)),
            ((0.,0.),(9.5,50.4999),(9.5001,50.5)),
            tuple(_synthetic_lonlat(c,r) for c,r in (
                (878,878),(882,882),(878,882),(882,878))),
            tuple(_synthetic_lonlat(c,r) for c,r in (
                (879,879),(879,879),(881,881))),
            tuple(_synthetic_lonlat(c,r) for c,r in (
                (850,850),(865,850),(865,865),(850,865))),
            (SYNTHETIC_FOOTPRINT_WGS84,),
        ]
        fixture=bytes([10])*(SIDE*SIDE)
        for i,ring in enumerate(malformed):
            with self.subTest(case=i),self.assertRaises(PolygonOverlapBlocked):
                evaluate_synthetic_polygon_in_block(fixture,ring=ring)

    def test_bounded_source_bytes_and_class_codes_are_required(self):
        with self.assertRaises(PolygonOverlapBlocked):
            evaluate_synthetic_polygon_in_block(bytes(128))
        pixel=bytearray([10])*(SIDE*SIDE)
        pixel[880*SIDE+880]=255
        with self.assertRaises(PolygonOverlapBlocked):
            evaluate_synthetic_polygon_in_block(bytes(pixel))


if __name__ == "__main__":
    unittest.main()
