# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ACT/EUBUCCO original-file bounded-window overlay regressions."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HAS_RUNTIME = all(importlib.util.find_spec(x) for x in ("pyarrow", "shapely", "pyproj"))
if HAS_RUNTIME:
    import pyarrow as pa
    import pyarrow.parquet as pq
    from pyproj import Transformer
    from shapely.geometry import Polygon
    from shapely.ops import transform
    from shapely import wkb
    from research_runners.luxembourg_act_eubucco_bounded_overlap_v0 import (
        OverlapPilotError, run_pilot,
    )
    from tests.test_luxembourg_gpkg_schema_window_v0 import write_source


@unittest.skipUnless(HAS_RUNTIME, "Requires pinned PyArrow, PyProj and Shapely")
class LuxembourgOriginalOverlapResearchTests(unittest.TestCase):
    def setUp(self):
        obj = tempfile.TemporaryDirectory()
        self.addCleanup(obj.cleanup)
        self.gpkg = Path(obj.name) / "research.gpkg"
        self.parquet = Path(obj.name) / "LU00.parquet"
        write_source(self.gpkg, count=3)

        convert = Transformer.from_crs("EPSG:2169", "EPSG:3035", always_xy=True)
        shape = Polygon([(75000, 75000), (75020, 75000),
                         (75020, 75020), (75000, 75020)])
        projected = transform(convert.transform, shape)
        table = pa.table({
            "id": pa.array(["SYN-LU-1"], type=pa.string()),
            "region_id": pa.array(["LU000"], type=pa.string()),
            "geometry": pa.array([wkb.dumps(projected)], type=pa.binary()),
            "geometry_source": pa.array(["gov-luxembourg"], type=pa.string()),
        })
        pq.write_table(table, self.parquet)
        back = Transformer.from_crs("EPSG:2169", "EPSG:4326", always_xy=True)
        self.lon, self.lat = back.transform(75010, 75010)
        self.gpkg_hash = hashlib.sha256(self.gpkg.read_bytes()).hexdigest()
        self.parquet_hash = hashlib.sha256(self.parquet.read_bytes()).hexdigest()

    def compare(self, **kwargs):
        return run_pilot(
            self.gpkg, self.parquet,
            longitude=self.lon, latitude=self.lat,
            half_width_m=30, max_features=5,
            act_sha256=self.gpkg_hash, eubucco_sha256=self.parquet_hash,
            act_layer="buildings", act_id_field="building_ref",
            **kwargs,
        )

    def test_one_realistic_synthetic_overlap_and_provenance_boundaries(self):
        report = self.compare()
        self.assertEqual(report["original_local_sample"]["act_roof_features"], 1)
        self.assertEqual(report["original_local_sample"]["eubucco_footprint_features"], 1)
        self.assertEqual(report["overlap_candidate_diagnostics"]["matched_unique_at_iou_0_60"], 1)
        self.assertFalse(report["eubucco_upstream_independence_proven"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["act_coordinate_axis_order_ground_control_verified"])
        self.assertNotIn("SYN-LU-1", json.dumps(report))
        self.assertNotIn("B-1", json.dumps(report))

    def test_invalid_original_source_pin_fails_closed(self):
        with self.assertRaisesRegex(OverlapPilotError, "Original source"):
            self.compare(act_sha256="bad")  # duplicated keyword supplied below intentionally forbidden

    def test_geographic_window_limits_fail_closed(self):
        with self.assertRaisesRegex(OverlapPilotError, "outside Luxembourg"):
            run_pilot(self.gpkg, self.parquet, longitude=25, latitude=49.6)
        with self.assertRaisesRegex(OverlapPilotError, "Unbounded"):
            run_pilot(self.gpkg, self.parquet, longitude=self.lon, latitude=self.lat,
                      half_width_m=2000)

    def test_empty_window_does_not_produce_fictitious_match(self):
        with self.assertRaises(OverlapPilotError):
            run_pilot(
                self.gpkg, self.parquet,
                longitude=self.lon+0.3, latitude=self.lat,
                half_width_m=30, max_features=5,
                act_sha256=self.gpkg_hash, eubucco_sha256=self.parquet_hash,
                act_layer="buildings", act_id_field="building_ref",
            )


if __name__ == "__main__":
    unittest.main()
