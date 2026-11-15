# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source-locked ACT rooftop / GeoBase building spatial tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

HAS_GEO = all(importlib.util.find_spec(x) is not None for x in ("shapely", "pyproj"))
if HAS_GEO:
    from pyproj import Transformer
    from tests.test_luxembourg_gpkg_schema_window_v0 import write_source
    from research_runners import luxembourg_act2023_geobase2026_geometry_v0 as mod


@unittest.skipUnless(HAS_GEO, "Requires pinned spatial requirements")
class OriginalSameACTGeometryTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.a = Path(temp.name) / "act.gpkg"
        self.b = Path(temp.name) / "geo.gpkg"
        write_source(self.a, count=3)
        write_source(self.b, count=3)
        t = Transformer.from_crs(2169, 4326, always_xy=True)
        self.lon, self.lat = t.transform(75010, 75010)

    def probe(self, **kwargs):
        h1 = hashlib.sha256(self.a.read_bytes()).hexdigest()
        h2 = hashlib.sha256(self.b.read_bytes()).hexdigest()
        with (patch.object(mod, "ACT_GPKG_SHA", h1),
              patch.object(mod, "GEOBASE_GPKG_SHA", h2),
              patch.object(mod, "ACT_COUNT", 3),
              patch.object(mod, "GEOBASE_COUNT", 3)):
            options = dict(lon=self.lon, lat=self.lat, halfwidth=30,
                           max_features=5, act_sha=h1, geobase_sha=h2,
                           act_layer="buildings", geobase_layer="buildings",
                           act_id="building_ref", geobase_id="building_ref")
            options.update(kwargs)
            return mod.research(self.a, self.b, **options)

    def test_identical_geom_candidate_is_not_a_validated_building_identity(self):
        r = self.probe()
        self.assertEqual(r["source_counts"]["act_roof_polygons"], 1)
        self.assertEqual(r["source_counts"]["geobase_building_polygons"], 1)
        self.assertEqual(r["iou_0_60_unique_candidates"], 1)
        self.assertFalse(r["native_axis_ground_control_verified"])
        self.assertFalse(r["independent_ground_truth_proven"])
        self.assertFalse(r["CAT_model_input_admitted"])
        self.assertFalse(r["original_id_pairs_or_geometry_exported"])
        self.assertNotIn("B-1", json.dumps(r))

    def test_wrong_digest_rejected(self):
        with self.assertRaisesRegex(mod.SameFamilyOverlapError, "hashes"):
            self.probe(act_sha="0"*64)

    def test_out_of_scope_geography_rejected(self):
        with self.assertRaisesRegex(mod.SameFamilyOverlapError, "bounds"):
            self.probe(lon=15)

    def test_out_of_budget_region_rejected(self):
        with self.assertRaisesRegex(mod.SameFamilyOverlapError, "bounds"):
            self.probe(halfwidth=1000)


if __name__ == "__main__":
    unittest.main()
