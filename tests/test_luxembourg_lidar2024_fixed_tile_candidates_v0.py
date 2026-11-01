# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source-pinned Luxembourg LiDAR tile spatial selection tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from research_runners.luxembourg_lidar2024_fixed_tile_candidates_v0 import (
    LidarTileSelectionError, select_original_tiles
)


@unittest.skipUnless(importlib.util.find_spec("pyproj"), "Requires pinned PyProj optional source profile")
class RealisticSyntheticIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = Path(self.tmp.name)/"tile-fixture.gpkg"

    def create_index(self, *, url2="http://untrusted.invalid/secret.zip", include_rtree=True,
                     crs=2169):
        db = sqlite3.connect(self.file)
        db.execute("PRAGMA application_id=1196436551")  # 0x47504B47
        db.execute("CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER,min_x REAL,min_y REAL,max_x REAL,max_y REAL)")
        db.execute("CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER)")
        db.execute("CREATE TABLE TableauAssemblage(fid INTEGER PRIMARY KEY,geom BLOB,Fichier TEXT,Dossier TEXT,DownloadLink TEXT)")
        db.execute("INSERT INTO gpkg_contents VALUES (?,?,?,?,?,?,?)",
                   ("TableauAssemblage","features",crs,40000,50000,115000,145000))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?)",
                   ("TableauAssemblage","geom","POLYGON",crs))
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (?)", (crs,))
        db.execute("INSERT INTO TableauAssemblage VALUES (1,?,?,?,?)",
                   (b"ORIGINAL_PRIVATE_GEOMETRY", "SECRET_TILE_A",
                    "PRIVATE_FOLDER", "https://download.data.public.lu/r/tile-a.zip"))
        db.execute("INSERT INTO TableauAssemblage VALUES (2,?,?,?,?)",
                   (b"ORIGINAL_PRIVATE_GEOMETRY", "SECRET_TILE_B",
                    "PRIVATE_FOLDER", url2))
        if include_rtree:
            db.execute("CREATE VIRTUAL TABLE rtree_TableauAssemblage_geom USING rtree(id,minx,maxx,miny,maxy)")
            db.executemany("INSERT INTO rtree_TableauAssemblage_geom VALUES (?,?,?,?,?)",
                           [(1,40000,115000,50000,145000),(2,40000,115000,50000,145000)])
        db.commit()
        db.close()
        return hashlib.sha1(self.file.read_bytes()).hexdigest(), hashlib.sha256(self.file.read_bytes()).hexdigest()

    def test_two_original_rt_index_candidates_no_tile_identity_leak(self):
        sha1,sha256=self.create_index()
        report=select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256)
        self.assertEqual(report["rtree_bbox_candidate_tiles"],2)
        self.assertEqual(report["download_link_format_counts"],{"https":1,"non_https_or_ambiguous":1})
        self.assertEqual(report["public_download_link_host_counts"],{"download.data.public.lu":1})
        self.assertEqual(report["index_feature_rows"],2)
        self.assertFalse(report["actual_tile_polygon_intersection_confirmed"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["measured_building_heights"])
        text=json.dumps(report)
        self.assertNotIn("SECRET_TILE",text)
        self.assertNotIn("PRIVATE_FOLDER",text)
        self.assertNotIn("untrusted.invalid",text)
        self.assertNotIn("tile-a.zip",text)
        self.assertEqual(report,select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256))

    def test_wrong_exact_sha256_blocks(self):
        sha1,_=self.create_index()
        with self.assertRaisesRegex(LidarTileSelectionError,"SHA256"):
            select_original_tiles(self.file,expected_sha1=sha1,expected_sha256="0"*64)

    def test_wrong_original_publisher_sha1_blocks(self):
        _,sha256=self.create_index()
        with self.assertRaisesRegex(LidarTileSelectionError,"preflight"):
            select_original_tiles(self.file,expected_sha256=sha256)

    def test_missing_spatial_rtree_blocks(self):
        sha1,sha256=self.create_index(include_rtree=False)
        with self.assertRaisesRegex(LidarTileSelectionError,"spatial index"):
            select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256)

    def test_bad_source_crs_blocks(self):
        sha1,sha256=self.create_index(crs=3857)
        with self.assertRaisesRegex(LidarTileSelectionError,"preflight"):
            select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256)

    def test_tile_candidate_bound_refuses_too_many(self):
        sha1,sha256=self.create_index()
        with self.assertRaisesRegex(LidarTileSelectionError,"too many"):
            select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256,candidate_cap=1)

    def test_too_wide_and_outside_country_windows_block(self):
        sha1,sha256=self.create_index()
        for kwargs in ({"half_width_m":1000}, {"longitude":-1}, {"latitude":1}, {"longitude":float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(LidarTileSelectionError,"window"):
                select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256,**kwargs)

    def test_empty_index_window_refused(self):
        sha1,sha256=self.create_index()
        db=sqlite3.connect(self.file)
        db.execute("DELETE FROM rtree_TableauAssemblage_geom")
        db.commit()
        db.close()
        sha1=hashlib.sha1(self.file.read_bytes()).hexdigest()
        sha256=hashlib.sha256(self.file.read_bytes()).hexdigest()
        with self.assertRaisesRegex(LidarTileSelectionError,"No tiles"):
            select_original_tiles(self.file,expected_sha1=sha1,expected_sha256=sha256)


if __name__=="__main__":
    unittest.main()
