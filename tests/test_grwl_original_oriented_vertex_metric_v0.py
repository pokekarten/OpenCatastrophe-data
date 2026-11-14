# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GRWL vertex correspondence tests; no original river coordinates."""
import io
import math
import struct
import unittest
import zipfile

from research_runners.grwl_original_oriented_vertex_metric_v0 import (
    OriginalZipError, _haversine_metres, compare_geometry,
    compare_original_by_objectid, main, read_original_polylines,
)
from research_runners.grwl_original_aggregate_semantic_diff_v0 import read_dbf_semantics
from tests.test_grwl_original_aggregate_semantic_diff_v0 import artifact, A, B, C


def geometry(*parts):
    flat = [pt for part in parts for pt in part]
    return tuple(len(part) for part in parts), b"".join(struct.pack("<dd", *p) for p in flat)


def fixture(rows, xy_parts=(A, B)):
    fields=(("objectid","N",10),("width_mean","N",12),
            ("lakeflag","N",3),("region","C",3))
    payload=artifact(rows=rows, points=xy_parts, fields=fields)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        return read_dbf_semantics(z), read_original_polylines(z)[0]


def keyed(a,b):
    da,sa=a
    db,sb=b
    return compare_original_by_objectid(da,db,sa,sb)


class OrientedVertexTests(unittest.TestCase):
    def test_byte_identical(self):
        g=geometry(A)
        self.assertEqual(compare_geometry(g,g)["class"],"byte_identical")

    def test_whole_polyline_reverse_without_displacement(self):
        x=compare_geometry(geometry(A),geometry(tuple(reversed(A))))
        self.assertEqual(x["class"],"direction_or_part_order_only")
        self.assertEqual(x["max_vertex_correspondence_metres"],0.0)

    def test_multipart_reordering_or_reverse_without_displacement(self):
        early=geometry(A,B)
        late=geometry(tuple(reversed(B)),tuple(reversed(A)))
        x=compare_geometry(early,late)
        self.assertEqual(x["class"],"direction_or_part_order_only")

    def test_one_degree_spherical_separation_approx_111km(self):
        g1=geometry(((0.,0.),(1.,0.)))
        g2=geometry(((0.,1.),(1.,1.)))
        x=compare_geometry(g1,g2)
        self.assertEqual(x["class"],"oriented_vertex_correspondence")
        self.assertGreater(x["max_vertex_correspondence_metres"],100_000)
        self.assertLess(x["max_vertex_correspondence_metres"],120_000)

    def test_tiny_coordinates_below_centimetre(self):
        g1=geometry(((0.,0.),(1.,0.)))
        g2=geometry(((0.,1e-9),(1.,1e-9)))
        x=compare_geometry(g1,g2)
        self.assertGreater(x["max_vertex_correspondence_metres"],0)
        self.assertLess(x["max_vertex_correspondence_metres"],0.01)

    def test_vertex_count_change_is_unmatchable_not_zero(self):
        a=geometry(((0.,0.),(1.,0.)))
        b=geometry(((0.,0.),(0.5,0.),(1.,0.)))
        x=compare_geometry(a,b)
        self.assertEqual(x["class"],"vertex_topology_not_correspondable")
        self.assertIsNone(x["max_vertex_correspondence_metres"])

    def test_different_part_counts_are_unmatchable(self):
        a=geometry(((0.,0.),(0.5,0.)),((0.5,0.),(1.,0.)))
        b=geometry(((0.,0.),(0.5,0.),(1.,0.)))
        self.assertEqual(compare_geometry(a,b)["class"],"vertex_topology_not_correspondable")

    def test_dateline_wrapping(self):
        d=_haversine_metres((179.9,0.),(-179.9,0.))
        self.assertGreater(d,20_000)
        self.assertLess(d,23_000)

    def test_sphere_distance_unchanged_coordinate(self):
        self.assertEqual(_haversine_metres((0.,0.),(0.,0.)),0.)

    def test_original_shp_synthetic_read(self):
        rows=((1,100,0,"DE"),(2,200,0,"FR"))
        result=fixture(rows)
        self.assertEqual(len(result[1]),2)
        self.assertEqual(result[1][0][0],(2,))

    def test_original_shp_out_of_domain_rejected(self):
        payload=artifact(points=(A,((181.,0.),(182.,0.))))
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            with self.assertRaises(OriginalZipError):
                read_original_polylines(archive)

    def test_original_shp_nan_rejected(self):
        payload=artifact(points=(A,((math.nan,0.),(2.,0.))))
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            with self.assertRaises(OriginalZipError):
                read_original_polylines(archive)

    def test_matching_candidate_preserves_reversed_order(self):
        a=fixture(((1,100,0,"DE"),(2,200,0,"FR")),(A,B))
        b=fixture(((2,200,0,"FR"),(1,100,0,"DE")),(B,A))
        result=keyed(a,b)
        self.assertEqual(result["matched_unique_export_objectid_candidates"],2)
        self.assertFalse(result["export_objectid_order_equal"])
        self.assertEqual(result["geometry_match_classes"]["byte_identical"],2)
        self.assertFalse(result["export_objectid_verified_as_hydrologic_identity"])

    def test_nontrivial_movement_aggregate_and_no_coordinates(self):
        a=fixture(((1,100,0,"DE"),(2,200,0,"FR")),(A,B))
        b=fixture(((1,100,0,"DE"),(2,200,0,"FR")),(A,C))
        result=keyed(a,b)
        self.assertEqual(result["geometry_match_classes"]["byte_identical"],1)
        self.assertEqual(result["geometry_match_classes"]["oriented_vertex_correspondence"],1)
        self.assertEqual(result["features_with_max_correspondence_greater_than_metres"]["1000.0"],1)
        self.assertFalse(result["any_original_keys_or_coordinates_published"])

    def test_key_duplicate_blocks_comparison(self):
        a=fixture(((1,100,0,"DE"),(1,200,0,"FR")),(A,B))
        with self.assertRaises(OriginalZipError):keyed(a,a)

    def test_missing_key_blocks_comparison(self):
        a=fixture(((1,100,0,"DE"),(2,200,0,"FR")),(A,B))
        b=fixture(((1,100,0,"DE"),(3,200,0,"FR")),(A,B))
        with self.assertRaises(OriginalZipError):keyed(a,b)

    def test_no_network_without_explicit_live(self):
        self.assertEqual(main([]),2)


if __name__=="__main__":
    unittest.main()
