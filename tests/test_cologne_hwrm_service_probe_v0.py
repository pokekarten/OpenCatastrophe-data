# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline-only negative and positive WMS capability contracts for Cologne pilot."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "research_runners" / "cologne_hwrm_service_probe_v0.py"
spec = importlib.util.spec_from_file_location("cologne_hwrm_service_probe_v0", MODULE)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

WMS = b"""<?xml version="1.0"?>
<WMS_Capabilities xmlns="http://www.opengis.net/wms" version="1.3.0">
 <Capability><Layer><Layer><Name>river_depth</Name></Layer>
 <Layer><Name>river_velocity</Name></Layer></Layer></Capability>
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


if __name__ == "__main__":
    unittest.main()
