# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic tests for fixed NRW LoD2 multi-region QA, no HTTP calls."""

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
    SampleError, assess,
)
from scripts.assess_nrw_lod2_five_area_v0 import (
    AREAS, StudyArea, fetch_fixed_area, main, summarize,
)
from tests.test_assess_nrw_lod2_cityjson_sample_v0 import encoded, sample


def invented_fixture(area: StudyArea) -> bytes:
    doc = sample()
    x, y, _, _ = area.bbox
    doc["transform"]["translate"] = [x, y, 0]
    doc["metadata"]["geographicalExtent"] = [x, y, 5, x + 0.0002, y + 0.0002, 8]
    return encoded(doc)


def invented_observations():
    return [(area, invented_fixture(area), "application/city+json") for area in AREAS]


class FiveAreaCityJSONTests(unittest.TestCase):
    def test_distinct_allowlisted_areas_have_exact_capped_urls(self):
        self.assertEqual(len(AREAS), 5)
        self.assertEqual(len({a.code for a in AREAS}), 5)
        for area in AREAS:
            self.assertTrue(area.url.startswith(
                "https://ogc-api.nrw.de/3dg/v1/collections/building/items?"
                "f=cityjson&limit=5&bbox="
            ))
            self.assertEqual(len(area.url.split("bbox=")[1].split(",")), 4)

    def test_five_area_aggregate_does_not_include_source_ids(self):
        output = summarize(invented_observations())
        self.assertEqual(output["areas_attempted"], 5)
        self.assertEqual(output["total_root_buildings"], 5)
        self.assertEqual(output["total_building_parts"], 5)
        self.assertEqual(output["root_attribute_present"]["roofType"], 5)
        self.assertEqual(output["part_attribute_present"]["roofType"], 5)
        self.assertEqual(output["root_missing_with_part_attribute"]["roofType"], 0)
        self.assertFalse(output["model_ready"])
        self.assertFalse(output["independent_insurer_exposure"])
        self.assertNotIn("fictional-building", json.dumps(output))
        self.assertNotIn("fictional-part", json.dumps(output))
        self.assertNotIn("synthetic-roof", json.dumps(output))

    def test_child_only_roof_is_diagnostic_not_filled_into_parent(self):
        a = AREAS[0]
        doc = json.loads(invented_fixture(a))
        del doc["CityObjects"]["fictional-building"]["attributes"]["roofType"]
        receipt = assess(encoded(doc), bbox=a.bbox, source_url=a.url)
        self.assertEqual(receipt["root_attribute_present"]["roofType"], 0)
        self.assertEqual(receipt["part_attribute_present"]["roofType"], 1)
        self.assertEqual(receipt["root_missing_with_part_attribute"]["roofType"], 1)

    def test_wrong_region_and_wrong_original_url_are_blocked(self):
        a, b = AREAS[0], AREAS[1]
        with self.assertRaises(SampleError):
            assess(invented_fixture(a), bbox=b.bbox, source_url=b.url)
        with self.assertRaises(SampleError):
            assess(invented_fixture(a), bbox=a.bbox, source_url=b.url)

    def test_mismatched_or_duplicated_area_responses_are_blocked(self):
        original = invented_observations()
        for observations in (
            original[:-1],
            original + [original[0]],
            original[:-1] + [original[0]],
        ):
            with self.subTest(count=len(observations)), self.assertRaises(SampleError):
                summarize(observations)
        unknown = StudyArea("fake", "unapproved", (7.0, 51.0, 7.004, 51.004))
        with self.assertRaises(SampleError):
            summarize(original[:-1] + [(unknown, invented_fixture(unknown), "application/city+json")])

    def test_invalid_geojson_and_too_many_roots_are_blocked(self):
        a = AREAS[0]
        with self.assertRaises(SampleError):
            assess(invented_fixture(a), bbox=a.bbox, source_url=a.url, media_type="application/geo+json")
        doc = json.loads(invented_fixture(a))
        for i in range(5):
            clone = copy.deepcopy(doc["CityObjects"]["fictional-building"])
            clone["children"] = []
            doc["CityObjects"][f"fictional-extra-{i}"] = clone
        with self.assertRaises(SampleError):
            assess(encoded(doc), bbox=a.bbox, source_url=a.url)

    def test_offline_mode_never_calls_provider(self):
        with tempfile.TemporaryDirectory() as dirname:
            for area in AREAS:
                (Path(dirname) / f"{area.code}.json").write_bytes(invented_fixture(area))
            output = io.StringIO()
            with patch(
                "scripts.assess_nrw_lod2_five_area_v0.fetch_fixed_area",
                side_effect=AssertionError("network request forbidden"),
            ), contextlib.redirect_stdout(output):
                self.assertEqual(main(["--offline-dir", dirname]), 0)
            receipt = json.loads(output.getvalue())
            self.assertFalse(receipt["transport_verified_by_script"])
            self.assertEqual(receipt["areas_attempted"], 5)
            self.assertNotIn("fictional-building", output.getvalue())

    def test_offline_missing_or_oversize_fixtures_fail_closed(self):
        with tempfile.TemporaryDirectory() as dirname:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--offline-dir", dirname]), 1)
        with tempfile.TemporaryDirectory() as dirname:
            for area in AREAS:
                (Path(dirname) / f"{area.code}.json").write_bytes(invented_fixture(area))
            (Path(dirname) / f"{AREAS[0].code}.json").write_bytes(b"x" * 65537)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--offline-dir", dirname]), 1)

    def test_plan_prints_endpoints_without_network(self):
        out = io.StringIO()
        with patch(
            "scripts.assess_nrw_lod2_five_area_v0.fetch_fixed_area",
            side_effect=AssertionError("network request forbidden"),
        ), contextlib.redirect_stdout(out):
            self.assertEqual(main(["--plan"]), 0)
        plan = json.loads(out.getvalue())
        self.assertEqual(len(plan), 5)
        self.assertEqual(plan[0]["url"], AREAS[0].url)

    def test_fixed_live_get_has_one_request_and_no_redirect(self):
        from scripts.assess_nrw_lod2_five_area_v0 import MAX_BYTES
        area = AREAS[1]
        body = invented_fixture(area)

        class Response:
            status = 200
            headers = {"Content-Type": "application/city+json", "Content-Length": str(len(body))}
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def geturl(self): return area.url
            def read(self, count):
                self_test.assertEqual(count, MAX_BYTES + 1)
                return body

        class Opener:
            def open(self, req, timeout):
                self_test.assertEqual(req.full_url, area.url)
                self_test.assertEqual(req.get_method(), "GET")
                self_test.assertEqual(timeout, 15)
                return Response()

        self_test = self
        with patch("scripts.assess_nrw_lod2_five_area_v0.build_opener", return_value=Opener()):
            received, media_type = fetch_fixed_area(area)
        self.assertEqual(received, body)
        self.assertEqual(media_type, "application/city+json")
        not_allowed = StudyArea("unplanned", "none", (7.0, 50.0, 7.01, 50.01))
        with self.assertRaises(SampleError):
            fetch_fixed_area(not_allowed)

    def test_reusing_one_area_payload_for_other_area_fails(self):
        original = invented_observations()
        bad = list(original)
        bad[1] = (bad[1][0], bad[0][1], bad[0][2])
        with self.assertRaises(SampleError):
            summarize(bad)


if __name__ == "__main__":
    unittest.main()
