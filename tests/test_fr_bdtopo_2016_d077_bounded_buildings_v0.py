# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only shapefile geometry fixtures; optional spatial dependencies."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
try:
    from pyproj import CRS, Transformer
    import shapefile
    from fr_bdtopo_2016_d077_bounded_buildings_v0 import (
        FAMILIES, BoundedBuildingError, profile,
    )
    HAS_SPATIAL = True
except ImportError:
    HAS_SPATIAL = False


@unittest.skipUnless(HAS_SPATIAL, "optional pinned spatial dependencies unavailable")
class BoundedBuildingProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.t = Transformer.from_crs(4326, 2154, always_xy=True)
        for name in FAMILIES:
            self.make(name, [(2.547, 48.537)] if name == "BATI_INDIFFERENCIE" else [])

    def make(self, name, coordinates):
        with shapefile.Writer(str(self.folder / name), shapeType=shapefile.POLYGON) as writer:
            writer.field("CODE", "C")
            for longitude, latitude in coordinates:
                x, y = self.t.transform(longitude, latitude)
                writer.poly([[(x, y), (x, y+5), (x+5, y+5), (x+5, y), (x, y)]])
                writer.record("synthetic")
        (self.folder / (name + ".prj")).write_text(CRS.from_epsg(2154).to_wkt())

    def test_bounded_geometry_counts_and_no_model_admission(self):
        result = profile(self.folder)
        self.assertEqual(result["historical_mapped_footprint_candidates_in_pilot_box"], 1)
        self.assertEqual(result["candidate_geometries_checked"], 1)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["individual_building_records_exported"])

    def test_distant_footprint_excluded(self):
        self.make("BATI_INDIFFERENCIE", [(2.8, 48.6)])
        self.assertEqual(profile(self.folder)["historical_mapped_footprint_candidates_in_pilot_box"], 0)

    def test_incomplete_source_family_blocks(self):
        (self.folder / "BATI_INDUSTRIEL.prj").unlink()
        with self.assertRaisesRegex(BoundedBuildingError, "incomplete"):
            profile(self.folder)

    def test_wrong_crs_blocks(self):
        (self.folder / "BATI_REMARQUABLE.prj").write_text(CRS.from_epsg(4326).to_wkt())
        with self.assertRaisesRegex(BoundedBuildingError, "unverified source CRS"):
            profile(self.folder)

    def test_large_bbox_blocks(self):
        with self.assertRaisesRegex(BoundedBuildingError, "bounded geographic"):
            profile(self.folder, bbox_lonlat=(0, 48, 10, 49))


if __name__ == "__main__":
    unittest.main()
