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
 <Service><Name>WMS</Name><Title>NRW HWRM flood hazard WMS</Title><AccessConstraints>Datenlizenz Deutschland Namensnennung 2.0; Land NRW</AccessConstraints></Service>
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
        self.assertTrue(result["service_mentions_attribution"])
        self.assertEqual(len(result["service_access_constraints_sha256"]), 64)
        self.assertFalse(result["rights_reviewed"])
        self.assertFalse(result["model_admitted"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_reviewed_original_service_terms_sha_is_pinned(self):
        self.assertEqual(
            probe.REVIEWED_WMS_SERVICE_TERMS_SHA256,
            "2b280a54d318695d430248562d1fbc0d074349dd27df444d3e72633e2f978c03",
        )
        self.assertEqual(probe.REVIEWED_WMS_VERSION, "1.3.0")

    def test_reviewed_metadata_cannot_silently_accept_rights_drift(self):
        receipt = probe.parse_wms_capabilities(WMS)
        with self.assertRaises(probe.SourceProbeError):
            probe.verify_reviewed_service_metadata(receipt)
        with mock.patch.object(
            probe, "REVIEWED_WMS_SERVICE_TERMS_SHA256",
            receipt["service_access_constraints_sha256"],
        ):
            checked = probe.verify_reviewed_service_metadata(receipt)
        self.assertTrue(checked["reviewed_service_terms_match"])
        self.assertEqual(checked["required_attribution"], "Land NRW")
        self.assertFalse(checked["model_admitted"])
        self.assertFalse(checked["rights_reviewed"])

    def test_reviewed_wms_version_and_attribution_cannot_drift(self):
        receipt = probe.parse_wms_capabilities(WMS)
        with mock.patch.object(
            probe, "REVIEWED_WMS_SERVICE_TERMS_SHA256",
            receipt["service_access_constraints_sha256"],
        ):
            for mutated in (
                {**receipt, "wms_version": "1.1.1"},
                {**receipt, "service_mentions_attribution": False},
                {**receipt, "named_layer_count": 0},
            ):
                with self.subTest(mutated=mutated), self.assertRaises(probe.SourceProbeError):
                    probe.verify_reviewed_service_metadata(mutated)

    def test_wrong_root_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(b"<html><Layer><Name>fake</Name></Layer></html>")

    def test_no_layers_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(b'<WMS_Capabilities version="1.3.0"/>')

    def test_wrong_version_rejected(self):
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(WMS.replace(b'1.3.0', b'2.0.0'))

    def test_utf16_dtd_rejected_before_entity_expansion(self):
        clean = WMS.decode("ascii")
        dtd = clean.replace("?>", '?>' + '<!DOCTYPE WMS_Capabilities ['
                            '<!ENTITY title "NRW HWRM flood hazard WMS">]>', 1)
        dtd = dtd.replace("<Title>NRW HWRM flood hazard WMS</Title>",
                          "<Title>&title;</Title>")
        empty_dtd = clean.replace("?>", "?><!DOCTYPE WMS_Capabilities>", 1)
        for encoding, bom in (("utf-16-le", b"\xff\xfe"),
                              ("utf-16-be", b"\xfe\xff")):
            with self.subTest(encoding=encoding):
                self.assertEqual(probe.parse_wms_capabilities(
                    bom + clean.encode(encoding))["named_layer_count"], 2)
                for payload in (dtd, empty_dtd):
                    with self.assertRaisesRegex(probe.SourceProbeError, "DTD forbidden"):
                        probe.parse_wms_capabilities(bom + payload.encode(encoding))

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

        expected_sha = probe.parse_wms_capabilities(WMS)["service_access_constraints_sha256"]
        with (
            mock.patch.object(probe, "build_opener", return_value=Opener()),
            mock.patch.object(probe, "REVIEWED_WMS_SERVICE_TERMS_SHA256", expected_sha),
        ):
            receipt = probe.probe_live()
        self.assertEqual(receipt["provider_url"], probe.CAPABILITIES_URL)
        self.assertTrue(receipt["verified_live"])
        self.assertTrue(receipt["reviewed_service_terms_match"])
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

    def test_missing_wms_access_constraints_rejected(self):
        invalid = WMS.replace(
            b"<AccessConstraints>Datenlizenz Deutschland Namensnennung 2.0; Land NRW</AccessConstraints>",
            b"",
        )
        with self.assertRaises(probe.SourceProbeError):
            probe.parse_wms_capabilities(invalid)

    def test_no_automatic_rights_grant_from_service_notice(self):
        notice = WMS.replace(b"Namensnennung", b"Zero")
        result = probe.parse_wms_capabilities(notice)
        self.assertFalse(result["service_mentions_attribution"])
        self.assertFalse(result["rights_reviewed"])
        self.assertFalse(result["model_admitted"])


if __name__ == "__main__":
    unittest.main()
