# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic-only negative-regression tests for NYC source identity."""

import copy
import unittest
from research_runners.nyc_pluto_ll84_linkage_v0 import analyze, LinkageError


def fixture():
    return {
        "pluto_release": "26v2",
        "pluto_rows": [
            {"bbl": "1008450027", "num_buildings": 1},
            {"bbl": "2001000001", "num_buildings": 2},
        ],
        "ll84_rows": [
            {"property_id": "12345", "calendar_year": 2024,
             "bbls": "1008450027", "bins": "1001234"},
        ],
    }


class TestLinkage(unittest.TestCase):
    def test_clean_candidate_not_actual_match_or_insured_value(self):
        result = analyze(fixture())
        self.assertEqual(result["reason_counts"], {"unverified_single_bbl_bin_candidate": 1})
        self.assertEqual(result["candidate_property_years"], {"2024": 1})
        self.assertFalse(result["building_identity_proven"])
        self.assertFalse(result["insured_tiv_or_loss_calculated"])
        self.assertFalse(result["raw_identifiers_exported"])
        self.assertNotIn("1008450027", str(result))
        self.assertNotIn("12345", str(result))

    def test_deterministic(self):
        self.assertEqual(analyze(fixture()), analyze(copy.deepcopy(fixture())))

    def test_multibbl_property(self):
        x = fixture()
        x["ll84_rows"][0]["bbls"] = "1008450027;2001000001"
        self.assertEqual(analyze(x)["reason_counts"], {"multi_taxlot_campus": 1})

    def test_multibin_property(self):
        x = fixture()
        x["ll84_rows"][0]["bins"] = "1001234;1005678"
        self.assertEqual(analyze(x)["reason_counts"], {"multi_bin_campus": 1})

    def test_multi_building_pluto_lot(self):
        x = fixture()
        x["ll84_rows"][0]["bbls"] = "2001000001"
        self.assertEqual(analyze(x)["reason_counts"], {"pluto_multibuilding_or_unknown": 1})

    def test_same_bbl_cannot_be_matched_to_two_properties_in_same_year(self):
        x = fixture()
        x["ll84_rows"].append({"property_id": "67890", "calendar_year": 2024,
                               "bbls": "1008450027", "bins": "1005678"})
        self.assertEqual(analyze(x)["reason_counts"], {"shared_bbl_same_year": 2})
        self.assertEqual(analyze(x)["candidate_property_years"], {})

    def test_cross_year_repeated_bbl_does_not_double_count_within_year(self):
        x = fixture()
        x["ll84_rows"].append({"property_id": "12345", "calendar_year": 2025,
                               "bbls": "1008450027", "bins": "1001234"})
        self.assertEqual(analyze(x)["candidate_property_years"], {"2024": 1, "2025": 1})

    def test_missing_identifiers_are_explicit(self):
        x = fixture()
        x["ll84_rows"][0]["bbls"] = ""
        self.assertEqual(analyze(x)["reason_counts"], {"missing_bbl": 1})
        x["ll84_rows"][0]["bbls"] = "1008450027"
        x["ll84_rows"][0]["bins"] = ""
        self.assertEqual(analyze(x)["reason_counts"], {"missing_bin": 1})

    def test_missing_in_pluto_subset_not_zero_buildings(self):
        x = fixture()
        x["ll84_rows"][0]["bbls"] = "3008450027"
        self.assertEqual(analyze(x)["reason_counts"], {"bbl_absent_from_supplied_pluto": 1})

    def test_bad_ids_duplicate_tokens_and_bad_years_fail_closed(self):
        for field, bad in [("bbls", "1008450027;1008450027"),
                           ("bbls", "1008450027;bad"),
                           ("bbls", "1008450027;"),
                           ("bins", "1001234;1001234"),
                           ("bins", "1001234,1005678"),
                           ("bins", "9999999")]:
            x = fixture()
            x["ll84_rows"][0][field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(LinkageError):
                analyze(x)
        for year in [2021, 2027, "2024", True]:
            x = fixture()
            x["ll84_rows"][0]["calendar_year"] = year
            with self.subTest(year=year), self.assertRaises(LinkageError):
                analyze(x)

    def test_duplicate_source_records_and_extra_fields_rejected(self):
        x = fixture()
        x["pluto_rows"].append(copy.deepcopy(x["pluto_rows"][0]))
        with self.assertRaises(LinkageError):
            analyze(x)
        x = fixture()
        x["ll84_rows"].append(copy.deepcopy(x["ll84_rows"][0]))
        with self.assertRaises(LinkageError):
            analyze(x)
        x = fixture()
        x["pluto_rows"][0]["insurer"] = "invented"
        with self.assertRaises(LinkageError):
            analyze(x)
        x = fixture()
        x["ll84_rows"][0]["owner_name"] = "forbidden"
        with self.assertRaises(LinkageError):
            analyze(x)

    def test_bad_counts_release_and_bounds(self):
        for val in [-1, True, "1"]:
            x = fixture()
            x["pluto_rows"][0]["num_buildings"] = val
            with self.assertRaises(LinkageError):
                analyze(x)
        x = fixture()
        x["pluto_release"] = "26v1"
        with self.assertRaises(LinkageError):
            analyze(x)
        x = fixture()
        x["ll84_rows"] = x["ll84_rows"] * 10001
        with self.assertRaises(LinkageError):
            analyze(x)


if __name__ == "__main__":
    unittest.main()
