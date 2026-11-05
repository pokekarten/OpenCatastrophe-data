# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic EuroCrops preflight regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from shapely import wkb
from shapely.geometry import Polygon
from research_runners.eurocrops_v202_preflight_v0 import Blocked, asset_identity, audit_rows, geo_metadata


class EuroCropsPreflight(unittest.TestCase):
    def test_header_footer_and_region(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "de4_2023.parquet"
            path.write_bytes(b"PAR1" + b"A" * 10 + b"PAR1")
            region, year, digest = asset_identity(path)
            self.assertEqual((region, year), ("de4", 2023))
            self.assertEqual(len(digest), 64)
            with self.assertRaises(Blocked):
                asset_identity(Path(d) / "de4_stack.parquet")
            path.write_bytes(b"JUNK" + b"A" * 10 + b"PAR1")
            with self.assertRaises(Blocked):
                asset_identity(path)

    def test_metadata_is_fail_closed(self):
        names = ["cropfield", "original_code", "area_ha", "geom"]
        good = {b"geo": json.dumps({"primary_column": "geom", "columns": {
            "geom": {"crs": {"id": {"authority": "EPSG", "code": 3035}}}}}).encode()}
        self.assertEqual(geo_metadata(good, names)["crs"], "EPSG:3035")
        with self.assertRaises(Blocked):
            geo_metadata(None, names)
        with self.assertRaises(Blocked):
            geo_metadata(good, names[:-1])
        bad = {b"geo": json.dumps({"primary_column": "geom", "columns": {
            "geom": {"crs": "EPSG:4326"}}}).encode()}
        with self.assertRaises(Blocked):
            geo_metadata(bad, names)

    def test_polygon_errors(self):
        square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
        rows = [
            {"cropfield": 1, "original_code": "wheat", "area_ha": 1.0, "geom": wkb.dumps(square)},
            {"cropfield": 1, "original_code": None, "area_ha": 2.0, "geom": wkb.dumps(square)},
            {"cropfield": 3, "original_code": "barley", "area_ha": float("nan"), "geom": b"bad"},
        ]
        report = audit_rows(rows)
        self.assertEqual(report["sampled"], 3)
        for key in ("duplicate_cropfield_in_sample", "missing_crop_code",
                    "invalid_area_ha", "area_disagreement_over_5pct",
                    "invalid_or_empty_geometry"):
            self.assertEqual(report[key], 1)


if __name__ == "__main__":
    unittest.main()
