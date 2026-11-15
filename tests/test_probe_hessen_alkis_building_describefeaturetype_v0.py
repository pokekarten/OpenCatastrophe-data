# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic WFS Building DescribeFeatureType original-XSD checks."""
from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from scripts import probe_hessen_alkis_building_describefeaturetype_v0 as xsd


def fixture(*, with_building=True, target=xsd.BUILDING_NS, with_import=True):
    types = (
        '<xsd:element name="Building" type="bu-core2d:BuildingType"/>'
        if with_building else
        '<xsd:element name="Other" type="xsd:string"/>'
    )
    imports = (
        '<xsd:import namespace="http://example.invalid/schema" '
        'schemaLocation="https://example.invalid/never-follow.xsd"/>'
        if with_import else ""
    )
    return (
        f'<xsd:schema xmlns:xsd="{xsd.XSD_NS}" '
        f'targetNamespace="{target}" '
        'xmlns:bu-core2d="http://inspire.ec.europa.eu/schemas/bu-core2d/4.0">'
        + imports + types + '</xsd:schema>'
    ).encode("utf-8")


class Reply(io.BytesIO):
    status = 200
    def __init__(self, data=None, *, url=xsd.URL, status=200, headers=None):
        super().__init__(fixture() if data is None else data)
        self.url = url
        self.status = status
        self.headers = (
            {"Content-Type": "text/xml", "Content-Length": str(len(self.getvalue()))}
            if headers is None else headers
        )
        self.read_sizes = []
    def geturl(self):
        return self.url
    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class HessenBuildingXsdTests(unittest.TestCase):
    def test_exact_original_service_request_without_feature_payload(self):
        self.assertIsNone(xsd.validate_exact_source())
        self.assertIn("REQUEST=DescribeFeatureType", xsd.URL)
        self.assertIn("TYPENAMES=bu-core2d:Building", xsd.URL)
        with patch.object(xsd, "URL", "https://invalid.example/a"):
            with self.assertRaises(xsd.SchemaBlocked):
                xsd.validate_exact_source()
        with self.assertRaises(SystemExit):
            xsd.main([])

    def test_named_global_building_type_is_metadata_not_imported_schema(self):
        data = xsd.inspect_xsd(fixture())
        self.assertTrue(data["global_building_element_declared"])
        self.assertTrue(data["target_namespace_matches_building_if_declared"])
        self.assertEqual(data["building_type_local_declaration_if_present"], "bu-core2d:BuildingType")
        self.assertEqual(data["xsd_import_count_not_followed"], 1)
        self.assertEqual(data["schema_dependencies_downloaded"], 0)
        self.assertFalse(data["building_type_structure_fully_resolved"])
        self.assertFalse(data["provider_getfeature_number_returned_discrepancy_resolved"])
        self.assertFalse(data["model_input_approved"])
        self.assertNotIn("never-follow", str(data))

    def test_aggregator_xsd_with_no_element_cannot_claim_building_schema(self):
        data = xsd.inspect_xsd(fixture(with_building=False))
        self.assertFalse(data["global_building_element_declared"])
        self.assertIsNone(data["building_type_local_declaration_if_present"])
        self.assertFalse(data["source_building_polygon_validated"])

    def test_reject_non_schema_wrong_target_duplicate_or_entities(self):
        cases = [
            b"", b"<ExceptionReport/>", b"<schema/>",
            b"invalid-xsd", b"x"*(xsd.MAX_BYTES+1),
            fixture(target="http://invalid.example/unrelated"),
            fixture().replace(b"</xsd:schema>", b'<xsd:element name="Building"/></xsd:schema>'),
            b'<!DOCTYPE x [<!ENTITY y SYSTEM "https://invalid.example/never.dtd">]>' + fixture(),
            fixture() + b"junk",
        ]
        for i, raw in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(xsd.SchemaBlocked):
                xsd.inspect_xsd(raw)

    def test_single_original_http_request_replies_metadata_only(self):
        answer = Reply()
        seen = []
        def fake(req, timeout):
            seen.append((req.get_method(), req.full_url,
                         req.get_header("Accept-encoding"), timeout))
            return answer
        receipt = xsd.probe(open_request=fake)
        self.assertEqual(seen, [("GET", xsd.URL, "identity", xsd.TIMEOUT_SECONDS)])
        self.assertEqual(answer.read_sizes, [xsd.MAX_BYTES+1])
        self.assertFalse(receipt["raw_source_xml_persisted"])
        self.assertFalse(receipt["source_building_attributes_or_coordinates_emitted"])
        self.assertEqual(len(receipt["original_xsd_sha256"]), 64)
        self.assertFalse(receipt["model_input_approved"])

    def test_bad_http_mime_encoding_status_size_redirect_are_blocked(self):
        standard = {
            "Content-Type": "text/xml",
            "Content-Length": str(len(fixture())),
        }
        replies = [
            Reply(status=404), Reply(status=206),
            Reply(url="https://invalid.example/redirect"),
            Reply(headers={**standard, "Content-Type": "text/html"}),
            Reply(headers={**standard, "Content-Encoding": "gzip"}),
            Reply(headers={**standard, "Content-Length": "2000000"}),
            Reply(data=b"z"*(xsd.MAX_BYTES+1), headers={"Content-Type": "application/xml"}),
        ]
        for i, reply in enumerate(replies):
            with self.subTest(i=i), self.assertRaises(xsd.SchemaBlocked):
                xsd.probe(open_request=lambda req, timeout: reply)


if __name__ == "__main__":
    unittest.main()
