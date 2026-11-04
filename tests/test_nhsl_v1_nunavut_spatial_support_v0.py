# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only geometry and centroid spatial-support regression tests."""

from __future__ import annotations

import copy
import math
import struct
import unittest

from scripts.nhsl_v1_nunavut_spatial_support_v0 import (
    NHSLSpatialError, _gpkg_polygon, _is_on_footprint, spatial_profile,
)


def polygon_wkb(rings: list[list[tuple[float, float]]]) -> bytes:
    blob = b"\x01" + struct.pack("<I", 3) + struct.pack("<I", len(rings))
    for ring in rings:
        blob += struct.pack("<I", len(ring))
        blob += b"".join(struct.pack("<dd", x, y) for x, y in ring)
    return blob


def gpkgbinary(rings: list[list[tuple[float, float]]],
               *, multi: bool = False, srs_id: int = 4326) -> bytes:
    wkb = polygon_wkb(rings)
    if multi:
        wkb = b"\x01" + struct.pack("<II", 6, 1) + wkb
    return b"GP\x00\x01" + struct.pack("<i", srs_id) + wkb


def tiny_square(x: float = -100.0, y: float = 60.0) -> bytes:
    outer = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1), (x, y)]
    return gpkgbinary([outer])


def fake_nunavut() -> tuple[list[dict], list[dict]]:
    """103 entirely invented polygons and 2087 invented archetypes."""
    polygons = []
    for i in range(103):
        lon, lat = -100.5 + i / 1000, 60.5
        polygons.append({
            "Sauid": f"FAKE-SAUID-{i}",
            "E_SauidLon": lon, "E_SauidLat": lat,
            "Et_AssetValue": 1000.0 + i,
            "geom_poly": tiny_square(-101.0 + i / 1000, 60.0),
        })
    archetypes = []
    for i in range(2087):
        polygon = polygons[i % len(polygons)]
        archetypes.append({
            "Sauid": polygon["Sauid"],
            "BldgLon": polygon["E_SauidLon"],
            "BldgLat": polygon["E_SauidLat"],
        })
    return polygons, archetypes


