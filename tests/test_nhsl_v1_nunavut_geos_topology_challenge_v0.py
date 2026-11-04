# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic-only independent GEOS NHSL polygon/centroid tests."""

from __future__ import annotations

import math
import struct
import unittest

from shapely.geometry import MultiPolygon, Polygon, box

from scripts.nhsl_v1_nunavut_geos_topology_challenge_v0 import (
    NHSLTopologyError, _wkb_from_gpkg, independent_topology,
)


def gpkg(geometry, *, srs: int = 4326) -> bytes:
    # Artificial GPKG header and actual valid Shapely WKB; no source data.
    return b"GP\x00\x01" + struct.pack("<i", srs) + geometry.wkb


def fixture():
    # Fully invented polygons, 1 hole, and one disjoint MultiPolygon.
    ring_hole = Polygon(
        [(0, 0), (4, 0), (4, 4), (0, 4)],
        holes=[[(1, 1), (3, 1), (3, 3), (1, 3)]],
    )
    return [
        {"Sauid": "SYNTH-A", "E_SauidLon": -99, "E_SauidLat": 61,
         "Et_AssetValue": 100, "geom_poly": gpkg(box(-100, 60, -98, 62))},
        {"Sauid": "SYNTH-B", "E_SauidLon": 2, "E_SauidLat": 2,
         "Et_AssetValue": 300, "geom_poly": gpkg(ring_hole)},
        {"Sauid": "SYNTH-C", "E_SauidLon": 20, "E_SauidLat": 20,
         "Et_AssetValue": 600,
         "geom_poly": gpkg(MultiPolygon([box(8, 8, 9, 9), box(10, 10, 11, 11)]))},
    ]


class TestNHSLIndependentGEOSChallenge(unittest.TestCase):
    def test_shapely_covers_centroids_and_reports_value_share(self) -> None:
        r = independent_topology(fixture())
        self.assertEqual(r["polygons"], 3)
        self.assertEqual(r["geos_valid_geometry_count"], 3)
        self.assertEqual(r["geos_centroids_in_or_on_polygon_count"], 1)
        self.assertEqual(r["geos_reported_centroids_outside_polygon_count"], 2)
        self.assertEqual(r["geos_interiors_hole_count"], 1)
        self.assertEqual(r["geos_multipart_area_count"], 1)
        self.assertEqual(r["outside_centroid_modeled_value_share"], 0.9)
        self.assertGreater(r["max_outside_centroid_to_polygon_nearest_point_km_proxy"], 0)
        self.assertFalse(r["source_admitted"])
        self.assertFalse(r["oed_insured_locations_exportable"])
        self.assertFalse(r["geodesic_topology_or_hazard_coverage_proven"])
        self.assertEqual(r["admission_status"], "not_admitted")
        self.assertNotIn("SYNTH", str(r))
        self.assertNotIn("geom_poly", str(r))

    def test_on_boundary_is_covered(self) -> None:
        rows = fixture()
        rows[0]["E_SauidLon"] = -100
        result = independent_topology(rows)
        self.assertEqual(result["geos_reported_centroids_on_boundary_count"], 1)
        self.assertEqual(result["geos_reported_centroids_outside_polygon_count"], 2)

    def test_wrong_srs_gpkg_flags_missing_geometry_rejected(self) -> None:
        base = fixture()
        for value in (None, b"", b"bogus", gpkg(box(0, 0, 1, 1), srs=3857),
                      gpkg(box(0, 0, 1, 1))[:3] + b"\xFF"
                      + gpkg(box(0, 0, 1, 1))[4:]):
            with self.subTest(case=str(value)[:18]):
                rows = fixture()
                rows[0]["geom_poly"] = value
                with self.assertRaises(NHSLTopologyError):
                    independent_topology(rows)

    def test_nan_negative_and_missing_cost_fail(self) -> None:
        for value in (None, -100, True, float("nan"), "500"):
            with self.subTest(value=repr(value)):
                rows = fixture()
                rows[0]["Et_AssetValue"] = value
                with self.assertRaises(NHSLTopologyError):
                    independent_topology(rows)

    def test_nonpolygon_and_empty_geometry_fail(self) -> None:
        from shapely.geometry import LineString, Polygon as Poly
        for geom in (LineString([(0, 0), (1, 1)]), Poly()):
            with self.subTest(geom=geom.geom_type):
                rows = fixture()
                rows[0]["geom_poly"] = gpkg(geom)
                with self.assertRaisesRegex(NHSLTopologyError, "nonempty polygon"):
                    independent_topology(rows)

    def test_self_intersection_detected_not_silently_repaired(self) -> None:
        bow = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
        self.assertFalse(bow.is_valid)
        rows = fixture()
        rows[0]["geom_poly"] = gpkg(bow)
        receipt = independent_topology(rows)
        self.assertEqual(receipt["geos_invalid_geometry_count"], 1)
        self.assertEqual(receipt["geos_valid_geometry_count"], 2)

    def test_duplicate_sauid_or_empty_source_rejected(self) -> None:
        with self.assertRaisesRegex(NHSLTopologyError, "empty"):
            independent_topology([])
        rows = fixture()
        rows[1]["Sauid"] = rows[0]["Sauid"]
        with self.assertRaisesRegex(NHSLTopologyError, "duplicate"):
            independent_topology(rows)


if __name__ == "__main__":
    unittest.main()
