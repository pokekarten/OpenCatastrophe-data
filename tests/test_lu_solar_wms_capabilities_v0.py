# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only WMS metadata contract checks (no network/provider buildings)."""
from __future__ import annotations

import unittest

from research_runners.lu_solar_wms_capabilities_v0 import parse_capabilities, WMSMetadataError

EXAMPLE = b"""<?xml version="1.0"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
 <Service><Name>WMS</Name><Title>Luxembourg synthetic demo</Title></Service>
 <Capability>
  <Request>
   <GetMap><Format>image/png</Format></GetMap>
   <GetFeatureInfo><Format>text/plain</Format><Format>application/json</Format></GetFeatureInfo>
  </Request>
  <Layer queryable="0"><Title>Root</Title>
   <Layer queryable="1"><Name>buildings</Name><Title>Buildings</Title><CRS>EPSG:2169</CRS></Layer>
   <Layer queryable="1"><Name>dachteilflaechen</Name><Title>Dachteilflaechen solar</Title>
    <Layer><Name>facets</Name><Title>Roof facets</Title></Layer>
   </Layer>
  </Layer>
 </Capability>
</WMS_Capabilities>
"""


class WMSCapabilityTests(unittest.TestCase):
    def test_layer_tree_and_featureinfo_are_only_advertised(self):
        p = parse_capabilities(EXAMPLE)
        self.assertEqual(p["named_layer_count"], 3)
        self.assertIn("dachteilflaechen", p["roof_name_candidates"])
        self.assertIn("facets", p["roof_name_candidates"])
        self.assertTrue(p["get_feature_info_advertised"])
        self.assertEqual(p["get_feature_info_formats"], ["application/json", "text/plain"])
        self.assertTrue(p["named_layers"][2]["queryable_advertised"])
        self.assertFalse(p["vector_download_supported_verified"])
        self.assertFalse(p["actual_roof_tilt_aspect_data_read"])
        self.assertFalse(p["model_input_admitted"])

    def test_not_an_actual_tilt_or_area_measurement(self):
        p = parse_capabilities(EXAMPLE)
        self.assertNotIn("tilt", p)
        self.assertNotIn("aspect", p)
        self.assertNotIn("area3d", p)

    def test_1_1_1_legacy_service(self):
        x = EXAMPLE.replace(b"WMS_Capabilities version=\"1.3.0\" xmlns=\"http://www.opengis.net/wms\"",
                            b"WMT_MS_Capabilities version=\"1.1.1\"")
        x = x.replace(b"</WMS_Capabilities>", b"</WMT_MS_Capabilities>")
        self.assertEqual(parse_capabilities(x)["wms_version"], "1.1.1")

    def test_service_exception_is_blocked(self):
        with self.assertRaisesRegex(WMSMetadataError, "Not a WMS"):
            parse_capabilities(b"<ServiceExceptionReport>" + b"x"*80 + b"</ServiceExceptionReport>")

    def test_html_or_login_is_blocked(self):
        with self.assertRaisesRegex(WMSMetadataError, "Not a WMS"):
            parse_capabilities(b"<html><body>" + b"x"*90 + b"</body></html>")

    def test_xml_entities_are_blocked(self):
        with self.assertRaisesRegex(WMSMetadataError, "DTD"):
            parse_capabilities(b"<!DOCTYPE a [<!ENTITY x 'hi'>]>" + EXAMPLE)

    def test_repeated_layer_names_are_blocked(self):
        duplicate = EXAMPLE.replace(b"<Name>dachteilflaechen</Name>",
                                    b"<Name>buildings</Name>")
        with self.assertRaisesRegex(WMSMetadataError, "Repeated"):
            parse_capabilities(duplicate)

    def test_missing_feature_info_does_not_invent_query(self):
        x = EXAMPLE.replace(b"<GetFeatureInfo><Format>text/plain</Format><Format>application/json</Format></GetFeatureInfo>", b"")
        p = parse_capabilities(x)
        self.assertFalse(p["get_feature_info_advertised"])
        self.assertEqual(p["get_feature_info_formats"], [])

    def test_bad_version_fails(self):
        with self.assertRaisesRegex(WMSMetadataError, "version"):
            parse_capabilities(EXAMPLE.replace(b'version="1.3.0"', b'version="2.0.0"'))

    def test_missing_named_layers_fails(self):
        x = EXAMPLE.replace(b"<Name>buildings</Name>", b"").replace(b"<Name>dachteilflaechen</Name>", b"").replace(b"<Name>facets</Name>", b"")
        with self.assertRaisesRegex(WMSMetadataError, "No named"):
            parse_capabilities(x)


if __name__ == "__main__":
    unittest.main()
