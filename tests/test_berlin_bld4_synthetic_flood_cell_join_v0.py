# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only depth-cell and building footprint checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

try:
    from shapely.geometry import box
except ImportError:
    box = None

from research_runners.berlin_bld4_synthetic_flood_cell_join_v0 import (
    GridJoinError, read_synthetic_grid, run,
    GRID_PROFILE, BUILDING_APP_ID, CAT4_SCHEMA,
)


def grid(**kwargs):
    data = {"profile": GRID_PROFILE, "source_class": "synthetic_test_only",
            "crs": "EPSG:25833", "peril": "flood_water_depth", "unit": "m",
            "top_left_x_m": 391780, "top_left_y_m": 5820080,
            "cell_size_m": 10, "width": 2, "height": 2,
            "cells": [[1.0, 0.0], [None, None]]}
    data.update(kwargs)
    return data


def create_sqlite(path, polys, *, app_id=BUILDING_APP_ID, model_admitted=0,
                  vintage="current_mutable_unknown_feature_date"):
    with sqlite3.connect(path) as db:
        db.execute(f"PRAGMA application_id={app_id}")
        db.execute("PRAGMA user_version=1")
        db.execute("CREATE TABLE provenance (schema_id TEXT, source_response_sha256 TEXT, "
                   "source_rights TEXT, building_vintage TEXT, boundary_vintage INTEGER, "
                   "model_admitted INTEGER)")
        db.execute("INSERT INTO provenance VALUES (?,?,?,?,?,?)", (
            CAT4_SCHEMA, hashlib.sha256(b"synthetic source only").hexdigest(),
            "dl-de-zero-2.0", vintage, 2021, model_admitted))
        db.execute("CREATE TABLE building_sample (ordinal INTEGER, "
                   "projected_epsg25833_geometry_wkb BLOB, footprint_area_m2 REAL, "
                   "nuts1_region TEXT)")
        for idx, poly in enumerate(polys, 1):
            db.execute("INSERT INTO building_sample VALUES (?, ?, ?, 'DE3')",
                       (idx, poly.wkb, float(poly.area)))


