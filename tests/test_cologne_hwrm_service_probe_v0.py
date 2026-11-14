# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline-only negative and positive WMS capability contracts for Cologne pilot."""

from __future__ import annotations

import importlib.util
import unittest
from unittest import mock
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "research_runners" / "cologne_hwrm_service_probe_v0.py"
spec = importlib.util.spec_from_file_location("cologne_hwrm_service_probe_v0", MODULE)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

WMS = b"""<?xml version="1.0"?>
<WMS_Capabilities xmlns="http://www.opengis.net/wms" version="1.3.0">
 <Service><Name>WMS</Name><Title>NRW HWRM flood hazard WMS</Title></Service>
 <Capability>
  <Request><GetCapabilities/><GetMap/></Request>
  <Layer><Layer><Name>river_depth</Name></Layer>
  <Layer><Name>river_velocity</Name></Layer></Layer>
 </Capability>
</WMS_Capabilities>"""


class CologneHwrmProbeTests(unittest.TestCase):
    def test_valid_namespaced_wms_receipt_is_not_admission(self):
        result = probe.parse_wms_capabilities(WMS)
        self.assertEqual(result["named_layer_count"], 2)
        self.assertEqual(result["first_layer_names"], ["river_depth", "river_velocity"])
        self.assertEqual(len(result["sha256"]), 64)
        self.assertFalse(result["verified_live"])
        self.assertFalse(result["model_admitted"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_wrong_root_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(b"<html><Layer><Name>fake</Name></Layer></html>")

    def test_no_layers_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(b'<WMS_Capabilities version="1.3.0"/>')

    def test_wrong_version_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(WMS.replace(b'1.3.0', b'2.0.0'))

    def test_doctype_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(b'<!DOCTYPE x><WMS_Capabilities version="1.3.0"/>')

    def test_malformed_xml_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(b'<WMS_Capabilities version="1.3.0">')

    def test_empty_or_oversized_rejected(self):
        for raw in (b'', b'x' * (probe.MAX_RESPONSE_BYTES + 1)):
            with self.subTest(length=len(raw)):
                with self.assertRaises(probe.SourceProbeError):
                    probe.parse_wms_capabilities(raw)

    def test_service_identity_required(self):
        invalid = WMS.replace(b"<Name>WMS</Name>", b"<Name>WFS</Name>")
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(invalid)

    def test_getmap_is_required(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(WMS.replace(b"<GetMap/>", b""))

    def test_namespace_is_restricted(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(
                WMS.replace(b"http://www.opengis.net/wms", b"urn:untrusted:namespace")
            )

    def test_legacy_wms_111_accepted(self):
        legacy = (
            WMS.replace(b'xmlns="http://www.opengis.net/wms" ', b"")
            .replace(b"WMS_Capabilities", b"WMT_MS_Capabilities")
            .replace(b"1.3.0", b"1.1.1")
            .replace(b"<Name>WMS</Name>", b"<Name>OGC:WMS</Name>")
        )
        result = probe.parse_wms_capabilities(legacy)
        self.assertEqual(result["wms_version"], "1.1.1")

    def test_live_wrapper_fixed_url_receipt_with_mock_only(self):
        class Headers:
            def get_content_type(self):
                return "text/xml"

            def get(self, name):
                return None

        class Response:
            status = 200
            headers = Headers()

            def __init__(self, url):
                self.url = url

            def geturl(self):
                return self.url

            def read(self, limit):
                assert limit == probe.MAX_RESPONSE_BYTES + 1
                return WMS

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        class Opener:
            def open(self, request, timeout):
                assert timeout == 20
                assert request.full_url == probe.CAPABILITIES_URL
                return Response(request.full_url)

        with mock.patch.object(probe, "build_opener", return_value=Opener()):
            receipt = probe.probe_live()
        self.assertEqual(receipt["provider_url"], probe.CAPABILITIES_URL)
        self.assertTrue(receipt["verified_live"])
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["model_admitted"])

    def test_redirected_response_rejected_with_mock_only(self):
        class Headers:
            def get_content_type(self):
                return "text/xml"

            def get(self, name):
                return None

        class Response:
            status = 200
            headers = Headers()

            def geturl(self):
                return "https://example.org/fake.xml"

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        class Opener:
            def open(self, request, timeout):
                return Response()

        with mock.patch.object(probe, "build_opener", return_value=Opener()):
            with self.assertRaises(probe.SourceProbeError):
                probe.probe_live()


if __name__ == "__main__":
    unittest.main()
