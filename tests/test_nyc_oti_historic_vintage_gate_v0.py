# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic-only tests for the NYC 2024 historic archive gate."""

import json
import unittest
from urllib.parse import parse_qs, urlsplit

from research_runners.nyc_oti_historic_vintage_gate_v0 import (
    HistoricError, HistoricTransportError, METRICS, N, historic_bin_count_query,
    ll84_query, main, metric_queries, parse_cohort, parse_count, run_live,
    summarize_counts,
)


def figures():
    return {
        "historic_all_rows": 50995,
        "historic_doitt_zero_rows": 9490,
        "historic_placeholder_million_bin_rows": 5319,
        "historic_demolition_year_2024_rows": 1127,
        "historic_demolition_year_2025_rows": 1082,
        "historic_demolition_year_present_rows": 47677,
        "historic_last_edited_2025_or_later_rows": 3820,
    }


def ll84_cohort():
    return [
        {"property_id": str(2100 + i),
         "nyc_borough_block_and_lot": f"1000{i:06d}",
         "nyc_building_identification": f"100{i+1:04d}",
         "report_year": "2024"}
        for i in range(N)
    ]


def count_response(n):
    return json.dumps([{"count": str(n)}]).encode("utf-8")


class NYCArchiveVintageTests(unittest.TestCase):
    def test_report_explicitly_refuses_2024_inventory_proof(self):
        report = summarize_counts(figures(), 0)
        self.assertEqual(report["ll84_2024_convenience_cohort_bin_count"], 30)
        self.assertEqual(report["historic_source_feature_rows_for_30_bins"], 0)
        self.assertEqual(report["reported_aggregate_counts"]["historic_doitt_zero_rows"], 9490)
        for key in (
            "historical_feature_archive_is_complete_2024_building_stock",
            "historic_last_edit_is_demolition_date",
            "historical_inventory_2024_snapshot_bytes_acquired",
            "historical_inventory_2024_verified",
            "historical_2024_building_presence_inferred",
            "source_rights_or_model_admission_approved",
            "insured_tiv_or_loss_calculated",
            "raw_original_property_ids_or_bins_exported",
        ):
            self.assertFalse(report[key])
        self.assertNotIn("1000001", str(report))
        self.assertNotIn("2100", str(report))

    def test_all_histogram_queries_aggregate_only_pinned(self):
        requests = metric_queries()
        self.assertEqual(set(requests), set(METRICS))
        for k, url in requests.items():
            with self.subTest(metric=k):
                parts = urlsplit(url)
                q = parse_qs(parts.query)
                self.assertEqual(parts.scheme, "https")
                self.assertEqual(parts.hostname, "data.cityofnewyork.us")
                self.assertEqual(parts.path, "/resource/ipkp-snf6.json")
                self.assertEqual(q["$select"], ["count(*)"])
                self.assertNotIn("$order", q)
                self.assertNotIn("$limit", q)
                self.assertNotIn("token", url)

    def test_ll84_cohort_query_is_fixed(self):
        p = urlsplit(ll84_query())
        q = parse_qs(p.query)
        self.assertEqual(q["$limit"], ["30"])
        self.assertEqual(q["$order"], ["property_id ASC"])
        self.assertEqual(
            q["$where"], ["report_year = 2024 AND nyc_borough_block_and_lot like '1000%'"])
        self.assertNotIn("name", q["$select"][0])
        self.assertNotIn("address", q["$select"][0])
        self.assertEqual(len(parse_cohort(json.dumps(ll84_cohort()).encode())), 30)

    def test_bin_batch_query_disallows_sql_injection_or_dummy_bin(self):
        valid = tuple(f"100{i+1:04d}" for i in range(5))
        qs = parse_qs(urlsplit(historic_bin_count_query(valid)).query)
        self.assertEqual(qs["$select"], ["count(*)"])
        for bad in [
            (), ("1000000",), ("1000001", "1000001"),
            ("1000001.00",), ("1000001 OR 1=1",),
            tuple(f"100{i+1:04d}" for i in range(6)),
            (1000001,),
        ]:
            with self.subTest(bad=bad), self.assertRaises(HistoricError):
                historic_bin_count_query(bad)

    def test_reject_bad_json_and_extra_source_rows(self):
        bad = [
            b"", b"not json", b"{}", b"[]", b'[{"count":"1"},{"count":"2"}]',
            b'[{"count":"12","bin":"1000001"}]', b'[{"count":12}]',
            b'[{"count":"-3"}]', b'[{"count":"12.5"}]',
            b'[{"count":"10000001"}]', b'[{"count":null}]',
            b'[{"count":"1"}]' + b" " * 25000,
        ]
        for data in bad:
            with self.subTest(data=data[:45]), self.assertRaises(HistoricError):
                parse_count(data)
        self.assertEqual(parse_count(b'[{"count":"0"}]'), 0)

    def test_invalid_counts_are_blocked(self):
        for key, invalid in [
            ("historic_all_rows", 0),
            ("historic_doitt_zero_rows", 51000),
            ("historic_placeholder_million_bin_rows", True),
            ("historic_demolition_year_2024_rows", -1),
            ("historic_demolition_year_present_rows", 1),
        ]:
            vals = figures()
            vals[key] = invalid
            with self.subTest(key=key), self.assertRaises(HistoricError):
                summarize_counts(vals, 0)
        vals = figures()
        vals["extra_provider_metric"] = 42
        with self.assertRaises(HistoricError):
            summarize_counts(vals, 0)
        with self.assertRaises(HistoricError):
            summarize_counts(figures(), 99999999)

    def test_empty_historic_cohort_is_not_presence_proof(self):
        source = {url: count_response(figures()[k])
                  for k, url in metric_queries().items()}
        source[ll84_query()] = json.dumps(ll84_cohort()).encode()
        for i in range(0, N, 5):
            bb = tuple(f"100{j+1:04d}" for j in range(i, i + 5))
            source[historic_bin_count_query(bb)] = count_response(0)
        calls = []
        def fetch(url):
            calls.append(url)
            return source[url]
        result = run_live(fetch)
        self.assertEqual(result["historic_source_feature_rows_for_30_bins"], 0)
        self.assertFalse(result["historical_2024_building_presence_inferred"])
        self.assertEqual(len(calls), 7 + 1 + 6)
        self.assertTrue(all(urlsplit(u).hostname == "data.cityofnewyork.us" for u in calls))

    def test_transport_timeout_retry_individually_not_silently_as_zero(self):
        static = {url: count_response(figures()[k])
                  for k, url in metric_queries().items()}
        static[ll84_query()] = json.dumps(ll84_cohort()).encode()
        retries = []
        def fetch(url):
            if url in static:
                return static[url]
            q = parse_qs(urlsplit(url).query)
            where = q["$where"][0]
            self.assertTrue(where.startswith("bin in("))
            bb = where[len("bin in("):-1].split(",")
            if len(bb) == 5 and bb[0] == "1000006":
                raise HistoricTransportError("batch timeout")
            if len(bb) == 1:
                retries.append(bb[0])
            return count_response(2 if len(bb) == 1 and bb[0] == "1000006" else 0)
        report = run_live(fetch)
        self.assertEqual(report["historic_source_feature_rows_for_30_bins"], 2)
        self.assertEqual(len(retries), 5)
        self.assertFalse(report["historical_2024_building_presence_inferred"])

    def test_persistent_single_bin_timeout_aborts(self):
        static = {url: count_response(figures()[k])
                  for k, url in metric_queries().items()}
        static[ll84_query()] = json.dumps(ll84_cohort()).encode()
        def fetch(url):
            if url in static:
                return static[url]
            raise HistoricTransportError("still not available")
        with self.assertRaises(HistoricTransportError):
            run_live(fetch)

    def test_untrusted_cohort_incomplete_wrong_year_or_duplicate_rejected(self):
        for kind in ("incomplete", "wrong_year", "wrong_bbl", "multi_bin",
                     "million_bin", "dup_id", "dup_bin", "extra_field"):
            rows = ll84_cohort()
            if kind == "incomplete":
                rows.pop()
            elif kind == "wrong_year":
                rows[0]["report_year"] = "2023"
            elif kind == "wrong_bbl":
                rows[0]["nyc_borough_block_and_lot"] = "2000000001"
            elif kind == "multi_bin":
                rows[0]["nyc_building_identification"] += ";1009999"
            elif kind == "million_bin":
                rows[0]["nyc_building_identification"] = "1000000"
            elif kind == "dup_id":
                rows[0]["property_id"] = rows[1]["property_id"]
            elif kind == "dup_bin":
                rows[0]["nyc_building_identification"] = rows[1]["nyc_building_identification"]
            elif kind == "extra_field":
                rows[0]["insured_tiv"] = "100000"
            with self.subTest(kind=kind), self.assertRaises(HistoricError):
                parse_cohort(json.dumps(rows).encode())

    def test_no_network_without_explicit_live(self):
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
