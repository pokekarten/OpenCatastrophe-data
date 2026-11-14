# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only EPSG4326 -> EPSG27700 categorical area QA."""
from __future__ import annotations

import json
import unittest

try:
    from pyproj import Transformer
    from shapely.geometry import box, mapping, Polygon, MultiPolygon
    from shapely.ops import transform
except ImportError:
    Transformer = None

from scripts.ea_flood_synthetic_crs_overlay_v0 import (
    PROFILE, OverlayBlocked, audit_synthetic_overlay,
)


@unittest.skipUnless(Transformer is not None, "optional pyproj/Shapely runtime not installed")
class SyntheticEAOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

    def geo(self, geometry):
        return mapping(transform(self.t.transform, geometry))

    def payload(self):
        return {
            "profile": PROFILE,
            "source_class": "synthetic_test_only",
            "scenario": "ea_defended_river_sea_3p3_present",
            "source_crs": "EPSG:4326",
            "area_crs": "EPSG:27700",
            "synthetic_hazards": [
                {"geometry": self.geo(box(430000, 280000, 430004, 280010)),
                 "depth_band": "150-300mm", "flood_source": "river"},
                {"geometry": self.geo(box(430004, 280000, 430007, 280010)),
                 "depth_band": "unavailable", "flood_source": "unavailable"},
            ],
            "synthetic_buildings": [{"geometry": self.geo(box(430000, 280000, 430010, 280010))}],
        }

    def run_case(self, source):
        return audit_synthetic_overlay(json.dumps(source, sort_keys=True).encode())

    def test_exact_synthetic_area_partition(self):
        r = self.run_case(self.payload())
        self.assertAlmostEqual(r["total_synthetic_footprint_area_m2"], 100, places=2)
        self.assertAlmostEqual(r["known_depth_band_support_area_m2"], 40, places=2)
        self.assertAlmostEqual(r["depth_unavailable_support_area_m2"], 30, places=2)
        self.assertAlmostEqual(r["outside_hazard_support_area_m2"], 30, places=2)
        self.assertAlmostEqual(r["flood_source_unavailable_area_m2_nonadditive"], 30, places=2)
        self.assertTrue(r["area_partition_conserved_in_projected_epsg27700"])
        self.assertTrue(r["crs_transformation_is_always_xy"])
        self.assertFalse(r["model_data_admitted"])
        self.assertFalse(r["actual_ea_polygons_or_buildings_used"])
        self.assertFalse(r["building_depth_or_loss_calculated"])
        self.assertNotIn("430000", json.dumps(r))
        self.assertNotIn("280000", json.dumps(r))

    def test_depth_unknown_not_dry_and_source_unknown_nonadditive(self):
        data = self.payload()
        data["synthetic_hazards"][1]["flood_source"] = "river"
        r = self.run_case(data)
        self.assertAlmostEqual(r["depth_unavailable_support_area_m2"], 30, places=2)
        self.assertAlmostEqual(r["flood_source_unavailable_area_m2_nonadditive"], 0, places=2)
        self.assertTrue(r["outside_source_support_is_not_proven_dry"])

    def test_depth_present_but_flood_source_unknown(self):
        data = self.payload()
        data["synthetic_hazards"][0]["flood_source"] = "unavailable"
        r = self.run_case(data)
        self.assertAlmostEqual(r["flood_source_unavailable_area_m2_nonadditive"], 70, places=2)
        self.assertAlmostEqual(r["known_depth_band_support_area_m2"], 40, places=2)

    def test_neighbouring_polygons_may_share_boundary(self):
        self.assertTrue(self.run_case(self.payload())["area_partition_conserved_in_projected_epsg27700"])

    def test_polygon_with_hole_is_not_supported_inside_hole(self):
        data = self.payload()
        hole = Polygon(
            [(430000, 280000), (430010, 280000), (430010, 280010),
             (430000, 280010), (430000, 280000)],
            holes=[[(430002, 280002), (430008, 280002), (430008, 280008),
                    (430002, 280008), (430002, 280002)]],
        )
        data["synthetic_hazards"] = [{
            "geometry": self.geo(hole), "depth_band": "<150mm", "flood_source": "sea",
        }]
        out = self.run_case(data)
        self.assertAlmostEqual(out["known_depth_band_support_area_m2"], 64, places=2)
        self.assertAlmostEqual(out["outside_hazard_support_area_m2"], 36, places=2)

    def test_multipolygon_parts_both_contribute_metric_area(self):
        data = self.payload()
        pieces = MultiPolygon([box(430000, 280000, 430002, 280010),
                               box(430004, 280000, 430006, 280010)])
        data["synthetic_hazards"] = [{
            "geometry": self.geo(pieces), "depth_band": "300-600mm", "flood_source": "river",
        }]
        out = self.run_case(data)
        self.assertAlmostEqual(out["known_depth_band_support_area_m2"], 40, places=2)
        self.assertAlmostEqual(out["outside_hazard_support_area_m2"], 60, places=2)

    def test_overlapping_hazards_rejected(self):
        data = self.payload()
        data["synthetic_hazards"][1]["geometry"] = self.geo(box(430003, 280000, 430007, 280010))
        with self.assertRaisesRegex(OverlayBlocked, "double-count"):
            self.run_case(data)

    def test_overlapping_buildings_rejected(self):
        data = self.payload()
        data["synthetic_buildings"].append({"geometry": self.geo(box(430001, 280001, 430009, 280009))})
        with self.assertRaisesRegex(OverlayBlocked, "double-count"):
            self.run_case(data)

    def test_swapped_crs_declared_rejected(self):
        for key, value in (("source_crs", "EPSG:27700"), ("area_crs", "EPSG:4326")):
            data = self.payload()
            data[key] = value
            with self.subTest(key=key), self.assertRaises(OverlayBlocked):
                self.run_case(data)

    def test_swapped_axis_values_rejected(self):
        data = self.payload()
        data["synthetic_hazards"][0]["geometry"] = {"type": "Polygon", "coordinates": [[[51.5, -0.1], [51.5, -0.11], [51.6, -0.11], [51.5, -0.1]]]}
        with self.assertRaises(OverlayBlocked):
            self.run_case(data)

    def test_outside_source_envelope_rejected(self):
        data = self.payload()
        data["synthetic_buildings"][0]["geometry"] = self.geo(box(1000000, 280000, 1000010, 280010))
        with self.assertRaises(OverlayBlocked):
            self.run_case(data)

    def test_malformed_self_intersection_rejected(self):
        data = self.payload()
        valid = data["synthetic_hazards"][0]["geometry"]
        ring = valid["coordinates"][0]
        data["synthetic_hazards"][0]["geometry"] = {"type": "Polygon", "coordinates": [[ring[0], ring[2], ring[1], ring[3], ring[0]]]}
        with self.assertRaises(OverlayBlocked):
            self.run_case(data)

    def test_unreviewed_band_or_flood_source_rejected(self):
        for key, value in (("depth_band", "Unavailable"), ("flood_source", "flood")):
            data = self.payload()
            data["synthetic_hazards"][0][key] = value
            with self.subTest(key=key), self.assertRaises(OverlayBlocked):
                self.run_case(data)

    def test_reject_real_feature_and_private_id_fields(self):
        data = self.payload()
        data["source_class"] = "ea_live_api"
        with self.assertRaises(OverlayBlocked):
            self.run_case(data)
        data = self.payload()
        data["synthetic_buildings"][0]["insured_id"] = "EXAMPLE"
        with self.assertRaises(OverlayBlocked):
            self.run_case(data)

    def test_hazard_scenario_not_convertible_to_climate(self):
        data = self.payload()
        data["scenario"] = "ea_defended_river_sea_3p3_climate"
        with self.assertRaises(OverlayBlocked):
            self.run_case(data)

    def test_bad_json_nan_overflow_duplicate_and_size(self):
        from scripts.ea_flood_synthetic_crs_overlay_v0 import MAX_BYTES
        for raw in (b'{"x":NaN}', b'{"x":1e999}', b'{"x":1,"x":2}', b"x" * (MAX_BYTES + 1)):
            with self.subTest(raw=raw[:15]), self.assertRaises(OverlayBlocked):
                audit_synthetic_overlay(raw)

    def test_empty_or_invalid_input(self):
        with self.assertRaises(OverlayBlocked):
            audit_synthetic_overlay(b"")
        with self.assertRaises(OverlayBlocked):
            audit_synthetic_overlay("not bytes")


if __name__ == "__main__":
    unittest.main()
