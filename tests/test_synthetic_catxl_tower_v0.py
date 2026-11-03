# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict, independent synthetic-only multi-layer loss arithmetic regression tests."""
import copy
import json
import unittest

from research_runners.synthetic_catxl_tower_v0 import (
    ToyTowerInputError, calculate_toy_tower, fictional_example,
)


class SyntheticTowerTests(unittest.TestCase):
    def setUp(self):
        self.pos, self.ev, self.ct = fictional_example()

    def result(self):
        return calculate_toy_tower(self.pos, self.ev, self.ct)

    def assert_rejects(self):
        with self.assertRaises(ToyTowerInputError):
            self.result()

    def test_exact_reconciliation(self):
        r = self.result()
        self.assertEqual((r["gross_eur"],r["ceded_eur"],r["net_insured_loss_eur"]),
                         (2000000, 1100000, 900000))
        self.assertEqual([x["ceded_eur"] for x in r["events"]], [0,200000,700000,200000])
        self.assertEqual([x["net_insured_loss_eur"] for x in r["events"]], [100000,200000,200000,400000])
        for event in r["events"]:
            self.assertEqual(event["gross_eur"],event["ceded_eur"]+event["net_insured_loss_eur"])
            self.assertEqual(sum(x["ceded_eur"] for x in event["layers"]),event["ceded_eur"])
        self.assertEqual(sum(x["ceded_eur"] for x in r["layers"]),r["ceded_eur"])

    def test_layer_totals_and_perils(self):
        r = self.result()
        self.assertEqual([x["ceded_eur"] for x in r["layers"]], [400000,500000,200000])
        self.assertEqual([x["ceded_eur"] for x in r["events"][1]["layers"]], [200000,0,0])
        self.assertFalse(r["events"][1]["layers"][1]["covered"])
        self.assertEqual([x["ceded_eur"] for x in r["events"][2]["layers"]], [200000,300000,200000])
        self.assertEqual([x["ceded_eur"] for x in r["events"][3]["layers"]], [0,200000,0])

    def test_reinstatement_premiums_and_cash_bases(self):
        r = self.result()
        self.assertEqual([x["reinstatement_premium_cents"] for x in r["layers"]], [2500000,1000000,0])
        self.assertEqual([x["reinstatement_premium_cents"] for x in r["events"]], [0,0,2500000,1000000])
        self.assertEqual(r["reinstatement_premium_cents"],3500000)
        self.assertEqual(r["base_premium_cents"],9500000)
        self.assertEqual(r["net_plus_reinstatement_premium_cents"],93500000)
        self.assertEqual(r["net_plus_all_toy_premiums_cents"],103000000)

    def test_loss_max_per_asset_each_event(self):
        self.ev[0]["losses_eur"]["SYNTH-01"]=125001
        self.assert_rejects()

    def test_duplicate_events(self):
        self.ev[1]["event_id"]=self.ev[0]["event_id"]
        self.assert_rejects()

    def test_event_out_of_order(self):
        self.ev[1]["date"]="2026-11-01"
        self.assert_rejects()

    def test_event_same_day_rejected(self):
        self.ev[1]["date"]=self.ev[0]["date"]
        self.assert_rejects()

    def test_date_cross_year_and_wrong_format(self):
        for date in ("2025-11-02","2027-01-01","2026-11-2","2026-14-55","2026-11-01"):
            with self.subTest(date=date):
                ev=copy.deepcopy(self.ev);ev[0]["date"]=date
                with self.assertRaises(ToyTowerInputError):
                    calculate_toy_tower(self.pos,ev,self.ct)

    def test_extra_contract_field(self):
        self.ct["cedent"]="REAL COMPANY"
        self.assert_rejects()

    def test_non_synthetic_policy_rejected(self):
        self.ct["synthetic_only"]=False
        self.assert_rejects()

    def test_layer_name_must_be_fictional(self):
        self.ct["layers"][0]["layer_id"]="REAL"
        self.assert_rejects()

    def test_no_duplicate_layers(self):
        self.ct["layers"][1]["layer_id"]=self.ct["layers"][0]["layer_id"]
        self.assert_rejects()

    def test_overlap_rejected(self):
        self.ct["layers"][1]["attachment_eur"]=399999
        self.assert_rejects()

    def test_layer_reversal_rejected(self):
        self.ct["layers"].reverse()
        self.assert_rejects()

    def test_missing_and_malformed_layers(self):
        for layers in ([],None,"layers",[{}]):
            with self.subTest(layers=layers):
                c=copy.deepcopy(self.ct);c["layers"]=layers
                with self.assertRaises(ToyTowerInputError):
                    calculate_toy_tower(self.pos,self.ev,c)

    def test_uncovered_flood_event_preserves_l2_capacity(self):
        r=self.result()
        self.assertEqual(r["events"][1]["layers"][1]["aggregate_remaining_before_eur"],600000)
        self.assertEqual(r["events"][1]["layers"][1]["aggregate_remaining_after_eur"],600000)

    def test_no_reinstatement_l1_capacity_exhausts(self):
        self.ct["layers"][0]["reinstatements"]=0
        r=self.result()
        self.assertEqual(r["layers"][0]["ceded_eur"],200000)
        self.assertEqual(r["layers"][0]["reinstatement_premium_cents"],0)
        self.assertEqual(r["ceded_eur"],900000)

    def test_partial_ri_rate_sensitivity(self):
        self.ct["layers"][1]["reinstatement_rate_bps"]=10000
        r=self.result()
        self.assertEqual(r["layers"][1]["reinstatement_premium_cents"],2000000)
        self.assertEqual(r["reinstatement_premium_cents"],4500000)

    def test_earned_ri_no_charge_before_reinstated_capacity_is_used(self):
        self.ev=self.ev[:1]
        self.assertEqual(self.result()["reinstatement_premium_cents"],0)

    def test_deep_copy_determinism(self):
        r=self.result()
        self.assertEqual(r,calculate_toy_tower(copy.deepcopy(self.pos),copy.deepcopy(self.ev),copy.deepcopy(self.ct)))
        self.assertEqual(json.dumps(r,sort_keys=True),json.dumps(self.result(),sort_keys=True))

    def test_no_mutation(self):
        before=copy.deepcopy((self.pos,self.ev,self.ct))
        self.result()
        self.assertEqual(before,(self.pos,self.ev,self.ct))

    def test_negative_and_type_confused_loss(self):
        for value in (-1,10.5,True,"5000",None,10**14):
            with self.subTest(value=value):
                ev=copy.deepcopy(self.ev);ev[0]["losses_eur"]["SYNTH-01"]=value
                with self.assertRaises(ToyTowerInputError):
                    calculate_toy_tower(self.pos,ev,self.ct)

    def test_wrong_treaty_terms_and_price_basis(self):
        for field,value in (("currency","USD"),("basis","net_of_prior_layer"),
                            ("reinstatement_premium_convention","unknown"),("year",2025),
                            ("as_of_date","2027-01-01")):
            with self.subTest(field=field):
                c=copy.deepcopy(self.ct);c[field]=value
                with self.assertRaises(ToyTowerInputError):
                    calculate_toy_tower(self.pos,self.ev,c)

    def test_invalid_reinstatements_and_rates(self):
        for field,value in (("reinstatements",-1),("reinstatements",4),
                            ("reinstatement_rate_bps",-1),("reinstatement_rate_bps",20001),
                            ("limit_eur",0),("base_premium_cents",-1)):
            with self.subTest(field=field):
                c=copy.deepcopy(self.ct);c["layers"][0][field]=value
                with self.assertRaises(ToyTowerInputError):
                    calculate_toy_tower(self.pos,self.ev,c)

    def test_bad_peril_lists_and_unsupported_event_peril(self):
        for covered in (["windstorm","flood"],["flood","flood"],["earthquake"],[1,"flood"],[],None):
            with self.subTest(covered=covered):
                c=copy.deepcopy(self.ct);c["layers"][0]["covered_perils"]=covered
                with self.assertRaises(ToyTowerInputError):
                    calculate_toy_tower(self.pos,self.ev,c)
        self.ev[0]["peril"]="earthquake"
        self.assert_rejects()

    def test_unknown_unit_rejected(self):
        self.ev[0]["losses_eur"]={"SYNTH-INVALID":5}
        self.assert_rejects()

    def test_non_synthetic_unit_rejected(self):
        self.pos={"REAL-001":100000}
        self.assert_rejects()

    def test_gross_with_gaps_between_nonoverlap_layers(self):
        self.ct["layers"][2]["attachment_eur"]=1000000
        r=self.result()
        self.assertLessEqual(r["ceded_eur"],r["gross_eur"])
        self.assertEqual(r["layers"][2]["ceded_eur"],0)

    def test_cumulative_ri_premium_rounding_invariant(self):
        # Cumulative half-up cents avoid per-event rounding drift.
        pos={"SYNTH-01":1000}
        ct={"synthetic_only":True,"currency":"EUR","year":2026,
            "as_of_date":"2026-11-01","basis":"independent_gross_occurrence",
            "reinstatement_premium_convention":"toy_consumed_reinstated_limit_pro_rata_no_time",
            "layers":[{"layer_id":"FICTIONAL-ONLY","attachment_eur":0,"limit_eur":3,
                       "reinstatements":1,"base_premium_cents":101,
                       "reinstatement_rate_bps":10000,"covered_perils":["flood"]}]}
        events=[{"event_id":f"FICTIONAL-{i}","date":f"2026-11-0{i}",
                 "peril":"flood","losses_eur":{"SYNTH-01":2}} for i in (2,3,4,5)]
        result=calculate_toy_tower(pos,events,ct)
        self.assertEqual(result["ceded_eur"],6)
        self.assertEqual(result["reinstatement_premium_cents"],101)
        self.assertEqual(sum(e["reinstatement_premium_cents"] for e in result["events"]),101)


if __name__=="__main__":
    unittest.main()
