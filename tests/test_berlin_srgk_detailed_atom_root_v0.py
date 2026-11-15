# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline only official detailed flood Atom root metadata-source gates."""
import json
import unittest
from datetime import datetime, timezone

from research_runners.berlin_srgk_detailed_atom_root_v0 import (
    DetailedAtomBlocked, URL, inspect, probe,
)


def feed(links=None):
    if links is None:
        links=[
            ('self','https://gdi.berlin.de/data/ua_srgk/atom/','application/atom+xml'),
            ('alternate','https://gdi.berlin.de/data/ua_srgk/atom/0.atom','application/atom+xml'),
        ]
    edges="".join(
      f'<link href="{url}" rel="{rel}" type="{type_}"/>'
      for rel,url,type_ in links
    )
    return f'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">{edges}<entry><title>Original public service</title></entry></feed>'.encode()


class Response:
    status=200
    def __init__(self,url,raw,media="application/atom+xml"):
        self.url,self.raw=url,raw
        self.headers={"Content-Type":media}
    def geturl(self):
        return self.url
    def read(self,n):
        return self.raw[:n]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class DetailedAtomRootTests(unittest.TestCase):
    def test_exact_official_url_only(self):
        self.assertEqual(URL,"https://gdi.berlin.de/data/ua_srgk/atom/")
        self.assertNotIn("ua_srhk",URL)
    def test_just_root_metadata_and_no_downstream_admission(self):
        r=inspect(feed())
        self.assertEqual(r["original_root_link_count"],2)
        self.assertEqual(r["original_root_entries"],1)
        self.assertEqual(r["direct_root_zip_href_count"],0)
        self.assertTrue(r["child_atom_feeds_or_zip_links_not_followed"])
        self.assertFalse(r["real_depth_tiff_or_water_units_retrieved"])
        self.assertFalse(r["insurance_cat_input_admitted"])
    def test_zip_urls_counted_but_not_followed(self):
        r=inspect(feed([('alternate','https://gdi.berlin.de/data/ua_srgk/atom/test.zip','application/zip')]))
        self.assertEqual(r["direct_root_zip_href_count"],1)
        self.assertFalse(r["source_licence_for_each_raster_verified"])
        self.assertTrue(r["child_atom_feeds_or_zip_links_not_followed"])
    def test_invalid_or_abusive_xml_fails(self):
        for raw in (b"",b"<x/>",b"not xml",
            b'<!DOCTYPE feed [<!ENTITY bad SYSTEM "https://fake.tld/">]><feed/>',
            b"x"*262145,feed([])):
            with self.subTest(size=len(raw)),self.assertRaises(DetailedAtomBlocked):
                inspect(raw)
    def test_many_links_or_invalid_href_fail(self):
        many=[("alternate","https://gdi.berlin.de/a","text/xml")]*501
        with self.assertRaises(DetailedAtomBlocked):
            inspect(feed(many))
        with self.assertRaises(DetailedAtomBlocked):
            inspect(feed([("alternate","","text/xml")]))
    def test_live_style_one_fixed_get_and_no_raw_payload(self):
        calls=[]
        def fake(req,timeout):
            calls.append((req.full_url,timeout))
            return Response(req.full_url,feed())
        r=probe(opener=fake,clock=lambda:datetime(2026,11,2,tzinfo=timezone.utc))
        self.assertEqual(calls,[(URL,35)])
        self.assertEqual(r["provider_source_gets"],1)
        self.assertEqual(len(r["original_xml_sha256"]),64)
        self.assertTrue(r["raw_atom_payload_persisted"] is False)
        self.assertFalse(r["insurance_cat_input_admitted"])
        self.assertNotIn("Original public service",json.dumps(r))


if __name__=="__main__":
    unittest.main()
