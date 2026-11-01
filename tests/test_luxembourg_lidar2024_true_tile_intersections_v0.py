# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic byte-pinned GeoPackage geometry and source URL safety regression."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
import unittest

from research_runners.luxembourg_lidar2024_true_tile_intersections_v0 import (
    TileIntersectionError, fixed_window, inspect_actual_tile_intersections
)

HAS_SPATIAL = importlib.util.find_spec("shapely") is not None and importlib.util.find_spec("pyproj") is not None


@unittest.skipUnless(HAS_SPATIAL, "Requires optional pinned Shapely/PyProj spatial profile")
class SyntheticSourceTileGeometryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = Path(self.tmp.name)/"synthetic-original.gpkg"

    def make_original(self, *, url2="https://data.public.lu/en/tile-b.zip",
                      missing_rtree=False, both_geometries=False,
                      malformed_blob=False):
        from shapely.geometry import box
        from shapely import wkb
        target = fixed_window(lon=6.1319,lat=49.6116,half_width_m=125)
        xmin, ymin, xmax, ymax = target.bounds
        # First tile contains the entire ROI. Second RTree bbox intersects,
        # but small polygon at its bottom-left bounding-box corner lies outside
        # the rotated original EPSG2169 equal-area target polygon.
        full = box(xmin-10,ymin-10,xmax+10,ymax+10)
        remote = box(xmin-10,ymin-10,xmin+1,ymin+1) if not both_geometries else full
        db = sqlite3.connect(self.file)
        db.execute("PRAGMA application_id=1196444487")
        db.execute("CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER,min_x REAL,min_y REAL,max_x REAL,max_y REAL)")
        db.execute("CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER)")
        db.execute("CREATE TABLE TableauAssemblage(fid INTEGER PRIMARY KEY,geom BLOB,Fichier TEXT,Dossier TEXT,DownloadLink TEXT)")
        db.execute("INSERT INTO gpkg_contents VALUES (?,?,?,?,?,?,?)",("TableauAssemblage","features",2169,xmin,ymin,xmax,ymax))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?)",("TableauAssemblage","geom","POLYGON",2169))
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (2169)")
        if not missing_rtree:
            db.execute("CREATE VIRTUAL TABLE rtree_TableauAssemblage_geom USING rtree(id,minx,maxx,miny,maxy)")
        for i,polygon in enumerate([full,remote],1):
            blob=b"GP"+bytes([0,1])+struct.pack("<i",2169)+wkb.dumps(polygon)
            if i==1 and malformed_blob:
                blob=b"GARBAGE"
            db.execute("INSERT INTO TableauAssemblage VALUES (?,?,?,?,?)",(i,blob,"PRIVATE_TILE_"+str(i),"PRIVATE_FOLDER", url2 if i==2 else "https://data.public.lu/en/tile-a.zip"))
            if not missing_rtree:
                a,b,c,d=polygon.bounds
                db.execute("INSERT INTO rtree_TableauAssemblage_geom VALUES (?,?,?,?,?)",(i,a,c,b,d))
        db.commit()
        db.close()
        return hashlib.sha1(self.file.read_bytes()).hexdigest(), hashlib.sha256(self.file.read_bytes()).hexdigest()

    def run_source(self, **kwargs):
        sha1,sha256=self.make_original(**kwargs)
        # This fixture original source is SHA-pinned and differs by test.
        from unittest.mock import patch
        with patch("research_runners.luxembourg_lidar2024_fixed_tile_candidates_v0.PUBLISHER_SHA1",sha1):
            # Imported function default expected_sha1 was bound at definition,
            # therefore patch the callable used by the stricter new runner.
            from research_runners import luxembourg_lidar2024_fixed_tile_candidates_v0 as previous
            original_select=previous.select_original_tiles
            def patched(file, **parameters):
                parameters["expected_sha1"]=sha1
                return original_select(file,**parameters)
            with patch("research_runners.luxembourg_lidar2024_true_tile_intersections_v0.select_original_tiles",side_effect=patched):
                return inspect_actual_tile_intersections(self.file, expected_sha256=sha256)

    def test_true_intersections_avoid_rtree_corner_false_positive(self):
        result=self.run_source()
        self.assertEqual(result["rtree_bbox_candidates"],2)
        self.assertEqual(result["positive_area_tile_intersections"],1)
        self.assertEqual(result["intersection_union_coverage_fraction_rounded_6dp"],1.0)
        self.assertEqual(result["intersecting_public_https_hosts"],{"data.public.lu":1})
        self.assertFalse(result["cat_model_input_admitted"])
        self.assertFalse(result["provider_laz_downloaded"])
        self.assertFalse(result["source_axis_ground_control_approved"])
        report=json.dumps(result)
        self.assertNotIn("PRIVATE_TILE",report)
        self.assertNotIn("tile-a.zip",report)
        self.assertNotIn("PRIVATE_FOLDER",report)

    def test_both_original_polygons_intersect_and_overlap_count_is_two(self):
        result=self.run_source(both_geometries=True)
        self.assertEqual(result["positive_area_tile_intersections"],2)
        self.assertEqual(result["distinct_intersecting_download_link_count"],2)
        self.assertEqual(result["distinct_intersecting_directory_count"],1)
        self.assertEqual(result["intersection_union_coverage_fraction_rounded_6dp"],1.0)

    def test_unreviewed_http_provider_rejected_when_polygon_intersects(self):
        with self.assertRaisesRegex(TileIntersectionError,"unreviewed provider URL"):
            self.run_source(both_geometries=True,url2="http://data.public.lu/tile.zip")

    def test_unreviewed_external_host_rejected(self):
        with self.assertRaisesRegex(TileIntersectionError,"unreviewed provider URL"):
            self.run_source(both_geometries=True,url2="https://evil.invalid/tile.zip")

    def test_corrupt_original_gpkg_polygon_blocks(self):
        with self.assertRaisesRegex(TileIntersectionError,"decoded"):
            self.run_source(malformed_blob=True)

    def test_missing_original_rtree_blocks(self):
        with self.assertRaisesRegex(TileIntersectionError,"source or pilot"):
            self.run_source(missing_rtree=True)

    def test_original_sha256_cannot_be_replaced(self):
        sha1,_=self.make_original()
        with self.assertRaisesRegex(TileIntersectionError,"source or pilot"):
            inspect_actual_tile_intersections(self.file, expected_sha256="0"*64)

    def test_fixed_window_is_valid_and_nontrivial(self):
        region=fixed_window(lon=6.1319,lat=49.6116,half_width_m=125)
        self.assertTrue(region.is_valid)
        self.assertGreater(region.area,50000)
        self.assertLess(region.area,70000)


if __name__=="__main__":
    unittest.main()
