# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic geometry QA tests; no original source assets stored."""
from __future__ import annotations

import json
import sqlite3
import struct
import tempfile
from pathlib import Path
import unittest

from shapely.geometry import Polygon, MultiPolygon
from shapely import wkb
from research_runners.luxembourg_geobase_2026_repair_diagnostic_v0 import RepairDiagnostics

from research_runners.luxembourg_geobase_2026_geometry_quality_v0 import (
    _decode_gpkg, profile, audit, GeoBaseError
)


def gpkg(geom, *, epsg=2169, envelope=0):
    flag = 1 | (envelope << 1)
    coords = b""
    if envelope == 1:
        xmin, ymin, xmax, ymax = geom.bounds
        coords = struct.pack("<dddd", xmin, xmax, ymin, ymax)
    return b"GP" + bytes([0, flag]) + struct.pack("<i", epsg) + coords + wkb.dumps(geom)


def synthetic_db():
    db = sqlite3.connect(":memory:")
    db.execute('CREATE TABLE "Buildings_BU_Building" '
               '(id integer primary key, geom blob, BU_BuildingID text, Source text)')
    good = MultiPolygon([Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])])
    bad = Polygon([(0, 0), (2, 2), (0, 2), (2, 0)])
    db.executemany('INSERT INTO "Buildings_BU_Building" VALUES (?,?,?,?)', [
        (1, gpkg(good), "B-01", "official"),
        (2, gpkg(good, envelope=1), "B-02", "official"),
        (3, gpkg(bad), "B-03", "official"),
        (4, None, "B-04", "official"),
    ])
    return db


