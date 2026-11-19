# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic XML + injected fake WFS network: never live on CI."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import unittest

from research_runners.berlin_alkis_gebaeude_wfs_capabilities_v0 import (
    URL, MAX_BYTES, TIMEOUT, BerlinWfsError, inspect_capabilities,
    retrieve_capabilities,
)


def xml(*, name="alkis:gebaeude", crs="urn:ogc:def:crs:EPSG::25833",
        version="2.0.0") -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" '
        f'version="{version}">'
        f'<wfs:FeatureTypeList><wfs:FeatureType>'
        f'<wfs:Name>{name}</wfs:Name>'
        f'<wfs:DefaultCRS>{crs}</wfs:DefaultCRS>'
        f'</wfs:FeatureType></wfs:FeatureTypeList>'
        f'</wfs:WFS_Capabilities>'
    ).encode()


class FakeResponse(io.BytesIO):
    status = 200

    def __init__(self, data: bytes, *, url: str = URL,
                 content_type: str = "application/xml; charset=utf-8"):
        super().__init__(data)
        self.url = url
        self.headers = {"Content-Type": content_type}

    def geturl(self):
        return self.url


class BerlinWfsCapabilitiesTests(unittest.TestCase):
    def test_public_layer_names_and_crs_metadata_only(self):
        report = inspect_capabilities(xml())
        self.assertEqual(report["wfs_version"], "2.0.0")
        self.assertEqual(report["advertised_feature_type_count"], 1)
        self.assertEqual(report["candidate_building_feature_types"], [{
            "name": "alkis:gebaeude",
            "advertised_crs": ["urn:ogc:def:crs:EPSG::25833"],
        }])
        self.assertFalse(report["source_geometry_or_owner_data_obtained"])
        self.assertFalse(report["provider_data_imported"])

    def test_fixed_url_injected_network_receipt(self):
        def fake(req, timeout):
            self.assertEqual(timeout, TIMEOUT)
            self.assertEqual(req.full_url, URL)
            self.assertEqual(req.get_method(), "GET")
            return FakeResponse(xml())

        receipt = retrieve_capabilities(
            opener=fake,
            utc_clock=lambda: datetime(2026, 11, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertEqual(receipt["response_bytes"], len(xml()))
        self.assertFalse(receipt["buildings_sampled"])
        self.assertFalse(receipt["raw_xml_persisted"])
        self.assertFalse(receipt["model_input_admitted"])

    def test_non_official_xml_or_missing_building_layer_blocked(self):
        bad = (
            b'<ExceptionReport/>',
            xml(name="unrelated:roads"),
            xml(version="9.9.9"),
            b'<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" '
            b'version="2.0.0"/>',
            b'<!DOCTYPE x [<!ENTITY x "abc">]><WFS_Capabilities>&x;</WFS_Capabilities>',
            b'<!doctype WFS_Capabilities SYSTEM "http://evil.example/evil.dtd">',
            b'not xml',
            b'',
            b'x' * (MAX_BYTES + 1),
        )
        for raw in bad:
            with self.subTest(payload=raw[:35]), self.assertRaises(BerlinWfsError):
                inspect_capabilities(raw)

    def test_duplicate_feature_names_are_blocked(self):
        s = xml().decode()
        dup = s.replace("</wfs:FeatureTypeList>",
                        "<wfs:FeatureType><wfs:Name>alkis:gebaeude</wfs:Name>"
                        "</wfs:FeatureType></wfs:FeatureTypeList>")
        with self.assertRaisesRegex(BerlinWfsError, "duplicate"):
            inspect_capabilities(dup.encode())

    def test_changed_url_media_type_and_timestamp_blocked(self):
        for response in (
            FakeResponse(xml(), url="https://example.com/redirect"),
            FakeResponse(xml(), content_type="text/html"),
            FakeResponse(b"x" * (MAX_BYTES + 1)),
        ):
            with self.subTest(url=response.url), self.assertRaises(BerlinWfsError):
                retrieve_capabilities(opener=lambda req, timeout: response)
        with self.assertRaisesRegex(BerlinWfsError, "timezone-aware"):
            retrieve_capabilities(
                opener=lambda req, timeout: FakeResponse(xml()),
                utc_clock=lambda: datetime(2026, 11, 1),
            )


if __name__ == "__main__":
    unittest.main()
