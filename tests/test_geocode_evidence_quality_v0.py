# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic geocode evidence is used in this offline regression suite."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest

from scripts.geocode_evidence_quality_v0 import benchmark, GeocodeEvidenceError


def row(*, candidate_lat=49.6, candidate_lon=6.1, family="original_geo", as_of="2020-06-01", precision="address_point", rank=1):
    return {"case_id": "synthetic-001", "engine": "synthetic-engine", "reference": {
        "lat": 49.6, "lon": 6.1, "crs": "EPSG:4326", "source_family": "separate_survey", "as_of": "2021-01-01"},
        "candidates": [{"rank": rank, "lat": candidate_lat, "lon": candidate_lon,
                        "crs": "EPSG:4326", "source_family": family,
                        "source_id": "synthetic-feature-1", "snapshot": "synthetic-v1",
                        "as_of": as_of, "precision": precision}]}


class GeocodeQualityTests(unittest.TestCase):
    def test_exact_synthetic_reference_is_analysis_only(self):
        r = benchmark([row()])
        self.assertTrue(r["analysis_only"])
        self.assertEqual(r["status_counts"], {"within_threshold_analysis_only": 1})
        self.assertEqual(r["rank1_median_error_m"], 0.0)

    def test_far_candidate_is_not_a_building_match(self):
        self.assertEqual(benchmark([row(candidate_lon=6.12)])["results"][0]["status"], "outside_threshold")

    def test_coarse_place_centroid_cannot_pass_as_rooftop(self):
        self.assertEqual(benchmark([row(precision="place_centroid")])["results"][0]["status"], "coarse_precision")

    def test_source_lineage_overlap_ignores_spurious_accuracy(self):
        self.assertEqual(benchmark([row(family="separate_survey")])["results"][0]["status"], "known_shared_lineage")

    def test_historical_snapshot_must_not_be_after_reference(self):
        self.assertEqual(benchmark([row(as_of="2026-01-01")])["results"][0]["status"], "post_reference_snapshot")

    def test_multiple_candidates_fail_closed_regardless_of_closeness(self):
        case = row()
        other = deepcopy(case["candidates"][0])
        other["rank"] = 2
        other["source_id"] = "synthetic-feature-2"
        case["candidates"].append(other)
        self.assertEqual(benchmark([case])["results"][0]["status"], "ambiguous_candidates")

    def test_empty_result_is_not_implicitly_a_location(self):
        case = row()
        case["candidates"] = []
        self.assertEqual(benchmark([case])["results"][0]["status"], "no_result")

    def test_invalid_coordinates_and_crs_fail_closed(self):
        for field, value in [("lat", 91.0), ("lon", 180.0), ("lat", True), ("lat", math.nan), ("crs", "EPSG:3857")]:
            case = row()
            case["candidates"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(GeocodeEvidenceError):
                benchmark([case])

    def test_duplicate_rank_or_duplicate_feature_fails_closed(self):
        case = row()
        duplicate = deepcopy(case["candidates"][0])
        case["candidates"].append(duplicate)
        with self.assertRaises(GeocodeEvidenceError):
            benchmark([case])
        case["candidates"][1]["source_id"] = "different-feature"
        with self.assertRaises(GeocodeEvidenceError):
            benchmark([case])

    def test_never_use_reference_to_reorder_candidates(self):
        case = row(candidate_lon=6.12)
        other = deepcopy(case["candidates"][0]); other.update({"rank": 2, "source_id": "synthetic-feature-2", "lon": 6.1})
        case["candidates"].append(other)
        result = benchmark([case])["results"][0]
        self.assertEqual(result["status"], "ambiguous_candidates")
        self.assertGreater(result["rank1_error_m"], 1000)

    def test_nonexistent_calendar_day_fails_closed(self):
        case = row(); case["reference"]["as_of"] = "2026-02-30"
        with self.assertRaises(GeocodeEvidenceError): benchmark([case])

    def test_duplicate_case_engine_fails_closed(self):
        with self.assertRaises(GeocodeEvidenceError): benchmark([row(), row()])

    def test_aggregation_includes_only_eligible_rank1_distances(self):
        rows = [row(), row(candidate_lon=6.101)]
        rows[1]["case_id"] = "synthetic-002"
        rows.append(row(family="separate_survey")); rows[2]["case_id"] = "synthetic-003"
        result = benchmark(rows)
        self.assertEqual(result["case_count"], 3)
        self.assertIsNotNone(result["rank1_p95_error_m"])
        self.assertGreater(result["rank1_p95_error_m"], result["rank1_median_error_m"])
        self.assertEqual(result["status_counts"]["known_shared_lineage"], 1)

    def test_unhashable_precision_fails_as_contract_error(self):
        case = row()
        case["candidates"][0]["precision"] = []
        with self.assertRaises(GeocodeEvidenceError):
            benchmark([case])

    def test_invalid_score_threshold_fails_closed(self):
        for val in (-1, math.inf, True, 1e8):
            with self.subTest(threshold=val), self.assertRaises(GeocodeEvidenceError):
                benchmark([row()], threshold_metres=val)


if __name__ == "__main__":
    unittest.main()
