# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic WFS DescribeFeatureType and geometry-property tests."""
import unittest
from datetime import datetime, timezone

from research_runners.berlin_srgk_model_area_feature_schema_v0 import (
    URL, SchemaBlocked, inspect, probe,
)


def xsd(children=''):
    return ("""<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:gml="http://www.opengis.net/gml/3.2"
           targetNamespace="https://gdi.berlin.de/data/ua_srgk">
<xs:element name="a_modellgebiete" type="ModelAreaType"/>
<xs:complexType name="ModelAreaType"><xs:sequence>
%s
</xs:sequence></xs:complexType>
</xs:schema>""" % children).encode()


def fields():
    return '<xs:element name="geom" type="gml:MultiSurfacePropertyType"/><xs:element name="layer" type="xs:string"/><xs:element name="jahr" type="xs:int"/>'


class FakeResponse:
    status = 200

    def __init__(self, url, body, media="text/xml"):
        self.url, self.body, self.headers = url, body, {"Content-Type": media}

    def geturl(self):
        return self.url

    def read(self, count):
        return self.body[:count]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class SchemaTests(unittest.TestCase):
    def test_exact_official_source_url_and_source_only_request(self):
        self.assertTrue(URL.startswith("https://gdi.berlin.de/services/wfs/ua_srgk?"))
        self.assertIn("DescribeFeatureType", URL)
        self.assertIn("a_modellgebiete", URL)
        self.assertNotIn("GetFeature", URL)

    def test_one_source_geometry_field_detected_without_values(self):
        out = inspect(xsd(fields()))
        self.assertTrue(out["single_geometry_field_confirmed"])
        self.assertEqual(out["model_area_geometry_candidate_fields"],
                         [{"property_name": "geom", "declared_type": "gml:MultiSurfacePropertyType"}])
        self.assertTrue(out["pilot_bbox_filter_still_not_validated"])
        self.assertFalse(out["model_input_admitted"])

    def test_absent_type_is_unknown_not_fabricated(self):
        out = inspect(xsd('<xs:element name="layer" type="xs:string"/>'))
        self.assertFalse(out["single_geometry_field_confirmed"])
        self.assertEqual(out["geometry_candidate_count"], 0)
        self.assertFalse(out["model_input_admitted"])

    def test_rejects_wrong_root_dtd_and_missing_feature(self):
        for raw in (
            b"not XML", b"<x/>", b"<!DOCTYPE foo><foo/>",
            xsd('<xs:element name="geom" type="gml:PointPropertyType"/>').replace(
                b'name="a_modellgebiete"', b'name="wrong_layer"'),
            b"z" * 524289,
        ):
            with self.subTest(raw=raw[:32]), self.assertRaises(SchemaBlocked):
                inspect(raw)

    def test_rejects_duplicate_feature_and_ambiguous_property(self):
        raw = xsd(fields()).replace(
            b'<xs:element name="a_modellgebiete" type="ModelAreaType"/>',
            b'<xs:element name="a_modellgebiete" type="ModelAreaType"/><xs:element name="a_modellgebiete" type="ModelAreaType"/>',
        )
        with self.assertRaisesRegex(SchemaBlocked, "uniquely"):
            inspect(raw)
        raw = xsd(fields() + '<xs:element name="geom" type="xs:string"/>')
        with self.assertRaisesRegex(SchemaBlocked, "ambiguous"):
            inspect(raw)

    def test_rejects_excessive_field_inventory(self):
        raw = xsd(fields() + ''.join(
            '<xs:element name="field%d" type="xs:int"/>' % i for i in range(300)
        ))
        with self.assertRaisesRegex(SchemaBlocked, "unbounded"):
            inspect(raw)

    def test_live_style_probe_uses_one_fixed_get_and_does_not_store_source(self):
        visited = []
        def fake_opener(req, timeout):
            visited.append((req.full_url, timeout))
            return FakeResponse(req.full_url, xsd(fields()))
        out = probe(opener=fake_opener,
                    clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(visited, [(URL, 40)])
        self.assertEqual(out["geometry_candidate_count"], 1)
        self.assertTrue(out["original_xsd_body_not_persisted"])
        self.assertFalse(out["source_feature_or_raster_bytes_retrieved"])
        self.assertFalse(out["model_input_admitted"])


if __name__ == "__main__":
    unittest.main()
