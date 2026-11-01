# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only official index geometry and source digest gate tests."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import struct
import tempfile
import unittest

SPATIAL = all(importlib.util.find_spec(x) for x in ("pyproj", "shapely"))
if SPATIAL:
    from shapely.geometry import box
    from shapely import wkb
    from pyproj import Transformer
    from research_runners.luxembourg_lidar2024_classified_tile_index_v0 import (
        LidarIndexGateError, PUBLISHED_SHA1, SITES, inspect, _study_polygon,
    )


def synthetic_source(path: Path, *, srs=2169, missing_site=None, bad_geo=False,
                     include_tile_fields=True):
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA application_id = 1196437808")  # 0x47504B50? reset below
        db.execute("PRAGMA application_id = 1196436295")  # 0x47504B47
        db.execute("CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,identifier TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER,organization TEXT,organization_coordsys_id INTEGER)")
        db.execute("INSERT INTO gpkg_contents VALUES('lidar_ta','features','Tile map',?)", (srs,))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES('lidar_ta','geom','POLYGON',?)", (srs,))
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES(2169,'EPSG',2169)")
        db.execute("CREATE TABLE lidar_ta(fid INTEGER PRIMARY KEY, geom BLOB, tile TEXT, fichier_zip TEXT)")
        for i,(name, (lon,lat)) in enumerate(SITES.items()):
            if name == missing_site:
                continue
            x,y=Transformer.from_crs(4326,2169,always_xy=True).transform(lon,lat)
            poly=box(x-250,y-250,x+250,y+250)
            payload=b"GP\x00\x01"+struct.pack("<i",srs)+wkb.dumps(poly)
            if bad_geo and i==0:
                payload=b"NO-GPKG"
            db.execute("INSERT INTO lidar_ta VALUES(?,?,?,?)",(
                i+1,payload,f"tile_{i+1}",f"lidar2024-c0{i+1:02d}-r001.zip",
            ))
        db.commit()


@unittest.skipUnless(SPATIAL, "requires pinned Shapely and PyProj")
class ClassifiedTileIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"official.gpkg"
        synthetic_source(self.path)

    def run_receipt(self,path=None,sha=None):
        p=path or self.path
        return inspect(p, published_sha1=sha or hashlib.sha1(p.read_bytes()).hexdigest())

    def test_both_fixed_regions_have_exactly_one_tile(self):
        r=self.run_receipt()
        self.assertEqual(set(r["fixed_study_tile_intersections"]),set(SITES))
        self.assertEqual([v["tile_count"] for v in r["fixed_study_tile_intersections"].values()],[1,1])
        self.assertEqual(r["tile_index_schema"]["source_records"],2)
        self.assertIn("fichier_zip",r["tile_reference_columns"])
        self.assertTrue(r["original_published_sha1_verified"])
        self.assertEqual(len(r["source_sha256"]),64)
        self.assertFalse(r["building_vs_vegetation_classified_points_observed"])
        self.assertFalse(r["model_input_admitted"])

    def test_real_published_sha1_is_not_overridden_implicitly(self):
        with self.assertRaisesRegex(LidarIndexGateError,"published ACT SHA1"):
            inspect(self.path)  # synthetic bytes can never match official source
        with self.assertRaisesRegex(LidarIndexGateError,"published ACT SHA1"):
            self.run_receipt(sha=PUBLISHED_SHA1)

    def test_unknown_and_arbitrary_research_coordinates_block(self):
        with self.assertRaisesRegex(LidarIndexGateError,"not preapproved"):
            _study_polygon("private-residence")
        self.assertEqual(_study_polygon("luxembourg-city").area,
                         _study_polygon("luxembourg-city").area)

    def test_bad_original_epsg_blocks(self):
        bad=Path(self.tmp.name)/"wrong.gpkg"
        synthetic_source(bad,srs=3857)
        with self.assertRaisesRegex(LidarIndexGateError,"2169"):
            self.run_receipt(bad)

    def test_unmatched_published_site_blocks(self):
        bad=Path(self.tmp.name)/"missing.gpkg"
        synthetic_source(bad,missing_site="berdorf-village")
        with self.assertRaisesRegex(LidarIndexGateError,"Missing official classified tile"):
            self.run_receipt(bad)

    def test_invalid_geopackage_shape_blocks(self):
        bad=Path(self.tmp.name)/"invalid.gpkg"
        synthetic_source(bad,bad_geo=True)
        with self.assertRaisesRegex(LidarIndexGateError,"Malformed original tile polygon"):
            self.run_receipt(bad)

    def test_mutated_source_hash_fails(self):
        checksum=hashlib.sha1(self.path.read_bytes()).hexdigest()
        with self.path.open("ab") as out:
            out.write(b"not-the-published-original")
        with self.assertRaisesRegex(LidarIndexGateError,"published ACT SHA1"):
            inspect(self.path,published_sha1=checksum)

    def test_invalid_source_extension_rejected(self):
        other=Path(self.tmp.name)/"original.sqlite"
        other.write_bytes(self.path.read_bytes())
        with self.assertRaisesRegex(LidarIndexGateError,"original local"):
            self.run_receipt(other)

    def test_no_individual_building_records_in_receipt(self):
        import json
        r=self.run_receipt()
        self.assertNotIn("street",json.dumps(r).lower())
        self.assertFalse(r["per_building_data_exported"])
        self.assertFalse(r["point_records_or_laz_archives_downloaded"])

    def test_site_geometry_includes_official_2169_transform(self):
        for label,(lon,lat) in SITES.items():
            x,y=Transformer.from_crs(4326,2169,always_xy=True).transform(lon,lat)
            with self.subTest(label=label):
                self.assertTrue(_study_polygon(label).contains(box(x-1,y-1,x+1,y+1)))
                self.assertTrue(9700<_study_polygon(label).area<10300)


if __name__=="__main__":
    unittest.main()
