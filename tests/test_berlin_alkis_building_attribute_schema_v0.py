# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic XSD / official five-building GeoJSON / byte-limited WFS tests."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_alkis_building_attribute_schema_v0 import (
    DESCRIBE_URL, FEATURE_URL, SCHEMA_MAX_BYTES, SAFE_FIELDS,
    AttributeAuditError, inspect_sample_fields, inspect_schema_xml, probe,
)
from tests.test_berlin_alkis_gebaeude_five_feature_join_v0 import (
    HAS_SPATIAL, fixture, raw,
)


def schema() -> bytes:
    return (b'<?xml version="1.0"?>'
            b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" '
            b'targetNamespace="https://gdi.berlin.de/alkis">'
            b'<xs:element name="gebaeude" type="xs:string"/>'
            b'<xs:element name="gfk" type="xs:int"/>'
            b'<xs:element name="aog" type="xs:integer"/>'
            b'<xs:element name="aug" type="xs:integer"/>'
            b'<xs:element name="uuid" type="xs:string"/>'
            b'</xs:schema>')


class Reply(io.BytesIO):
    status = 200
    def __init__(self, b: bytes, *, url: str, media: str):
        super().__init__(b)
        self.url = url
        self.headers = {"Content-Type": media}
    def geturl(self):
        return self.url


class SchemaTests(unittest.TestCase):
    def test_only_approved_public_attribute_names_printed(self):
        report = inspect_schema_xml(schema())
        self.assertEqual(report["official_documented_fields_in_xsd"],
                         ["aog", "aug", "gfk"])
        self.assertEqual(report["other_product_fields_in_xsd"], [])
        self.assertFalse(report["all_xsd_field_names_exported"])

    def test_xml_entity_malicious_or_service_exception_fails_closed(self):
        for b in (
            b"<!DOCTYPE x [<!ENTITY bad 'secret'>]><xs:schema/>",
            b'<!doctype x SYSTEM "http://example.com/bad">',
            b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows"/>',
            b'<schema/>', b'garbage',
            b"", b"x"*(SCHEMA_MAX_BYTES+1),
        ):
            with self.subTest(payload=b[:40]), self.assertRaises(AttributeAuditError):
                inspect_schema_xml(b)

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed GIS dependencies available")
    def test_source_payload_is_reduced_to_safe_field_counts_only(self):
        f = fixture(n=2)
        f["features"][0]["properties"].update({
            "gfk": 1000, "bezgfk": "Wohnhaus", "aog": 4,
            "hnr": "private-test-address", "uuid": "source-private-id",
        })
        f["features"][1]["properties"].update({
            "gfk": 1000, "bezgfk": None, "aog": None,
            "hnr": "another-address", "uuid": "other-private-id",
        })
        report = inspect_sample_fields(raw(f))
        self.assertEqual(report["official_field_presence_counts"]["gfk"], 2)
        self.assertEqual(report["official_field_non_null_counts"]["gfk"], 2)
        self.assertEqual(report["official_field_non_null_counts"]["aog"], 1)
        self.assertEqual(report["official_field_non_null_counts"]["bezgfk"], 1)
        self.assertFalse(report["building_vs_part_classification_verified"])
        self.assertFalse(report["building_construction_year_verified"])
        self.assertNotIn("private-test-address", str(report))
        self.assertNotIn("Wohnhaus", str(report))
        self.assertNotIn("private-id", str(report))

    @unittest.skipUnless(HAS_SPATIAL, "Reviewed GIS dependencies available")
    def test_two_fixed_requests_single_safe_source_receipt(self):
        f = fixture(n=2)
        f["features"][0]["properties"]["gfk"] = 1000
        b = raw(f)
        calls = []
        def fake(req, timeout):
            calls.append((req.full_url, timeout))
            if req.full_url == DESCRIBE_URL:
                return Reply(schema(), url=DESCRIBE_URL, media="application/xml")
            if req.full_url == FEATURE_URL:
                return Reply(b, url=FEATURE_URL, media="application/json")
            raise AssertionError("unexpected WFS source request")
        report = probe(opener=fake, clock=lambda:datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual(len(calls),2)
        self.assertEqual(report["exact_requests_per_proof"],2)
        self.assertEqual(report["sampled_valid_original_polygons"],2)
        self.assertEqual(report["field_in_schema_but_not_in_five_feature_sample"],["aog", "aug"])
        self.assertFalse(report["original_source_bytes_persisted"])
        self.assertFalse(report["CAT_database_modified"])
        self.assertFalse(report["attributes_approved_for_insured_value_model"])
        self.assertNotIn("coordinates", str(report))
        self.assertNotIn("uuid", str(report))
        self.assertEqual(set(SAFE_FIELDS), set(report["official_field_presence_counts"]))

    @unittest.skipUnless(HAS_SPATIAL,"Reviewed GIS dependencies available")
    def test_foreign_provider_response_and_wrong_types_fail(self):
        def fake(req, timeout):
            if req.full_url == DESCRIBE_URL:
                return Reply(schema(), url=DESCRIBE_URL,
                             media="text/html")
            raise AssertionError("should not fetch real building source")
        with self.assertRaises(AttributeAuditError):
            probe(opener=fake)
        def redirected(req, timeout):
            return Reply(schema(), url="https://unrelated.example/x",
                         media="text/xml")
        with self.assertRaises(AttributeAuditError):
            probe(opener=redirected)
        bad = fixture(n=1)
        bad["features"][0]["properties"]["gfk"] = {"secret": "nested"}
        with self.assertRaises(AttributeAuditError):
            inspect_sample_fields(raw(bad))


if __name__ == "__main__":
    unittest.main()
