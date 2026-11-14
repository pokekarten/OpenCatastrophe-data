# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fully offline synthetic-only tests; no live provider calls or raw data."""

import json
import re
import unittest
from urllib.parse import parse_qs, urlsplit

from research_runners.nyc_pluto_ll84_original_sample_v0 import (
    BIN, BBL, N, CHUNK, SampleError, canonical_pluto_bbl, ll84_url,
    pluto_url, run_live, summarize,
)


def fixture():
    rows = [
        {
            "property_id": str(2000 + n),
            "nyc_borough_block_and_lot": f"1000{n:06d}",
            "nyc_building_identification": f"100{n:04d}",
            "parent_property_id": "Not Applicable: Standalone Property",
            "number_of_buildings": "1",
            "report_year": "2024",
        }
        for n in range(N)
    ]
    buildings = [
        {"bbl": f"1000{n:06d}.00000000", "numbldgs": "2" if n >= 28 else "1"}
        for n in range(N)
    ]
    return rows, buildings


class TestOriginalSample(unittest.TestCase):
    def test_lossless_original_pluto_decimal_bbl(self):
        self.assertEqual(canonical_pluto_bbl("1000000001.00000000"), "1000000001")
        self.assertEqual(canonical_pluto_bbl("1000000001"), "1000000001")
        self.assertEqual(canonical_pluto_bbl("1000000001.0"), "1000000001")
        for raw in ["1000000001.00000100", "1000000001.1",
                    "10000000010.000", "100000001", "1e9", "0000000000",
                    1000000001, None, "1000000001.00000000;1000000002"]:
            with self.subTest(raw=raw), self.assertRaises(SampleError):
                canonical_pluto_bbl(raw)

    def test_realistic_28_plus_2_synthetic_reasons(self):
        ll84, pluto = fixture()
        result = summarize(ll84, pluto)
        self.assertEqual(result["ll84_rows"], 30)
        self.assertEqual(result["unique_pluto_bbls_returned"], 30)
        self.assertEqual(result["reason_counts"], {
            "pluto_taxlot_not_single_building": 2,
            "unverified_single_lot_building_candidate": 28,
        })
        self.assertFalse(result["representative"])
        self.assertFalse(result["building_identity_proven"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["raw_identifiers_exported"])
        self.assertNotIn("1000000000", str(result))
        self.assertNotIn("2000", str(result))

    def test_bounded_pinned_queries(self):
        u = urlsplit(ll84_url())
        qs = parse_qs(u.query)
        self.assertEqual(u.hostname, "data.cityofnewyork.us")
        self.assertEqual(qs["$limit"], ["30"])
        self.assertEqual(qs["$order"], ["property_id ASC"])
        self.assertEqual(qs["$where"], ["report_year = 2024 AND nyc_borough_block_and_lot like '1000%'"])
        ll84, _ = fixture()
        x = pluto_url(tuple(r["nyc_borough_block_and_lot"] for r in ll84[:CHUNK]))
        p = parse_qs(urlsplit(x).query)
        self.assertEqual(p["$select"], ["bbl,numbldgs"])
        self.assertEqual(p["$limit"], ["5"])
        self.assertNotIn("token", x)

    def test_reject_query_injection_and_overlarge_batch(self):
        for values in [(), tuple(f"1000{i:06d}" for i in range(6)),
                       ("1000000001", "1000000001"),
                       ("1 OR 1=1",), ("1000000001.00000000",)]:
            with self.subTest(values=values), self.assertRaises(SampleError):
                pluto_url(values)

    def test_mocked_source_read_and_chunking(self):
        ll84, pluto = fixture()
        by_bbl = {r["bbl"].split(".")[0]: r for r in pluto}
        calls = []
        def fake_get(url):
            calls.append(url)
            if url == ll84_url():
                return json.dumps(ll84).encode()
            where = parse_qs(urlsplit(url).query)["$where"][0]
            match = re.fullmatch(r"bbl in \(([0-9,]+)\)", where)
            self.assertIsNotNone(match)
            rows = [by_bbl[k] for k in match.group(1).split(",") if k in by_bbl]
            return json.dumps(rows).encode()
        result = run_live(fake_get)
        self.assertEqual(result["reason_counts"]["unverified_single_lot_building_candidate"], 28)
        self.assertEqual(len(calls), 7)  # one LL84 + six PLUTO batches
        self.assertTrue(all("data.cityofnewyork.us" in url for url in calls))

    def test_failed_batch_retries_individual_without_claiming_missing(self):
        ll84, pluto = fixture()
        lookup = {r["bbl"].split(".")[0]: r for r in pluto}
        stats = {"failures": 0, "single_calls": 0}
        def fake_get(url):
            if url == ll84_url():
                return json.dumps(ll84).encode()
            keys = parse_qs(urlsplit(url).query)["$where"][0].split("(")[1].rstrip(")").split(",")
            if len(keys) == 5 and keys[0] == "1000000010":
                stats["failures"] += 1
                raise SampleError("simulated provider batch timeout")
            if len(keys) == 1:
                stats["single_calls"] += 1
            return json.dumps([lookup[k] for k in keys]).encode()
        result = run_live(fake_get)
        self.assertEqual(result["unique_pluto_bbls_returned"], 30)
        self.assertEqual(stats, {"failures": 1, "single_calls": 5})

    def test_failed_single_retry_blocks_entire_result(self):
        ll84, pluto = fixture()
        def bad_get(url):
            if url == ll84_url():
                return json.dumps(ll84).encode()
            raise SampleError("simulated persistent source timeout")
        with self.assertRaises(SampleError):
            run_live(bad_get)

    def test_invalid_or_missing_source_keys_fail_closed(self):
        for which in ("duplicate_ll84", "wrong_year", "duplicate_pluto",
                      "fractional_bbl", "unexpected_pluto_field", "truncated_ll84"):
            ll84, pluto = fixture()
            if which == "duplicate_ll84":
                ll84[1]["property_id"] = ll84[0]["property_id"]
            elif which == "wrong_year":
                ll84[0]["report_year"] = "2023"
            elif which == "duplicate_pluto":
                pluto.append(dict(pluto[0]))
            elif which == "fractional_bbl":
                pluto[0]["bbl"] = "1000000000.12345678"
            elif which == "unexpected_pluto_field":
                pluto[0]["address"] = "should never be downloaded"
            elif which == "truncated_ll84":
                ll84.pop()
            with self.subTest(which=which), self.assertRaises(SampleError):
                summarize(ll84, pluto)

    def test_shared_taxlot_and_campus_cannot_be_auto_joined(self):
        ll84, pluto = fixture()
        ll84[1]["nyc_borough_block_and_lot"] = ll84[0]["nyc_borough_block_and_lot"]
        result = summarize(ll84, pluto)
        self.assertEqual(result["reason_counts"]["same_sample_bbl_shared_by_multiple_properties"], 2)
        ll84, pluto = fixture()
        ll84[0]["nyc_borough_block_and_lot"] += ";1000000001"
        self.assertEqual(summarize(ll84, pluto)["reason_counts"]["ll84_multibbl_or_invalid_bbl"], 1)
        ll84, pluto = fixture()
        ll84[0]["parent_property_id"] = "4001234"
        self.assertEqual(summarize(ll84, pluto)["reason_counts"]["ll84_parent_child_or_unknown_status"], 1)
        ll84, pluto = fixture()
        ll84[0]["nyc_building_identification"] += ";1009999"
        self.assertEqual(summarize(ll84, pluto)["reason_counts"]["ll84_multibin_or_invalid_bin"], 1)

    def test_missing_current_pluto_lot_is_not_missing_physical_building(self):
        ll84, pluto = fixture()
        pluto.pop()
        result = summarize(ll84, pluto)
        self.assertEqual(result["reason_counts"]["pluto_bbl_missing_in_current_release"], 1)
        self.assertFalse(result["building_identity_proven"])


if __name__ == "__main__":
    unittest.main()
