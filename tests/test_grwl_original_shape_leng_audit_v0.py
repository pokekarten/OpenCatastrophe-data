# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only SHAPE_LENG value, units and keyed source tests."""
import io
import math
import struct
import unittest
import zipfile

from research_runners.grwl_original_aggregate_semantic_diff_v0 import (
    OriginalZipError, read_dbf_semantics,
)
from research_runners.grwl_original_oriented_vertex_metric_v0 import read_original_polylines
from research_runners.grwl_original_shape_leng_audit_v0 import (
    SCHEMA, compare_length_releases, main, read_keyed_source_lengths,
    spherical_centerline_length_km, planar_original_wgs84_length_in_degrees,
)
from tests.test_grwl_original_aggregate_semantic_diff_v0 import (
    A, B, C, artifact,
)

FIELDS = (
    ("objectid", "N", 10),
    ("width_mean", "F", 19),
    ("shape_leng", "F", 19),
    ("region", "C", 3),
)


def sample(rows=((1, "50", "100", "DE"), (2, "60", "200", "FR")), points=(A, B)):
    payload = artifact(rows=rows, points=points, fields=FIELDS)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        meta = read_dbf_semantics(archive)
        ids, lengths = read_keyed_source_lengths(archive, meta)
        shapes, count = read_original_polylines(archive)
    assert count == 4
    return ids, lengths, shapes


