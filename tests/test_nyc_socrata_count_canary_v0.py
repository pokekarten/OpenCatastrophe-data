# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Pure offline negative tests; never contact the NYC original provider."""

import json
import unittest
from urllib.parse import parse_qs, urlsplit

from research_runners.nyc_socrata_count_canary_v0 import (
    CanaryError, CONDITIONS, analyze_counts, parse_count, queries,
    run_canary, validate_query_url,
)


def sample_counts():
    return {
        "pluto_total": 858284,
        "ll84_2024_total": 39090,
        "multi_bbl": 866,
        "multi_bin": 3305,
        "missing_bbl_literal": 219,
        "missing_bin_literal": 346,
        "any_of_four_special_cases": 3812,
    }


class NYCOriginalCanaryTests(unittest.TestCase):
    def test_pinned_aggregate_urls_are_read_only_and_bounded(self):
        request_urls = queries()
        self.assertEqual(len(request_urls), 7)
        for key, url in request_urls.items():
            with self.subTest(key=key):
                validate_query_url(url)
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, "https")
                self.assertEqual(parsed.hostname, "data.cityofnewyork.us")
                self.assertEqual(parse_qs(parsed.query)["$select"], ["count(*)"])
                self.assertNotIn("$limit", parse_qs(parsed.query))
                self.assertNotIn("$offset", parse_qs(parsed.query))
                self.assertNotIn("token", url)
        for key in CONDITIONS:
            self.assertIn("report_year", parse_qs(urlsplit(request_urls[key]).query)["$where"][0])

    def test_mocked_original_response_is_counts_only(self):
        values = sample_counts()
        by_url = {url: json.dumps([{"count": str(values[key])}]).encode()
                  for key, url in queries().items()}
        result = run_canary(lambda url: by_url[url])
        self.assertEqual(result["counts"]["ll84_rows_with_any_four_special_case"], 3812)
        self.assertEqual(result["counts"]["pluto_taxlot_rows"], 858284)
        self.assertFalse(result["raw_source_rows_downloaded"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["insured_tiv_or_loss_calculated"])
        self.assertFalse(result["building_identity_proven"])

    def test_reject_raw_or_bad_aggregate_shapes(self):
        bad = [b"", b"{}", b"[]", b'[{"count":"1"},{"count":"2"}]',
               b'[{"count":"5","bbl":"1000000001"}]',
               b'[{"count":5}]', b'[{"count":true}]',
               b'[{"count":"-1"}]', b'[{"count":"1.5"}]',
               b'[{"count":"NaN"}]', b'[{"count":"100000001"}]',
               b'[{"count":null}]', b'["count"]',
               b'[{"count":"1"}]' + b' ' * 5000]
        for body in bad:
            with self.subTest(body=body[:40]), self.assertRaises(CanaryError):
                parse_count(body)
        self.assertEqual(parse_count(b'[{"count":"0"}]'), 0)

    def test_reject_host_swap_and_row_queries(self):
        correct = queries()["pluto_total"]
        for wrong in [
            correct.replace("data.cityofnewyork.us", "evil.example.org"),
            correct.replace("https:", "http:"),
            correct.replace("count%28%2A%29", "%2A"),
            correct + "&$limit=100",
            correct + "&token=secret",
        ]:
            with self.subTest(wrong=wrong), self.assertRaises(CanaryError):
                validate_query_url(wrong)

    def test_reject_impossible_or_malformed_summary(self):
        for key, bad in [
            ("pluto_total", 0),
            ("ll84_2024_total", 0),
            ("any_of_four_special_cases", 39091),
            ("multi_bin", 3813),
            ("multi_bbl", -1),
            ("multi_bbl", True),
            ("missing_bbl_literal", "219"),
        ]:
            values = sample_counts()
            values[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(CanaryError):
                analyze_counts(values)
        values = sample_counts()
        values["any_of_four_special_cases"] = 2
        with self.assertRaises(CanaryError):
            analyze_counts(values)
        values = sample_counts()
        values["unknown"] = 0
        with self.assertRaises(CanaryError):
            analyze_counts(values)

    def test_overlap_is_not_sum_and_does_not_prove_matchability(self):
        result = analyze_counts(sample_counts())
        c = result["counts"]
        self.assertLess(c["ll84_rows_with_any_four_special_case"],
                        sum(c["individual_overlapping_categories"].values()))
        self.assertFalse(result["ll84_covers_entire_building_stock"])
        self.assertTrue(result["special_cases_can_overlap"])


if __name__ == "__main__":
    unittest.main()
