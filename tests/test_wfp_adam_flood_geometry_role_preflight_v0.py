# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests for WFP ADAM flood event geometry roles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.wfp_adam_flood_geometry_role_preflight_v0 import (
    ADAMGeometryError, inspect_adam_flood_event_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def fake(kind="Point"):
    ring = [[12, 50], [13, 50], [13, 51], [12, 51], [12, 50]]
    coords = (
        [12.5, 50.5] if kind == "Point" else
        [ring] if kind == "Polygon" else
        [[ring]]
    )
    return {
        "type": "FeatureCollection", "id": "adam.adam_fl_events",
        "numberMatched": 1277, "numberReturned": 1,
        "links": [{"rel": "self"}, {"rel": "next"}],
        "features": [{
            "type": "Feature", "id": "synthetic-do-not-export",
            "geometry": {"type": kind, "coordinates": coords},
            "properties": {"name": "SYNTHETIC", "fl_popn": 200, "flood_area": 123},
        }],
    }


def encoded(obj):
    return (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")


def inspect(obj):
    data = encoded(obj)
    return inspect_adam_flood_event_bytes(data, hashlib.sha256(data).hexdigest())


class WFPADAMGeometryTests(unittest.TestCase):
    def test_flood_event_point_is_not_inundation_area(self):
        receipt = inspect(fake())
        self.assertEqual(receipt["observed_example_geometry_type"], "Point")
        self.assertEqual(receipt["geometry_semantic_role"], "EVENT_LOCATION_POINT_NOT_INUNDATION")
        self.assertTrue(receipt["one_feature_response_checked"])
        self.assertFalse(receipt["observed_inundation_footprint_confirmed"])
        self.assertFalse(receipt["building_intersection_permitted"])
        self.assertFalse(receipt["model_input_admitted"])
        self.assertNotIn("synthetic-do-not-export", json.dumps(receipt))
        self.assertNotIn("fl_popn", json.dumps(receipt))
        self.assertNotIn("coordinates", json.dumps(receipt))

    def test_even_structurally_valid_polygon_is_not_an_observed_footprint(self):
        for kind in ("Polygon", "MultiPolygon"):
            with self.subTest(kind=kind):
                report = inspect(fake(kind))
                self.assertEqual(report["observed_example_geometry_type"], kind)
                self.assertEqual(report["geometry_semantic_role"],
                                 "UNVERIFIED_SOURCE_POLYGON_NOT_OBSERVED_INUNDATION")
                self.assertFalse(report["geometry_topology_certified"])
                self.assertFalse(report["building_intersection_permitted"])

    def test_wrong_collection_counts_pagination_and_multi_feature_fail(self):
        cases = []
        x = fake()
        x["id"] = "adam.adam_ts_events"
        cases.append(x)
        x = fake()
        x["features"].append(x["features"][0].copy())
        cases.append(x)
        x = fake()
        x["numberReturned"] = 2
        cases.append(x)
        x = fake()
        x["numberMatched"] = 0
        cases.append(x)
        x = fake()
        x["links"] = [{"rel": "self"}]
        cases.append(x)
        x = fake()
        x["crs"] = "EPSG:3857"
        cases.append(x)
        for obj in cases:
            with self.subTest(item=len(cases)):
                with self.assertRaises(ADAMGeometryError):
                    inspect(obj)

    def test_coordinates_polygon_rings_and_unknown_types_fail(self):
        cases = []
        x = fake()
        x["features"][0]["geometry"]["coordinates"] = [50.0, 190.0]
        cases.append(x)
        x = fake()
        x["features"][0]["geometry"]["coordinates"] = [True, 49.0]
        cases.append(x)
        x = fake()
        x["features"][0]["geometry"] = {"type": "LineString", "coordinates": [[12, 50], [13, 51]]}
        cases.append(x)
        x = fake("Polygon")
        x["features"][0]["geometry"]["coordinates"][0][-1] = [14, 52]
        cases.append(x)
        x = fake("Polygon")
        x["features"][0]["geometry"]["coordinates"][0] = [[12, 50], [13, 50], [14, 50], [12, 50]]
        cases.append(x)
        x = fake()
        x["features"][0]["geometry"] = None
        cases.append(x)
        for obj in cases:
            with self.assertRaises(ADAMGeometryError):
                inspect(obj)

    def test_original_source_hash_duplicate_keys_and_byte_cap(self):
        source = encoded(fake())
        with self.assertRaisesRegex(ADAMGeometryError, "SHA256 mismatch"):
            inspect_adam_flood_event_bytes(source, "0" * 64)
        corrupt = b'{"type":"FeatureCollection","type":"FeatureCollection"}'
        with self.assertRaisesRegex(ADAMGeometryError, "duplicate"):
            inspect_adam_flood_event_bytes(corrupt, hashlib.sha256(corrupt).hexdigest())
        for source in (b"", b"\xff", b"X" * 524289):
            with self.assertRaises(ADAMGeometryError):
                inspect_adam_flood_event_bytes(source, hashlib.sha256(source).hexdigest())

    def test_cli_only_metadata_and_source_never_overwritten(self):
        data = encoded(fake())
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "provider.geojson"
            output = Path(folder) / "receipt.json"
            source.write_bytes(data)
            command = [sys.executable,
                str(ROOT / "research_runners/wfp_adam_flood_geometry_role_preflight_v0.py"),
                str(source), "--expected-sha256", hashlib.sha256(data).hexdigest(),
                "--out", str(output)]
            good = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertFalse(json.loads(output.read_text(encoding="utf-8"))["building_intersection_permitted"])
            self.assertNotIn("synthetic-do-not-export", output.read_text(encoding="utf-8"))
            blocked = subprocess.run(command[:-1] + [str(source)], capture_output=True, text=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(source.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
