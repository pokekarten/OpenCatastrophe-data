# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only independent Berlin LoD2-derived height WFS receipt tests."""
from __future__ import annotations
from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_umweltatlas_height_wfs_metadata_v0 import (
    URL, TIMEOUT, MAX_BYTES, BerlinHeightWfsError,
    inspect_height_service, probe,
)


def synthetic_xml() -> bytes:
    return (b'<?xml version="1.0"?>'
            b'<wfs:WFS_Capabilities version="2.0.0" '
            b'xmlns:wfs="http://www.opengis.net/wfs/2.0">'
            b'<wfs:FeatureTypeList><wfs:FeatureType>'
            b'<wfs:Name>ua_gebaeudehoehen:gebaeudehoehen2022</wfs:Name>'
            b'<wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25833</wfs:DefaultCRS>'
            b'</wfs:FeatureType></wfs:FeatureTypeList>'
            b'</wfs:WFS_Capabilities>')


class FakeResponse(io.BytesIO):
    status=200
    def __init__(self, content: bytes, *, url=URL, media="application/xml"):
        super().__init__(content)
        self.url=url
        self.headers={"Content-Type":media}
    def geturl(self):
        return self.url


class OfficialHeightSourceTests(unittest.TestCase):
    def test_separate_valid_building_height_layer_metadata(self):
        d=inspect_height_service(synthetic_xml())
        self.assertEqual(d["height_candidate_feature_type_count"],1)
        self.assertFalse(d["provider_original_height_values_obtained"])
        self.assertFalse(d["official_source_identifier_mapped_to_ALKIS"])
        self.assertFalse(d["object_building_vs_part_mapping_verified"])

    def test_one_fixed_request_does_not_claim_building_enrichment(self):
        calls=[]
        def fake(req, timeout):
            calls.append(req.full_url)
            self.assertEqual(timeout,TIMEOUT)
            return FakeResponse(synthetic_xml())
        d=probe(opener=fake,clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(calls,[URL])
        self.assertFalse(d["height_or_age_inferred_to_insured_buildings"])
        self.assertFalse(d["CAT_database_modified"])
        self.assertEqual(len(d["original_response_sha256"]),64)
        self.assertTrue(d["catalogue_license_label"].startswith("dl-de-"))

    def test_fail_closed_wrong_root_redirect_oversize_media_version(self):
        for raw in (
            b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows"/>',
            b'<!DOCTYPE a [<!ENTITY h "bad">]><WFS_Capabilities>&h;</WFS_Capabilities>',
            b'<notCapabilities/>', b'',
            b'0'*(MAX_BYTES+1)
        ):
            with self.subTest(payload=raw[:25]), self.assertRaises(BerlinHeightWfsError):
                inspect_height_service(raw)
        for response in (
            FakeResponse(synthetic_xml(),url="https://attacker.example/other"),
            FakeResponse(synthetic_xml(),media="text/html"),
            FakeResponse(b'<!doctype html><html></html>')
        ):
            with self.assertRaises(BerlinHeightWfsError):
                probe(opener=lambda req,timeout:response)


if __name__=="__main__":
    unittest.main()
