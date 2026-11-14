# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fictional row-and-WKB unit tests; no JRC source bytes committed."""
from __future__ import annotations

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from shapely import wkb
from shapely.geometry import Point, Polygon, box

from research_runners import eurocrops_original_full_geometry_code_qc_v0 as m


class FakeBatch:
    def __init__(self, rows):
        self.rows = rows
        self.num_rows = len(rows)

    def to_pylist(self):
        return list(self.rows)


class FakeParquet:
    def __init__(self, rows, *, geometry_column="geometry", footer_rows=None):
        self.rows = rows
        self.metadata = SimpleNamespace(
            num_rows=len(rows) if footer_rows is None else footer_rows
        )
        self.schema_arrow = SimpleNamespace(
            names=["cropfield", "original_code", "area_ha", geometry_column],
            metadata={b"geo": json.dumps({
                "primary_column": geometry_column,
                "columns": {geometry_column: {
                    "encoding": "WKB", "crs": {
                        "id": {"authority": "EPSG", "code": 3035}
                    }
                }}
            }).encode()}
        )

    def iter_batches(self, *, batch_size, columns):
        assert batch_size == m.BATCH_SIZE
        assert columns == ["cropfield", "original_code", "area_ha", "geometry"]
        for i in range(0, len(self.rows), batch_size):
            yield FakeBatch(self.rows[i:i + batch_size])


def record(id_, code, area, geom):
    return {
        "cropfield": id_, "original_code": code,
        "area_ha": area, "geometry": geom,
    }


MAPPING = [
    {"nuts": "de4", "original_code": "001", "hcat4_code": "100"},
    {"nuts": "de4", "original_code": "002", "hcat4_code": "999"},
    {"nuts": "dea", "original_code": "001", "hcat4_code": "100"},
    {"nuts": "de4", "original_code": "", "hcat4_code": "3390000000"},
]
HCAT = [{"hcat4_code": "100"}, {"hcat4_code": "3390000000"}]


class CompleteCropOriginalQCTests(unittest.TestCase):
    def test_whole_file_counts_conserve_source_values_and_geometry(self):
        bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0)])
        data = [
            record(1, "001", 1.0, wkb.dumps(box(0, 0, 100, 100))),
            record(2, "002", 1.0, wkb.dumps(box(0, 0, 100, 100))),
            record(3, "other", 1.0, wkb.dumps(box(0, 0, 100, 100))),
            record(4, "001", 0.0, wkb.dumps(Polygon())),
            record(1, "", 1.0, wkb.dumps(bowtie)),
        ]
        with patch.object(m, "PREVIOUS_COMPLETE_ZERO_AREA_COUNT", 1):
            report = m.complete_original_geometry_and_code_qc(
                FakeParquet(data), MAPPING, HCAT, expected_rows=5
            )
        stats = report["full_original_geometry_and_code_quality"]
        self.assertEqual(stats["source_rows"], 5)
        self.assertEqual(stats["source_area_ha_zero_rows"], 1)
        self.assertEqual(stats["geometry_empty_rows"], 1)
        self.assertEqual(stats["geometry_invalid_topology_rows"], 1)
        self.assertEqual(stats["geometry_valid_positive_polygon_rows"], 3)
        self.assertEqual(stats["source_cropfield_duplicate_subsequent_rows"], 1)
        self.assertEqual(stats["source_code_mapping_resolved_to_hcat4_rows"], 2)
        self.assertEqual(stats["source_code_mapping_to_absent_hcat4_rows"], 1)
        self.assertEqual(stats["source_crop_code_absent_from_regional_mapping_rows"], 1)
        self.assertEqual(stats["source_crop_code_blank_or_nonstring_rows"], 1)
        self.assertEqual(report["raw_source_area_ha_sum_not_unique_land_area"], 4.0)
        self.assertEqual(report["raw_valid_polygon_area_ha_sum_not_union_area"], 3.0)
        self.assertFalse(report["agricultural_parcel_overlaps_or_complete_coverage_verified"])
        self.assertFalse(report["original_raw_rows_or_geometries_output"])

    def test_geometric_area_disagreement_and_missing_wkb(self):
        data = [
            record(1, "001", 1.0, wkb.dumps(box(0, 0, 200, 100))),
            record(2, "001", 1.0, b"not-wkb"),
            record(3, "001", 0.0, wkb.dumps(Polygon())),
        ]
        with patch.object(m, "PREVIOUS_COMPLETE_ZERO_AREA_COUNT", 1):
            report = m.complete_original_geometry_and_code_qc(
                FakeParquet(data), MAPPING, HCAT, expected_rows=3
            )
        s = report["full_original_geometry_and_code_quality"]
        self.assertEqual(s["valid_positive_polygon_area_delta_gt_1pct_rows"], 1)
        self.assertEqual(s["valid_positive_polygon_area_delta_gt_5pct_rows"], 1)
        self.assertEqual(s["valid_positive_polygon_area_delta_gt_50pct_rows"], 1)
        self.assertEqual(s["wkb_missing_or_unreadable_rows"], 1)

    def test_unknown_codes_do_not_auto_map_to_sentinel(self):
        data = [record(1, "", 0.0, wkb.dumps(Polygon()))]
        with patch.object(m, "PREVIOUS_COMPLETE_ZERO_AREA_COUNT", 1):
            report = m.complete_original_geometry_and_code_qc(
                FakeParquet(data), MAPPING, HCAT, expected_rows=1
            )
        s = report["full_original_geometry_and_code_quality"]
        self.assertEqual(s["source_code_mapping_resolved_to_hcat4_rows"], 0)
        self.assertEqual(s["source_crop_code_blank_or_nonstring_rows"], 1)

    def test_pin_and_wrong_geometry_column_fail_closed(self):
        data = [record(1, "001", 1.0, wkb.dumps(box(0, 0, 100, 100)))]
        with self.assertRaisesRegex(m.Blocked, "footer row count"):
            m.complete_original_geometry_and_code_qc(
                FakeParquet(data, footer_rows=2), MAPPING, HCAT,
                expected_rows=1,
            )
        with self.assertRaisesRegex(m.Blocked, "unexpected original JRC"):
            m.complete_original_geometry_and_code_qc(
                FakeParquet(data, geometry_column="geom"), MAPPING, HCAT,
                expected_rows=1,
            )

    def test_negative_values_or_duplicated_mapping_block(self):
        data = [record(1, "001", -1.0, wkb.dumps(box(0, 0, 100, 100)))]
        with self.assertRaisesRegex(m.Blocked, "source area changed"):
            m.complete_original_geometry_and_code_qc(
                FakeParquet(data), MAPPING, HCAT, expected_rows=1
            )
        with self.assertRaisesRegex(m.Blocked, "duplicated regional crop"):
            m.complete_original_geometry_and_code_qc(
                FakeParquet(data),
                MAPPING + [{"nuts": "de4", "original_code": "001",
                            "hcat4_code": "100"}],
                HCAT, expected_rows=1,
            )
