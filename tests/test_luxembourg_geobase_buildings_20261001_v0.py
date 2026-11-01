# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Safe research-only original Luxembourg GeoBase Buildings archive tests."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
import stat
import tempfile
import unittest
import zipfile

from research_runners.luxembourg_geobase_buildings_20261001_v0 import GeoBaseError, inspect


class GeoBaseOriginalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "source.zip"
        self.gpkg = Path(self.temp.name) / "synthetic.gpkg"

    def make_gpkg(self, *, epsg=2169, geom="MULTIPOLYGON", appid=0x47504B47):
        db = sqlite3.connect(self.gpkg)
        db.execute(f"PRAGMA application_id={appid}")
        db.execute("CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER)")
        db.execute("CREATE TABLE BuildingFeature(id INTEGER PRIMARY KEY,geom BLOB,source_id TEXT)")
        db.execute("INSERT INTO gpkg_contents VALUES ('BuildingFeature','features',?)", (epsg,))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES ('BuildingFeature','geom',?,?)", (geom,epsg))
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (?)", (epsg,))
        db.execute("INSERT INTO BuildingFeature VALUES (1,?,?)", (b"PRIVATE_GEOM", "SECRET_BUILDING_ID"))
        db.commit()
        db.close()

    def build(self, members=None):
        if members is None:
            self.make_gpkg()
            members = [("archive/Buildings.gpkg", self.gpkg.read_bytes())]
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in members:
                z.writestr(name, data)
        return hashlib.md5(self.path.read_bytes()).hexdigest()

    def test_original_metadata_is_bounded_reproducible_and_private(self):
        md5 = self.build()
        result = inspect(self.path, expected_md5=md5)
        self.assertEqual(result["original_zip_md5"], md5)
        self.assertEqual(len(result["original_gpkg_files"]), 1)
        layer = result["original_gpkg_files"][0]["gpkg_layer_metadata"][0]
        self.assertEqual(layer["feature_rows"], 1)
        self.assertEqual(layer["epsg_declared"], 2169)
        self.assertEqual(layer["field_names_only"], ["id", "geom", "source_id"])
        self.assertNotIn("SECRET_BUILDING_ID", str(result))
        self.assertNotIn("PRIVATE_GEOM", str(result))
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["same_provider_act2023v2_independence_verified"])
        self.assertEqual(result, inspect(self.path, expected_md5=md5))

    def test_wrong_resource_pin_is_blocked(self):
        self.build()
        with self.assertRaisesRegex(GeoBaseError, "MD5"):
            inspect(self.path)

    def test_nonpolygon_is_blocked(self):
        self.make_gpkg(geom="POINT")
        md5 = self.build([("Buildings.gpkg", self.gpkg.read_bytes())])
        with self.assertRaisesRegex(GeoBaseError, "nonpolygon"):
            inspect(self.path, expected_md5=md5)

    def test_wrong_crs_is_blocked(self):
        self.make_gpkg(epsg=3857)
        md5 = self.build([("Buildings.gpkg", self.gpkg.read_bytes())])
        with self.assertRaisesRegex(GeoBaseError, "2169"):
            inspect(self.path, expected_md5=md5)

    def test_wrong_sqlite_application_id_is_blocked(self):
        self.make_gpkg(appid=0)
        md5 = self.build([("Buildings.gpkg", self.gpkg.read_bytes())])
        with self.assertRaisesRegex(GeoBaseError, "application ID"):
            inspect(self.path, expected_md5=md5)

    def test_path_traversal_and_windows_paths_fail_closed(self):
        for name in ("../oops.gpkg", "/root.gpkg", "C:/drive.gpkg", "dir\\bad.gpkg"):
            md5 = self.build([(name, b"wrong")])
            with self.subTest(path=name), self.assertRaisesRegex(GeoBaseError, "Unsafe"):
                inspect(self.path, expected_md5=md5)

    def test_duplicate_source_path_fails(self):
        self.make_gpkg()
        md5 = self.build([("a.gpkg",self.gpkg.read_bytes()), ("a.gpkg",self.gpkg.read_bytes())])
        with self.assertRaisesRegex(GeoBaseError, "Duplicate"):
            inspect(self.path, expected_md5=md5)

    def test_symlink_member_fails(self):
        zi = zipfile.ZipInfo("a.gpkg")
        zi.create_system = 3
        zi.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.path, "w") as zip:
            zip.writestr(zi, b"target")
        with self.assertRaisesRegex(GeoBaseError, "Unsafe"):
            inspect(self.path, expected_md5=hashlib.md5(self.path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
