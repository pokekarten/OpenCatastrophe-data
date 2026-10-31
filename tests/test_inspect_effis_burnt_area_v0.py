# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
import unittest
from scripts.inspect_effis_burnt_area_v0 import EFFISSourceError, inspect_event_json


def event():
    return {
        "count": 1, "next": None, "results": [{
            "id": 646790, "country": "NL",
            "firedate": "2026-08-25T13:01:00+02:00",
            "area_ha": 12,
            "shape": {"type": "MultiPolygon", "coordinates": [
                [[[5.95, 52.41], [5.96, 52.41],
                  [5.96, 52.42], [5.95, 52.41]]]
            ]},
            "centroid": {"type": "Point", "coordinates": [5.955, 52.415]},
            "bbox": [5.95, 52.41, 5.96, 52.42],
        }],
    }


def blob(payload):
    return json.dumps(payload, sort_keys=True).encode("utf-8")


class EFFISWildfireGeometryTests(unittest.TestCase):
    def test_one_polygon_event_metadata_only(self):
        r = inspect_event_json(blob(event()), 646790)
        self.assertEqual((r["event_id"], r["reported_area_ha"], r["vertex_count"]),
                         (646790, "12", 4))
        self.assertFalse(r["result_includes_raw_geometry"])
        self.assertFalse(r["model_admission"])
        self.assertFalse(r["snapshot_immutable"])
        self.assertFalse(r["insured_loss_computed"])

    def test_rejects_mismatched_event(self):
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(blob(event()), 646789)

    def test_rejects_missing_timezone(self):
        data = event()
        data["results"][0]["firedate"] = "2026-08-25T13:01:00"
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(blob(data), 646790)

    def test_rejects_inverted_lonlat(self):
        data = event()
        data["results"][0]["shape"]["coordinates"][0][0][0] = [52.41, 195]
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(blob(data), 646790)

    def test_rejects_open_polygon_ring(self):
        data = event()
        data["results"][0]["shape"]["coordinates"][0][0][-1] = [5.952, 52.41]
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(blob(data), 646790)

    def test_rejects_zero_reported_area(self):
        data = event()
        data["results"][0]["area_ha"] = "0"
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(blob(data), 646790)

    def test_rejects_multiple_results(self):
        data = event()
        data["count"] = 2
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(blob(data), 646790)

    def test_rejects_duplicate_json_keys(self):
        with self.assertRaises(EFFISSourceError):
            inspect_event_json(b'{"count":1,"count":1}', 646790)


if __name__ == "__main__":
    unittest.main()
