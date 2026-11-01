# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only WFS model-area schema / count-only hits source tests."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
import unittest

from research_runners.berlin_srgk_wfs_schema_hits_v0 import (
    BASE, SCHEMA_URL, CONTROL_HITS_URL, PILOT_HITS_URL,
    CAPS, MetadataBlocked, _fetch, inspect_schema, inspect_hits,
    classify_counts, probe,
)


def xsd():
    return b'''<?xml version="1.0" encoding="utf-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:gml="http://www.opengis.net/gml/3.2">
<xsd:element name="a_modellgebiete" type="a_modellgebieteType"/>
<xsd:complexType name="a_modellgebieteType"><xsd:sequence>
<xsd:element name="geom" type="gml:MultiSurfacePropertyType"/>
<xsd:element name="gisid" type="xsd:string"/>
<xsd:element name="jahr" type="xsd:integer"/>
</xsd:sequence></xsd:complexType>
</xsd:schema>'''


def hits(number):
    return (f'''<?xml version="1.0" encoding="utf-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
numberMatched="{number}" numberReturned="0"/>''').encode()


class Fake(BytesIO):
    def __init__(self, url, raw, *, status=200, media="application/xml", encoding="identity"):
        super().__init__(raw)
        self.status = status
        self._url = url
        self.headers = {"Content-Length": str(len(raw)),
                        "Content-Type": media, "Content-Encoding": encoding}
    def geturl(self):
        return self._url


class BerlinOriginalWfsSchemaHitsTests(unittest.TestCase):
    def test_schema_extracts_public_geom_candidate_without_source_feature(self):
        record = inspect_schema(xsd())
        self.assertEqual(record["geometry_property_name_candidates"], ["geom"])
        self.assertTrue(record["schema_is_wellformed_xsd"])
        self.assertFalse(record["geometry_property_type_proven_for_filter"])
        self.assertFalse(record["filter_capabilities_and_server_bbox_behavior_proven"])
        self.assertFalse(record["geometry_downloaded_or_stored"])

    def test_hits_only_xml_requires_zero_returned_features(self):
        result = inspect_hits(hits(0))
        self.assertEqual(result["number_matched"], 0)
        self.assertTrue(result["no_source_feature_or_coordinates_read"])
        with self.assertRaisesRegex(MetadataBlocked, "positive features"):
            inspect_hits(hits(1).replace(b'numberReturned="0"', b'numberReturned="1"'))
        with self.assertRaisesRegex(MetadataBlocked, "source features"):
            inspect_hits(hits(1).replace(b'/>', b'><wfs:member/></wfs:FeatureCollection>'))
        with self.assertRaises(MetadataBlocked):
            inspect_hits(b'<ServiceExceptionReport/>')

    def test_counts_never_claim_coverage_not_even_if_zero(self):
        self.assertEqual(
            classify_counts({"number_matched": 10}, {"number_matched": 0}),
            "PILOT_HITS_ZERO_NOT_A_PROVEN_COVERAGE_OR_DRYNESS")
        self.assertEqual(
            classify_counts({"number_matched": 10}, {"number_matched": 1}),
            "PILOT_HITS_POSITIVE_REQUIRES_EXACT_GEOMETRY_INTERSECTION")
        self.assertEqual(
            classify_counts({"number_matched": 10}, {"number_matched": None}),
            "COUNT_UNRESOLVED_NO_SPATIAL_ASSERTION")
        with self.assertRaises(MetadataBlocked):
            classify_counts({"number_matched": 1}, {"number_matched": 2})

    def test_exact_three_source_requests_no_geometry_output(self):
        urls = []
        responses = {SCHEMA_URL: xsd(), CONTROL_HITS_URL: hits(19),
                     PILOT_HITS_URL: hits(0)}
        def opener(req):
            urls.append(req.full_url)
            return Fake(req.full_url, responses[req.full_url])
        out = probe(opener=opener,
                    clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(urls, [SCHEMA_URL, CONTROL_HITS_URL, PILOT_HITS_URL])
        self.assertTrue(all(u.startswith(BASE+"?") for u in urls))
        self.assertEqual(out["source_count_comparison_status"],
                         "PILOT_HITS_ZERO_NOT_A_PROVEN_COVERAGE_OR_DRYNESS")
        self.assertFalse(out["original_WFS_bbox_honored_proven"])
        self.assertFalse(out["pilot_covered_or_not_covered_proven"])
        self.assertFalse(out["model_input_admitted"])
        self.assertFalse(out["original_source_xml_or_feature_geometries_persisted"])
        self.assertNotIn("coordinates", json.dumps(out))
        self.assertNotIn("GML", json.dumps(out))

    def test_untrusted_xml_entities_dtd_and_non_xml_schema_fail_closed(self):
        for raw in (b'<!DOCTYPE wfs [<!ENTITY x "XX">]><schema/>',
                    b'<ServiceExceptionReport/>', b'x'* (512*1024 + 1),
                    b'<xsd:schema', b''):
            with self.subTest(len=len(raw)), self.assertRaises(MetadataBlocked):
                inspect_schema(raw)
        with self.assertRaises(MetadataBlocked):
            inspect_schema(xsd().replace(b'name="geom"', b'name="bad location / private"'))

    def test_bounded_http_fixed_identity_and_refuse_unreviewed_transport(self):
        url = SCHEMA_URL
        with self.assertRaisesRegex(MetadataBlocked, "unapproved"):
            _fetch("https://evil.example.net/wfs")
        for kwargs in ({"status": 206}, {"media": "image/png"}, {"encoding": "gzip"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(MetadataBlocked):
                _fetch(url, opener=lambda req: Fake(req.full_url, xsd(), **kwargs))
        with self.assertRaisesRegex(MetadataBlocked, "exceeds cap"):
            _fetch(CONTROL_HITS_URL, opener=lambda req:
                   Fake(req.full_url, b"x"*17000))

    def test_wfs_xml_unknown_count_is_ambiguous_not_no_coverage(self):
        out = inspect_hits(hits("unknown"))
        self.assertIsNone(out["number_matched"])
        self.assertEqual(
            classify_counts({"number_matched": None}, {"number_matched": None}),
            "COUNT_UNRESOLVED_NO_SPATIAL_ASSERTION")
        with self.assertRaises(MetadataBlocked):
            inspect_hits(hits("-1"))
        with self.assertRaises(MetadataBlocked):
            inspect_hits(hits("NaN"))

    def test_source_schema_with_bounded_missing_geom_property_does_not_invent_one(self):
        raw = xsd().replace(b'gml:MultiSurfacePropertyType', b'xsd:string')
        record = inspect_schema(raw)
        self.assertEqual(record["geometry_property_name_candidates"], [])
        self.assertFalse(record["filter_capabilities_and_server_bbox_behavior_proven"])


if __name__ == "__main__":
    unittest.main()
