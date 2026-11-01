# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Invented-only ALKIS ETRS89-to-WGS84/GEOS regression cases.

Optional spatial dependencies are installed and asserted by the dedicated
original-provider workflow; standard Python CI may explicitly skip them.
"""
from __future__ import annotations

import importlib.util
import io
import unittest
from unittest.mock import patch

from research_runners import hessen_alkis_one_building_crs_geos_v0 as crs
from tests.test_probe_hessen_alkis_one_gml_ring_v0 import fixture

HAS_SPATIAL=bool(importlib.util.find_spec("pyproj")
                 and importlib.util.find_spec("shapely"))


class Reply(io.BytesIO):
    status=200
    def __init__(self, raw=None, *, url=crs.URL, status=200, headers=None):
        super().__init__(fixture() if raw is None else raw)
        self.url=url
        self.status=status
        self.headers=(
            {"Content-Type":"application/gml+xml",
             "Content-Length":str(len(self.getvalue()))}
            if headers is None else headers
        )
        self.read_sizes=[]
    def geturl(self):
        return self.url
    def read(self,n=-1):
        self.read_sizes.append(n)
        return super().read(n)


@unittest.skipUnless(HAS_SPATIAL, "dedicated spatial CI installs pinned PyProj and Shapely")
class OfficialSourceCRSGeosTests(unittest.TestCase):
    def test_synthetic_epsg4258_polygon_has_offline_nonballpark_wgs84_operation(self):
        result=crs.inspect_original_crs_and_topology(fixture())
        self.assertEqual(result["building_polygon_surfaces_from_original"],1)
        self.assertEqual(result["building_exterior_vertex_positions_including_closure"],5)
        self.assertTrue(result["original_epsg4258_geos_valid"])
        self.assertTrue(result["transformed_epsg4326_geos_valid"])
        self.assertTrue(result["coordinate_operation_is_non_ballpark"])
        self.assertTrue(result["coordinate_operation_is_offline"])
        self.assertGreater(result["coordinate_operation_accuracy_metres_declared"],0)
        self.assertLessEqual(result["coordinate_operation_accuracy_metres_declared"],1.0)
        self.assertTrue(result["wgs84_polygon_vertices_within_source_block"])
        self.assertTrue(result["all_vertices_more_than_operation_accuracy_from_block_edges"])
        self.assertEqual(result["source_reported_number_returned"],0)
        self.assertTrue(result["wfs_count_discrepancy_still_blocked"])
        self.assertFalse(result["worldcover_2021_original_pixel_intersection_performed"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("50.515",str(result))
        self.assertNotIn("9.482",str(result))

    def test_one_invented_polygon_with_hole_cannot_be_promoted(self):
        payload=fixture(hole=True)
        with self.assertRaises(crs.CRSBlocked):
            crs.inspect_original_crs_and_topology(payload)

    def test_swapped_axis_and_nonfinite_geometry_are_rejected(self):
        swapped=fixture(points=[
            (9.482,50.515),(9.484,50.515),(9.484,50.517),
            (9.482,50.517),(9.482,50.515),
        ])
        with self.assertRaises(crs.CRSBlocked):
            crs.inspect_original_crs_and_topology(swapped)
        with self.assertRaises(crs.CRSBlocked):
            crs.inspect_original_crs_and_topology(fixture().replace(b"50.515",b"NaN"))

    def test_non_simple_polygon_is_not_declared_valid(self):
        # Source ring contains proper crossing despite non-zero shoelace area.
        crossed=fixture(points=[
            (50.515,9.482),(50.517,9.484),(50.515,9.484),
            (50.517,9.482),(50.516,9.481),(50.515,9.482),
        ])
        with self.assertRaises(crs.CRSBlocked):
            crs.inspect_original_crs_and_topology(crossed)

    def test_version_drift_and_unsupported_crs_op_block(self):
        import pyproj
        with patch.object(pyproj,"__version__","0.0.0"):
            with self.assertRaises(crs.CRSBlocked):
                crs._reviewed_transformer()

    def test_near_gridline_coordinate_is_not_treated_as_survey_exact(self):
        # Synthetic ETRS89 lon precisely equals one WorldCover grid line.
        exact_grid=crs.GRID_WEST + (5*crs.BLOCK_SIDE+288)*crs.PIXEL_STEP_DEGREES
        poly=fixture(points=[
            (50.5160,exact_grid),(50.5160,exact_grid+0.00006),
            (50.5161,exact_grid+0.00006),(50.5161,exact_grid),
            (50.5160,exact_grid),
        ])
        result=crs.inspect_original_crs_and_topology(poly)
        self.assertFalse(result["all_vertices_more_than_operation_accuracy_from_raster_grid_lines"])
        self.assertFalse(result["model_input_approved"])

    def test_one_exact_bounded_original_wfs_and_no_unsafe_output(self):
        answer=Reply()
        seen=[]
        def fake(req,timeout):
            seen.append((req.full_url,req.get_method(),
                         req.get_header("Accept-encoding"),timeout))
            return answer
        receipt=crs.probe(open_request=fake)
        self.assertEqual(seen,[(crs.URL,"GET","identity",crs.TIMEOUT_SECONDS)])
        self.assertEqual(answer.read_sizes,[crs.MAX_BYTES+1])
        self.assertFalse(receipt["raw_source_geometry_or_address_persisted"])
        self.assertFalse(receipt["raw_building_coordinates_or_ids_emitted"])
        self.assertEqual(len(receipt["source_response_sha256"]),64)
        self.assertFalse(receipt["model_input_approved"])

    def test_bad_http_status_redirect_transport_mime_and_size_fail_closed(self):
        standard={"Content-Type":"application/gml+xml",
                  "Content-Length":str(len(fixture()))}
        cases=[
            Reply(status=206),Reply(status=404),
            Reply(url="https://invalid.example/wfs"),
            Reply(headers={**standard,"Content-Type":"text/html"}),
            Reply(headers={**standard,"Content-Encoding":"gzip"}),
            Reply(headers={**standard,"Content-Length":"90000000"}),
            Reply(raw=b"x"*(crs.MAX_BYTES+1),
                  headers={"Content-Type":"application/xml"}),
        ]
        for index,r in enumerate(cases):
            with self.subTest(index=index),self.assertRaises(crs.CRSBlocked):
                crs.probe(open_request=lambda req,timeout:r)


if __name__=="__main__":
    unittest.main()
