# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only PLATEAU 6697 envelope and inline LOD0 ring screening."""

from __future__ import annotations

import json
import unittest

from research_runners.plateau_citygml_sample_structure_v0 import (
    CityGMLPreflightError,
    inspect_gml_bytes,
)

CORE = "http://www.opengis.net/citygml/2.0"
GML = "http://www.opengis.net/gml"
BLDG = "http://www.opengis.net/citygml/building/2.0"
CRS = "http://www.opengis.net/def/crs/EPSG/0/6697"
RECT = ("35.660 139.660 20 35.660 139.670 20 "
        "35.670 139.670 20 35.670 139.660 20 35.660 139.660 20")


def lod0(coords: str, tag: str = "lod0FootPrint", interior: str = "") -> str:
    return (
        f"<bldg:{tag}><gml:MultiSurface><gml:surfaceMember><gml:Polygon>"
        "<gml:exterior><gml:LinearRing><gml:posList>"
        + coords +
        "</gml:posList></gml:LinearRing></gml:exterior>"
        + interior +
        f"</gml:Polygon></gml:surfaceMember></gml:MultiSurface></bldg:{tag}>"
    )


def fixture(inner: str, *, corner_dimensions: bool = False) -> bytes:
    env_dim = "" if corner_dimensions else ' srsDimension="3"'
    corner_dim = ' srsDimension="3"' if corner_dimensions else ""
    return (
        f'<core:CityModel xmlns:core="{CORE}" xmlns:gml="{GML}" xmlns:bldg="{BLDG}">'
        f'<gml:boundedBy><gml:Envelope srsName="{CRS}"{env_dim}>'
        f'<gml:lowerCorner{corner_dim}>35.65 139.65 12</gml:lowerCorner>'
        f'<gml:upperCorner{corner_dim}>35.71 139.77 89</gml:upperCorner>'
        '</gml:Envelope></gml:boundedBy>'
        '<core:cityObjectMember><bldg:Building gml:id="synthetic_building_1">'
        + inner + '</bldg:Building></core:cityObjectMember></core:CityModel>'
    ).encode("utf-8")


