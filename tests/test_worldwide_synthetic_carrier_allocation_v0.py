# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only tests for non-admitted worldwide insurer cohort allocation."""

import copy
import unittest

from research_runners.worldwide_synthetic_carrier_allocation_v0 import InvalidPortfolio, allocate


A = "a" * 64
B = "b" * 64


def fixture():
    return {
        "carrier": {"carrier_id": "fictional-de-carrier", "legal_scope": "solo",
                    "country_code": "DE", "as_of": "2025-12-31", "coverage_class": "residential_building",
                    "observed_policy_count": 11, "source_url": "https://example.org/official-report",
                    "source_sha256": A, "source_measure": "carrier_reported_policy_count"},
        "physical_proxy": {"as_of": "2022-05-15", "source_url": "https://example.org/physical-stock",
                           "source_sha256": B, "proxy_measure": "non_insurer_physical_building_count",
                           "regions": [{"region_id": "DE-BY", "building_count": 2},
                                       {"region_id": "DE-NW", "building_count": 1},
                                       {"region_id": "DE-HE", "building_count": 1}]},
        "scenarios": [{"scenario_id": "uniform", "description": "Fictional equal physical opportunity",
                       "regional_factors": {"DE-BY": "1", "DE-NW": "1", "DE-HE": "1"}},
                      {"scenario_id": "south", "description": "Fictional doubled south selection",
                       "regional_factors": {"DE-BY": "2", "DE-NW": "1", "DE-HE": "1"}}]
    }


class AllocationTests(unittest.TestCase):
    def test_two_scenarios_and_tie_break(self):
        result = allocate(fixture())
        self.assertEqual(result["scenarios"][0]["allocation"], [
            {"region_id": "DE-BY", "synthetic_policy_count": 5},
            {"region_id": "DE-HE", "synthetic_policy_count": 3},
            {"region_id": "DE-NW", "synthetic_policy_count": 3}])
        self.assertEqual(result["scenarios"][1]["allocation"], [
            {"region_id": "DE-BY", "synthetic_policy_count": 7},
            {"region_id": "DE-HE", "synthetic_policy_count": 2},
            {"region_id": "DE-NW", "synthetic_policy_count": 2}])
        self.assertTrue(result["scenario_sensitivity_available"])
        self.assertFalse(result["model_ready"])
        self.assertFalse(result["source_bytes_verified"])
        self.assertNotIn("tiv", result)

    def test_deterministic_independent_of_region_order(self):
        a = fixture()
        b = copy.deepcopy(a)
        b["physical_proxy"]["regions"].reverse()
        self.assertEqual(allocate(a), allocate(b))

    def test_zero_policies_and_zero_stock_cell(self):
        d = fixture()
        d["carrier"]["observed_policy_count"] = 0
        d["physical_proxy"]["regions"][1]["building_count"] = 0
        for s in allocate(d)["scenarios"]:
            self.assertEqual(s["total_synthetic_policies"], 0)

    def test_many_carriers_are_separate(self):
        a = fixture()
        b = fixture()
        b["carrier"]["carrier_id"] = "fictional-other-carrier"
        b["carrier"]["observed_policy_count"] = 37
        self.assertEqual(allocate(a)["scenarios"][0]["total_synthetic_policies"], 11)
        self.assertEqual(allocate(b)["scenarios"][0]["total_synthetic_policies"], 37)

    def test_invalid_inputs_fail_closed(self):
        cases = []
        def bad(path, value):
            d = fixture()
            ptr = d
            for key in path[:-1]:
                ptr = ptr[key]
            ptr[path[-1]] = value
            cases.append(d)
        bad(["carrier", "observed_policy_count"], True)
        bad(["carrier", "observed_policy_count"], -1)
        bad(["carrier", "observed_policy_count"], 1.5)
        bad(["carrier", "source_measure"], "gross_written_premium")
        bad(["carrier", "source_sha256"], "not-a-hash")
        bad(["carrier", "source_url"], "http://bad.invalid")
        bad(["carrier", "country_code"], "USA")
        bad(["carrier", "legal_scope"], "unknown")
        bad(["physical_proxy", "proxy_measure"], "insured_locations")
        bad(["physical_proxy", "regions"], [])
        bad(["physical_proxy", "regions"], [{"region_id": "FR-IDF", "building_count": 1}])
        bad(["scenarios", 0, "regional_factors", "DE-BY"], "-1")
        bad(["scenarios", 0, "regional_factors", "DE-BY"], 1.0)
        bad(["scenarios", 0, "regional_factors", "DE-BY"], "NaN")
        bad(["scenarios", 0, "regional_factors"], {"DE-BY": "1"})
        bad(["scenarios", 0, "description"], " ")
        bad(["scenarios"], [])
        bad(["scenarios", 1, "scenario_id"], "uniform")
        bad(["carrier", "as_of"], "2025-13-01")
        bad(["carrier", "as_of"], "2025-02-31")
        bad(["physical_proxy", "source_url"], "https://")
        bad(["carrier", "premium"], 100)
        for index, case in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(InvalidPortfolio):
                allocate(case)

    def test_duplicate_and_all_zero_denominator(self):
        a = fixture()
        a["physical_proxy"]["regions"][1]["region_id"] = "DE-BY"
        with self.assertRaises(InvalidPortfolio):
            allocate(a)
        b = fixture()
        for r in b["physical_proxy"]["regions"]:
            r["building_count"] = 0
        with self.assertRaises(InvalidPortfolio):
            allocate(b)
        c = fixture()
        for s in c["scenarios"]:
            s["regional_factors"] = {r: "0" for r in s["regional_factors"]}
        with self.assertRaises(InvalidPortfolio):
            allocate(c)


if __name__ == "__main__":
    unittest.main()
