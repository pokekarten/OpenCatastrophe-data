# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Metadata-only synthetic WFS hits conformance and strict bounded HTTP tests."""
from __future__ import annotations

import io
from unittest import TestCase, main
from unittest.mock import patch
from scripts import probe_hessen_alkis_wfs_hits_v0 as hits


def xml(*, matched="1", returned="0", member=False):
    return (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"'
        f' numberMatched="{matched}" numberReturned="{returned}">'
        + ('<wfs:member><Building/></wfs:member>' if member else '')
        + '</wfs:FeatureCollection>'
    ).encode("utf-8")


class Reply(io.BytesIO):
    status=200
    def __init__(self, body=None, *, url=hits.URL, status=200, headers=None):
        super().__init__(xml() if body is None else body)
        self.url=url
        self.status=status
        self.headers=(
            {"Content-Type":"application/gml+xml",
             "Content-Length":str(len(self.getvalue()))}
            if headers is None else headers
        )
        self.read_sizes=[]
    def geturl(self):
        return self.url
    def read(self,n=-1):
        self.read_sizes.append(n)
        return super().read(n)


class HessenWfsHitsTests(TestCase):
    def test_reviewed_hits_only_source_uri_and_axis_order(self):
        self.assertIsNone(hits.validate_reviewed_hits())
        self.assertIn("RESULTTYPE=hits",hits.QUERY)
        self.assertIn("COUNT=1",hits.QUERY)
        self.assertTrue(hits.QUERY.endswith(
            "BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258"
        ))
        with patch.object(hits,"URL","https://invalid.example/other"):
            with self.assertRaises(hits.HitsBlocked):
                hits.validate_reviewed_hits()
        with self.assertRaises(SystemExit):
            hits.main([])

    def test_count_only_does_not_fetch_building_features(self):
        evidence=hits.inspect_hits(xml(matched="5",returned="0"))
        self.assertEqual(evidence["features_in_hits_response"],0)
        self.assertEqual(evidence["number_matched_if_integer"],5)
        self.assertTrue(evidence["provider_claims_positive_matches"])
        self.assertFalse(evidence["original_feature_payload_downloaded"])
        self.assertFalse(evidence["source_building_polygon_validated"])
        self.assertFalse(evidence["model_input_approved"])

    def test_zero_and_unknown_are_not_inferred_no_buildings(self):
        empty=hits.inspect_hits(xml(matched="0"))
        unknown=hits.inspect_hits(xml(matched="unknown"))
        self.assertEqual(empty["number_matched_if_integer"],0)
        self.assertIsNone(unknown["number_matched_if_integer"])
        self.assertTrue(unknown["provider_match_count_unknown"])
        self.assertFalse(empty["model_input_approved"])

    def test_xml_hits_must_not_contain_feature_members_or_invalid_headers(self):
        cases=[
            b"",b"<ExceptionReport/>",
            xml(member=True),
            xml(returned="1"),
            xml(matched="negative"),
            xml(matched="-1"),
            b'<!DOCTYPE a [<!ENTITY x SYSTEM "https://invalid.example/bad.dtd">]>'+xml(),
            xml()+b"x",
            b"x"*(hits.MAX_BYTES+1),
        ]
        for index, raw in enumerate(cases):
            with self.subTest(index=index),self.assertRaises(hits.HitsBlocked):
                hits.inspect_hits(raw)

    def test_one_only_exact_http_get_and_no_source_raw_output(self):
        response=Reply()
        calls=[]
        def fake(req,timeout):
            calls.append((req.full_url,req.get_method(),
                          req.get_header("Accept-encoding"),timeout))
            return response
        result=hits.probe(open_request=fake)
        self.assertEqual(calls,[(hits.URL,"GET","identity",hits.TIMEOUT_SECONDS)])
        self.assertEqual(response.read_sizes,[hits.MAX_BYTES+1])
        self.assertEqual(len(result["original_hits_sample_sha256"]),64)
        self.assertFalse(result["raw_source_xml_stored"])
        self.assertFalse(result["source_ids_attributes_or_coordinates_emitted"])

    def test_http_bad_status_redirect_mime_size_or_encoding_rejected(self):
        default={"Content-Type":"application/xml","Content-Length":str(len(xml()))}
        cases=[
            Reply(status=302),Reply(status=500),
            Reply(url="https://invalid.example/other"),
            Reply(headers={**default,"Content-Type":"text/html"}),
            Reply(headers={**default,"Content-Encoding":"gzip"}),
            Reply(headers={**default,"Content-Length":"123456789"}),
            Reply(body=b"x"*(hits.MAX_BYTES+1),
                  headers={"Content-Type":"application/xml"}),
        ]
        for index,response in enumerate(cases):
            with self.subTest(index=index),self.assertRaises(hits.HitsBlocked):
                hits.probe(open_request=lambda req,timeout:response)


if __name__=="__main__":
    main()
