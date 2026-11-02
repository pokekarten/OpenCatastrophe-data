# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic GML/raster inputs; actual provider exercise uses reviewed workflow."""
from __future__ import annotations

import importlib.util
import unittest

from research_runners import hessen_alkis_one_building_worldcover_pair_v0 as pair
from tests.test_probe_hessen_alkis_one_gml_ring_v0 import fixture

HAVE_SPATIAL=bool(
    importlib.util.find_spec("pyproj") and importlib.util.find_spec("shapely")
)

def invented_small_building():
    # Completely made-up 2D ETRS89 single polygon; not an address or roof.
    return fixture(points=[
        (50.51600,9.48300),
        (50.51600,9.48315),
        (50.51615,9.48315),
        (50.51615,9.48300),
        (50.51600,9.48300),
    ])


@unittest.skipUnless(HAVE_SPATIAL,"dedicated spatial CI installs pinned PyProj and Shapely")
class PairSourceTests(unittest.TestCase):
    def test_one_invented_source_polygon_uniform_worldcover_fixture_remains_unadmitted(self):
        evidence=pair.inspect_original_pair(
            invented_small_building(),bytes([10])*(pair.SIDE*pair.SIDE)
        )
        self.assertTrue(evidence["actual_polygon_raster_research_intersection_executed"])
        self.assertTrue(evidence["original_epsg4258_geos_valid"])
        self.assertTrue(evidence["transformed_epsg4326_geos_valid"])
        self.assertEqual(evidence["source_building_feature_members_parsed"],1)
        self.assertEqual(evidence["source_wfs_reported_number_returned"],0)
        self.assertTrue(evidence["wfs_count_discrepancy_still_blocked"])
        self.assertEqual(evidence["baseline_area_weighted_original_class_fractions"],{"10":1.0})
        self.assertEqual(evidence["max_total_variation_over_grid_shifts"],0)
        self.assertEqual(evidence["fixed_research_scenarios"],17)
        self.assertFalse(evidence["source_building_physical_identity_verified"])
        self.assertFalse(evidence["model_input_approved"])
        self.assertFalse(evidence["source_coordinates_or_raw_pixel_values_exported"])
        self.assertNotIn("50.516",str(evidence))
        self.assertNotIn("9.483",str(evidence))

    def test_invented_landcover_edge_changes_area_weighted_class_fraction(self):
        values=bytearray([10])*(pair.SIDE*pair.SIDE)
        for row in range(682,694):
            for col in range(677,687):
                values[row*pair.SIDE+col]=50
        evidence=pair.inspect_original_pair(invented_small_building(),bytes(values))
        self.assertGreater(evidence["max_total_variation_over_grid_shifts"],0)
        self.assertIn("50",evidence["class_fraction_ranges_over_grid_shifts"])
        self.assertGreater(
            evidence["class_fraction_ranges_over_grid_shifts"]["50"]["maximum"],
            evidence["class_fraction_ranges_over_grid_shifts"]["50"]["minimum"],
        )
        self.assertFalse(evidence["model_input_approved"])

    def test_swapped_axis_hole_and_oversized_building_never_admitted(self):
        pixels=bytes([30])*(pair.SIDE*pair.SIDE)
        bad=[
            fixture(hole=True),
            fixture(points=[
                (9.483,50.516),(9.48315,50.516),
                (9.48315,50.51615),(9.483,50.51615),
                (9.483,50.516)
            ]),
            # 0.002 degrees is 24x24=576 raster cells, over reviewed 256.
            fixture(),
        ]
        for i,raw in enumerate(bad):
            with self.subTest(i=i),self.assertRaises(pair.PairBlocked):
                pair.inspect_original_pair(raw,pixels)

    def test_bad_class_on_intersected_cell_or_missing_pixel_bytes_blocked(self):
        raw=invented_small_building()
        with self.assertRaises(pair.PairBlocked):
            pair.inspect_original_pair(raw,bytes([10])*100)
        pixels=bytearray([10])*(pair.SIDE*pair.SIDE)
        pixels[688*pair.SIDE+676]=255
        with self.assertRaises(pair.PairBlocked):
            pair.inspect_original_pair(raw,bytes(pixels))

    def test_alternate_count_header_accepted_only_as_research_diagnostic_block(self):
        raw=invented_small_building().replace(
            b'numberReturned="0"',b'numberReturned="3"'
        )
        evidence=pair.inspect_original_pair(raw,bytes([30])*(pair.SIDE*pair.SIDE))
        self.assertTrue(evidence["wfs_count_discrepancy_still_blocked"])
        self.assertEqual(evidence["source_wfs_reported_number_returned"],3)
        self.assertFalse(evidence["model_input_approved"])


if __name__=="__main__":
    unittest.main()