@unittest.skipUnless(box is not None, "Reviewed optional Shapely required")
class SyntheticFloodSupportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="oc-blc-synthetic-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.bld = self.root / "buildings.cat.sqlite"
        self.gri = self.root / "grid.json"
        self.polys = [box(391780, 5820070, 391790, 5820080),
                      box(391790, 5820070, 391800, 5820080)]
        create_sqlite(self.bld, self.polys)
        self.gri.write_text(json.dumps(grid()), encoding="utf-8")

    def write_grid(self, **kw):
        self.gri.write_text(json.dumps(grid(**kw)), encoding="utf-8")

    def test_exact_area_and_no_loss_or_building_details(self):
        report = run(self.bld, self.gri)
        self.assertEqual(report["building_polygons_checked"], 2)
        self.assertEqual(report["grid_cells_checked"], 4)
        self.assertEqual(report["building_area_m2"], 200)
        self.assertEqual(report["wet_supported_area_m2"], 100)
        self.assertEqual(report["dry_supported_area_m2"], 100)
        self.assertEqual(report["nodata_area_m2"], 0)
        self.assertEqual(report["outside_grid_area_m2"], 0)
        self.assertEqual(report["building_count_with_complete_valid_hazard_support"], 2)
        self.assertEqual(report["building_count_with_any_positive_synthetic_depth"], 1)
        self.assertEqual(report["building_count_without_any_valid_hazard_support"], 0)
        self.assertTrue(report["grid_is_synthetic_not_real_hazard"])
        self.assertFalse(report["real_building_hazard_link_admitted"])
        self.assertFalse(report["vulnerability_or_insured_losses_calculated"])
        self.assertFalse(report["individual_building_footprints_or_ids_exported"])
        self.assertNotIn("391780", json.dumps(report))
        self.assertNotIn("WKB", json.dumps(report))

    def test_no_data_is_not_zero_depth_and_partial_support_is_accounted(self):
        self.bld.unlink()
        create_sqlite(self.bld, [box(391785, 5820065, 391795, 5820075)])
        out = run(self.bld, self.gri)
        self.assertEqual(out["building_area_m2"], 100)
        self.assertEqual(out["wet_supported_area_m2"], 25)
        self.assertEqual(out["dry_supported_area_m2"], 25)
        self.assertEqual(out["nodata_area_m2"], 50)
        self.assertEqual(out["outside_grid_area_m2"], 0)
        self.assertEqual(out["building_count_with_complete_valid_hazard_support"], 0)
        self.assertEqual(out["building_count_with_any_positive_synthetic_depth"], 1)

    def test_building_partially_outside_grid_remains_missing(self):
        self.bld.unlink()
        create_sqlite(self.bld, [box(391775, 5820070, 391785, 5820080)])
        out = run(self.bld, self.gri)
        self.assertEqual(out["wet_supported_area_m2"], 50)
        self.assertEqual(out["outside_grid_area_m2"], 50)
        self.assertEqual(out["nodata_area_m2"], 0)
        self.assertEqual(out["building_count_with_complete_valid_hazard_support"], 0)

    def test_all_nodata_cannot_be_inferred_dry(self):
        self.write_grid(cells=[[None, None], [None, None]])
        out = run(self.bld, self.gri)
        self.assertEqual(out["nodata_area_m2"], 200)
        self.assertEqual(out["wet_supported_area_m2"], 0)
        self.assertEqual(out["dry_supported_area_m2"], 0)
        self.assertEqual(out["building_count_without_any_valid_hazard_support"], 2)

    def test_foreign_crs_metre_mismatch_and_fake_real_hazard_refused(self):
        cases = [
            ("crs", "EPSG:4326"), ("unit", "cm"),
            ("source_class", "verified_provider_hazard"),
            ("peril", "river_drought"), ("profile", "unknown")
        ]
        for name, bad in cases:
            with self.subTest(field=name):
                self.write_grid(**{name: bad})
                with self.assertRaisesRegex(GridJoinError, "real, unverified"):
                    run(self.bld, self.gri)

    def test_invalid_cell_geometry_numbers_and_missing_fields(self):
        cases = [
            {"width": 3}, {"cells": [[-1, 0], [0, 1]]},
            {"cells": [[True, 0], [0, 1]]},
            {"cells": [[float('nan'), 0], [0, 1]]},
            {"height": 99}, {"cell_size_m": 0},
        ]
        for case in cases:
            with self.subTest(case=str(case)):
                self.write_grid(**case)
                with self.assertRaises(GridJoinError):
                    run(self.bld, self.gri)
        self.gri.write_bytes(b'{"width":1,"width":2}')
        with self.assertRaises(GridJoinError):
            read_synthetic_grid(self.gri)

    def test_reject_fake_source_db_or_accepted_model(self):
        self.bld.unlink()
        create_sqlite(self.bld, self.polys, app_id=0x43415434)
        with self.assertRaisesRegex(GridJoinError, "not independently staged"):
            run(self.bld, self.gri)
        self.bld.unlink()
        create_sqlite(self.bld, self.polys, model_admitted=1)
        with self.assertRaisesRegex(GridJoinError, "provenance or non-admission"):
            run(self.bld, self.gri)
        self.bld.unlink()
        create_sqlite(self.bld, self.polys, vintage="claimed_historic_2021")
        with self.assertRaisesRegex(GridJoinError, "provenance or non-admission"):
            run(self.bld, self.gri)

    def test_overlapping_building_parts_block_double_counting(self):
        self.bld.unlink()
        create_sqlite(self.bld, [box(391780, 5820070, 391790, 5820080),
                                 box(391785, 5820070, 391795, 5820080)])
        with self.assertRaisesRegex(GridJoinError, "double-count"):
            run(self.bld, self.gri)

    def test_unrelated_or_malformed_building_geometry_refused(self):
        self.bld.unlink()
        create_sqlite(self.bld, [box(400000, 5820000, 400010, 5820010)])
        with self.assertRaisesRegex(GridJoinError, "metric geometry"):
            run(self.bld, self.gri)

    def test_no_write_and_nonidentifying_output(self):
        before = self.bld.read_bytes()
        run(self.bld, self.gri)
        self.assertEqual(self.bld.read_bytes(), before)
        self.assertEqual(set(self.root.iterdir()), {self.bld, self.gri})


if __name__ == "__main__":
    unittest.main()