class SHAPELengthAuditTests(unittest.TestCase):
    def test_exact_same_values_and_xy(self):
        x = sample()
        output = compare_length_releases(x, x)
        self.assertEqual(output["schema"], SCHEMA)
        self.assertEqual(output["reported_shape_leng_value_changed"], 0)
        self.assertEqual(output["matched_unique_export_objectid_candidates"], 2)
        self.assertEqual(output["same_xy_pair_count"], 2)
        self.assertEqual(output["ratio_2026_over_2018"]["p50"], 1)
        self.assertFalse(output["model_source_admitted"])
        self.assertFalse(output["raw_original_rows_or_coordinates_emitted"])

    def test_systematic_multiplier_is_reported(self):
        early = sample()
        later = sample(rows=((1, "50", "110", "DE"), (2, "60", "220", "FR")))
        report = compare_length_releases(early, later)
        self.assertEqual(report["reported_shape_leng_value_changed"], 2)
        self.assertEqual(report["ratio_2026_over_2018"]["p50"], 1.1)
        self.assertEqual(report["same_xy_pair_count"], 2)
        self.assertEqual(report["same_xy_pair_abs_relative_change"]["p50"], 0.1)
        self.assertEqual(report["features_with_absolute_relative_change_exceeding_fraction"]["0.01"], 2)

    def test_unchanged_width_and_changed_shape_length_do_not_confuse_report(self):
        a = sample()
        b = sample(rows=((1, "50", "99.9", "DE"), (2, "60", "200.1", "FR")))
        r = compare_length_releases(a, b)
        self.assertEqual(r["reported_shape_leng_value_changed"], 2)
        self.assertFalse(r["river_width_change_verified"])

    def test_export_rows_can_be_reordered(self):
        a = sample()
        b = sample(rows=((2, "60", "200", "FR"), (1, "50", "100", "DE")), points=(B, A))
        r = compare_length_releases(a, b)
        self.assertFalse(r["export_objectid_order_equal"])
        self.assertEqual(r["reported_shape_leng_value_changed"], 0)
        self.assertEqual(r["same_xy_pair_count"], 2)

    def test_changed_geometry_not_counted_as_same_xy(self):
        a = sample()
        b = sample(points=(A, C))
        r = compare_length_releases(a, b)
        self.assertEqual(r["same_xy_pair_count"], 1)
        self.assertEqual(r["different_xy_pair_abs_relative_change"]["count"], 1)

    def test_zero_source_length_excluded_from_ratio_but_not_count(self):
        a = sample(rows=((1, "50", "0", "DE"), (2, "60", "200", "FR")))
        b = sample(rows=((1, "50", "1", "DE"), (2, "60", "200", "FR")))
        r = compare_length_releases(a, b)
        self.assertEqual(r["zero_source_length_denominator_pairs"], 1)
        self.assertEqual(r["reported_shape_leng_value_changed"], 1)
        self.assertEqual(r["ratio_2026_over_2018"]["count"], 1)

    def test_identical_geographic_coordinates_zero_length_diagnostic(self):
        zero = ((0., 0.), (0., 0.))
        x = sample(points=(zero, B))
        r = compare_length_releases(x, x)
        self.assertEqual(r["nonpositive_spherical_centerline_length_count_by_release"]["2018"], 1)
        self.assertEqual(r["reported_shape_leng_over_spherical_centerline_km_by_release"]["2018"]["count"], 1)

    def test_one_degree_at_equator_km(self):
        x = sample()
        value = spherical_centerline_length_km(x[2][0])
        self.assertGreater(value, 110)
        self.assertLess(value, 112)

    def test_missing_or_nonmatching_candidate_id_set_rejected(self):
        a = sample()
        b = sample(rows=((1, "50", "100", "DE"), (3, "60", "200", "FR")))
        with self.assertRaises(OriginalZipError):
            compare_length_releases(a, b)

    def test_duplicate_ids_rejected_before_comparison(self):
        payload = artifact(rows=((1, "50", "100", "DE"), (1, "60", "200", "FR")), fields=FIELDS)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            with self.assertRaises(OriginalZipError):
                read_keyed_source_lengths(archive, read_dbf_semantics(archive))

    def test_negative_source_length_rejected(self):
        payload = artifact(rows=((1, "50", "-1", "DE"), (2, "60", "200", "FR")), fields=FIELDS)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            with self.assertRaises(OriginalZipError):
                read_keyed_source_lengths(archive, read_dbf_semantics(archive))

    def test_null_shape_length_rejected(self):
        payload = artifact(rows=((1, "50", "", "DE"), (2, "60", "200", "FR")), fields=FIELDS)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            with self.assertRaises(OriginalZipError):
                read_keyed_source_lengths(archive, read_dbf_semantics(archive))

    def test_zero_vertex_segments_result_zero(self):
        with self.assertRaises(OriginalZipError):
            spherical_centerline_length_km(((1,), b"\0" * 16))

    def test_parts_cannot_exceed_coordinate_bytes(self):
        with self.assertRaises(OriginalZipError):
            spherical_centerline_length_km(((2,), b"\0" * 16))

    def test_all_flags_fail_closed(self):
        x = sample()
        r = compare_length_releases(x, x)
        for field in ("geodesic_distance_or_projection_method_of_source_verified",
                      "source_shape_leng_units_independently_verified",
                      "source_formula_change_explained",
                      "export_objectid_verified_as_hydrologic_identity",
                      "flood_hazard_or_insured_loss_calculated",
                      "production_database_modified"):
            self.assertFalse(r[field], field)

    def test_planar_degree_control_equator(self):
        line = sample()[2][0]
        self.assertEqual(planar_original_wgs84_length_in_degrees(line), 1.0)
        self.assertGreater(spherical_centerline_length_km(line), 110)

    def test_planar_degree_control_multipart_does_not_join_parts(self):
        pts = ((0., 0.), (1., 0.), (10., 10.), (10., 11.))
        coords = b"".join(struct.pack("<dd", *p) for p in pts)
        self.assertEqual(planar_original_wgs84_length_in_degrees(((2, 2), coords)), 2)

    def test_planar_degree_control_does_not_wrap_dateline(self):
        coords = (struct.pack("<dd", 179.9, 0.) +
                  struct.pack("<dd", -179.9, 0.))
        self.assertAlmostEqual(
            planar_original_wgs84_length_in_degrees(((2,), coords)), 359.8)

    def test_same_geometry_2018_degree_units_and_2026_kilometres(self):
        old = sample(rows=((1, "50", "1", "DE"), (2, "60", "1", "FR")))
        new = sample(rows=((1, "50", "111.195", "DE"),
                           (2, "60", "111.195", "FR")))
        out = compare_length_releases(old, new)
        degree_ratio = out["original_2018_shape_leng_over_wgs84_planar_degrees"]
        km_ratio = out["reported_shape_leng_over_spherical_centerline_km_by_release"]["2026"]
        self.assertEqual(degree_ratio["p50"], 1.0)
        self.assertGreater(km_ratio["p50"], .99)
        self.assertLess(km_ratio["p50"], 1.01)
        self.assertEqual(out["original_2018_features_exceeding_planar_degree_rel_error"]["0.01"], 0)
        self.assertEqual(out["original_2026_features_exceeding_spherical_km_rel_error"]["0.01"], 0)
        self.assertTrue(out["planar_degree_control_is_not_ground_distance"])
        self.assertFalse(out["source_formula_change_explained"])

    def test_planar_degree_outlier_count_is_not_suppressed(self):
        old = sample(rows=((1, "50", "2", "DE"), (2, "60", "1", "FR")))
        new = sample()
        out = compare_length_releases(old, new)
        self.assertEqual(out["original_2018_features_exceeding_planar_degree_rel_error"]["0.01"], 1)
        self.assertEqual(out["original_2018_abs_relative_error_vs_planar_degrees"]["count"], 2)

    def test_no_network_by_default(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
