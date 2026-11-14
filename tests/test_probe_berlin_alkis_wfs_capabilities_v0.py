# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic XML only; no original provider payload or cadastral feature in Git."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import unittest
from unittest.mock import patch

from scripts.probe_berlin_alkis_wfs_capabilities_v0 import (
    ACCESS_ID, FROZEN_CRS, FROZEN_LAYER, MAX_BYTES, TIMEOUT, URL,
    BerlinWFSBlocked, NoRedirect, inspect_capabilities, probe,
    verify_reviewed_contract,
)


CAPABILITIES = b"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0"
  xmlns:ows="http://www.opengis.net/ows/1.1" version="2.0.0">
  <ows:ServiceIdentification>
    <ows:Title>ALKIS Berlin Geb&#228;ude</ows:Title>
    <ows:ServiceType>WFS</ows:ServiceType>
    <ows:ServiceTypeVersion>2.0.0</ows:ServiceTypeVersion>
    <ows:Fees>Datenlizenz Deutschland - Zero - Version 2.0</ows:Fees>
    <ows:AccessConstraints>Es gelten keine Zugriffsbeschr&#228;nkungen</ows:AccessConstraints>
  </ows:ServiceIdentification>
  <ows:ServiceProvider>
    <ows:ProviderName>Senatsverwaltung f&#252;r Stadtentwicklung, Bauen und Wohnen Berlin</ows:ProviderName>
  </ows:ServiceProvider>
  <ows:OperationsMetadata>
    <ows:Operation name="GetCapabilities"/>
    <ows:Operation name="GetFeature"/>
  </ows:OperationsMetadata>
  <wfs:FeatureTypeList><wfs:FeatureType>
    <wfs:Name>alkis_gebaeude:gebaeude</wfs:Name>
    <wfs:Title>Geb&#228;ude</wfs:Title>
    <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25833</wfs:DefaultCRS>
  </wfs:FeatureType></wfs:FeatureTypeList>
