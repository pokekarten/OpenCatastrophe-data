# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: Luxembourg LiDAR2024 original group URLs, no real download."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from research_runners import luxembourg_lidar2024_tile_group_link_preflight_v0 as mod
from research_runners.luxembourg_lidar2024_fixed_tile_candidates_v0 import (
    select_original_tiles,
)

U1="https://data.public.lu/en/datasets/r/11111111-1111-4111-8111-111111111111"
U2="https://data.public.lu/fr/datasets/r/22222222-2222-4222-8222-222222222222"


def original_index(path, urls):
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA application_id=1196444487")
        db.execute("CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER,min_x REAL,min_y REAL,max_x REAL,max_y REAL)")
        db.execute("CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER)")
        db.execute("CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER)")
        db.execute("CREATE TABLE TableauAssemblage(fid INTEGER PRIMARY KEY,geom BLOB,Fichier TEXT,Dossier TEXT,DownloadLink TEXT)")
        db.execute("INSERT INTO gpkg_contents VALUES (?,?,?,?,?,?,?)",
                   ("TableauAssemblage","features",2169,40000,50000,115000,145000))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?)",
                   ("TableauAssemblage","geom","POLYGON",2169))
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (2169)")
        db.execute("CREATE VIRTUAL TABLE rtree_TableauAssemblage_geom USING rtree(id,minx,maxx,miny,maxy)")
        for ix,url in enumerate(urls,start=1):
            db.execute("INSERT INTO TableauAssemblage VALUES (?,?,?,?,?)",
                       (ix,b"SYNTHETIC_TILE_GEOMETRY",f"SYN-PRIVATE-{ix}","SYN-PRIVATE-GROUP",url))
            db.execute("INSERT INTO rtree_TableauAssemblage_geom VALUES (?,?,?,?,?)",
                       (ix,40000,115000,50000,145000))
    sha1=hashlib.sha1(path.read_bytes()).hexdigest()
    sha256=hashlib.sha256(path.read_bytes()).hexdigest()
    return sha1,sha256


class TileResourcePreflightTests(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"original.gpkg"

    def check(self,urls,*,probe_head=False):
        sha1,sha256=original_index(self.path,urls)
        def verified(source):
            return select_original_tiles(source,expected_sha1=sha1,expected_sha256=sha256)
        with patch.object(mod,"select_original_tiles",side_effect=verified):
            return mod.inspect(self.path,probe_head=probe_head)

    def test_two_tiles_same_public_group_not_two_laz_downloads(self):
        report=self.check([U1,U1])
        self.assertEqual(report["rtree_candidate_tile_rows"],2)
        self.assertEqual(report["distinct_allowlisted_group_urls"],1)
        self.assertTrue(report["one_link_can_serve_multiple_tiles"])
        self.assertEqual(report["provider_resource_link_type_counts"],
                         {"provider_catalogue_resource":2})
        self.assertFalse(report["original_laz_or_zip_bytes_downloaded"])
        self.assertFalse(report["building_heights_verified"])
        self.assertNotIn("SYN-PRIVATE",str(report))
        self.assertNotIn("11111111-1111",str(report))

    def test_two_different_original_resource_groups(self):
        report=self.check([U1,U2])
        self.assertEqual(report["distinct_allowlisted_group_urls"],2)
        self.assertFalse(report["one_link_can_serve_multiple_tiles"])

    def test_source_link_domain_and_path_whitelist(self):
        for url in (
            "http://data.public.lu/en/datasets/r/"+("1"*36),
            "https://data.public.lu.evil.invalid/en/datasets/r/"+("1"*36),
            "https://127.0.0.1/en/datasets/r/"+("1"*36),
            "https://data.public.lu/en/datasets/r/../../internal",
            "https://data.public.lu/en/datasets/r/"+("1"*36)+"?session=private",
            "https://data.public.lu/en/datasets/r/"+("1"*36)+"#fragment",
            "https://someone@data.public.lu/en/datasets/r/"+("1"*36),
            "https://data.public.lu:444/en/datasets/r/"+("1"*36),
        ):
            with self.subTest(url=url):
                self.assertEqual(mod.classify_link(url),"not_allowlisted")

    def test_known_provider_direct_zip_accepted(self):
        path=("https://download.data.public.lu/resources/"
              "bd-l-lidar2024-releve-3d-du-territoire-luxembourgeois/"
              "20241129-132357/lidar2024-c001-r027.zip")
        self.assertEqual(mod.classify_link(path),"provider_direct_tile_group_zip")

    def test_unreviewed_resource_link_blocks_before_head(self):
        with self.assertRaisesRegex(mod.LidarLinkError,"unallowlisted"):
            self.check(["https://evil.invalid/private",U2])

    def test_head_is_not_called_by_default(self):
        with patch.object(mod,"head_source",side_effect=AssertionError("unexpected request")):
            out=self.check([U1,U2])
        self.assertFalse(out["head_checks_executed"])

    def test_head_only_after_whitelist_and_dedup(self):
        with patch.object(mod,"head_source",return_value={
            "http_status":302,"head_request_reachable":True,
            "declared_content_length_bytes":None,"destination_host_class":
            "provider_direct_tile_group_zip"}) as mock:
            result=self.check([U1,U1],probe_head=True)
        self.assertEqual(mock.call_count,1)
        self.assertEqual(result["head_probe_per_group_without_original_url"][0]["http_status"],302)
        self.assertNotIn(U1,json.dumps(result))

    def test_invalid_head_target_fails_before_network(self):
        with self.assertRaisesRegex(mod.LidarLinkError,"Refuse"):
            mod.head_source("https://evil.invalid/private.zip")


if __name__=="__main__":
    unittest.main()
