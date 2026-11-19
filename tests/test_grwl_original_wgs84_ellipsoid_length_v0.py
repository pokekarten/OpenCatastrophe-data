# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only WGS84 ellipsoidal GRWL source-length regressions."""
from __future__ import annotations

import importlib.util
import math
from unittest.mock import patch
import struct
import unittest

from research_runners.grwl_original_aggregate_semantic_diff_v0 import OriginalZipError
from research_runners.grwl_original_wgs84_ellipsoid_length_v0 import (
    GEODESIC_VERSION_PIN, SCHEMA, _wgs84_geodesic,
    compare_ellipsoid_reference, ellipsoid_centerline_length_km, main,
)


def shape(*parts):
    flat = [point for part in parts for point in part]
    return tuple(len(part) for part in parts), b"".join(
        struct.pack("<dd", *point) for point in flat)


class SourceGateWithoutDependencies(unittest.TestCase):
    def test_real_network_disabled_by_default(self):
        self.assertEqual(main([]), 2)

    def test_version_is_explicitly_pinned(self):
        self.assertEqual(GEODESIC_VERSION_PIN, "2.1")

    def test_part_byte_extent_rejected_before_geodesic_call(self):
        with self.assertRaises(OriginalZipError):
            ellipsoid_centerline_length_km(((2,), b"\x00" * 16), None)

    def test_part_less_than_two_vertices_rejected(self):
        with self.assertRaises(OriginalZipError):
            ellipsoid_centerline_length_km(shape(((0., 0.),)), None)

    def test_nonmatching_source_record_count_fails_closed(self):
        with self.assertRaises(OriginalZipError):
            compare_ellipsoid_reference(
                [b"one"], [1.0], [shape(((0., 0.), (1., 0.)))], None)


