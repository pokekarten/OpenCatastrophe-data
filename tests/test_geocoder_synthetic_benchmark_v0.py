# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic geocoder benchmark and fail-closed regression tests."""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.geocoder_synthetic_benchmark_v0 import (
    GeocoderBenchmarkError, evaluate, main, _distance,
)


def fixture():
    return {
        "schema_version": "oc-geocoder-benchmark-synthetic-v0",
        "synthetic_only": True, "crs": "EPSG:4326",
        "distance_threshold_m": 50,
        "truth": [
            {"case_id": "synthetic:A", "latitude": 49.0, "longitude": 6.0},
            {"case_id": "synthetic:B", "latitude": 49.1, "longitude": 6.1},
            {"case_id": "synthetic:C", "latitude": 49.2, "longitude": 6.2},
        ],
        "runs": [{
            "engine": "pelias", "engine_version": "test1", "index_snapshot_id": "snapshot1",
            "candidates": [
                {"case_id": "synthetic:A", "rank": 1, "latitude": 49.0, "longitude": 6.0},
                {"case_id": "synthetic:B", "rank": 1, "latitude": 49.11, "longitude": 6.1},
                {"case_id": "synthetic:B", "rank": 2, "latitude": 49.1, "longitude": 6.1},
            ],
        }],
    }


class SyntheticGeocodingBenchmarkTests(unittest.TestCase):
    def test_aggregate_recall_rank_and_missing_cases(self):
        report = evaluate(fixture())
        row = report["runs"][0]
        self.assertEqual(row["synthetic_cases"], 3)
        self.assertEqual(row["cases_with_candidates"], 2)
        self.assertEqual(row["no_candidate_cases"], 1)
        self.assertAlmostEqual(row["recall_at_1"], 1 / 3, delta=0.000001)
        self.assertAlmostEqual(row["recall_at_3"], 2 / 3, delta=0.000001)
        self.assertGreater(row["median_top1_error_m"], 500)
        self.assertGreater(row["p95_top1_error_m"], row["median_top1_error_m"])
        self.assertFalse(report["building_identity_proven"])
        self.assertFalse(report["cat_model_input_admitted"])
        self.assertFalse(report["source_rights_admitted"])

    def test_different_data_snapshots_flag_not_comparable(self):
        data = fixture()
        second = copy.deepcopy(data["runs"][0])
        second["engine"] = "photon"
        second["index_snapshot_id"] = "different"
        data["runs"].append(second)
        self.assertFalse(evaluate(data)["same_index_snapshot_across_engines"])
        data["runs"][1]["index_snapshot_id"] = "snapshot1"
        self.assertTrue(evaluate(data)["same_index_snapshot_across_engines"])

    def test_no_candidates_gives_null_errors_not_perfect_accuracy(self):
        data = fixture()
        data["runs"][0]["candidates"] = []
        row = evaluate(data)["runs"][0]
        self.assertEqual(row["recall_at_1"], 0)
        self.assertEqual(row["recall_at_3"], 0)
        self.assertIsNone(row["median_top1_error_m"])
        self.assertEqual(row["no_candidate_cases"], 3)

    def test_denominator_is_all_truth_cases(self):
        data = fixture()
        data["truth"].append({"case_id": "synthetic:D", "latitude": 49.3, "longitude": 6.3})
        self.assertEqual(evaluate(data)["runs"][0]["recall_at_3"], .5)

    def test_rank_gap_and_duplicate_fail_closed(self):
        data = fixture()
        data["runs"][0]["candidates"][2]["rank"] = 3
        with self.assertRaisesRegex(GeocoderBenchmarkError, "contiguous"):
            evaluate(data)
        data["runs"][0]["candidates"][2]["rank"] = 1
        with self.assertRaisesRegex(GeocoderBenchmarkError, "duplicate"):
            evaluate(data)

    def test_unknown_case_and_duplicate_truth_fail_closed(self):
        data = fixture()
        data["runs"][0]["candidates"][0]["case_id"] = "synthetic:unknown"
        with self.assertRaisesRegex(GeocoderBenchmarkError, "unknown"):
            evaluate(data)
        data = fixture()
        data["truth"].append(copy.deepcopy(data["truth"][0]))
        with self.assertRaisesRegex(GeocoderBenchmarkError, "duplicate"):
            evaluate(data)

    def test_real_or_extra_address_fields_disallowed(self):
        data = fixture()
        data["truth"][0]["address"] = "PRIVATE ADDRESS"
        with self.assertRaisesRegex(GeocoderBenchmarkError, "fields"):
            evaluate(data)
        data = fixture()
        data["truth"][0]["case_id"] = "real:address-1"
        with self.assertRaisesRegex(GeocoderBenchmarkError, "synthetic"):
            evaluate(data)
        data = fixture()
        data["synthetic_only"] = False
        with self.assertRaisesRegex(GeocoderBenchmarkError, "synthetic-only"):
            evaluate(data)

    def test_invalid_crs_and_coordinates_fail_closed(self):
        for axis, value in [("latitude", 91), ("longitude", 181),
                            ("latitude", float("nan")), ("latitude", float("inf")),
                            ("latitude", True), ("longitude", "6.0")]:
            with self.subTest(axis=axis, value=str(value)):
                data = fixture()
                data["truth"][0][axis] = value
                with self.assertRaises(GeocoderBenchmarkError):
                    evaluate(data)
        data = fixture()
        data["crs"] = "EPSG:3857"
        with self.assertRaisesRegex(GeocoderBenchmarkError, "EPSG:4326"):
            evaluate(data)
        data = fixture()
        data["distance_threshold_m"] = True
        with self.assertRaises(GeocoderBenchmarkError):
            evaluate(data)

    def test_antimeridian_distance_is_short(self):
        self.assertLess(_distance((0, 179.999), (0, -179.999)), 300)

    def test_no_case_coordinates_or_identifiers_leak_in_report(self):
        report = json.dumps(evaluate(fixture()))
        self.assertNotIn("synthetic:A", report)
        self.assertNotIn("49.11", report)
        self.assertNotIn("PRIVATE", report)

    def test_cli_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "duplicate.json"
            target.write_text('{"synthetic_only":true,"synthetic_only":true}', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()) as err:
                code = main(["--input", str(target)])
            self.assertEqual(code, 2)
            self.assertNotIn("true", err.getvalue())

    def test_cli_success_and_no_row_leak(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "synthetic.json"
            target.write_text(json.dumps(fixture()), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as stream:
                result = main(["--input", str(target)])
            self.assertEqual(result, 0)
            self.assertNotIn("synthetic:A", stream.getvalue())
            self.assertFalse(json.loads(stream.getvalue())["building_identity_proven"])


if __name__ == "__main__":
    unittest.main()
