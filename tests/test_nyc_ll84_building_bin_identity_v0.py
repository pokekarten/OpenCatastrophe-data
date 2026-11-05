# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only offline tests for independently sourced NYC OTI BIN identity."""

import json
import re
import unittest
from urllib.parse import parse_qs, urlsplit

from research_runners.nyc_ll84_building_bin_identity_v0 import (
    N, ProbeError, TransportError, footprint_url, ll84_url, run_live, summarize,
)


def fixture():
    ll84 = [
        {"property_id": str(2000 + i),
         "nyc_borough_block_and_lot": f"1000{i:06d}",
         "nyc_building_identification": f"100{i:04d}",
         "parent_property_id": "Not Applicable: Standalone Property",
         "number_of_buildings": "1", "report_year": "2024"}
        for i in range(N)
    ]
    fp = [
        {"bin": f"100{i:04d}",
         "doitt_id": str(70000 + i),
         "base_bbl": f"1000{i if i < 22 else i + 1000:06d}",
         "feature_code": "2100"}
        for i in range(N)
    ]
    return ll84, fp


class NYCBuildingFootprintTests(unittest.TestCase):
    def test_measured_pattern_is_synthetic_only_and_unverified(self):
        ll84, fp = fixture()
        report = summarize(ll84, fp)
        self.assertEqual(report["ll84_property_year_rows"], 30)
        self.assertEqual(report["distinct_footprint_bin_values"], 30)
        self.assertEqual(report["single_bin_base_bbl_relation"], {"different": 8, "same": 22})
        self.assertEqual(report["reason_counts"], {
            "unique_bin_different_base_bbl_requires_billing_crosswalk": 8,
            "unique_bin_matching_base_bbl_unverified": 22,
        })
        for key in ("building_identity_proven", "source_admitted_for_models",
                    "insured_value_or_losses_inferred", "actual_polygon_geometries_examined",
                    "raw_external_source_rows_exported"):
            self.assertFalse(report[key])
        self.assertNotIn("1000000000", str(report))
        self.assertNotIn("70000", str(report))

    def test_requests_fixed_and_no_geometries(self):
        u = urlsplit(ll84_url())
        q = parse_qs(u.query)
        self.assertEqual(q["$limit"], ["30"])
        self.assertEqual(q["$order"], ["property_id ASC"])
        self.assertNotIn("address", q["$select"][0])
        bins = tuple(f"100{i:04d}" for i in range(5))
        u = urlsplit(footprint_url(bins))
        q = parse_qs(u.query)
        self.assertEqual(u.scheme, "https")
        self.assertEqual(u.hostname, "data.cityofnewyork.us")
        self.assertEqual(q["$select"], ["bin,doitt_id,base_bbl,feature_code"])
        self.assertEqual(q["$limit"], ["100"])
        self.assertNotIn("the_geom", str(q))

    def test_reject_query_injection_or_unbounded_batch(self):
        for x in [(), ("1000001",) * 2,
                  tuple(f"100{i:04d}" for i in range(6)),
                  ("1000000); DROP TABLE building",),
                  ("1000000.00",), (1000001,)]:
            with self.subTest(x=x), self.assertRaises(ProbeError):
                footprint_url(x)

    def test_offline_mock_run_batches_only(self):
        ll84, fp = fixture()
        lookup = {r["bin"]: r for r in fp}
        calls = []
        def mock_fetch(url):
            calls.append(url)
            if url == ll84_url():
                return json.dumps(ll84).encode()
            q = parse_qs(urlsplit(url).query)
            match = re.fullmatch(r"bin in \(([0-9,]+)\)", q["$where"][0])
            self.assertIsNotNone(match)
            bins = match.group(1).split(",")
            return json.dumps([lookup[b] for b in bins]).encode()
        result = run_live(mock_fetch)
        self.assertEqual(result["single_bin_base_bbl_relation"], {"different": 8, "same": 22})
        self.assertEqual(len(calls), 7)

    def test_transport_batch_timeout_retried_as_individual_bins(self):
        ll84, fp = fixture()
        lookup = {r["bin"]: r for r in fp}
        count = {"retry": 0, "failed": 0}
        def mock_fetch(url):
            if url == ll84_url():
                return json.dumps(ll84).encode()
            keys = parse_qs(urlsplit(url).query)["$where"][0].split("(")[1].rstrip(")").split(",")
            if len(keys) == 5 and keys[0] == "1000005":
                count["failed"] += 1
                raise TransportError("simulated outage")
            if len(keys) == 1:
                count["retry"] += 1
            return json.dumps([lookup[x] for x in keys]).encode()
        report = run_live(mock_fetch)
        self.assertEqual(count, {"retry": 5, "failed": 1})
        self.assertEqual(report["distinct_footprint_bin_values"], 30)

    def test_persistent_single_bin_failure_blocks_all(self):
        ll84, _ = fixture()
        def fail(url):
            if url == ll84_url():
                return json.dumps(ll84).encode()
            raise TransportError("simulated outage")
        with self.assertRaises(TransportError):
            run_live(fail)

    def test_million_bin_placeholder_cannot_prove_identity(self):
        ll84, fp = fixture()
        ll84[0]["nyc_building_identification"] = "1000000"
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["placeholder_million_bin"], 1)

    def test_shared_bin_across_ll84_properties_does_not_double_count(self):
        ll84, fp = fixture()
        ll84[1]["nyc_building_identification"] = ll84[0]["nyc_building_identification"]
        report = summarize(ll84, fp)
        self.assertEqual(report["reason_counts"]["shared_bin_across_ll84_properties"], 2)

    def test_multiple_footprints_for_one_bin_not_unique(self):
        ll84, fp = fixture()
        fp.append({**fp[0], "doitt_id": "99999", "base_bbl": "1000002222"})
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["nonunique_bin_multiple_footprint_features"], 1)

    def test_nonbuilding_placeholder_or_other_code_blocked(self):
        ll84, fp = fixture()
        fp[0]["feature_code"] = "1003"
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["non_standard_building_or_placeholder_feature"], 1)

    def test_campus_parent_and_non_one_building_blocked(self):
        ll84, fp = fixture()
        ll84[0]["parent_property_id"] = "3001010"
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["ll84_campus_parent_or_unknown"], 1)
        ll84, fp = fixture()
        ll84[0]["number_of_buildings"] = "2"
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["ll84_reported_building_count_not_one"], 1)

    def test_multi_bbl_and_multi_bin_cannot_auto_split(self):
        ll84, fp = fixture()
        ll84[0]["nyc_borough_block_and_lot"] += ";1000099999"
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["ll84_missing_multilot_or_invalid_bbl"], 1)
        ll84, fp = fixture()
        ll84[0]["nyc_building_identification"] += ";1009999"
        self.assertEqual(summarize(ll84, fp)["reason_counts"]["ll84_missing_multibin_or_invalid_bin"], 1)

    def test_missing_footprint_not_real_building_absence(self):
        ll84, fp = fixture()
        fp.pop()
        r = summarize(ll84, fp)
        self.assertEqual(r["reason_counts"]["bin_absent_from_current_footprint_source"], 1)
        self.assertFalse(r["building_identity_proven"])

    def test_duplicate_doitt_or_bad_base_bbl_rejected(self):
        ll84, fp = fixture()
        fp[1]["doitt_id"] = fp[0]["doitt_id"]
        with self.assertRaises(ProbeError):
            summarize(ll84, fp)
        ll84, fp = fixture()
        fp[0]["base_bbl"] = "1000000001.00000000"
        with self.assertRaises(ProbeError):
            summarize(ll84, fp)

    def test_invalid_cohort_or_schema_fails_closed(self):
        for mutation in ("short_cohort", "duplicate_property", "wrong_year", "bad_fp_schema"):
            ll84, fp = fixture()
            if mutation == "short_cohort":
                ll84.pop()
            elif mutation == "duplicate_property":
                ll84[1]["property_id"] = ll84[0]["property_id"]
            elif mutation == "wrong_year":
                ll84[0]["report_year"] = "2023"
            elif mutation == "bad_fp_schema":
                fp[0]["the_geom"] = "source polygon forbidden"
            with self.subTest(mutation=mutation), self.assertRaises(ProbeError):
                summarize(ll84, fp)


if __name__ == "__main__":
    unittest.main()
