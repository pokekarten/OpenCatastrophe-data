# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict one-feature Hessen original WFS tests using only synthetic GML."""
from __future__ import annotations

import io
from unittest import TestCase, main
from unittest.mock import patch

from scripts import probe_hessen_alkis_one_wfs_building_v0 as wfs


def fixture(*, members=1, returned=None, matched="unknown",
            building=True, srs="urn:ogc:def:crs:EPSG::4258"):
    if returned is None:
        returned=members
    one=(
        '<wfs:member><bu:Building xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-core2d/4.0">'
        '<gml:Polygon srsName="'+srs+'"><gml:exterior><gml:LinearRing>'
        '<gml:posList>50.516 9.483 50.517 9.483 50.517 9.484 50.516 9.483'
        '</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>'
        '<secret>should-not-be-printed</secret></bu:Building></wfs:member>'
    ) if building else (
        '<wfs:member><bu:BuildingPart xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-core2d/4.0">'
        '<secret>no</secret></bu:BuildingPart></wfs:member>'
    )
    return (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"'
        ' xmlns:gml="http://www.opengis.net/gml/3.2"'
        f' numberMatched="{matched}" numberReturned="{returned}">'
        + one*members + '</wfs:FeatureCollection>'
    ).encode("utf-8")


class Reply(io.BytesIO):
    status=200
    def __init__(self,data=None,*,status=200,url=wfs.URL,headers=None):
        super().__init__(fixture() if data is None else data)
        self.status=status
        self.url=url
        self.headers=({
            "Content-Type":"application/gml+xml",
            "Content-Length":str(len(self.getvalue()))
        } if headers is None else headers)
        self.read_sizes=[]
    def geturl(self):
        return self.url
    def read(self,n=-1):
        self.read_sizes.append(n)
        return super().read(n)


class HessenOneBuildingWfsTests(TestCase):
    def test_only_fixed_source_count_one_and_explicit_latitude_longitude_axis(self):
        self.assertIsNone(wfs.validate_frozen_getfeature())
        self.assertIn("COUNT=1",wfs.QUERY)
        self.assertIn("SRSNAME=urn:ogc:def:crs:EPSG::4258",wfs.QUERY)
        self.assertTrue(wfs.QUERY.endswith(
            "BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258"))
        with patch.object(wfs,"URL","https://invalid.example/other"):
            with self.assertRaises(wfs.BuildingFeatureBlocked):
                wfs.validate_frozen_getfeature()
        with self.assertRaises(SystemExit):
            wfs.main([])

    def test_one_original_gml_feature_does_not_expose_id_or_coordinates(self):
        result=wfs.inspect_feature_xml(fixture())
        self.assertEqual(result["original_feature_members_parsed_not_admitted"],1)
        self.assertEqual(result["reported_number_returned_if_integer"],1)
        self.assertIsNone(result["reported_number_matched_if_integer"])
        self.assertTrue(result["source_geometry_markup_present"])
        self.assertTrue(result["geometry_crs_declared_and_matches_requested"])
        self.assertFalse(result["actual_2d_polygon_topology_verified"])
        self.assertFalse(result["actual_building_worldcover_overlap_verified"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("secret",str(result))
        self.assertNotIn("50.516",str(result))

    def test_empty_page_cannot_confirm_absent_buildings(self):
        result=wfs.inspect_feature_xml(fixture(members=0,returned=0,matched=0))
        self.assertEqual(result["original_feature_members_parsed_not_admitted"],0)
        self.assertFalse(result["source_geometry_markup_present"])
        self.assertIsNone(result["geometry_crs_declared_and_matches_requested"])
        self.assertTrue(result["not_a_complete_building_inventory"])

    def test_malformed_xml_and_bad_member_count_block(self):
        cases=[
            b"",
            b"<ExceptionReport/>",
            b"<FeatureCollection/>",
            b"<not-valid",
            fixture(members=2,returned=2),
            fixture(members=1,returned=0),
            fixture(members=1,matched="0"),
            fixture(members=1,building=False),
            fixture(members=1,returned="notanumber"),
            b'<!DOCTYPE test [<!ENTITY e SYSTEM "https://invalid.example/a.dtd">]>'+fixture(),
            fixture()+b"trailing",
            b"x"*(wfs.MAX_BYTES+1),
        ]
        for n,raw in enumerate(cases):
            with self.subTest(n=n),self.assertRaises(wfs.BuildingFeatureBlocked):
                wfs.inspect_feature_xml(raw)

    def test_provider_header_count_mismatch_is_blocked_but_can_be_safely_diagnosed(self):
        payload=fixture(members=1,returned=0)
        with self.assertRaisesRegex(wfs.BuildingFeatureBlocked,"WFS count mismatch"):
            wfs.inspect_feature_xml(payload)
        result=wfs.inspect_feature_xml(payload,diagnostic_only=True)
        self.assertEqual(result["source_validation_status"],
                         "BLOCKED_CONTRADICTORY_WFS_COUNTS")
        self.assertEqual(result["original_feature_members_parsed_not_admitted"],1)
        self.assertEqual(result["reported_number_returned_if_integer"],0)
        self.assertFalse(result["reported_member_count_consistent"])
        self.assertFalse(result["actual_building_worldcover_overlap_verified"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("secret",str(result))
        with self.assertRaises(wfs.BuildingFeatureBlocked):
            wfs.inspect_feature_xml(payload,diagnostic_only="unsafe")

    def test_unexpected_crs_is_explicitly_not_verified(self):
        result=wfs.inspect_feature_xml(fixture(srs="EPSG:25832"))
        self.assertFalse(result["geometry_crs_declared_and_matches_requested"])
        result=wfs.inspect_feature_xml(fixture(srs=""))
        self.assertFalse(result["geometry_crs_declared_and_matches_requested"])

    def test_single_exact_http_request_keeps_source_transient(self):
        response=Reply()
        calls=[]
        def fake(req,timeout):
            calls.append((req.full_url,req.get_method(),
                          req.get_header("Accept-encoding"),timeout))
            return response
        evidence=wfs.probe(open_request=fake)
        self.assertEqual(calls,[(wfs.URL,"GET","identity",wfs.TIMEOUT_SECONDS)])
        self.assertEqual(response.read_sizes,[wfs.MAX_BYTES+1])
        self.assertEqual(evidence["original_feature_members_parsed_not_admitted"],1)
        self.assertFalse(evidence["source_raw_features_or_gml_persisted"])
        self.assertFalse(evidence["feature_identifiers_addresses_or_coordinates_emitted"])
        self.assertNotIn("50.516",str(evidence))

    def test_http_redirect_html_encoding_and_oversize_reject(self):
        default={"Content-Type":"application/gml+xml","Content-Length":str(len(fixture()))}
        replies=[
            Reply(status=206),Reply(status=404),
            Reply(url="https://invalid.example/other"),
            Reply(headers={**default,"Content-Type":"text/html"}),
            Reply(headers={**default,"Content-Encoding":"gzip"}),
            Reply(headers={**default,"Content-Length":"99999999"}),
            Reply(data=b"X"*(wfs.MAX_BYTES+1),
                  headers={"Content-Type":"application/xml"}),
        ]
        for n,reply in enumerate(replies):
            with self.subTest(n=n),self.assertRaises(wfs.BuildingFeatureBlocked):
                wfs.probe(open_request=lambda req,timeout:reply)


if __name__=="__main__":
    main()