class PlateauLod0RingScreenTests(unittest.TestCase):
    def test_valid_footprint_screens_only_structure(self):
        r = inspect_gml_bytes(fixture(lod0(RECT)))
        self.assertEqual(r["lod0_footprint_inline_ring_screened_count"], 1)
        self.assertEqual(r["lod0_roofedge_inline_ring_screened_count"], 0)
        self.assertEqual(r["lod0_geometry_unresolved_property_count"], 0)
        self.assertFalse(r["geometry_topology_validated"])
        self.assertFalse(r["geodesic_building_area_computed"])
        self.assertFalse(r["model_input_approved"])
        self.assertNotIn("139.660", json.dumps(r))

    def test_roof_edge_distinct_from_footprint(self):
        r = inspect_gml_bytes(fixture(lod0(RECT, tag="lod0RoofEdge")))
        self.assertEqual(r["lod0_footprint_inline_ring_screened_count"], 0)
        self.assertEqual(r["lod0_roofedge_inline_ring_screened_count"], 1)

    def test_corner_only_dimensions_are_valid_per_official_spec(self):
        r = inspect_gml_bytes(fixture(lod0(RECT), corner_dimensions=True))
        self.assertTrue(r["envelope_explicit_three_dimensional_declaration"])
        self.assertEqual(r["lod0_footprint_inline_ring_screened_count"], 1)

    def test_one_corner_dimension_does_not_prove_3d(self):
        src = fixture(lod0(RECT), corner_dimensions=True)
        src = src.replace(b'<gml:upperCorner srsDimension="3">', b"<gml:upperCorner>")
        with self.assertRaisesRegex(CityGMLPreflightError, "explicitly use EPSG"):
            inspect_gml_bytes(src)

    def test_empty_geometry_remains_unknown(self):
        r = inspect_gml_bytes(fixture("<bldg:lod0FootPrint><gml:MultiSurface/></bldg:lod0FootPrint>"))
        self.assertEqual(r["lod0_geometry_unresolved_property_count"], 1)
        self.assertEqual(r["lod0_footprint_inline_ring_screened_count"], 0)

    def test_unclosed_polygon_rejected(self):
        src = RECT.rsplit(" ", 3)[0] + " 35.661 139.660 20"
        with self.assertRaisesRegex(CityGMLPreflightError, "not closed"):
            inspect_gml_bytes(fixture(lod0(src)))

    def test_out_of_envelope_polygon_rejected(self):
        with self.assertRaisesRegex(CityGMLPreflightError, "outside the root"):
            inspect_gml_bytes(fixture(lod0(RECT.replace("139.670", "139.900"))))

    def test_bad_triples_and_nonfinite_values_rejected(self):
        for bad in (
            "35.66 139.66 20 35.67 139.67 20 35.66 139.66",
            RECT.replace("35.660", "NaN", 1),
        ):
            with self.subTest(bad=bad[:28]), self.assertRaises(CityGMLPreflightError):
                inspect_gml_bytes(fixture(lod0(bad)))

    def test_not_enough_points_and_duplicate_horizontal_vertex_rejected(self):
        invalid = (
            "35.660 139.660 20 35.670 139.670 20 "
            "35.660 139.660 20 35.660 139.660 20",
            "35.660 139.660 20 35.660 139.670 20 "
            "35.670 139.670 20 35.660 139.670 20 "
            "35.660 139.660 20",
        )
        for bad in invalid:
            with self.subTest(bad=bad[:30]), self.assertRaises(CityGMLPreflightError):
                inspect_gml_bytes(fixture(lod0(bad)))

    def test_self_crossing_rings_blocked(self):
        bowtie = (
            "35.660 139.660 20 35.670 139.670 20 "
            "35.660 139.670 20 35.670 139.660 20 "
            "35.660 139.660 20"
        )
        with self.assertRaises(CityGMLPreflightError):
            inspect_gml_bytes(fixture(lod0(bowtie)))

    def test_hole_is_unresolved_not_validated(self):
        interior = (
            "<gml:interior><gml:LinearRing><gml:posList>"
            + RECT + "</gml:posList></gml:LinearRing></gml:interior>"
        )
        r = inspect_gml_bytes(fixture(lod0(RECT, interior=interior)))
        self.assertEqual(r["lod0_geometry_unresolved_property_count"], 1)
        self.assertEqual(r["lod0_footprint_inline_ring_screened_count"], 0)

    def test_xlink_referenced_geometry_unresolved(self):
        geom = (
            '<bldg:lod0FootPrint xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<gml:MultiSurface xlink:href="#synthetic-ref"/>'
            '</bldg:lod0FootPrint>'
        )
        r = inspect_gml_bytes(fixture(geom))
        self.assertEqual(r["lod0_geometry_unresolved_property_count"], 1)
        self.assertFalse(r["unreferenced_geometry_resolved"])

    def test_more_than_400_real_style_polygons_are_partial_not_corrupt(self):
        member = (
            "<gml:surfaceMember><gml:Polygon>"
            "<gml:exterior><gml:LinearRing><gml:posList>"
            + RECT +
            "</gml:posList></gml:LinearRing></gml:exterior>"
            "</gml:Polygon></gml:surfaceMember>"
        )
        gml = (
            "<bldg:lod0FootPrint><gml:MultiSurface>"
            + member * 403 +
            "</gml:MultiSurface></bldg:lod0FootPrint>"
        )
        r = inspect_gml_bytes(fixture(gml))
        self.assertEqual(r["lod0_footprint_inline_ring_screened_count"], 400)
        self.assertEqual(r["lod0_polygons_not_screened_due_to_budget"], 3)
        self.assertEqual(r["lod0_geometry_unresolved_property_count"], 3)
        self.assertTrue(r["lod0_polygon_screen_budget_exhausted"])
        self.assertFalse(r["geometry_topology_validated"])
        self.assertFalse(r["model_input_approved"])

    def test_bad_polygon_in_first_400_remains_blocked(self):
        valid = lod0(RECT)
        invalid = lod0("35.66 139.66 20 35.66 139.67 20 "
                       "35.67 139.67 20 35.66 139.66 20 35.66 139.66 20")
        with self.assertRaises(CityGMLPreflightError):
            inspect_gml_bytes(fixture(valid * 399 + invalid))

    def test_ring_vertex_limit(self):
        coords = ["35.660 139.660 20"] + [
            f"35.66 {139.660 + j * 0.0000001:.8f} 20"
            for j in range(1, 130)
        ] + ["35.660 139.660 20"]
        with self.assertRaisesRegex(CityGMLPreflightError, "vertex budget"):
            inspect_gml_bytes(fixture(lod0(" ".join(coords))))


if __name__ == "__main__":
    unittest.main()
