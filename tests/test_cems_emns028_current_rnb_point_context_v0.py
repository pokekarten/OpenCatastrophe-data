# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline test: source RNB points are 2026 context, never historical insured loss."""
import importlib.util
import tempfile
from pathlib import Path
import unittest
from research_runners.cems_emns028_current_rnb_point_context_v0 import (
    CURRENT_RNB_CENTROIDS, compare_original_layers_to_current_points,
)

AVAILABLE = (
    importlib.util.find_spec("fiona") is not None
    and importlib.util.find_spec("shapely") is not None
)


@unittest.skipUnless(AVAILABLE, "Pinned spatial GitHub CI installs Fiona and Shapely")
class ContextTests(unittest.TestCase):
    def test_synthetic_filegdb_layer_names_via_geopackage_fixtures(self):
        import fiona
        from fiona.transform import transform
        from shapely.geometry import MultiPolygon, Polygon, mapping

        lon, lat = CURRENT_RNB_CENTROIDS[0][1:]
        east, north = transform("EPSG:4326", "EPSG:32631", [lon], [lat])
        x, y = east[0], north[0]
        # Two-dimensional polygons only, fully synthetic and outside
        # commercial/historical data pathways.
        bowtie = Polygon([
            (x-200, y-200), (x+200, y+200), (x-200, y+200),
            (x+200, y-200), (x-200, y-200),
        ])
        near = Polygon([
            (x-10, y-10), (x+10, y-10),
            (x+10, y+10), (x-10, y+10), (x-10, y-10),
        ])
        far = Polygon([
            (x+1000, y+1000), (x+1100, y+1000),
            (x+1100, y+1100), (x+1000, y+1100), (x+1000, y+1000),
        ])
        with tempfile.TemporaryDirectory() as td:
            dataset = Path(td) / "synthetic.gpkg"
            schema = {"geometry": "MultiPolygon", "properties": {"act_id": "str"}}
            for idx, (layer, shapes) in enumerate([
                ("Flooded_area", [MultiPolygon([bowtie])]),
                ("Estimated_Max_Flood_Extent",
                 [MultiPolygon([near]), MultiPolygon([far])]),
            ]):
                with fiona.open(
                    str(dataset), mode="w", driver="GPKG", layer=layer,
                    schema=schema, crs="EPSG:32631",
                    append_subdataset=idx>0,
                ) as w:
                    for p in shapes:
                        w.write({"geometry": mapping(p), "properties": {"act_id":"EMSN028"}})
            r = compare_original_layers_to_current_points(dataset)
        self.assertEqual(r["original_observed_layer"]["source_rows"], 1)
        self.assertTrue(r["original_observed_layer"]["research_only_linework_repair_used"])
        self.assertEqual(r["original_estimated_maximum_layer"]["source_rows"], 2)
        self.assertFalse(r["cat_model_admitted"])
        self.assertFalse(r["event_time_and_building_vintage_aligned"])
        self.assertFalse(r["aoi04_specific_original_polygon_verified"])
        self.assertFalse(r["historical_insurer_exposure_or_loss_proven"])
        self.assertFalse(r["source_rnb_centroid_coordinates_printed"])
        self.assertFalse(r["original_or_repaired_geodata_stored"])

    def test_input_is_exactly_two_current_unverified_points(self):
        self.assertEqual(len(CURRENT_RNB_CENTROIDS), 2)
        self.assertEqual({x[0] for x in CURRENT_RNB_CENTROIDS},
                         {"5TR6PNH2YQPT", "TCHNNF59Y27V"})


if __name__ == "__main__":
    unittest.main()
