# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline tests for bounded 2016 versus current RNB polygons."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pyproj import CRS, Transformer
import shapefile
from shapely.geometry import Polygon, mapping

from research_runners.fr_bdtopo_2016_rnb_polygon_bridge_v0 import (
    BridgeError, RNB_IDS, compare, current_rnb_shape, historical_bounded_shapes,
)


def square(x, y, radius):
    # Explicit clockwise exterior for ESRI shapefile ring orientation.
    return [(x-radius, y-radius), (x-radius, y+radius),
            (x+radius, y+radius), (x+radius, y-radius),
            (x-radius, y-radius)]


class HistoricalRnbBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        p = Transformer.from_crs(4326, 2154, always_xy=True)
        places = [(2.54700, 48.53663), (2.54762, 48.53673),
                  (2.54830, 48.53715)]
        centres = [p.transform(*loc) for loc in places]
        for family in ("BATI_INDIFFERENCIE", "BATI_INDUSTRIEL", "BATI_REMARQUABLE"):
            with shapefile.Writer(str(self.path / family), shapeType=shapefile.POLYGON) as w:
                w.field("id", "C")
                if family == "BATI_INDIFFERENCIE":
                    for i, (x, y) in enumerate(centres):
                        w.poly([square(x, y, 5)])
                        w.record(f"SYNTHETIC{i}")
            (self.path / (family + ".prj")).write_text(
                CRS.from_epsg(2154).to_wkt(), encoding="utf-8")
        self.placed = places

    def payload(self, rnb_id, polygon=None, *, status="constructed"):
        lon, lat = self.placed[0 if rnb_id == RNB_IDS[0] else 1]
        polygon = polygon or Polygon(square(lon, lat, 0.00004))
        return json.dumps({
            "rnb_id": rnb_id, "status": status, "is_active": True,
            "shape": mapping(polygon), "addresses": [],
        }).encode()

    def test_three_historic_candidates_two_current_footprints(self):
        historical = historical_bounded_shapes(self.path)
        self.assertEqual(len(historical), 3)
        self.assertEqual({item[0] for item in historical}, {"BATI_INDIFFERENCIE"})
        report = compare(self.path, fetch=self.payload)
        self.assertEqual(report["2016_historic_bbox_source_candidates"], 3)
        self.assertEqual(report["current_rnb_source_records"], 2)
        self.assertEqual(len(report["historic_current_pairwise_polygon_matrix"]), 3)
        self.assertEqual(
            len(report["historic_current_pairwise_polygon_matrix"][0]["current_polygon_comparisons"]), 2
        )
        self.assertTrue(report["historic_current_pairwise_polygon_matrix"][0]
                        ["current_polygon_comparisons"][0]["polygon_intersects"])
        pair = report["historic_current_pairwise_polygon_matrix"][0]["current_polygon_comparisons"][0]
        self.assertIn("symmetric_difference_area_m2", pair)
        self.assertIn("hausdorff_distance_m", pair)
        self.assertFalse(pair["same_physical_building_identity_proven"])
        self.assertFalse(report["historic_to_modern_identity_automatically_assigned"])
        self.assertFalse(report["source_independence_proven"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["original_shapefiles_and_rnb_responses_saved"])

    def test_source_rnb_identity_must_match_url(self):
        with self.assertRaisesRegex(BridgeError, "identity/status"):
            current_rnb_shape(RNB_IDS[0], self.payload(RNB_IDS[1]))

    def test_current_demolished_does_not_pass(self):
        with self.assertRaisesRegex(BridgeError, "identity/status"):
            current_rnb_shape(RNB_IDS[0], self.payload(RNB_IDS[0], status="demolished"))

    def test_no_point_only_as_building_geometry(self):
        with self.assertRaisesRegex(BridgeError, "polygon"):
            current_rnb_shape(
                RNB_IDS[0], json.dumps({
                    "rnb_id": RNB_IDS[0], "is_active": True, "status": "constructed",
                    "shape": {"type": "Point", "coordinates": [2.547, 48.537]}
                }).encode())

    def test_reject_huge_response(self):
        with self.assertRaisesRegex(BridgeError, "over cap"):
            current_rnb_shape(RNB_IDS[0], b"x" * 128001)

    def test_missing_historical_components_fail_closed(self):
        (self.path / "BATI_INDUSTRIEL.prj").unlink()
        with self.assertRaisesRegex(BridgeError, "missing or unsafe"):
            historical_bounded_shapes(self.path)


if __name__ == "__main__":
    unittest.main()