</wfs:WFS_Capabilities>
"""


class FakeResponse:
    def __init__(self, raw=CAPABILITIES, status=200, url=URL, media="text/xml",
                 extra_headers=None):
        self.body, self.status, self.url = raw, status, url
        self.headers = {
            "Content-Type": media,
            "Content-Length": str(len(raw)),
            "Content-Encoding": "identity",
        }
        self.headers.update(extra_headers or {})

    def geturl(self):
        return self.url

    def read(self, maximum):
        return self.body[:maximum]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class BerlinWFSProbeTests(unittest.TestCase):
    def test_original_provider_identity_is_fixed_to_metadata_only(self):
        verify_reviewed_contract()
        self.assertEqual(ACCESS_ID, "de.berlin.alkis-gebaeude.wfs")
        self.assertEqual(
            URL,
            "https://gdi.berlin.de/services/wfs/alkis_gebaeude"
            "?request=GetCapabilities&service=WFS",
        )
        self.assertEqual(MAX_BYTES, 1_048_576)
        self.assertEqual(TIMEOUT, 30)
        self.assertEqual(FROZEN_LAYER, "alkis_gebaeude:gebaeude")
        self.assertEqual(FROZEN_CRS, "urn:ogc:def:crs:EPSG::25833")

    def test_approved_synthetic_wfs_capabilities_metadata(self):
        report = inspect_capabilities(CAPABILITIES)
        self.assertEqual(report["wfs_version"], "2.0.0")
        self.assertTrue(report["service_identity_verified"])
        self.assertEqual(report["original_licence_terms_confirmed"], "DL-DE Zero 2.0")
        self.assertEqual(report["default_crs_verified"], "EPSG:25833")
        self.assertEqual(report["feature_requests_executed"], 0)
        self.assertEqual(report["individual_buildings_retrieved"], 0)

    def test_license_provider_layer_and_version_changes_fail_closed(self):
        for old, new in (
            (b"Data", b"fake"),
            (b"Datenlizenz Deutschland", b"restricted internal use"),
            (b"keine Zugriffsbeschr&#228;nkungen", b"keine Eigentuemerdaten"),
            (b"ALKIS Berlin Geb&#228;ude", b"Another WFS Layer"),
            (b"Senatsverwaltung f&#252;r Stadtentwicklung", b"Fake Betreiber"),
            (b'xmlns:wfs="http://www.opengis.net/wfs/2.0"', b'xmlns:wfs="urn:fake"'),
            (b'version="2.0.0"', b'version="1.1.0"'),
            (b"alkis_gebaeude:gebaeude", b"alkis_gebaeude:owner"),
            (b"urn:ogc:def:crs:EPSG::25833", b"EPSG:4326"),
            (b'Operation name="GetCapabilities"', b'Operation name="GetFeature"'),
        ):
            with self.subTest(old=old):
                self.assertNotEqual(old, new)
                if old not in CAPABILITIES:
                    continue
                with self.assertRaises(BerlinWFSBlocked):
                    inspect_capabilities(CAPABILITIES.replace(old, new))

    def test_entity_declarations_and_malformed_xml_rejected(self):
        for body in (
            b"",
            b"<owner id='123'/>",
            b"not-xml",
            CAPABILITIES.replace(b"<?xml", b"<!DOCTYPE xxx [<!ENTITY x 'foo'>]><?xml"),
            CAPABILITIES.replace(b"<?xml", b"<!ENTITY foo 'bar'><?xml"),
            b"a" * (MAX_BYTES + 1),
        ):
            with self.subTest(body=body[:25]):
                with self.assertRaises(BerlinWFSBlocked):
                    inspect_capabilities(body)

    def test_strict_one_response_receipt_no_payload_leak(self):
        calls = []

        def fake_open(request, timeout):
            calls.append((request.full_url, request.get_method(), timeout))
            return FakeResponse()

        result = probe(open_request=fake_open, clock=lambda: datetime(2026, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(calls, [(URL, "GET", TIMEOUT)])
        self.assertEqual(result["response_sha256"], hashlib.sha256(CAPABILITIES).hexdigest())
        self.assertEqual(result["response_bytes"], len(CAPABILITIES))
        self.assertFalse(result["building_geometry_acquired"])
        self.assertFalse(result["owner_information_acquired"])
        self.assertFalse(result["raw_provider_bytes_persisted"])
        self.assertFalse(result["scientific_model_input_approved"])
        self.assertNotIn("geometries", result)
        self.assertNotIn("building_addresses", result)

    def test_reject_non_200_redirect_media_encoding_and_length(self):
        samples = (
            FakeResponse(status=206),
            FakeResponse(url="https://evil.example/wfs"),
            FakeResponse(media="application/json"),
            FakeResponse(extra_headers={"Content-Encoding": "gzip"}),
            FakeResponse(extra_headers={"Content-Length": str(MAX_BYTES + 1)}),
            FakeResponse(extra_headers={"Content-Length": "wrong"}),
            FakeResponse(extra_headers={"Content-Length": str(len(CAPABILITIES) + 10)}),
            FakeResponse(raw=CAPABILITIES + b" " * MAX_BYTES),
        )
        for sample in samples:
            with self.subTest(sample=sample.status, url=sample.url, headers=sample.headers):
                with self.assertRaises(BerlinWFSBlocked):
                    probe(open_request=lambda req, timeout: sample)

    def test_network_not_attempted_without_opt_in(self):
        from scripts.probe_berlin_alkis_wfs_capabilities_v0 import main
        with patch("scripts.probe_berlin_alkis_wfs_capabilities_v0.probe") as action:
            with self.assertRaises(SystemExit) as caught:
                main([])
        self.assertEqual(caught.exception.code, 2)
        action.assert_not_called()

    def test_reject_provider_redirect(self):
        with self.assertRaises(BerlinWFSBlocked):
            NoRedirect().redirect_request(None, None, 302, "move", {},
                                          "https://example.com/other")


if __name__ == "__main__":
    unittest.main()
