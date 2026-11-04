# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only safety tests; never include original LiDAR polygons/URLs."""
from __future__ import annotations
import json
import hashlib
from unittest import mock
from pathlib import Path
import tempfile
import unittest

from research_runners.lu_act2019_original_lidar_tile_index_v0 import (
    CRS84, OriginalIndexError, _unique_pairs, _validate_asset_url,
    _validate_polygon, _reject_constant, profile_index, verify_original,
    SITES,
)

FAKE_PROVIDER = "https://download.data.public.lu/resources/lidar-2019-releve-3d-du-territoire-luxembourgeois/20200101-000000/synthetic-test.zip"
BOX = [[6.1,49.6],[6.2,49.6],[6.2,49.7],[6.1,49.7],[6.1,49.6]]


def fixture(*, urls=None):
    return {"type":"FeatureCollection","crs":{"type":"name","properties":{"name":CRS84}},
        "features":[{"type":"Feature","properties":{"url":u},
                     "geometry":{"type":"Polygon","coordinates":[[list(point) for point in BOX]]}}
                    for u in (urls or [FAKE_PROVIDER])]}


class OriginalLiDARIndexTests(unittest.TestCase):
    def test_known_public_research_sites_locked(self):
        self.assertEqual(SITES,{"luxembourg-city":(6.1319,49.6116),
                                "berdorf-village":(6.348821,49.820946)})

    def test_synthetic_geojson_feature_collection_accepted(self):
        self.assertEqual(len(profile_index(fixture())),1)

    def test_original_urls_only_official_zip_origin(self):
        _validate_asset_url(FAKE_PROVIDER)
        for url in ("http://download.data.public.lu/x.zip",
                    "https://example.org/foreign.zip",
                    FAKE_PROVIDER+"?token=secret",
                    "https://bad@download.data.public.lu/resources/lidar-2019-releve-3d-du-territoire-luxembourgeois/x.zip"):
            with self.subTest(url=url):
                with self.assertRaises(OriginalIndexError):
                    _validate_asset_url(url)

    def test_duplicate_original_urls_fail_closed(self):
        with self.assertRaises(OriginalIndexError):
            profile_index(fixture(urls=[FAKE_PROVIDER,FAKE_PROVIDER]))

    def test_schema_changed_or_unreviewed_projection_rejected(self):
        p=fixture()
        p["crs"]["properties"]["name"]="EPSG:3857"
        with self.assertRaises(OriginalIndexError):
            profile_index(p)

    def test_broken_ring_closedness_rejected(self):
        with self.assertRaises(OriginalIndexError):
            _validate_polygon({"type":"Polygon","coordinates":[BOX[:-1]]})

    def test_missing_original_feature_url_rejected(self):
        p=fixture()
        p["features"][0]["properties"]={}
        with self.assertRaises(OriginalIndexError):
            profile_index(p)

    def test_nonfinite_original_coordinate_rejected(self):
        p=fixture()
        p["features"][0]["geometry"]["coordinates"][0][0][0]=float("nan")
        with self.assertRaises(OriginalIndexError):
            profile_index(p)

    def test_bad_original_geometry_type_rejected(self):
        with self.assertRaises(OriginalIndexError):
            _validate_polygon({"type":"Point","coordinates":[6.1,49.6]})

    def test_duplicate_json_property_keys_rejected(self):
        with self.assertRaises(OriginalIndexError):
            json.loads('{"type":"FeatureCollection","type":"Point"}',
                       object_pairs_hook=_unique_pairs)

    def test_nan_constant_in_original_json_rejected(self):
        with self.assertRaises(OriginalIndexError):
            json.loads('{"a": NaN}',parse_constant=_reject_constant)

    def test_original_source_digest_mismatch_blocks_without_spatial_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"synthetic.geojson"
            f.write_text(json.dumps(fixture()),encoding="utf-8")
            with self.assertRaisesRegex(OriginalIndexError,"publisher SHA1"):
                verify_original(f)

    def test_publisher_sha1_alone_cannot_bypass_frozen_sha256(self):
        from research_runners import lu_act2019_original_lidar_tile_index_v0 as mod
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/"synthetic.geojson"
            raw=json.dumps(fixture()).encode("utf-8")
            f.write_bytes(raw)
            with mock.patch.object(mod,"PUBLISHED_SHA1",hashlib.sha1(raw).hexdigest()):
                with self.assertRaisesRegex(OriginalIndexError, "SHA256/size"):
                    verify_original(f)

    def test_frozen_actual_receipt_values_are_specific(self):
        from research_runners.lu_act2019_original_lidar_tile_index_v0 import (
            OBSERVED_FEATURES, OBSERVED_ORIGINAL_BYTES, OBSERVED_ORIGINAL_SHA256,
            OBSERVED_STUDY_TILE_COUNTS,
        )
        self.assertEqual(OBSERVED_FEATURES, 1287)
        self.assertEqual(OBSERVED_ORIGINAL_BYTES, 450512)
        self.assertEqual(len(OBSERVED_ORIGINAL_SHA256), 64)
        self.assertEqual(OBSERVED_STUDY_TILE_COUNTS, {"luxembourg-city":2,"berdorf-village":1})

    def test_missing_original_asset_rejected_without_network(self):
        with self.assertRaises(OriginalIndexError):
            verify_original(Path("definitely-missing-synthetic-lidar.geojson"))

    def test_no_silent_feature_cap_exceedance(self):
        with self.assertRaises(OriginalIndexError):
            profile_index(fixture(),min_items=2001)


if __name__=="__main__":
    unittest.main()
