# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fictional single-roof deflate ZIP prefix; no real building records."""
from __future__ import annotations

import json
import struct
import unittest
import zlib

from research_runners.microsoft_louisiana_original_building_sample_v0 import (
    SAMPLE_COMPRESSED_BYTES, SampleError, sample,
)
from tests.test_microsoft_louisiana_original_zip_receipt_v0 import (
    ETAG, N, fake_fetch,
)


def tiny_polygon():
    return {"type":"Feature","properties":{},
            "geometry":{"type":"Polygon","coordinates":[[
                [-90.1,29.9],[-90.0,29.9],[-90.0,30.0],
                [-90.1,30.0],[-90.1,29.9],
            ]]}}


def source_prefix(*, changed_geometry=None, text_override=None,
                  wrong_header=False, wrong_name=False):
    items=[tiny_polygon() if changed_geometry is None else changed_geometry]
    text=(json.dumps({"type":"FeatureCollection","features":items},
                     separators=(",",":"))
          if text_override is None else text_override)
    z=zlib.compressobj(level=6,wbits=-15)
    compressed=z.compress(text.encode("utf-8"))+z.flush()
    name=b"wrong.json" if wrong_name else b"Louisiana.geojson"
    header=struct.pack(
        "<IHHHHHIIIHH",0x04034b50,20,8,8,0,0,0,0,0,len(name),0,
    )
    if wrong_header:
        header=b"FAIL"+header[4:]
    data=header+name+compressed
    return data.ljust(SAMPLE_COMPRESSED_BYTES,b"\x00")


def mocked_full_source(*, document=None, text_override=None,
                       invalid_header=False, invalid_name=False,
                       ignores_range=False, changed_tag=False):
    base=fake_fetch()
    prefix=source_prefix(
        changed_geometry=document,text_override=text_override,
        wrong_header=invalid_header,wrong_name=invalid_name)
    def get(request, limit):
        if request.get_method()!="HEAD" and request.get_header("Range")==(
                f"bytes=0-{SAMPLE_COMPRESSED_BYTES-1}"):
            if ignores_range:
                return 200,{"content-length":"1"},b"\x00"
            headers={"content-length":str(SAMPLE_COMPRESSED_BYTES),
                     "content-range":f"bytes 0-{SAMPLE_COMPRESSED_BYTES-1}/{N}",
                     "etag":'"wrong-etag"' if changed_tag else ETAG}
            return 206,headers,prefix
        return base(request,limit)
    return get


class OriginalBuildingPrefixTests(unittest.TestCase):
    def test_tiny_synthetic_valid_polygon_is_not_admission(self):
        result=sample(fetch=mocked_full_source())
        self.assertEqual(result["first_completed_nonrandom_building_features"],1)
        self.assertEqual(result["valid_sample_polygon_features"],1)
        self.assertFalse(result["sample_statistically_representative"])
        self.assertFalse(result["insured_asset_or_policy_verified"])
        self.assertFalse(result["cat_model_input_admitted"])
        self.assertNotIn("geometry",result)
        self.assertNotIn("coordinates",result)

    def test_original_zip_prefix_must_match_expected_magic(self):
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(invalid_header=True))

    def test_original_member_filename_must_match_receipt(self):
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(invalid_name=True))

    def test_bounded_range_required(self):
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(ignores_range=True))

    def test_original_object_etag_cannot_change(self):
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(changed_tag=True))

    def test_no_unexpected_point_geometry(self):
        item=tiny_polygon()
        item["geometry"]={"type":"Point","coordinates":[-90.1,29.9]}
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(document=item))

    def test_out_of_louisiana_bbox_cannot_be_silent(self):
        item=tiny_polygon()
        item["geometry"]["coordinates"]=[[
            [-120,35],[-119,35],[-119,36],[-120,36],[-120,35],
        ]]
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(document=item))

    def test_unrecognized_source_container_rejected(self):
        with self.assertRaises(SampleError):
            sample(fetch=mocked_full_source(
                text_override='{"type":"GeometryCollection","geometries":[]}'))

    def test_first_records_allow_no_insurer_assumptions(self):
        item=tiny_polygon()
        item["properties"]={"label":"synthetic","policy_id":"should-not-output"}
        result=sample(fetch=mocked_full_source(document=item))
        self.assertFalse(result["insured_asset_or_policy_verified"])
        self.assertNotIn("policy_id",str(result))


if __name__=="__main__":
    unittest.main()