class LuxembourgGeoBaseFullGeometryTests(unittest.TestCase):
    def test_gpkg_endian_and_envelope_and_projected_area(self):
        geom = Polygon([(1, 2), (4, 2), (4, 6), (1, 6)])
        self.assertEqual(_decode_gpkg(gpkg(geom)).area, 12)
        self.assertEqual(_decode_gpkg(gpkg(geom, envelope=1)).area, 12)

    def test_full_scan_partitions_original_source_and_exports_only_aggregates(self):
        db = synthetic_db()
        self.addCleanup(db.close)
        result = profile(db, expected_rows=4)
        self.assertEqual(result["original_objects"], 4)
        self.assertEqual(result["polygon_valid_positive_area"], 2)
        self.assertEqual(result["invalid_topology"], 1)
        repair = result["invalid_polygon_repair_diagnostic"]
        self.assertEqual(repair["invalid_original_polygons_assessed"], 1)
        self.assertEqual(repair["repair_multiple_polygons"], 1)
        self.assertEqual(repair["repair_single_polygon"], 0)
        self.assertEqual(repair["repair_unusable_or_not_polygonal"], 0)
        self.assertEqual(repair["structure_challenge_usable"], 1)
        self.assertEqual(repair["structure_vs_linework_polygon_count_disagreements"], 0)
        self.assertEqual(repair["structure_vs_linework_area_disagreements_over_tolerance"], 0)
        self.assertEqual(repair["structure_vs_linework_topological_set_disagreements"], 0)
        self.assertEqual(
            repair["structure_vs_linework_symmetric_difference_area_disagreements_over_tolerance"], 0
        )
        self.assertEqual(repair["nonpositive_nominal_invalid_polygon_area"], 1)
        self.assertEqual(repair["source_boundary_to_linework_boundary_comparable"], 1)
        self.assertEqual(repair["source_boundary_to_linework_boundary_nonfinite_or_failed"], 0)
        self.assertEqual(repair["absolute_nominal_vs_repaired_area_change_sum_m2"], 2.0)
        self.assertTrue(repair["all_repaired_polygons_quarantined_for_manual_scientific_review"])
        self.assertEqual(sum(result["invalid_topology_classes_aggregate"].values()), 1)
        self.assertNotIn("[", json.dumps(result["invalid_topology_classes_aggregate"]))
        self.assertEqual(result["malformed_gpkg_geometry"], 1)
        self.assertEqual(result["valid_polygon_area_sum_projected_m2"], 200)
        self.assertTrue(result["source_rows_conserved"])
        self.assertFalse(result["building_geometry_model_input_approved"])
        self.assertFalse(result["all_source_geometries_parseable"])
        self.assertNotIn("B-01", json.dumps(result))
        self.assertNotIn("official", json.dumps(result))

    def test_repair_aggregates_reject_original_valid_polygons_and_never_expose_geometry(self):
        valid = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        invalid = Polygon([(0, 0), (3, 3), (0, 3), (3, 0)])
        diagnostics = RepairDiagnostics()
        with self.assertRaisesRegex(ValueError, "Only nonempty invalid"):
            diagnostics.observe(valid)
        with self.assertRaisesRegex(ValueError, "conserve"):
            diagnostics.summary(1)
        diagnostics.observe(invalid)
        report = diagnostics.summary(1)
        self.assertEqual(report["repair_multiple_polygons"], 1)
        self.assertEqual(report["repair_unusable_or_not_polygonal"], 0)
        self.assertEqual(report["relative_delta_over_1pct_of_nonzero_nominal"], 0)
        self.assertFalse(report["automatically_repaired_source_geometries_persisted"])
        self.assertNotIn("3 3", json.dumps(report))
        self.assertNotIn("POLYGON", json.dumps(report))
        self.assertNotIn("SYNTH-ACC", json.dumps(report))

    def test_invalid_spike_preserves_nominal_area_but_changes_boundary(self):
        # Deliberately invalid polygon: a retraced inward two-metre spike.
        # A nominal polygon area delta of zero MUST NOT hide this contour change.
        spike = Polygon([(0, 0), (4, 0), (4, 4), (2, 4),
                         (2, 2), (2, 4), (0, 4)])
        self.assertFalse(spike.is_valid)
        diagnostic = RepairDiagnostics()
        diagnostic.observe(spike)
        report = diagnostic.summary(1)
        self.assertEqual(report["repair_single_polygon"], 1)
        self.assertEqual(report["absolute_nominal_vs_repaired_area_change_sum_m2"], 0)
        self.assertEqual(report["source_boundary_to_linework_boundary_comparable"], 1)
        self.assertEqual(report["source_boundary_to_linework_hausdorff_over_1m"], 1)
        self.assertGreater(report["source_boundary_to_linework_hausdorff_max_projected_m"], 1)
        self.assertGreater(
            report["source_boundary_to_linework_boundary_length_change_sum_projected_m"], 0
        )
        self.assertFalse(report["source_boundary_position_accuracy_ground_control_verified"])
        # Original coordinate values are not present in report.
        self.assertNotIn("POLYGON", json.dumps(report))

    def test_untrusted_geom_flags_srs_and_size_fail(self):
        geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        for value in (None, b"fake", gpkg(geom, epsg=4326),
                      gpkg(geom)[:9], gpkg(geom, envelope=5),
                      b"GP" + bytes([0, 0xE1]) + gpkg(geom)[4:]):
            with self.subTest(value=value):
                with self.assertRaises(GeoBaseError):
                    _decode_gpkg(value)

    def test_missing_or_changed_population_fails_closed(self):
        db = synthetic_db()
        self.addCleanup(db.close)
        with self.assertRaisesRegex(GeoBaseError, "population changed"):
            profile(db, expected_rows=3)
        db.execute('DROP TABLE "Buildings_BU_Building"')
        with self.assertRaisesRegex(GeoBaseError, "Unexpected source layer"):
            profile(db, expected_rows=4)

    def test_original_archive_must_be_pinned_and_not_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            false = Path(tmp) / "fake.zip"
            false.write_bytes(b"not-publisher-source")
            with self.assertRaises(GeoBaseError):
                audit(false)
            alias = Path(tmp) / "shortcut.zip"
            alias.symlink_to(false)
            with self.assertRaises(GeoBaseError):
                audit(alias)


if __name__ == "__main__":
    unittest.main()
