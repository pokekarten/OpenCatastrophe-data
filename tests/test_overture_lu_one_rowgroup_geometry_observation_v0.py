# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only bounded real-source geometry smoke screen tests."""
import math
import struct
import unittest

from shapely.geometry import box
from research_runners.overture_lu_one_rowgroup_geometry_observation_v0 import (
    TARGET_ROW_COUNT, ProbeError, _coordinates_in_city_box,
    _expected_column_bytes, screen_original_rows, main,
)


def bbox(xmin=6.1291, ymin=49.6091, xmax=6.1292, ymax=49.6092):
    return {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


class Column:
    def __init__(self, path, size):
        self.path_in_schema = path
        self.total_compressed_size = size


class Group:
    def __init__(self, columns):
        self.columns = columns
        self.num_columns = len(columns)

    def column(self, i):
        return self.columns[i]


def columns():
    return Group([Column(name, 1000) for name in
                  ("geometry", "bbox.xmin", "bbox.ymin", "bbox.xmax", "bbox.ymax")])


class OriginalGeometryTests(unittest.TestCase):
    def test_bounds_overlap_uses_necessary_intersection(self):
        self.assertTrue(_coordinates_in_city_box(bbox()))
        self.assertFalse(_coordinates_in_city_box(bbox(5.0, 49.609, 5.1, 49.611)))

    def test_bad_coordinates_are_not_candidates(self):
        b = bbox()
        b["xmin"] = float("nan")
        self.assertFalse(_coordinates_in_city_box(b))

    def test_original_column_projection_budget(self):
        self.assertEqual(_expected_column_bytes(columns()), 5000)

    def test_missing_geometry_source_column_rejected(self):
        with self.assertRaises(ProbeError):
            _expected_column_bytes(Group(columns().columns[1:]))

    def test_large_source_column_budget_rejected(self):
        g = columns()
        g.columns[0].total_compressed_size = 13 * 1024 * 1024
        with self.assertRaises(ProbeError):
            _expected_column_bytes(g)

    def test_synthetic_actual_polygons_are_aggregated_only(self):
        valid = box(6.1291,49.6091,6.1292,49.6092).wkb
        bboxes = [bbox()] + [bbox(5.9,49.5,5.91,49.51)] * (TARGET_ROW_COUNT-1)
        blobs = [valid] + [b""] * (TARGET_ROW_COUNT-1)
        out = screen_original_rows(bboxes, blobs)
        self.assertEqual(out["source_bbox_candidates_in_research_window"], 1)
        self.assertEqual(out["original_valid_polygons_with_positive_window_overlap"], 1)
        self.assertGreater(out["profiled_geodesic_footprint_m2_median"], 1)
        self.assertFalse(out["individual_original_ids_or_polygons_emitted"])
        self.assertFalse(out["insurance_CAT_model_input_approved"])
        self.assertNotIn("6.1291", str(out))

    def test_synthetic_invalid_wkb_quarantined(self):
        bboxes = [bbox()] + [bbox(5.9,49.5,5.91,49.51)] * (TARGET_ROW_COUNT-1)
        blobs = [b"NotWKB"] + [b""]*(TARGET_ROW_COUNT-1)
        out = screen_original_rows(bboxes, blobs)
        self.assertEqual(out["malformed_geometry_candidates"],1)
        self.assertEqual(out["original_valid_polygons_with_positive_window_overlap"],0)

    def test_reject_rowgroup_rows_missing(self):
        with self.assertRaises(ProbeError):
            screen_original_rows([bbox()], [box(6.129,49.609,6.130,49.610).wkb])

    def test_no_original_download_by_default(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