@unittest.skipUnless(
    importlib.util.find_spec("geographiclib") is not None,
    "GeographicLib 2.1 installed in dedicated reviewed workflow; optional in core",
)
class WGS84EllipsoidSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.g = _wgs84_geodesic()

    def test_equatorial_one_degree_wgs84_inverse(self):
        got = ellipsoid_centerline_length_km(shape(((0., 0.), (1., 0.))), self.g)
        self.assertAlmostEqual(got, 111.319490793274, places=7)

    def test_meridional_one_degree_wgs84_inverse(self):
        got = ellipsoid_centerline_length_km(shape(((0., 0.), (0., 1.))), self.g)
        self.assertAlmostEqual(got, 110.574388557798, places=6)

    def test_antimeridian_shortest_path_not_360_degree_jump(self):
        src = shape(((179.9, 0.), (-179.9, 0.)))
        result = ellipsoid_centerline_length_km(src, self.g)
        self.assertGreater(result, 22)
        self.assertLess(result, 23)

    def test_reversing_direction_preserves_ellipsoid_length(self):
        a = shape(((0., 15.), (1., 15.), (2., 16.)))
        b = shape(((2., 16.), (1., 15.), (0., 15.)))
        self.assertAlmostEqual(ellipsoid_centerline_length_km(a, self.g),
                               ellipsoid_centerline_length_km(b, self.g), places=9)

    def test_multipart_segments_are_not_spuriously_connected(self):
        a = shape(((0., 0.), (1., 0.)), ((50., 50.), (50., 51.)))
        lon = shape(((0., 0.), (1., 0.)))
        lat = shape(((50., 50.), (50., 51.)))
        self.assertAlmostEqual(
            ellipsoid_centerline_length_km(a, self.g),
            ellipsoid_centerline_length_km(lon, self.g) +
            ellipsoid_centerline_length_km(lat, self.g),
            places=9)

    def test_zero_length_segment_is_counted_but_not_an_outlier(self):
        a = shape(((0., 0.), (0., 0.)))
        self.assertEqual(ellipsoid_centerline_length_km(a, self.g), 0.)

    def test_matched_synthetic_sources_no_relative_error(self):
        a = shape(((0., 0.), (1., 0.)))
        b = shape(((1., 1.), (2., 1.)))
        sources = [ellipsoid_centerline_length_km(a, self.g),
                   ellipsoid_centerline_length_km(b, self.g)]
        with patch("research_runners.grwl_original_wgs84_ellipsoid_length_v0.EXPECTED_SOURCE_FEATURES", 2):
            out = compare_ellipsoid_reference([b"a", b"b"], sources, [a, b], self.g)
        self.assertEqual(out["schema"], SCHEMA)
        self.assertEqual(out["features_with_relative_error_above"]["0.01"], 0)
        self.assertEqual(out["original_features_with_longitude_jump_above_180_degrees"], 0)
        self.assertFalse(out["model_input_admitted"])
        self.assertFalse(out["original_objectids_or_coordinates_published"])

    def test_dateline_only_outlier_is_reported_without_raw_feature(self):
        norm = shape(((0., 0.), (1., 0.)))
        dateline = shape(((179.9, 0.), (-179.9, 0.)))
        vals = [ellipsoid_centerline_length_km(norm, self.g),
                222 * ellipsoid_centerline_length_km(dateline, self.g)]
        with patch("research_runners.grwl_original_wgs84_ellipsoid_length_v0.EXPECTED_SOURCE_FEATURES", 2):
            out = compare_ellipsoid_reference(
                [b"not-original-id-1", b"not-original-id-2"], vals, [norm, dateline], self.g)
        self.assertEqual(out["original_features_with_longitude_jump_above_180_degrees"], 1)
        self.assertEqual(out["features_with_relative_error_above"]["0.01"], 1)
        self.assertEqual(out["dateline_features_with_relative_error_above"]["0.01"], 1)
        self.assertEqual(out["other_features_with_relative_error_above"]["0.01"], 0)
        self.assertGreater(out["source_over_ellipsoid_ratio_dateline"]["p50"], 200)
        self.assertFalse(out["antimeridian_source_length_cause_proven"])

    def test_normal_feature_outlier_not_classified_as_antimeridian(self):
        a = shape(((0., 0.), (1., 0.)))
        b = shape(((1., 1.), (2., 1.)))
        vals = [2 * ellipsoid_centerline_length_km(a, self.g),
                ellipsoid_centerline_length_km(b, self.g)]
        with patch("research_runners.grwl_original_wgs84_ellipsoid_length_v0.EXPECTED_SOURCE_FEATURES", 2):
            out = compare_ellipsoid_reference([b"a", b"b"], vals, [a, b], self.g)
        self.assertEqual(out["other_features_with_relative_error_above"]["0.01"], 1)
        self.assertEqual(out["dateline_features_with_relative_error_above"]["0.01"], 0)

    def test_duplicate_export_candidate_key_is_blocked(self):
        a = shape(((0., 0.), (1., 0.)))
        with patch("research_runners.grwl_original_wgs84_ellipsoid_length_v0.EXPECTED_SOURCE_FEATURES", 2):
            with self.assertRaises(OriginalZipError):
                compare_ellipsoid_reference([b"a", b"a"], [1., 1.], [a, a], self.g)

    def test_missing_source_or_shape_row_is_blocked(self):
        a = shape(((0., 0.), (1., 0.)))
        with patch("research_runners.grwl_original_wgs84_ellipsoid_length_v0.EXPECTED_SOURCE_FEATURES", 2):
            with self.assertRaises(OriginalZipError):
                compare_ellipsoid_reference([b"a", b"b"], [1.], [a, a], self.g)

    def test_negative_source_length_is_blocked(self):
        a = shape(((0., 0.), (1., 0.)))
        with patch("research_runners.grwl_original_wgs84_ellipsoid_length_v0.EXPECTED_SOURCE_FEATURES", 2):
            with self.assertRaises(OriginalZipError):
                compare_ellipsoid_reference([b"a", b"b"], [-1., 1.], [a, a], self.g)


if __name__ == "__main__":
    unittest.main()