class TestNHSLOriginalSpatialSupport(unittest.TestCase):
    def test_synthetic_103_2087_centroid_and_geometry_receipt(self) -> None:
        p, b = fake_nunavut()
        output = spatial_profile(p, b)
        self.assertEqual(output["original_source_polygon_areas"], 103)
        self.assertEqual(output["original_source_archetypes"], 2087)
        self.assertEqual(output["centroid_inside_polygon_count"], 103)
        self.assertEqual(output["centroid_outside_polygon_count"], 0)
        self.assertTrue(output["archetype_parent_centroid_agreement_passed"])
        self.assertEqual(output["archetype_missing_polygon_count"], 0)
        self.assertEqual(output["archetype_centroid_coordinate_mismatch_count"], 0)
        self.assertGreater(output["vertex_radius_proxy_km"]["p90"], 1)
        self.assertGreaterEqual(output["vertex_radius_proxy_km"]["maximum"],
                                output["vertex_radius_proxy_km"]["p95"])
        self.assertEqual(output["max_archetype_to_parent_center_km"], 0)
        self.assertGreater(output["area_radius_greater_than_km"]["1.0"]["replacement_value_share"], 0)
        for name in ("radius_is_true_building_location_error", "modeled_hazard_or_losses",
                     "individual_roof_coordinates_proven", "insured_tiv_proven",
                     "can_export_oed", "source_model_use_approved", "source_admitted"):
            self.assertIs(output[name], False, name)
        self.assertEqual(output["admission_status"], "not_admitted")
        self.assertNotIn("FAKE-SAUID", str(output))
        self.assertNotIn("geom_poly", str(output))

    def test_polygon_and_multipolygon_wkb_support(self) -> None:
        ring = [(-100, 60), (-99, 60), (-99, 61), (-100, 61), (-100, 60)]
        for multipart in (False, True):
            with self.subTest(multipart=multipart):
                polygon = _gpkg_polygon(gpkgbinary([ring], multi=multipart))
                self.assertEqual(len(polygon), 1)
                self.assertTrue(_is_on_footprint((-99.5, 60.5), polygon))
                self.assertTrue(_is_on_footprint((-100, 60.5), polygon))
                self.assertFalse(_is_on_footprint((-101, 60.5), polygon))

    def test_interior_hole_counts_as_outside(self) -> None:
        outside = [(-102, 60), (-98, 60), (-98, 64), (-102, 64), (-102, 60)]
        inside = [(-101, 61), (-99, 61), (-99, 63), (-101, 63), (-101, 61)]
        rings = _gpkg_polygon(gpkgbinary([outside, inside]))
        self.assertFalse(_is_on_footprint((-100, 62), rings))
        self.assertTrue(_is_on_footprint((-101.5, 62), rings))

    def test_duplicate_and_missing_sauid_rejected(self) -> None:
        p, b = fake_nunavut()
        p[1]["Sauid"] = p[0]["Sauid"]
        with self.assertRaisesRegex(NHSLSpatialError, "duplicate"):
            spatial_profile(p, b)
        p, b = fake_nunavut()
        p[0]["Sauid"] = None
        with self.assertRaisesRegex(NHSLSpatialError, "missing"):
            spatial_profile(p, b)

    def test_misaligned_archetype_centroid_cannot_pass(self) -> None:
        p, b = fake_nunavut()
        b[0]["BldgLon"] += 0.01
        result = spatial_profile(p, b)
        self.assertFalse(result["archetype_parent_centroid_agreement_passed"])
        self.assertEqual(result["archetype_centroid_coordinate_mismatch_count"], 1)
        self.assertGreater(result["max_archetype_to_parent_center_km"], 0)
        self.assertFalse(result["can_export_oed"])
        b[0]["Sauid"] = "ABSENT"
        result = spatial_profile(p, b)
        self.assertEqual(result["archetype_missing_polygon_count"], 1)
        self.assertFalse(result["archetype_parent_centroid_agreement_passed"])

    def test_outside_centroid_is_reported_not_silently_moved(self) -> None:
        p, b = fake_nunavut()
        p[0]["E_SauidLon"] = -90
        result = spatial_profile(p, b)
        self.assertEqual(result["centroid_outside_polygon_count"], 1)
        self.assertFalse(result["archetype_parent_centroid_agreement_passed"])

    def test_corrupt_binary_or_srs_and_wrong_geometry_rejected(self) -> None:
        valid = tiny_square()
        bad = [
            b"\x00" * 26,
            valid[:-4],
            valid + b"\x00",
            valid[:4] + struct.pack("<i", 3857) + valid[8:],
            valid[:8] + b"\x01" + struct.pack("<I", 1) + b"\x00" * 16,
            valid[:8] + b"\x01" + struct.pack("<I", 3003) + valid[13:],
            valid[:3] + b"\xff" + valid[4:],
        ]
        for i, original in enumerate(bad):
            with self.subTest(i=i):
                with self.assertRaises(NHSLSpatialError):
                    _gpkg_polygon(original)

    def test_open_rings_and_nonfinite_coordinates_rejected(self) -> None:
        open_ring = [(-100, 60), (-99, 60), (-99, 61), (-100, 61)]
        with self.assertRaisesRegex(NHSLSpatialError, "unclosed"):
            _gpkg_polygon(gpkgbinary([open_ring]))
        inf_ring = [(-100, 60), (-99, 60), (math.inf, 61), (-100, 61), (-100, 60)]
        with self.assertRaisesRegex(NHSLSpatialError, "nonfinite"):
            _gpkg_polygon(gpkgbinary([inf_ring]))

    def test_missing_negative_or_nan_source_values_rejected(self) -> None:
        for v in (-1.0, float("nan"), None, True):
            with self.subTest(value=str(v)):
                p, b = fake_nunavut()
                p[0]["Et_AssetValue"] = v
                with self.assertRaises(NHSLSpatialError):
                    spatial_profile(p, b)

    def test_dateline_spanning_geometry_rejected(self) -> None:
        ring = [(-179, 60), (179, 60), (179, 61), (-179, 61), (-179, 60)]
        p, b = fake_nunavut()
        p[0]["geom_poly"] = gpkgbinary([ring])
        with self.assertRaisesRegex(NHSLSpatialError, "dateline"):
            spatial_profile(p, b)


if __name__ == "__main__":
    unittest.main()
