# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent artificial one-event financial hierarchy/seed tests; no insurer."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import xws_kyrill_nrw10k_fictional_policy_ri_event_mc_v0 as m
from xws_kyrill_nrw10k_schwierz_conditional_loss_v0 import site_loss_cents


def tiny_source():
    winds=[]
    values={}
    for i,(gust,tiv,county) in enumerate(((30,100000,"05362"),(25,50000,"05774"),(42,300000,"05974")),1):
        ident=f"FICT-TEST-NOT-INSURED-{i}"
        values[ident]=(tiv,county)
        winds.append({
            "FictionalLocNumber":ident,"KreisAGS2022":county,
            "KyrillRecalMeanGustMS":str(gust),
            "IsActualRVInsuredSite":"false","WindVulnerabilityCalibrated":"false",
        })
    reference=sum(site_loss_cents(Decimal(w["KyrillRecalMeanGustMS"]),
              values[w["FictionalLocNumber"]][0],Decimal("1")) for w in winds)
    return winds,values,reference


class EventFinancialMcTests(unittest.TestCase):
    def test_simple_site_deductible_then_limit_then_qs(self):
        q=m.financial_tower([1000*100])
        self.assertEqual(q["groundup_cents"],100000)
        self.assertEqual(q["insured_before_reinsurance_cents"],75000)
        self.assertEqual(q["quota_share_ceded_cents"],15000)
        self.assertEqual(q["quota_share_retained_before_xl_cents"],60000)
        self.assertEqual(q["occurrence_xl_recovery_cents"],0)
        self.assertEqual(q["insurer_net_after_qs_xl_cents"],60000)

    def test_cat_xl_attaches_to_event_retained_not_groundup_or_expected(self):
        # Ten 10,000 EUR per-risk damages: after 250 deductible and 20% QS,
        # event retention = 10*7,800 = 78,000; 250k xs 15k XL pays 63k.
        q=m.financial_tower([10000*100]*10)
        self.assertEqual(q["groundup_cents"],10000000)
        self.assertEqual(q["insured_before_reinsurance_cents"],9750000)
        self.assertEqual(q["quota_share_ceded_cents"],1950000)
        self.assertEqual(q["quota_share_retained_before_xl_cents"],7800000)
        self.assertEqual(q["occurrence_xl_recovery_cents"],6300000)
        self.assertEqual(q["insurer_net_after_qs_xl_cents"],1500000)
        self.assertEqual(sum(q[k] for k in ("quota_share_ceded_cents",
                    "occurrence_xl_recovery_cents","insurer_net_after_qs_xl_cents")),
                    q["insured_before_reinsurance_cents"])

    def test_policy_limit_and_cat_xl_cap_enforced(self):
        q=m.financial_tower([10000000]*50)
        self.assertEqual(q["insured_before_reinsurance_cents"],50*50000*100)
        self.assertEqual(q["occurrence_xl_recovery_cents"],250000*100)
        self.assertEqual(q["insurer_net_after_qs_xl_cents"],
                         (50*50000*100*80//100)-250000*100)
        self.assertLessEqual(q["insured_before_reinsurance_cents"],q["groundup_cents"])

    def test_disallows_negative_or_noninteger_gul_and_wrong_probabilities(self):
        for xs in ([],[-1],[1.5],[0]*10001):
            with self.subTest(xs=xs[:2]),self.assertRaises(m.EventModelBlocked):
                m.financial_tower(xs)
        for share in (-1,0.24,1):
            with self.subTest(share=share),self.assertRaises(m.EventModelBlocked):
                m.one_scenario([("x",0.5,100)],share_weight=share,seed=42,trials=10)
        with self.assertRaises(m.EventModelBlocked):
            m.one_scenario([("x",0.5,100)],share_weight=0,seed=42,trials=0)

    def test_original_schwierz_site_mean_reconciled_to_two_point_law(self):
        w,v,reference=tiny_source()
        with patch.object(m,"EXPECTED_N",3),patch.object(m,"REFERENCE_CONDITIONAL_GUL_CENTS",reference):
            risks,analytic=m._risk_catalogue(w,v)
        self.assertEqual(len(risks),3)
        self.assertEqual(analytic["original_Schwierz_one_event_reference_conditional_GUL_EUR"],
                         f"{Decimal(reference)/100:.2f}")
        self.assertTrue(analytic["analytical_non_annual_pre_XL_marginals_same_across_dependence"])
        for _,p,sev in risks:
            self.assertTrue(0<=p<=1)
            self.assertGreaterEqual(sev,0)

    def test_matched_stream_reproducibility_and_extreme_exact_marginal_cases(self):
        risks=[("A",1.0,100000),("B",0.0,100000),("C",1.0,200000)]
        a=m.one_scenario(risks,share_weight=0,seed=12345,trials=50)
        b=m.one_scenario(risks,share_weight=0.25,seed=12345,trials=50)
        c=m.one_scenario(risks,share_weight=0,seed=12345,trials=50)
        self.assertEqual(a,c)
        self.assertEqual(a["summary"],b["summary"])
        self.assertEqual(a["fictional_sites_affected_sample_mean"],"2.000")
        self.assertEqual(a["replicates_with_no_triggered_site"],0)
        self.assertTrue(a["statistical_outputs_are_one_event_conditional_not_annual_return_period"])

    def test_dependence_hypothesis_changes_tail_without_marginal_changed(self):
        # Many identical 20%-probability sites have a correlated mixture
        # leading to positive event tail differences, with unchanged marginals.
        risks=[(str(i),0.20,100000) for i in range(150)]
        a=m.one_scenario(risks,share_weight=0,seed=20261105,trials=1024)
        b=m.one_scenario(risks,share_weight=0.25,seed=20261105,trials=1024)
        self.assertNotEqual(a["summary"]["groundup_eur"]["q95_one_event_eur"],
                            b["summary"]["groundup_eur"]["q95_one_event_eur"])
        self.assertEqual(a["n_conditionally_simulated_replicates_of_one_Kyrill_event"],1024)
        self.assertEqual(b["share_common_uniform_mixing_weight_not_pairwise_correlation"],0.25)

    def test_event_report_nonannual_labels_and_strict_source(self):
        w,v,reference=tiny_source()
        with patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_TIV",450000),patch.object(
              m,"REFERENCE_CONDITIONAL_GUL_CENTS",reference):
            report=m.execute(w,v,trials=20,seed=20261105)
        self.assertEqual(report["historical_event_count"],1)
        self.assertEqual(report["fictional_sample_site_count"],3)
        self.assertFalse(report["gross_net_OEP_AEP_computed"])
        self.assertFalse(report["native_Oasis_or_NextGen_Kyrill_financial_loss_run"])
        self.assertFalse(report["actual_RV_policy_terms_or_reinsurance_observed"])
        self.assertEqual(len(report["scenario_results"]),2)
        self.assertEqual(report["fixed_rng_seed_specific_to_this_toy_not_FFBK_RIM"],20261105)
        self.assertIn("Bernoulli",report["invented_secondary_uncertainty"])
        self.assertNotIn("annual_ep",json.dumps(report).lower())


if __name__=="__main__":
    unittest.main()
