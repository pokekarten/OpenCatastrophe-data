# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic original Hessen API probe negative tests (all fake HTTP)."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from scripts import probe_hessen_alkis_building_bbox_v0 as h


def feature(geometry_type="Polygon", *, x=9.495, y=50.51):
    ring=[[x,y],[x+0.0002,y],[x+0.0002,y+0.0002],
          [x,y+0.0002],[x,y]]
    coords=[ring] if geometry_type=="Polygon" else [[ring]]
    return {"type":"Feature","id":"never-log-person-id",
            "geometry":{"type":geometry_type,"coordinates":coords},
            "properties":{"secret":"must-never-be-emitted"}}


def fixture(*, features=None, extra=None):
    doc={"type":"FeatureCollection","features":[feature()] if features is None else features,
         "links":[{"rel":"next","href":"https://invalid.invalid/forbidden"}],
         "numberMatched":12}
    if extra:
        doc.update(extra)
    return json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()


class Reply(io.BytesIO):
    status=200
    def __init__(self,raw=None,*,status=200,url=h.URL,headers=None):
        super().__init__(fixture() if raw is None else raw)
        self.status=status
        self.url=url
        self.headers=({
            "Content-Type":"application/geo+json",
            "Content-Length":str(len(self.getvalue())),
        } if headers is None else headers)
        self.read_limits=[]
    def geturl(self):
        return self.url
    def read(self,n=-1):
        self.read_limits.append(n)
        return super().read(n)


class HessenAlkisBboxTests(unittest.TestCase):
    def test_verified_exact_2d_building_collection_and_bbox_scope(self):
        self.assertIsNone(h.validate_exact_review())
        self.assertIn("/bu-core2d:Building/items",h.URL)
        self.assertEqual(h.LIMIT,5)
        self.assertTrue(9.426 < h.BBOX[0] < h.BBOX[2] < 9.5121)
        self.assertTrue(50.488 < h.BBOX[1] < h.BBOX[3] < 50.5734)

    def test_original_source_geometry_metadata_without_private_attribute(self):
        observed=h.inspect_geojson(fixture())
        self.assertEqual(observed["returned_bounded_feature_count"],1)
        self.assertEqual(observed["reported_number_matched_if_integer"],12)
        self.assertEqual(observed["polygon_count"],1)
        self.assertTrue(observed["pagination_next_link_present_not_followed"])
        self.assertFalse(observed["real_building_worldcover_overlap_verified"])
        self.assertFalse(observed["model_input_approved"])
        self.assertNotIn("never-log-person-id",json.dumps(observed))
        self.assertNotIn("secret",json.dumps(observed))

    def test_actual_request_is_exact_and_bounded_with_no_source_persistence(self):
        response=Reply()
        calls=[]
        def open_request(req,timeout):
            calls.append((req.full_url,req.get_method(),
                          req.get_header("Accept-encoding"),timeout))
            return response
        observed=h.probe(open_request=open_request)
        self.assertEqual(calls,[(h.URL,"GET","identity",h.TIMEOUT_SECONDS)])
        self.assertEqual(response.read_limits,[h.MAX_BYTES+1])
        self.assertFalse(observed["source_raw_geometry_or_attributes_persisted"])
        self.assertFalse(observed["raw_identifiers_addresses_or_coordinates_printed"])
        self.assertEqual(len(observed["source_response_sha256"]),64)
        self.assertNotIn("secret",json.dumps(observed))

    def test_second_exact_hosenfeld_profile_and_true_bbox_envelope(self):
        city=fixture(features=[feature(x=9.483,y=50.516)])
        result=h.inspect_geojson(city,query_bbox=h.HOSENFELD_BBOX)
        self.assertEqual(result["returned_bounded_feature_count"],1)
        self.assertTrue(result["geometry_available_in_this_sample"])
        calls=[]
        def fake(req,timeout):
            calls.append((req.full_url,req.get_method(),timeout))
            return Reply(raw=city)
        receipt=h.probe(open_request=fake,hosenfeld=True)
        self.assertEqual(calls,[(h.HOSENFELD_URL,"GET",h.TIMEOUT_SECONDS)])
        self.assertIn("hosenfeld",receipt["profile"])
        self.assertFalse(receipt["real_building_worldcover_overlap_verified"])
        self.assertFalse(receipt["source_raw_geometry_or_attributes_persisted"])
        outside_town=fixture(features=[feature(x=9.495,y=50.51)])
        with self.assertRaises(h.HessenSourceBlocked):
            h.inspect_geojson(outside_town,query_bbox=h.HOSENFELD_BBOX)
        with self.assertRaises(h.HessenSourceBlocked):
            h.probe(open_request=fake,hosenfeld="caller-provided")

    def test_empty_page_is_not_misrepresented_as_hessen_completeness(self):
        result=h.inspect_geojson(fixture(features=[]))
        self.assertEqual(result["returned_bounded_feature_count"],0)
        self.assertFalse(result["complete_building_inventory_proven"])
        self.assertIsNone(result["returned_geometry_envelope_intersects_exact_bbox"])
        self.assertFalse(result["geometry_available_in_this_sample"])
        self.assertFalse(result["real_building_worldcover_overlap_verified"])

    def test_reject_private_or_unsupported_geometries_and_bad_crs(self):
        tests=[
            fixture(features=[feature("Point")]),
            fixture(features=[feature(x=50.51,y=9.495)]),
            fixture(features=[feature(x=11.5,y=50.5)]),
            fixture(features=[feature()]*6),
            fixture(extra={"crs":{"type":"name","properties":{"name":"EPSG:25832"}}}),
            fixture(extra={"type":"Error"}),
            b'{"type":"FeatureCollection","features":[],"features":[]}',
            b'{"type":"FeatureCollection","features":[],"numberMatched": NaN}',
            fixture(features=[{"type":"Feature","geometry":{"type":"Polygon",
                       "coordinates":[[[9.49,50.5],[9.5,50.5],[9.5,50.51]]]},
                       "properties":{}}]),
            fixture(features=[{"type":"Feature","geometry":feature()["geometry"],
                               "properties":None}]),
        ]
        for i,raw in enumerate(tests):
            with self.subTest(case=i),self.assertRaises(h.HessenSourceBlocked):
                h.inspect_geojson(raw)

    def test_reject_status_redirect_html_encoding_and_oversize_body(self):
        good={"Content-Type":"application/geo+json",
              "Content-Length":str(len(fixture()))}
        replies=[
            Reply(status=404),
            Reply(status=302),
            Reply(url="https://evil.invalid/other"),
            Reply(headers={**good,"Content-Type":"text/html"}),
            Reply(headers={**good,"Content-Encoding":"gzip"}),
            Reply(headers={**good,"Content-Length":"9999999"}),
            Reply(raw=b"x"*(h.MAX_BYTES+1),
                  headers={"Content-Type":"application/json"}),
        ]
        for i,reply in enumerate(replies):
            with self.subTest(case=i),self.assertRaises(h.HessenSourceBlocked):
                h.probe(open_request=lambda req,timeout:reply)

    def test_opt_in_and_original_host_is_not_user_configurable(self):
        with self.assertRaises(SystemExit):
            h.main([])
        with patch.object(h,"URL","https://evil.invalid/other"):
            with self.assertRaises(h.HessenSourceBlocked):
                h.validate_exact_review()


if __name__=="__main__":
    unittest.main()
