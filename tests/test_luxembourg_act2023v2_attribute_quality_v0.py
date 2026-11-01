# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ACT2023v2 attribute-quality tests; no original source bytes."""
from __future__ import annotations

import json
import sqlite3
import unittest

from research_runners.luxembourg_act2023v2_attribute_quality_v0 import profile
from research_runners.luxembourg_gpkg_schema_window_v0 import GeoPackageGateError


def fixture():
    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE sample (
          id INTEGER, geom BLOB, buildingid TEXT, gml_id TEXT,
          commune TEXT, lau2 TEXT, modelmodificationdate TEXT,
          area REAL, zmin REAL
        );
        INSERT INTO sample VALUES (1, X'01', 'B1','G1','A','L1','2023-08-01',20.0,100.0);
        INSERT INTO sample VALUES (2, X'02', 'B1','G2','A','L1',NULL,-2.0,0.0);
        INSERT INTO sample VALUES (3, NULL, NULL,'G3',NULL,'L1','2023-08-01',NULL,'oops');
        CREATE VIRTUAL TABLE rtree_sample_geom USING rtree(id,minx,maxx,miny,maxy);
        INSERT INTO rtree_sample_geom VALUES (1,0,1,0,1);
        INSERT INTO rtree_sample_geom VALUES (2,1,2,1,2);
    """)
    layer = {
        "table": "sample", "geometry_column": "geom",
        "srs_id": 2169, "geometry_type": "MULTIPOLYGON",
        "feature_count": 3, "has_rtree": True,
        "fields": [{"name": name} for name in (
            "id","geom","buildingid","gml_id","commune","lau2",
            "modelmodificationdate","area","zmin"
        )],
    }
    return db, layer


class LuxembourgAttributeQualityTests(unittest.TestCase):
    def test_nonidentifying_counts_exact(self):
        db, layer = fixture()
        try:
            r = profile(db, layer)
        finally:
            db.close()
        self.assertEqual(r["feature_row_count"], 3)
        self.assertEqual(r["null_geometry_count"], 1)
        self.assertEqual(r["original_id_diagnostics"]["buildingid"], {
            "distinct_nonblank": 1, "missing_or_blank": 1,
            "duplicate_nonblank_rows": 1,
        })
        self.assertEqual(r["original_id_diagnostics"]["gml_id"]["distinct_nonblank"], 3)
        self.assertEqual(r["numeric_field_diagnostics"]["area"]["nonpositive_numeric"], 1)
        self.assertEqual(r["numeric_field_diagnostics"]["area"]["null"], 1)
        self.assertEqual(r["numeric_field_diagnostics"]["zmin"]["nonnull_not_numeric_sqlite"], 1)
        self.assertEqual(r["missing_modification_date_count"], 1)
        self.assertEqual(r["rtree_entries"], 2)
        self.assertEqual(r["rtree_missing_entries_vs_features"], 1)
        self.assertFalse(r["raw_records_exported"])
        self.assertFalse(r["building_identity_approved"])

    def test_no_individual_identifiers_or_values_exposed(self):
        db, layer = fixture()
        try:
            r = profile(db, layer)
        finally:
            db.close()
        data = json.dumps(r, sort_keys=True)
        for hidden in ("B1", "G1", "G2", "G3", "2023-08-01", "oops"):
            self.assertNotIn(hidden, data)

    def test_schema_drift_blocks(self):
        db, layer = fixture()
        try:
            layer["fields"] = [item for item in layer["fields"]
                               if item["name"] != "buildingid"]
            with self.assertRaisesRegex(GeoPackageGateError, "columns"):
                profile(db, layer)
        finally:
            db.close()

    def test_crs_geometry_drift_blocks(self):
        db, layer = fixture()
        try:
            for key, bad in [("srs_id", 4326), ("geometry_type", "POINT")]:
                original = layer[key]
                layer[key] = bad
                with self.assertRaisesRegex(GeoPackageGateError, "CRS"):
                    profile(db, layer)
                layer[key] = original
        finally:
            db.close()

    def test_metadata_count_mismatch_blocks(self):
        db, layer = fixture()
        try:
            layer["feature_count"] = 4
            with self.assertRaisesRegex(GeoPackageGateError, "row count"):
                profile(db, layer)
        finally:
            db.close()

    def test_missing_rtree_not_fabricated(self):
        db, layer = fixture()
        try:
            layer["has_rtree"] = False
            r = profile(db, layer)
            self.assertIsNone(r["rtree_entries"])
            self.assertIsNone(r["rtree_missing_entries_vs_features"])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
