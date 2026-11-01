# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline Hessen GML ring diagnostic (all coordinates invented)."""
from __future__ import annotations

import io
import unittest

from scripts import probe_hessen_alkis_one_gml_ring_v0 as gml


def fixture(*, points=None, returned=0, with_polygon=True, hole=False):
    if points is None:
        points = [
            (50.515, 9.482), (50.515, 9.484), (50.517, 9.484),
            (50.517, 9.482), (50.515, 9.482),
        ]
    body = " ".join(f"{lat} {lon}" for lat,lon in points)
    outer = (
        '<gml:Polygon><gml:exterior><gml:LinearRing><gml:posList srsDimension="2">'
        + body + '</gml:posList></gml:LinearRing></gml:exterior>'
    )
    if hole:
        outer += (
            '<gml:interior><gml:LinearRing><gml:posList>'
            '50.5152 9.4822 50.5152 9.4824 50.5154 9.4824 '
            '50.5154 9.4822 50.5152 9.4822'
            '</gml:posList></gml:LinearRing></gml:interior>'
        )
    outer += "</gml:Polygon>"
    geom = (
        '<gml:MultiSurface srsName="urn:ogc:def:crs:EPSG::4258">'
        + outer + '</gml:MultiSurface>'
    ) if with_polygon else (
        '<gml:Point srsName="urn:ogc:def:crs:EPSG::4258">'
        '<gml:pos>50.516 9.483</gml:pos></gml:Point>'
    )
    return (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"'
        ' xmlns:gml="http://www.opengis.net/gml/3.2"'
        f' numberReturned="{returned}" numberMatched="unknown">'
        '<wfs:member><bu:Building xmlns:bu="http://inspire.ec.europa.eu/schemas/bu-core2d/4.0">'
        + geom + '</bu:Building></wfs:member></wfs:FeatureCollection>'
    ).encode()


class Reply(io.BytesIO):
    status=200
    def __init__(self, data=None, *, status=200, url=gml.URL, headers=None):
        super().__init__(fixture() if data is None else data)
        self.status=status
        self.url=url
        self.headers=(
            {"Content-Type":"application/gml+xml","Content-Length":str(len(self.getvalue()))}
            if headers is None else headers
        )
        self.read_sizes=[]
    def geturl(self):
        return self.url
    def read(self,size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class OneOriginalGmlTests(unittest.TestCase):
    def test_closed_polygon_under_known_contradictory_source_count_remains_blocked(self):
        result=gml.inspect_gml_preflight(fixture())
        self.assertEqual(result["polygon_surface_count"],1)
        self.assertEqual(result["exterior_ring_count"],1)
        self.assertEqual(result["gml_position_count"],5)
        self.assertEqual(result["source_reported_number_returned"],0)
        self.assertTrue(result["provider_count_discrepancy_remains_blocked"])
        self.assertTrue(result["all_rings_closed_nondegenerate_and_non_crossing"])
        self.assertTrue(result["all_coordinates_within_worldcover_original_block_extent"])
        self.assertFalse(result["etrs89_to_worldcover_wgs84_transform_verified"])
        self.assertFalse(result["physical_building_polygon_topology_verified"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("9.482",str(result))

    def test_interior_ring_count_preserved_not_silently_dropped(self):
        result=gml.inspect_gml_preflight(fixture(hole=True))
        self.assertEqual(result["interior_ring_count"],1)
        self.assertEqual(result["gml_ring_count"],2)
        self.assertFalse(result["actual_building_worldcover_overlap_verified"])

    def test_source_with_point_not_admitted_as_polygon(self):
        result=gml.inspect_gml_preflight(fixture(with_polygon=False))
        self.assertEqual(result["diagnostic_status"],"BLOCKED_UNSUPPORTED_NO_GML_POLYGON_SURFACE")
        self.assertFalse(result["model_input_approved"])

    def test_invalid_nonclosed_nonfinite_or_wrong_crs_source_rejected(self):
        cases=[
            fixture(points=[(50.515,9.482),(50.515,9.484),(50.517,9.484),(50.517,9.482)]),
            fixture(points=[(50.515,9.482),(50.515,9.484),(50.517,9.484),
                            (50.517,9.482),(50.515,9.482)]).replace(
                                b"50.517",b"NaN"),
            fixture().replace(b"EPSG::4258",b"EPSG::25832"),
            fixture() + b"x",
            fixture().replace(b"srsDimension=\"2\"",b"srsDimension=\"3\""),
            b"x"*(gml.MAX_BYTES+1),
        ]
        for i,raw in enumerate(cases):
            with self.subTest(i=i),self.assertRaises(gml.RingBlocked):
                gml.inspect_gml_preflight(raw)

    def test_contradictory_nonzero_source_member_count_is_flagged_not_admitted(self):
        result=gml.inspect_gml_preflight(fixture(returned=3))
        self.assertTrue(result["provider_count_discrepancy_remains_blocked"])
        self.assertEqual(result["source_reported_number_returned"],3)
        self.assertEqual(result["parsed_original_building_members"],1)
        self.assertFalse(result["model_input_approved"])

    def test_crossing_polygon_detected_and_blocked_from_use(self):
        result=gml.inspect_gml_preflight(fixture(points=[
            (50.515,9.482),(50.517,9.484),(50.515,9.484),
            (50.517,9.482),(50.516,9.481),(50.515,9.482)
        ]))
        self.assertFalse(result["all_rings_closed_nondegenerate_and_non_crossing"])
        self.assertEqual(result["diagnostic_status"],"BLOCKED_GML_RING_CROSSING_OR_BLOCK_EXTENT")

    def test_polygon_outside_original_raster_block_is_not_approved(self):
        result=gml.inspect_gml_preflight(fixture(points=[
            (50.515,9.67),(50.515,9.672),(50.517,9.672),
            (50.517,9.67),(50.515,9.67)
        ]))
        self.assertFalse(result["all_coordinates_within_worldcover_original_block_extent"])
        self.assertFalse(result["model_input_approved"])

    def test_one_exact_source_request_and_transient_output_only(self):
        answer=Reply()
        seen=[]
        def fake(req,timeout):
            seen.append((req.full_url,req.get_method(),
                         req.get_header("Accept-encoding"),timeout))
            return answer
        receipt=gml.probe(open_request=fake)
        self.assertEqual(seen,[(gml.URL,"GET","identity",gml.TIMEOUT_SECONDS)])
        self.assertEqual(answer.read_sizes,[gml.MAX_BYTES+1])
        self.assertEqual(len(receipt["source_response_sha256"]),64)
        self.assertFalse(receipt["original_coordinates_feature_ids_attributes_persisted"])
        self.assertFalse(receipt["original_coordinates_feature_ids_attributes_printed"])
        self.assertNotIn("50.515",str(receipt))
        self.assertFalse(receipt["model_input_approved"])

    def test_invalid_provider_http_rejected_before_coordinates(self):
        default={"Content-Type":"application/gml+xml","Content-Length":str(len(fixture()))}
        replies=[
            Reply(status=206),Reply(status=404),
            Reply(url="https://invalid.example/other"),
            Reply(headers={**default,"Content-Type":"text/html"}),
            Reply(headers={**default,"Content-Length":"999999999"}),
            Reply(headers={**default,"Content-Encoding":"gzip"}),
        ]
        for i,answer in enumerate(replies):
            with self.subTest(i=i),self.assertRaises(gml.RingBlocked):
                gml.probe(open_request=lambda req,timeout:answer)


if __name__ == "__main__":
    unittest.main()
