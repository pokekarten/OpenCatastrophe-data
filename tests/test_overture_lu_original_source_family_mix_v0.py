# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only upstream provider mix aggregation and anti-ID leakage tests."""
import unittest

from research_runners.overture_lu_original_source_family_mix_v0 import (
    TARGET_ROW_COUNT, ProbeError, _safe_label, summarize_sources, main
)


def bbox(inside=False):
    return {"xmin":6.1291,"ymin":49.6091,"xmax":6.1292,"ymax":49.6092} if inside else {
        "xmin":3.9,"ymin":48.7,"xmax":4.0,"ymax":48.8
    }


def synthetic(entries=None):
    boxes = [bbox(True)] * 69 + [bbox(False)] * (TARGET_ROW_COUNT - 69)
    src = [entries if entries is not None else
           [{"dataset":"OpenStreetMap","license":"ODbL-1.0",
             "record_id":"SECRET-SOURCE-RECORD-NOT-TO-PRINT"}]
           for _ in range(69)]
    src += [None] * (TARGET_ROW_COUNT - 69)
    return boxes, src


class SourceFamilyTests(unittest.TestCase):
    def test_source_labels_count_source_rows_not_entries(self):
        boxes, src = synthetic()
        out = summarize_sources(boxes, src)
        self.assertEqual(out["original_source_rows_intersecting_bbox"], 69)
        self.assertEqual(out["upstream_dataset_row_presence_counts"], {"OpenStreetMap":69})
        self.assertEqual(out["upstream_license_tag_row_presence_counts"], {"ODbL-1.0":69})
        self.assertNotIn("SECRET-SOURCE-RECORD-NOT-TO-PRINT", str(out))
        self.assertFalse(out["model_input_approved"])

    def test_duplicate_same_dataset_does_not_double_count(self):
        entries=[{"dataset":"OpenStreetMap"},{"dataset":"OpenStreetMap"}]
        out=summarize_sources(*synthetic(entries))
        self.assertEqual(out["upstream_dataset_row_presence_counts"]["OpenStreetMap"],69)
        self.assertEqual(out["city_bbox_rows_with_multiple_upstream_datasets"],0)

    def test_two_distinct_upstream_datasets_per_record(self):
        entries=[{"dataset":"OpenStreetMap"},{"dataset":"Microsoft Buildings"}]
        out=summarize_sources(*synthetic(entries))
        self.assertEqual(out["city_bbox_rows_with_multiple_upstream_datasets"],69)
        self.assertEqual(out["upstream_dataset_row_presence_counts"]["Microsoft Buildings"],69)

    def test_missing_source_metadata_keeps_city_count(self):
        boxes,src=synthetic()
        src[0]=None
        out=summarize_sources(boxes,src)
        self.assertEqual(out["original_source_rows_intersecting_bbox"],69)
        self.assertEqual(out["city_bbox_rows_without_source_entries"],1)

    def test_untrusted_labels_cannot_be_logged(self):
        self.assertEqual(_safe_label("Hidden\nOriginal\tCoordinates"),"unclassified")

    def test_bad_rowgroup_cardinality_rejected(self):
        with self.assertRaises(ProbeError):
            summarize_sources([bbox(True)],[None])

    def test_provider_geo_extent_drift_rejected(self):
        boxes,src=synthetic()
        boxes[0]=bbox(False)
        with self.assertRaises(ProbeError):
            summarize_sources(boxes,src)

    def test_default_never_connects_to_provider(self):
        self.assertEqual(main([]),2)


if __name__ == "__main__":
    unittest.main()
