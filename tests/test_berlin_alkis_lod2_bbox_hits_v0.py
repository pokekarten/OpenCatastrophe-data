# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only WFS 2.0 resultType=hits two-provider count checks."""
from __future__ import annotations
from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_alkis_lod2_bbox_hits_v0 import (
    MAX_BYTES, URLS, WfsCountError, parse_hits, probe,
)


def hits(n: str, returned: str = "0") -> bytes:
    return (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" '
        f'numberMatched="{n}" numberReturned="{returned}"/>'
    ).encode()


class Reply(io.BytesIO):
    status=200
    def __init__(self, raw:bytes,url:str,media="application/xml"):
        super().__init__(raw)
        self.url=url
        self.headers={"Content-Type":media}
    def geturl(self):return self.url


class WfsHitsTests(unittest.TestCase):
    def test_fixed_two_unchangeable_source_queries(self):
        self.assertEqual(len(URLS),2)
        for url in URLS.values():
            self.assertIn("resultType=hits",url)
            self.assertIn("count=1",url)
            self.assertIn("EPSG%3A25833",url)
            self.assertIn("391700",url)
            self.assertIn("391900",url)

    def test_exact_source_xml_counts(self):
        self.assertEqual(parse_hits(hits("214"))["numberMatched"],214)
        self.assertFalse(parse_hits(hits("0"))["feature_geometry_bytes_retrieved"])

    def test_reject_unknown_count_leaked_feature_and_entity(self):
        for raw in (
            hits("unknown"),hits("not_a_number"),hits("2000001"),
            hits("18","1"),b"<!DOCTYPE foo><FeatureCollection/>",
            b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows"/>',
            b"",b"x"*(MAX_BYTES+1),
            hits("3").replace(b'/>',b'><wfs:member/></wfs:FeatureCollection>'),
            hits("3").replace(b' numberReturned="0"',b''),
            hits("3").replace(b'/>',b'><gml:Polygon xmlns:gml="http://www.opengis.net/gml/3.2"/></wfs:FeatureCollection>'),
            hits("3").replace(b'/>',b'>private source attribute text</wfs:FeatureCollection>'),
        ):
            with self.subTest(payload=raw[:60]),self.assertRaises(WfsCountError):
                parse_hits(raw)

    def test_two_metadata_only_requests_and_no_source_feature_bytes(self):
        calls=[]
        def fake(req,timeout):
            calls.append(req.full_url)
            name="alkis" if req.full_url==URLS["alkis"] else "height_2022"
            return Reply(hits("14" if name=="alkis" else "19"),req.full_url)
        result=probe(opener=fake,clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(calls,[URLS["alkis"],URLS["height_2022"]])
        self.assertTrue(result["first_five_WFS_features_are_not_exhaustive"])
        self.assertEqual(result["count_receipts"]["alkis"]["numberMatched"],14)
        self.assertEqual(result["count_receipts"]["height_2022"]["numberMatched"],19)
        self.assertFalse(result["actual_geometry_or_height_values_obtained"])
        self.assertFalse(result["staged_insurer_or_CAT_db_modified"])

    def test_refuse_redirect_or_non_xml(self):
        with self.assertRaises(WfsCountError):
            probe(opener=lambda req,timeout:Reply(hits("5"),"https://other.invalid/"))
        with self.assertRaises(WfsCountError):
            probe(opener=lambda req,timeout:Reply(hits("5"),req.full_url,media="text/html"))


if __name__=="__main__":
    unittest.main()
