# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only LiDAR2024 original tile index source verification tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from research_runners.luxembourg_lidar2024_tile_index_receipt_v0 import (
    LidarIndexError, inspect,
)


class LuxembourgLidarTileReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / "synthetic.gpkg"

    def make_index(self, *, epsg=2169, geom="MULTIPOLYGON", app_id=0x47504B47,
                   row_count=2, geometry_column="geom"):
        db = sqlite3.connect(self.source)
        db.execute(f"PRAGMA application_id={app_id}")
        db.execute(
            "CREATE TABLE gpkg_contents (table_name TEXT,data_type TEXT,srs_id INTEGER,"
            "min_x REAL,min_y REAL,max_x REAL,max_y REAL)")
        db.execute(
            "CREATE TABLE gpkg_geometry_columns (table_name TEXT,column_name TEXT,"
            "geometry_type_name TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_spatial_ref_sys (srs_id INTEGER)")
        db.execute(
            'CREATE TABLE "Lidar_Index" (id INTEGER PRIMARY KEY,geom BLOB,'
            'download_url TEXT,tile_id TEXT)')
        db.execute(
            "INSERT INTO gpkg_contents VALUES (?,?,?,?,?,?,?)",
            ("Lidar_Index", "features", epsg, 40000, 60000, 110000, 130000))
        db.execute(
            "INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?)",
            ("Lidar_Index", geometry_column, geom, epsg))
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (?)", (epsg,))
        for i in range(row_count):
            db.execute("INSERT INTO Lidar_Index VALUES (?,?,?,?)", (
                i + 1, b"SECRET_POLYGON", "https://secret.invalid/laz/" + str(i),
                "SECRET_TILE_{}".format(i)))
        db.commit()
        db.close()
        return hashlib.sha1(self.source.read_bytes()).hexdigest()

    def test_pinned_original_gpkg_metadata_only(self):
        sha = self.make_index()
        report = inspect(self.source, expected_sha1=sha)
        self.assertEqual(report["original_sha1"], sha)
        self.assertEqual(report["original_sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(len(report["feature_layers"]), 1)
        layer = report["feature_layers"][0]
        self.assertEqual(layer["feature_rows"], 2)
        self.assertEqual(layer["declared_epsg"], 2169)
        self.assertEqual(layer["declared_geometry_type"], "MULTIPOLYGON")
        self.assertEqual(layer["field_names_only"], ["id", "geom", "download_url", "tile_id"])
        self.assertFalse(report["original_provider_tile_rows_exported"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["point_cloud_laz_downloaded"])
        self.assertNotIn("SECRET_TILE", json.dumps(report))
        self.assertNotIn("secret.invalid", json.dumps(report))
        self.assertEqual(report, inspect(self.source, expected_sha1=sha))

    def test_wrong_publisher_sha1_blocks(self):
        self.make_index()
        with self.assertRaisesRegex(LidarIndexError, "publisher-listed"):
            inspect(self.source)

    def test_malformed_sha1_blocks(self):
        self.make_index()
        with self.assertRaisesRegex(LidarIndexError, "Malformed"):
            inspect(self.source, expected_sha1="INVALID")

    def test_symlink_blocks(self):
        self.make_index()
        alias = Path(self.tmp.name) / "alias.gpkg"
        alias.symlink_to(self.source)
        with self.assertRaisesRegex(LidarIndexError, "symlinked"):
            inspect(alias, expected_sha1=hashlib.sha1(self.source.read_bytes()).hexdigest())

    def test_wrong_epsg_blocks(self):
        sha = self.make_index(epsg=3857)
        with self.assertRaisesRegex(LidarIndexError, "CRS"):
            inspect(self.source, expected_sha1=sha)

    def test_nonpolygon_geometry_blocks(self):
        sha = self.make_index(geom="POINT")
        with self.assertRaisesRegex(LidarIndexError, "CRS/type"):
            inspect(self.source, expected_sha1=sha)

    def test_missing_geometry_column_blocks(self):
        sha = self.make_index(geometry_column="not_geom")
        with self.assertRaisesRegex(LidarIndexError, "field"):
            inspect(self.source, expected_sha1=sha)

    def test_empty_original_index_blocks(self):
        sha = self.make_index(row_count=0)
        with self.assertRaisesRegex(LidarIndexError, "size budget"):
            inspect(self.source, expected_sha1=sha)

    def test_wrong_sqlite_application_id_blocks(self):
        sha = self.make_index(app_id=0)
        with self.assertRaisesRegex(LidarIndexError, "application ID"):
            inspect(self.source, expected_sha1=sha)

    def test_garbage_file_blocks_without_provider_ids(self):
        self.source.write_bytes(b"not a gpkg")
        with self.assertRaisesRegex(LidarIndexError, "SQLite"):
            inspect(self.source, expected_sha1=hashlib.sha1(self.source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
