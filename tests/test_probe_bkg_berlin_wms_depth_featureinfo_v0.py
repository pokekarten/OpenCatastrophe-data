# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic challenges for fixed BKG Berlin KOSTRA WMS probe."""
from __future__ import annotations

from io import BytesIO
import json
import unittest
from urllib import parse

from research_runners.probe_bkg_berlin_wms_depth_featureinfo_v0 import (
    BkgWmsBlocked, BASE, FIXED_BBOX, MAX_CAPABILITIES_BYTES,
    TARGET_LAYER, _read_bounded, inspect_capabilities,
    inspect_feature_info, probe,
)


def xmlcap(*, layer=TARGET_LAYER, queryable="1", format_="application/json"):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0"><Capability>
<Request><GetFeatureInfo><Format>{format_}</Format></GetFeatureInfo></Request>
<Layer queryable="0"><Name>all</Name>
<Layer queryable="{queryable}"><Name>{layer}</Name>
<Title>Berlin KOSTRA source layer</Title></Layer></Layer>
</Capability></WMS_Capabilities>'''.encode()


class FakeResponse(BytesIO):
    status = 200
    def __init__(self, url, content, *, status=200, media="text/xml", encoding="identity"):
        super().__init__(content)
        self._url = url
        self.status = status
        self.headers = {
            "Content-Type": media,
            "Content-Length": str(len(content)),
            "Content-Encoding": encoding,
        }
    def geturl(self):
        return self._url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class OriginalBkgWmsSourceTests(unittest.TestCase):
    def test_original_exact_berlin_kostra_layer_inherited_queryable_and_format(self):
        result = inspect_capabilities(xmlcap())
        self.assertEqual(result["exact_layer"], "be_tiefe_agw")
        self.assertTrue(result["layer_queryable"])
        self.assertEqual(result["supported_featureinfo_format_selected"], "application/json")
        self.assertFalse(result["raw_BKG_TIFF_unit_conversion_proven"])
        self.assertFalse(result["insured_building_loss_admitted"])

    def test_nonqueryable_service_does_not_query_original_featureinfo(self):
        hits = []
        def opener(req):
            hits.append(req.full_url)
            return FakeResponse(req.full_url, xmlcap(queryable="0"))
        receipt = probe(opener=opener)
        self.assertEqual(len(hits), 1)
        self.assertIsNone(receipt["supported_featureinfo_format_selected"])
        self.assertEqual(receipt["featureinfo"]["status"], "NO_QUERYABLE_OR_SUPPORTED_FORMAT")
        self.assertFalse(receipt["calibrated_physical_depth_available"])

    def test_fixed_original_info_probe_redacts_response_and_coordinates(self):
        hits = []
        info = json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {
                "GRAY_INDEX": 87, "unit": "cm", "possible_building_id": "secret-id"
            }}
        ]}).encode()
        def opener(req):
            hits.append(req.full_url)
            if "GetCapabilities" in req.full_url:
                return FakeResponse(req.full_url, xmlcap())
            return FakeResponse(req.full_url, info, media="application/json")
        receipt = probe(opener=opener)
        self.assertEqual(len(hits), 2)
        self.assertTrue(all(url.startswith(BASE + "?") for url in hits))
        params = parse.parse_qs(parse.urlsplit(hits[1]).query)
        self.assertEqual(params["LAYERS"], ["be_tiefe_agw"])
        self.assertEqual(params["CRS"], ["EPSG:25832"])
        self.assertEqual(params["BBOX"], [FIXED_BBOX])
        self.assertEqual(params["WIDTH"], ["64"])
        self.assertEqual(params["HEIGHT"], ["64"])
        self.assertEqual(params["I"], ["32"])
        self.assertEqual(params["J"], ["32"])
        self.assertEqual(receipt["featureinfo"]["explicit_unit_label_candidate_only"],
                         "centimetres")
        self.assertFalse(receipt["featureinfo"]["WMS_unit_implies_original_TIFF_Int16_scale"])
        self.assertFalse(receipt["insurance_cat_model_input_admitted"])
        stored = json.dumps(receipt)
        for forbidden in ("secret-id", "GRAY_INDEX", '"value": 87', '"coordinates":', "798800"):
            self.assertNotIn(forbidden, stored)

    def test_literal_map_label_is_not_a_physical_unit_claim(self):
        raw = b'{"features":[{"properties":{"value":"53 cm", "name":"metres", "GRAY_INDEX":99}}]}'
        result = inspect_feature_info(raw, "application/json")
        self.assertIsNone(result["explicit_unit_label_candidate_only"])
        self.assertFalse(result["building_depth_or_CAT_loss_authorized"])
        self.assertNotIn("value", result)

    def test_duplicate_or_conflicting_explicit_units_fail_closed(self):
        raw = b'{"features":[{"properties":{"unit":"cm"}}, {"properties":{"unit":"metres"}}]}'
        with self.assertRaisesRegex(BkgWmsBlocked, "conflicting"):
            inspect_feature_info(raw, "application/json")
        with self.assertRaises(BkgWmsBlocked):
            inspect_feature_info(b"not json", "application/json")

    def test_original_xml_capabilities_must_have_exact_and_unique_layer(self):
        cases = (
            xmlcap(layer="other_depth"),
            xmlcap().replace(b"</Layer></Layer>", b'</Layer><Layer queryable="1"><Name>be_tiefe_agw</Name></Layer></Layer>'),
            b'<!DOCTYPE wms [<!ENTITY x "something">]><WMS_Capabilities/>',
            b'<ServiceExceptionReport><ServiceException>rejected</ServiceException></ServiceExceptionReport>',
        )
        for raw in cases:
            with self.subTest(size=len(raw)), self.assertRaises(BkgWmsBlocked):
                inspect_capabilities(raw)

    def test_http_status_redirect_encoding_media_size_and_host_are_blocked(self):
        url=BASE+"?SERVICE=WMS"
        for config in (
            {"status": 206},
            {"encoding": "gzip"},
            {"media": "image/png"},
        ):
            with self.subTest(config=config),self.assertRaises(BkgWmsBlocked):
                _read_bounded(url,max_bytes=MAX_CAPABILITIES_BYTES,
                              opener=lambda req: FakeResponse(req.full_url,xmlcap(),**config))
        with self.assertRaises(BkgWmsBlocked):
            _read_bounded(url,max_bytes=100,
                          opener=lambda req:FakeResponse(req.full_url,xmlcap()))
        with self.assertRaises(BkgWmsBlocked):
            _read_bounded("https://evil.invalid/?x=2",max_bytes=1)

    def test_plain_text_explicit_unit_is_only_candidate(self):
        raw=b"GRAY_INDEX=42\nunit=mm\n"
        receipt=inspect_feature_info(raw, "text/plain")
        self.assertEqual(receipt["explicit_unit_label_candidate_only"],"millimetres")
        self.assertFalse(receipt["WMS_unit_implies_original_TIFF_Int16_scale"])
        self.assertFalse(receipt["original_featureinfo_value_or_coordinates_recorded"])


if __name__ == "__main__":
    unittest.main()
