# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only official ACT GeoPackage schema and bounded window tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest

from research_runners.luxembourg_gpkg_schema_window_v0 import (
    GeoPackageGateError, decode_gpkg_wkb, inspect, sample,
)

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None
ROOT = Path(__file__).resolve().parents[1]


def polygon_wkb(x=75000.0, y=75000.0):
    ring = [(x,y),(x+20,y),(x+20,y+20),(x,y+20),(x,y)]
    return (
        struct.pack("<BI", 1, 3) + struct.pack("<I", 1)
        + struct.pack("<I", len(ring))
        + b"".join(struct.pack("<dd", a,b) for a,b in ring)
    )


def write_source(path, *, count=3, srid=2169, indexed=True, duplicate_id=False,
                 appid=0x47504B47):
    con = sqlite3.connect(path)
    con.execute("PRAGMA application_id = " + str(appid))
    con.execute("CREATE TABLE gpkg_contents (table_name TEXT, data_type TEXT, identifier TEXT, srs_id INTEGER)")
    con.execute("CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, geometry_type_name TEXT, srs_id INTEGER)")
    con.execute("CREATE TABLE gpkg_spatial_ref_sys (srs_id INTEGER, organization TEXT, organization_coordsys_id INTEGER)")
    con.execute("INSERT INTO gpkg_contents VALUES ('buildings','features','Buildings',2169)")
    con.execute("INSERT INTO gpkg_geometry_columns VALUES ('buildings','geom','POLYGON',2169)")
    con.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (2169,'EPSG',2169)")
    con.execute("CREATE TABLE buildings (fid INTEGER PRIMARY KEY,building_ref TEXT,geom BLOB)")
    if indexed:
        con.execute("CREATE VIRTUAL TABLE rtree_buildings_geom USING rtree(id,minx,maxx,miny,maxy)")
    for n in range(count):
        x = 75000 + n*100
        binary = b"GP\x00\x01" + struct.pack("<i", srid) + polygon_wkb(x=x)
        con.execute("INSERT INTO buildings VALUES (?,?,?)",(
            n+1, "DUP" if duplicate_id else f"B-{n+1}", binary,
        ))
        if indexed:
            con.execute("INSERT INTO rtree_buildings_geom VALUES (?,?,?,?,?)",(
                n+1,x,x+20,75000,75020,
            ))
    con.commit()
    con.close()


class LuxembourgGpkgSchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "provider.gpkg"
        write_source(self.path)

    def open_source(self, path=None):
        asset = path or self.path
        return inspect(asset, expected_sha256=hashlib.sha256(asset.read_bytes()).hexdigest())

    def test_metadata_count_geometry_and_crs(self):
        report, con = self.open_source()
        con.close()
        self.assertEqual(report["layers"][0]["feature_count"], 3)
        self.assertEqual(report["layers"][0]["srs_id"], 2169)
        self.assertTrue(report["layers"][0]["has_rtree"])
        self.assertFalse(report["coordinate_axis_order_verified"])
        self.assertFalse(report["model_input_admitted"])
        self.assertEqual(len(report["source_gpkg_sha256"]), 64)
        self.assertNotIn("B-1", json.dumps(report))

    def test_pinned_original_checksum_required(self):
        with self.assertRaisesRegex(GeoPackageGateError,"predeclared"):
            inspect(self.path, expected_sha256="unknown")
        with self.assertRaisesRegex(GeoPackageGateError,"hash does not match"):
            inspect(self.path, expected_sha256="0"*64)

    def test_wrong_geopackage_id_fails(self):
        bad = Path(self.tmp.name) / "other.gpkg"
        write_source(bad, appid=0)
        with self.assertRaisesRegex(GeoPackageGateError,"application ID"):
            self.open_source(bad)

    def test_source_file_must_be_real_sqlite(self):
        bad = Path(self.tmp.name) / "invalid.gpkg"
        bad.write_bytes(b"no source data")
        with self.assertRaisesRegex(GeoPackageGateError, "SQLite"):
            self.open_source(bad)

    def test_geometry_srid_conflict_blocks_wkb(self):
        with self.assertRaisesRegex(GeoPackageGateError, "SRID differs"):
            decode_gpkg_wkb(b"GP\x00\x01"+struct.pack("<i",3857)+polygon_wkb(), 2169)

    def test_no_rtree_metadata_allowed_but_export_blocked(self):
        bad = Path(self.tmp.name) / "no-rtree.gpkg"
        write_source(bad, indexed=False)
        meta, con = self.open_source(bad)
        try:
            self.assertFalse(meta["layers"][0]["has_rtree"])
            with self.assertRaisesRegex(GeoPackageGateError,"RTree"):
                sample(con,meta["layers"][0],id_field="building_ref",
                       bbox=(74995,74995,75030,75030),limit=10,
                       output=Path(self.tmp.name)/"sample.geojson")
        finally:
            con.close()

    def test_dangerous_sql_identifier_not_permitted(self):
        meta, con = self.open_source()
        try:
            with self.assertRaisesRegex(GeoPackageGateError, "SQL identifier"):
                sample(con, meta["layers"][0], id_field="building_ref; DROP TABLE buildings",
                       bbox=(74995,74995,75030,75030),limit=10,
                       output=Path(self.tmp.name)/"sample.geojson")
        finally:
            con.close()

    @unittest.skipUnless(HAS_SHAPELY, "Requires optional reviewed shapely")
    def test_bounded_native_crs_sample(self):
        meta, con = self.open_source()
        target = Path(self.tmp.name) / "sample.geojson"
        try:
            n = sample(con,meta["layers"][0],id_field="building_ref",
                       bbox=(74995,74995,75030,75030),limit=10,output=target)
        finally:
            con.close()
        self.assertEqual(n,1)
        exported=json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(exported["features"][0]["properties"]["building_id"],"B-1")

    @unittest.skipUnless(HAS_SHAPELY, "Requires optional reviewed shapely")
    def test_bounded_window_rejects_overflow_and_duplicate(self):
        target=Path(self.tmp.name)/"sample.geojson"
        meta,con=self.open_source()
        try:
            with self.assertRaisesRegex(GeoPackageGateError,"too many"):
                sample(con,meta["layers"][0],id_field="building_ref",
                       bbox=(74995,74995,75300,75030),limit=2,output=target)
        finally:
            con.close()
        self.assertFalse(target.exists())
        other=Path(self.tmp.name)/"dup.gpkg"
        write_source(other,duplicate_id=True)
        meta,con=self.open_source(other)
        try:
            with self.assertRaisesRegex(GeoPackageGateError,"duplicate"):
                sample(con,meta["layers"][0],id_field="building_ref",
                       bbox=(74995,74995,75300,75030),limit=5,output=target)
        finally:
            con.close()
        self.assertFalse(target.exists())

    def test_cli_inspection_does_not_emit_original_building_ids(self):
        result=subprocess.run(
            [sys.executable,"research_runners/luxembourg_gpkg_schema_window_v0.py",
             "--gpkg",str(self.path),"--expected-gpkg-sha256",hashlib.sha256(self.path.read_bytes()).hexdigest()],
            cwd=ROOT,capture_output=True,text=True,check=False,timeout=20,
        )
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertNotIn("B-1",result.stdout)
        self.assertEqual(json.loads(result.stdout)["layers"][0]["feature_count"],3)


if __name__ == "__main__":
    unittest.main()
