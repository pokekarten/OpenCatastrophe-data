# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic original WFS capabilities and fixed HTTP request regressions."""
from __future__ import annotations

import io
from unittest import TestCase, main
from unittest.mock import patch

from scripts import probe_hessen_alkis_wfs_capabilities_v0 as wfs


def fixture(*, building=True, part=True, version="2.0.0"):
    ns="http://www.opengis.net/wfs/2.0"
    ows="http://www.opengis.net/ows/1.1"
    parts=[]
    if building:
        parts.append("""<wfs:FeatureType><wfs:Name>bu-core2d:Building</wfs:Name>
        <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25832</wfs:DefaultCRS>
        </wfs:FeatureType>""")
    if part:
        parts.append("""<wfs:FeatureType><wfs:Name>bu-core2d:BuildingPart</wfs:Name>
        <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25832</wfs:DefaultCRS>
        </wfs:FeatureType>""")
    parts.append("""<wfs:FeatureType><wfs:Name>xx:Other</wfs:Name>
        </wfs:FeatureType>""")
    xml=(
        f'<wfs:WFS_Capabilities xmlns:wfs="{ns}" xmlns:ows="{ows}" version="{version}">'
        "<ows:OperationsMetadata>"
        '<ows:Operation name="GetCapabilities"/>'
        '<ows:Operation name="DescribeFeatureType"/>'
        '<ows:Operation name="GetFeature"/>'
        "</ows:OperationsMetadata><wfs:FeatureTypeList>"
        + "".join(parts) + "</wfs:FeatureTypeList></wfs:WFS_Capabilities>"
    )
    return xml.encode("utf-8")


class Reply(io.BytesIO):
    def __init__(self, data=None, *, status=200, url=wfs.URL, headers=None):
        super().__init__(fixture() if data is None else data)
        self.status=status
        self.url=url
        self.headers=(
            {"Content-Type":"text/xml", "Content-Length":str(len(self.getvalue()))}
            if headers is None else headers
        )
        self.read_sizes=[]
    def geturl(self):
        return self.url
    def read(self,size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class HessenCapabilitiesTests(TestCase):
    def test_fixed_provider_and_url_cannot_change(self):
        self.assertIsNone(wfs.validate_exact_request())
        self.assertIn("REQUEST=GetCapabilities", wfs.URL)
        with patch.object(wfs,"URL","https://evil.invalid/a"):
            with self.assertRaises(wfs.CapabilityBlocked):
                wfs.validate_exact_request()
        with self.assertRaises(SystemExit):
            wfs.main([])

    def test_actual_ogc20_names_crs_and_operations_are_extracted(self):
        actual=wfs.inspect_capabilities(fixture())
        self.assertEqual(actual["advertised_feature_type_count"],3)
        self.assertTrue(actual["building_feature_type_present"])
        self.assertTrue(actual["building_part_feature_type_present"])
        self.assertEqual(actual["building_default_crs_if_advertised"],
                         ["urn:ogc:def:crs:EPSG::25832"])
        self.assertTrue(actual["advertises_getfeature"])
        self.assertTrue(actual["advertises_describefeaturetype"])
        self.assertFalse(actual["actual_building_feature_geometry_verified"])
        self.assertFalse(actual["feature_query_authorized"])
        self.assertFalse(actual["model_input_approved"])

    def test_capabilities_without_expected_building_layer_do_not_claim_success(self):
        actual=wfs.inspect_capabilities(fixture(building=False,part=False))
        self.assertEqual(actual["advertised_feature_type_count"],1)
        self.assertFalse(actual["building_feature_type_present"])
        self.assertEqual(actual["building_default_crs_if_advertised"],[])
        self.assertFalse(actual["feature_query_authorized"])

    def test_malformed_wfs_and_external_entity_are_rejected(self):
        failures=[
            b"",
            b"<ExceptionReport/>",
            b"<WFS_Capabilities version='2.0.0'/>",
            fixture(version="1.1.0"),
            b'<!DOCTYPE a [<!ENTITY x SYSTEM "https://example.invalid/entity.dtd">]>'+fixture(),
            b"<broken>",
            b"<x/>"*7,
            fixture().replace(b"bu-core2d:Building", b"../../unsafe"),
            fixture().replace(b"bu-core2d:BuildingPart", b"bu-core2d:Building"),
            b"A" * (wfs.MAX_BYTES + 1),
        ]
        for i,data in enumerate(failures):
            with self.subTest(case=i), self.assertRaises(wfs.CapabilityBlocked):
                wfs.inspect_capabilities(data)

    def test_one_only_exact_http_and_only_metadata_no_raw_source_bytes(self):
        response=Reply()
        calls=[]
        def fake(req,timeout):
            calls.append((req.full_url,req.get_method(),
                          req.get_header("Accept-encoding"),timeout))
            return response
        receipt=wfs.probe(open_request=fake)
        self.assertEqual(calls,[(wfs.URL,"GET","identity",wfs.TIMEOUT_SECONDS)])
        self.assertEqual(response.read_sizes,[wfs.MAX_BYTES+1])
        self.assertEqual(receipt["sample_bytes"],len(fixture()))
        self.assertEqual(len(receipt["sample_sha256"]),64)
        self.assertFalse(receipt["raw_xml_or_building_attributes_persisted"])
        self.assertFalse(receipt["source_feature_identifiers_or_coordinates_printed"])
        self.assertFalse(receipt["model_input_approved"])

    def test_bad_original_http_responses_reject_before_parsing(self):
        standard={"Content-Type":"text/xml","Content-Length":str(len(fixture()))}
        cases=[
            Reply(status=206),
            Reply(status=302),
            Reply(url="https://other.invalid/source"),
            Reply(headers={**standard,"Content-Type":"text/html"}),
            Reply(headers={**standard,"Content-Length":"3000000"}),
            Reply(headers={**standard,"Content-Encoding":"gzip"}),
            Reply(data=fixture()[:-1]),
            Reply(data=fixture()+b"X"),
        ]
        for i,response in enumerate(cases):
            with self.subTest(case=i),self.assertRaises(wfs.CapabilityBlocked):
                wfs.probe(open_request=lambda req,timeout:response)


if __name__=="__main__":
    main()
