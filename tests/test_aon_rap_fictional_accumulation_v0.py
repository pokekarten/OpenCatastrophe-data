# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""All cases fictional; no vendor score, annual event rate or real insured asset."""

import copy
import json
import unittest

from research.aon_rap_fictional_accumulation_v0 import (
    SyntheticAccumulationError, compare, example,
)


class FictionalUnderwriterComparisonTests(unittest.TestCase):
    def setUp(self):
        self.h = {"event_id": "FICTIONAL_STORM_1", "version": "toy-hazard-v1",
                  "damage_bps_by_zone": {"HIGH": 3000, "LOW": 500}}
        c = {"currency": "EUR", "deductible_cents": 25000, "limit_cents": 5000000}
        self.base = [
            {**c, "location_id": "BH", "policy_id": "BH", "zone": "HIGH", "tiv_cents": 10000000},
            {**c, "location_id": "BL", "policy_id": "BL", "zone": "LOW", "tiv_cents": 10000000},
        ]
        self.a = {**c, "location_id": "AH", "policy_id": "AH", "zone": "HIGH", "tiv_cents": 5000000}
        self.b = {**c, "location_id": "AL", "policy_id": "AL", "zone": "LOW", "tiv_cents": 5000000}

    def run_comparison(self):
        return compare(self.base, self.a, self.b, self.h)

    def test_before_after_loss_and_tiv_are_exact_cents(self):
        r = self.run_comparison()
        self.assertEqual(r["baseline"]["tiv_cents"], 20000000)
        self.assertEqual(r["baseline"]["gross_cents"], 3500000)
        self.assertEqual(r["baseline"]["insured_cents"], 3450000)
        self.assertEqual(r["proposals"]["A"]["delta"],
                         {"tiv_cents": 5000000, "gross_cents": 1500000, "insured_cents": 1475000})
        self.assertEqual(r["proposals"]["B"]["delta"],
                         {"tiv_cents": 5000000, "gross_cents": 250000, "insured_cents": 225000})
        self.assertEqual(r["proposals"]["A"]["post"]["insured_cents"], 4925000)
        self.assertEqual(r["proposals"]["B"]["post"]["insured_cents"], 3675000)

    def test_scenario_never_becomes_annual_ep_or_vendor_score(self):
        r = self.run_comparison()
        self.assertEqual(r["risk_metric_kind"], "conditional_scenario")
        self.assertFalse(r["annual_ep_admitted"])
        self.assertFalse(r["aon_data_or_score_used"])
        self.assertFalse(r["actual_insurer_data_used"])
        self.assertFalse(r["source_original_bytes_verified"])
        self.assertEqual(len(r["fictional_fixture_sha256"]), 64)
        self.assertEqual(r, self.run_comparison())
        self.assertEqual(r, json.loads(json.dumps(r)))

    def test_rejects_missing_hazard_zone_including_candidate(self):
        for zone in ("HIGH", "LOW"):
            with self.subTest(zone=zone):
                h = copy.deepcopy(self.h)
                del h["damage_bps_by_zone"][zone]
                with self.assertRaisesRegex(SyntheticAccumulationError, "footprint"):
                    compare(self.base, self.a, self.b, h)

    def test_rejects_duplicate_keys_and_wrong_currency(self):
        for field in ("location_id", "policy_id"):
            with self.subTest(field=field):
                a = {**self.a, field: self.base[0][field]}
                with self.assertRaisesRegex(SyntheticAccumulationError, "duplicate"):
                    compare(self.base, a, self.b, self.h)
        a = {**self.a, "currency": "GBP"}
        with self.assertRaisesRegex(SyntheticAccumulationError, "EUR"):
            compare(self.base, a, self.b, self.h)

    def test_rejects_incompatible_proposals(self):
        for field, value in (("tiv_cents", 4000000), ("deductible_cents", 0),
                             ("limit_cents", 10000), ("zone", "HIGH")):
            with self.subTest(field=field):
                with self.assertRaises(SyntheticAccumulationError):
                    compare(self.base, self.a, {**self.b, field: value}, self.h)

    def test_rejects_invalid_money_and_rates_without_coercion(self):
        for bad in (-1, 0.0, True, "0", 10**15 + 1):
            with self.subTest(money=bad):
                with self.assertRaises(SyntheticAccumulationError):
                    compare(self.base, {**self.a, "tiv_cents": bad}, self.b, self.h)
        for bad in (-1, 10001, 5.1, True, "2000"):
            with self.subTest(rate=bad):
                h = copy.deepcopy(self.h)
                h["damage_bps_by_zone"]["HIGH"] = bad
                with self.assertRaises(SyntheticAccumulationError):
                    compare(self.base, self.a, self.b, h)

    def test_rejects_annualization_or_multiple_events_as_input(self):
        for injected in ({"annual_ep": 10000}, {"annual_ep_admitted": True},
                         {"loss_rate": 0.1}):
            with self.subTest(injected=injected):
                with self.assertRaises(SyntheticAccumulationError):
                    compare(self.base, {**self.a, **injected}, self.b, self.h)
        with self.assertRaises(SyntheticAccumulationError):
            compare(self.base, self.a, self.b, {**self.h, "event_roster": ["other"]})

    def test_source_and_input_identity_affect_fixture_digest_without_mutation(self):
        input_snapshot = copy.deepcopy((self.base, self.a, self.b, self.h))
        before = self.run_comparison()["fictional_fixture_sha256"]
        changed = copy.deepcopy(self.h)
        changed["version"] = "toy-hazard-v2"
        after = compare(self.base, self.a, self.b, changed)["fictional_fixture_sha256"]
        self.assertNotEqual(before, after)
        self.assertEqual(input_snapshot, (self.base, self.a, self.b, self.h))
        self.assertEqual(example()["risk_metric_kind"], "conditional_scenario")


if __name__ == "__main__":
    unittest.main()
