# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic WKB-only tests for original zero-area targeted audit semantics."""
from __future__ import annotations

import json
from types import SimpleNamespace
import unittest

from shapely import wkb
from shapely.geometry import Polygon, Point, box

from research_runners.eurocrops_original_zero_area_geometry_v0 import (
    Blocked, audit_zero_area_geometry,
)


class FakeBatch:
    def __init__(self, rows):
        self.rows = rows
        self.num_rows = len(rows)

    def to_pylist(self):
        return self.rows


class FakeParquet:
    def __init__(self, rows, *, column="geometry", footer_rows=None):
        self.rows = rows
        self.metadata = SimpleNamespace(
            num_rows=len(rows) if footer_rows is None else footer_rows
        )
        self.schema_arrow = SimpleNamespace(
            names=["cropfield", "original_code", "area_ha", column],
            metadata={b"geo": json.dumps({
                "primary_column": column,
                "columns": {column: {
                    "encoding": "WKB", "crs": {
                        "id": {"authority": "EPSG", "code": 3035},
                    },
                }},
            }).encode("utf-8")}
        )

    def iter_batches(self, *, batch_size, columns):
        assert batch_size == 512
        assert columns == ["area_ha", "geometry"]
        for start in range(0, len(self.rows), 512):
            yield FakeBatch(self.rows[start:start + 512])


def rec(area, geometry):
    return {"area_ha": area, "geometry": geometry}


class OriginalZeroGeometryTests(unittest.TestCase):
    def test_zero_area_source_with_positive_polygon_is_reported_not_corrected(self):
        rows = [
            rec(0.0, wkb.dumps(box(0, 0, 100, 100))),
            rec(1.0, wkb.dumps(box(0, 0, 100, 100))),
            rec(0.0, wkb.dumps(box(0, 0, .1, .1))),
        ]
        report = audit_zero_area_geometry(
            FakeParquet(rows), expected_rows=3, expected_zero=2,
        )
        self.assertEqual(report["original_reported_zero_area_ha_rows"], 2)
        self.assertEqual(report["zero_ha_polygon_computed_area_positive_m2"], 2)
        self.assertEqual(report["zero_ha_polygon_positive_area_1e_minus_6_to_lt_1_m2"], 1)
        self.assertEqual(report["zero_ha_polygon_positive_area_gte_100_m2"], 1)
        self.assertAlmostEqual(report["min_computed_positive_polygon_area_m2"], .01)
        self.assertEqual(report["max_computed_positive_polygon_area_m2"], 10000.0)
        self.assertFalse(report["zero_area_source_rows_or_coordinates_output"])

    def test_nonpolygon_invalid_and_wkb_decode_failure_all_counted(self):
        bowtie = Polygon([(0, 0), (2, 2), (0, 2), (2, 0)])
        rows = [
            rec(0, wkb.dumps(Point(0, 0))),
            rec(0, wkb.dumps(bowtie)),
            rec(0, b"not-wkb"),
            rec(0, None),
            rec(0, wkb.dumps(Polygon())),
        ]
        out = audit_zero_area_geometry(
            FakeParquet(rows), expected_rows=5, expected_zero=5,
        )
        self.assertEqual(out["zero_ha_geometry_nonpolygon"], 1)
        self.assertEqual(out["zero_ha_geometry_invalid_topology"], 1)
        self.assertEqual(out["zero_ha_geometry_empty"], 1)
        self.assertEqual(out["zero_ha_wkb_invalid_or_missing"], 2)
        self.assertEqual(out["zero_ha_polygon_computed_area_positive_m2"], 0)

    def test_zero_area_count_drift_blocks(self):
        rows = [rec(0, wkb.dumps(box(0, 0, 1, 1)))]
        with self.assertRaisesRegex(Blocked, "more zero-area"):
            audit_zero_area_geometry(
                FakeParquet(rows), expected_rows=1, expected_zero=0
            )
        with self.assertRaisesRegex(Blocked, "zero-area count"):
            audit_zero_area_geometry(
                FakeParquet(rows + [rec(1, wkb.dumps(box(0, 0, 1, 1)))]),
                expected_rows=2, expected_zero=2
            )

    def test_source_crs_or_column_mismatch_blocks(self):
        rows = [rec(0, wkb.dumps(box(0, 0, 1, 1)))]
        with self.assertRaisesRegex(Blocked, "original JRC geometry"):
            audit_zero_area_geometry(
                FakeParquet(rows, column="geom"),
                expected_rows=1, expected_zero=1,
            )

    def test_corrupt_original_values_and_footer_totals_block(self):
        for bad in (-1, float("nan"), None, "1.0", float("inf")):
            with self.assertRaisesRegex(Blocked, "outside prior"):
                audit_zero_area_geometry(
                    FakeParquet([rec(bad, wkb.dumps(box(0, 0, 1, 1)))]),
                    expected_rows=1, expected_zero=0,
                )
        with self.assertRaisesRegex(Blocked, "row universe"):
            audit_zero_area_geometry(
                FakeParquet([rec(0, wkb.dumps(box(0, 0, 1, 1)))],
                            footer_rows=2),
                expected_rows=1, expected_zero=1,
            )
