# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests for the NRW five-building CityJSON QA."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.assess_nrw_lod2_cityjson_sample_v0 import (
    BBOX, CRS, MAX_BYTES, SAMPLE_URL, SampleError, acquire, assess, main,
)


def sample() -> dict:
    return {
        "type": "CityJSON", "version": "1.1",
        "metadata": {
            "referenceSystem": CRS,
            "geographicalExtent": [6.95, 50.93, 5, 6.9502, 50.9302, 8],
        },
        "transform": {"scale": [0.0001, 0.0001, 1], "translate": [6.95, 50.93, 0]},
        "vertices": [[0, 0, 5], [1, 0, 5], [1, 1, 5], [0, 1, 5], [2, 2, 8]],
        "CityObjects": {
            "fictional-building": {
                "type": "Building",
                "attributes": {"measuredHeight": 9.5, "roofType": "synthetic-roof", "creationDate": "2025-01-01"},
                "geometry": [{"type": "Solid", "boundaries": [[[[0, 1, 2, 3]]]]}],
                "children": ["fictional-part"],
            },
            "fictional-part": {
                "type": "BuildingPart",
                "parents": ["fictional-building"],
                "attributes": {"roofType": "synthetic-part-roof"},
                "geometry": [{"type": "Solid", "boundaries": [[[[1, 2, 4]]]]}],
            },
        },
    }


def encoded(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class CityJSONBoundedSampleTests(unittest.TestCase):
    def test_valid_3d_cityjson_reports_only_aggregate_fields(self):
        receipt = assess(encoded(sample()))
        self.assertEqual(receipt["buildings"], 1)
        self.assertEqual(receipt["building_parts"], 1)
        self.assertEqual(receipt["root_attribute_present"]["roofType"], 1)
        self.assertEqual(receipt["part_attribute_present"]["roofType"], 1)
        self.assertEqual(receipt["root_attribute_present"]["function"], 0)
        self.assertTrue(receipt["all_roots_intersect_request_bbox"])
        self.assertEqual(receipt["crs"], CRS)
        self.assertFalse(receipt["model_ready"])
        self.assertFalse(receipt["source_fitness_admitted"])
        self.assertNotIn("fictional-building", json.dumps(receipt))
        self.assertNotIn("fictional-part", json.dumps(receipt))
        self.assertNotIn("synthetic-roof", json.dumps(receipt))

    def test_wrong_mime_type_format_and_crs_blocked(self):
        raw = encoded(sample())
        with self.assertRaises(SampleError):
            assess(raw, media_type="text/html")
        for field, value in (("type", "FeatureCollection"), ("version", "2.0")):
            changed = sample()
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(SampleError):
                assess(encoded(changed))
        changed = sample()
        changed["metadata"]["referenceSystem"] = "http://www.opengis.net/def/crs/EPSG/0/5555"
        with self.assertRaises(SampleError):
            assess(encoded(changed))

    def test_reject_duplicate_json_keys_and_invalid_numbers(self):
        for raw in (b'{"type":"CityJSON","type":"CityJSON"}', b'{"type":NaN}', b'[]', b'', b'x' * (MAX_BYTES + 1)):
            with self.subTest(raw=raw[:30]), self.assertRaises(SampleError):
                assess(raw)

    def test_unsupported_geometry_and_invalid_reference(self):
        for geometry in (
            [{"type": "MultiPoint", "boundaries": [0, 1]}],
            [{"type": "Solid", "boundaries": [[[[0, 99]]]]}],
            [{"type": "Solid", "boundaries": [[[[True]]]]}],
            [],
        ):
            changed = sample()
            changed["CityObjects"]["fictional-building"]["geometry"] = geometry
            changed["CityObjects"]["fictional-part"]["geometry"] = []
            with self.subTest(geometry=geometry), self.assertRaises(SampleError):
                assess(encoded(changed))

    def test_building_outside_requested_region_is_rejected(self):
        changed = sample()
        changed["transform"]["translate"] = [7.6105, 51.42, 0]
        changed["metadata"]["geographicalExtent"] = [7.6105, 51.42, 5, 7.6107, 51.4202, 8]
        with self.assertRaises(SampleError):
            assess(encoded(changed))

    def test_extent_outside_region_even_if_geometry_inside_is_rejected(self):
        changed = sample()
        changed["metadata"]["geographicalExtent"] = [7.61, 51.42, 5, 7.62, 51.43, 8]
        with self.assertRaises(SampleError):
            assess(encoded(changed))

    def test_building_part_must_have_known_parent(self):
        changed = sample()
        changed["CityObjects"]["fictional-part"]["parents"] = ["not-a-building"]
        with self.assertRaises(SampleError):
            assess(encoded(changed))

    def test_building_count_capped_to_limit_five(self):
        changed = sample()
        for i in range(5):
            b = copy.deepcopy(changed["CityObjects"]["fictional-building"])
            b["children"] = []
            changed["CityObjects"][f"extra-building-{i}"] = b
        with self.assertRaises(SampleError):
            assess(encoded(changed))

    def test_offline_mode_uses_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "invented.json"
            fixture.write_bytes(encoded(sample()))
            output = io.StringIO()
            with patch("scripts.assess_nrw_lod2_cityjson_sample_v0.acquire", side_effect=AssertionError("network")):
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(["--offline-json", str(fixture)]), 0)
            receipt = json.loads(output.getvalue())
            self.assertFalse(receipt["live_http_verified"])
            self.assertEqual(receipt["fixed_request_url"], SAMPLE_URL)

    def test_live_mode_exact_request_and_content_bound(self):
        payload = encoded(sample())

        class Response:
            status = 200
            headers = {"Content-Type": "application/city+json", "Content-Length": str(len(payload))}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return SAMPLE_URL
            def read(self, size):
                self_test.assertEqual(size, MAX_BYTES + 1)
                return payload

        class Opener:
            def open(self, request, timeout):
                self_test.assertEqual(request.full_url, SAMPLE_URL)
                self_test.assertEqual(request.get_method(), "GET")
                self_test.assertEqual(timeout, 15)
                return Response()
        self_test = self
        with patch("scripts.assess_nrw_lod2_cityjson_sample_v0.build_opener", return_value=Opener()):
            raw, mime = acquire()
        self.assertEqual(raw, payload)
        self.assertEqual(mime, "application/city+json")

    def test_oversize_offline_fixture_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "oversize.json"
            fixture.write_bytes(b"a" * (MAX_BYTES + 1))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--offline-json", str(fixture)]), 1)


if __name__ == "__main__":
    unittest.main()
