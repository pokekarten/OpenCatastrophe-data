# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only building-footprint overlap regressions."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.building_footprint_overlap_v0 import compare, FootprintError

HAS_SPATIAL_DEPS = (
    importlib.util.find_spec("shapely") is not None
    and importlib.util.find_spec("pyproj") is not None
)
ROOT = Path(__file__).resolve().parents[1]


def rect(x1, y1, x2, y2):
    return {"type": "Polygon", "coordinates": [[[x1, y1], [x2, y1],
             [x2, y2], [x1, y2], [x1, y1]]]}


def write(path: Path, polys):
    path.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"building_id": key}, "geometry": geo}
        for key, geo in polys
    ]}), encoding="utf-8")


@unittest.skipUnless(HAS_SPATIAL_DEPS, "Requires reviewed optional shapely/pyproj dependencies")
class BuildingOverlapTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.a = Path(d.name) / "a.geojson"
        self.b = Path(d.name) / "b.geojson"

    def compare(self, **kwargs):
        return compare(self.a, self.b, left_source="synthetic", right_source="synthetic2",
                       left_crs="EPSG:3035", right_crs="EPSG:3035", **kwargs)

    def test_one_to_one_match_and_no_identity_proof(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        result = self.compare()
        self.assertEqual(result["counts"]["high_iou_unique_matches"], 1)
        self.assertEqual(result["matched_iou_mean"], 1)
        self.assertFalse(result["scientific_identity_proven"])
        self.assertFalse(result["model_input_admitted"])
        self.assertEqual(len(result["left_sha256"]), 64)

    def test_low_iou_not_passing(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B", rect(4e6 + 10, 3e6, 4e6 + 30, 3e6 + 20))])
        r = self.compare()
        self.assertEqual(r["counts"]["single_candidate_below_iou"], 1)
        self.assertEqual(r["counts"]["high_iou_unique_matches"], 0)

    def test_split_one_to_many_not_matched(self):
        write(self.a, [("A1", rect(4e6, 3e6, 4e6 + 10, 3e6 + 20)),
                       ("A2", rect(4e6 + 10, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        r = self.compare()
        self.assertEqual(r["counts"]["ambiguous_split_or_merge_left"], 2)
        self.assertEqual(r["counts"]["high_iou_unique_matches"], 0)

    def test_merge_many_to_one_not_matched(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B1", rect(4e6, 3e6, 4e6 + 10, 3e6 + 20)),
                       ("B2", rect(4e6 + 10, 3e6, 4e6 + 20, 3e6 + 20))])
        self.assertEqual(self.compare()["counts"]["ambiguous_split_or_merge_left"], 1)

    def test_nonoverlap_and_metric_counts(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B", rect(4e6 + 100, 3e6, 4e6 + 120, 3e6 + 20))])
        r = self.compare()
        self.assertEqual(r["counts"]["left_no_substantial_overlap"], 1)
        self.assertEqual(r["counts"]["right_without_any_geometric_intersection"], 1)
        self.assertIsNone(r["matched_iou_median"])

    def test_4326_to_3035_explicit_reprojection(self):
        write(self.a, [("A", rect(11.5, 48, 11.5001, 48.0001))])
        write(self.b, [("B", rect(11.5, 48, 11.5001, 48.0001))])
        r = compare(self.a, self.b, left_crs="EPSG:4326", right_crs="EPSG:4326",
                    left_source="synthetic", right_source="other")
        self.assertEqual(r["counts"]["high_iou_unique_matches"], 1)

    def test_invalid_geometry_duplicate_id_and_nonpolygon_block(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20)),
                       ("A", rect(4e6 + 40, 3e6, 4e6 + 60, 3e6 + 20))])
        write(self.b, [("B", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        with self.assertRaisesRegex(FootprintError, "Duplicate"):
            self.compare()
        write(self.a, [("A", {"type": "Point", "coordinates": [4e6, 3e6]})])
        with self.assertRaisesRegex(FootprintError, "Polygon"):
            self.compare()
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        with self.assertRaisesRegex(FootprintError, "CRS"):
            compare(self.a, self.b, left_crs="unsupported-crs",
                    right_crs="EPSG:3035", left_source="a", right_source="b")

    def test_raw_identity_never_leaks(self):
        write(self.a, [("PRIVATE-LOCAL-ID-SECRET", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("OTHER-PRIVATE-LOCAL-ID", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        output = json.dumps(self.compare())
        self.assertNotIn("PRIVATE-LOCAL-ID-SECRET", output)
        self.assertNotIn("OTHER-PRIVATE-LOCAL-ID", output)

    def test_adjacent_touch_is_not_an_overlap(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B", rect(4e6 + 20, 3e6, 4e6 + 40, 3e6 + 20))])
        r = self.compare()
        self.assertEqual(r["counts"]["high_iou_unique_matches"], 0)
        self.assertEqual(r["counts"]["right_without_any_geometric_intersection"], 1)

    def test_cli_is_deterministic_and_has_no_raw_matches(self):
        write(self.a, [("A", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        write(self.b, [("B", rect(4e6, 3e6, 4e6 + 20, 3e6 + 20))])
        args = [sys.executable, "scripts/building_footprint_overlap_v0.py",
                "--left", str(self.a), "--right", str(self.b),
                "--left-crs", "EPSG:3035", "--right-crs", "EPSG:3035",
                "--left-source", "synthetic.a", "--right-source", "synthetic.b"]
        one = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                             check=True, timeout=30)
        two = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                             check=True, timeout=30)
        self.assertEqual(one.stdout, two.stdout)
        self.assertEqual(json.loads(one.stdout)["counts"]["high_iou_unique_matches"], 1)


if __name__ == "__main__":
    unittest.main()
