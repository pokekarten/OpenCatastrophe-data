# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only building polygon matching diagnostics; no provider data."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPATIAL_DEPS_AVAILABLE = importlib.util.find_spec("shapely") is not None
if SPATIAL_DEPS_AVAILABLE:
    from shapely.geometry import box
    from scripts.building_polygon_crosswalk_v0 import FootprintAuditError, audit

ROOT = Path(__file__).resolve().parents[1]


def save(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("building_id", "geometry_wkt", "upstream_family"))
        for ident, shape, family in rows:
            writer.writerow((ident, shape if isinstance(shape, str) else shape.wkt, family))


@unittest.skipUnless(SPATIAL_DEPS_AVAILABLE, "requires requirements-eu-flood-spatial.txt")
class FootprintCrosswalkTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.left = Path(temp.name) / "left.csv"
        self.right = Path(temp.name) / "right.csv"
        self.left_rows = [("L1", box(0, 0, 10, 10), "official_cadastre")]
        self.right_rows = [("R1", box(0, 0, 10, 10), "independent_lidar")]

    def report(self, **kwargs):
        save(self.left, self.left_rows)
        save(self.right, self.right_rows)
        params = dict(left_source_id="synthetic.eubucco", right_source_id="synthetic.official",
                      left_vintage="2024-01-01", right_vintage="2024-01-01",
                      left_crs="EPSG:3035", right_crs="EPSG:3035")
        params.update(kwargs)
        return audit(self.left, self.right, **params)

    def test_perfect_overlap_unique_candidate_never_admitted(self):
        result = self.report()
        counts = result["counts"]
        self.assertEqual(counts["unique_high_iou_hypotheses_not_confirmed_matches"], 1)
        self.assertEqual(counts["positive_area_overlaps"], 1)
        self.assertEqual(counts["left_with_multiple_high_iou"], 0)
        self.assertEqual(result["unique_candidate_median_iou"], 1.0)
        self.assertFalse(result["source_rights_reviewed"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["individual_matches_exported"])
        self.assertNotIn("L1", json.dumps(result))

    def test_subthreshold_overlap_and_boundary_contact_are_not_matches(self):
        self.right_rows = [("R1", box(9, 0, 19, 10), "independent_lidar"),
                           ("R2", box(10, 0, 20, 10), "independent_lidar")]
        result = self.report()
        self.assertEqual(result["counts"]["positive_area_overlaps"], 1)
        self.assertEqual(result["counts"]["high_iou_hypothesis_edges"], 0)
        self.assertEqual(result["counts"]["left_with_no_high_iou"], 1)

    def test_ambiguous_two_sources_to_one_building_do_not_greedily_match(self):
        self.right_rows = [("R1", box(0, 0, 10, 10), "base"),
                           ("R2", box(0, 0, 10, 10), "base")]
        counts = self.report()["counts"]
        self.assertEqual(counts["high_iou_hypothesis_edges"], 2)
        self.assertEqual(counts["left_with_multiple_high_iou"], 1)
        self.assertEqual(counts["unique_high_iou_hypotheses_not_confirmed_matches"], 0)

    def test_two_left_to_one_right_no_spurious_unique(self):
        self.left_rows = [("L1", box(0, 0, 10, 10), "left"),
                          ("L2", box(0, 0, 10, 10), "left")]
        counts = self.report()["counts"]
        self.assertEqual(counts["right_with_multiple_high_iou"], 1)
        self.assertEqual(counts["unique_high_iou_hypotheses_not_confirmed_matches"], 0)

    def test_shared_upstream_not_independent_validation(self):
        self.right_rows = [("R1", box(0, 0, 10, 10), "official_cadastre")]
        result = self.report()
        self.assertEqual(result["counts"]["hypotheses_from_same_upstream_family"], 1)
        self.assertFalse(result["upstream_independence_established"])

    def test_different_vintage_does_not_silently_reconcile(self):
        result = self.report(right_vintage="2025-12-31")
        self.assertFalse(result["source_vintages_equal"])
        self.assertEqual(result["counts"]["unique_high_iou_hypotheses_not_confirmed_matches"], 1)
        self.assertIn("require human review", result["warning"])

    def test_reject_bad_crs_date_threshold(self):
        for change in ({"right_crs": "EPSG:4326"}, {"left_vintage": "2024-02-30"},
                       {"left_vintage": "2024"}, {"iou_threshold": float("nan")},
                       {"iou_threshold": 0}, {"iou_threshold": True}):
            with self.subTest(change=change), self.assertRaises(FootprintAuditError):
                self.report(**change)

    def test_invalid_bowtie_polygon_rejected(self):
        self.left_rows = [("L1", "POLYGON ((0 0, 10 10, 10 0, 0 10, 0 0))", "official")]
        with self.assertRaisesRegex(FootprintAuditError, "invalid building polygon"):
            self.report()

    def test_duplicate_identifiers_rejected(self):
        self.left_rows = [("L1", box(0, 0, 10, 10), "official"),
                          ("L1", box(20, 20, 30, 30), "official")]
        with self.assertRaisesRegex(FootprintAuditError, "duplicate building ID"):
            self.report()

    def test_deterministic_and_no_raw_geometry_output(self):
        result = self.report()
        self.assertEqual(result, self.report())
        self.assertNotIn("POLYGON", json.dumps(result))

    def test_cli_offline_and_aggregate_only(self):
        save(self.left, self.left_rows)
        save(self.right, self.right_rows)
        cmd = [sys.executable, str(ROOT / "scripts/building_polygon_crosswalk_v0.py"),
               "--left", str(self.left), "--right", str(self.right),
               "--left-source-id", "synthetic.eubucco", "--right-source-id", "synthetic.official",
               "--left-vintage", "2024-01-01", "--right-vintage", "2024-01-01",
               "--left-crs", "EPSG:3035", "--right-crs", "EPSG:3035"]
        run = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["counts"]["unique_high_iou_hypotheses_not_confirmed_matches"], 1)
        self.assertNotIn("L1", run.stdout)


if __name__ == "__main__":
    unittest.main()
