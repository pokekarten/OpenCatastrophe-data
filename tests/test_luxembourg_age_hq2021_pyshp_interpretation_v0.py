# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only PyShp original polygon alternate-interpreter challenge."""
from __future__ import annotations

import io
import json
import unittest

try:
    import shapefile
    HAS_PYSHP = True
except ImportError:
    HAS_PYSHP = False

from research_runners.luxembourg_age_hq2021_pyshp_interpretation_v0 import (
    OriginalInterpreterError, interpret_bytes,
)


def test_shp(*, two_polygons=False) -> tuple[bytes, bytes, bytes, int, int]:
    shape = io.BytesIO()
    index = io.BytesIO()
    dbf = io.BytesIO()
    with shapefile.Writer(shp=shape, shx=index, dbf=dbf,
                          shapeType=shapefile.POLYGON) as w:
        w.field("OBJECTID", "N")
        outer = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]
        hole = [(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)]
        rings = [outer, hole]
        if two_polygons:
            rings.append([(20, 0), (20, 10), (30, 10), (30, 0), (20, 0)])
        w.poly(rings)
        w.record(1)
    return (shape.getvalue(), index.getvalue(), dbf.getvalue(),
            len(rings), sum(len(r) for r in rings))


@unittest.skipUnless(HAS_PYSHP, "Optional pinned pyshp 2.3.1")
class IndependentPyShpInterpretationTests(unittest.TestCase):
    def test_original_shapefile_standard_exterior_hole(self):
        shp, shx, dbf, rings, points = test_shp()
        report = interpret_bytes(shp=shp, shx=shx, dbf=dbf,
                                 expected_rings=rings, expected_points=points)
        self.assertEqual(report["pyshp_geo_interface_geometry_type"], "Polygon")
        self.assertEqual(report["pyshp_interpreted_polygon_group_count"], 1)
        self.assertEqual(report["pyshp_interpreted_hole_ring_count"], 1)
        self.assertTrue(report["original_source_ring_count_conserved"])
        self.assertFalse(report["source_outline_hole_semantics_independently_verified"])
        self.assertFalse(report["CAT_model_input_admitted"])
        self.assertNotIn("coordinates", json.dumps(report))

    def test_multiple_exteriors_cannot_be_misread_as_one(self):
        shp, shx, dbf, rings, points = test_shp(two_polygons=True)
        r = interpret_bytes(shp=shp, shx=shx, dbf=dbf,
                            expected_rings=rings, expected_points=points)
        self.assertEqual(r["pyshp_geo_interface_geometry_type"], "MultiPolygon")
        self.assertEqual(r["pyshp_interpreted_polygon_group_count"], 2)
        self.assertEqual(r["pyshp_interpreted_hole_ring_count"], 1)

    def test_source_point_loss_and_ring_mismatch_fail(self):
        shp, shx, dbf, rings, points = test_shp()
        for rr, pp in ((rings + 1, points), (rings, points + 1)):
            with self.subTest(rr=rr, pp=pp), self.assertRaises(OriginalInterpreterError):
                interpret_bytes(shp=shp, shx=shx, dbf=dbf,
                                expected_rings=rr, expected_points=pp)
        with self.assertRaises(OriginalInterpreterError):
            interpret_bytes(shp=b"garbage" + shp, shx=shx, dbf=dbf,
                            expected_rings=rings, expected_points=points)

    def test_reject_unbounded_rings_and_nonsensical_counts(self):
        shp, shx, dbf, rings, points = test_shp()
        for rr, pp in ((0, points), (20001, 100000), (rings, 2000001),
                       (rings, -1)):
            with self.subTest(rr=rr, pp=pp), self.assertRaises(OriginalInterpreterError):
                interpret_bytes(shp=shp, shx=shx, dbf=dbf,
                                expected_rings=rr, expected_points=pp)


if __name__ == "__main__":
    unittest.main()
