# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.windstorm_europe_financial_years_v0 import aggregate

class FinancialYearsTests(unittest.TestCase):
    def test_cross_country_occurrence_then_treaty_and_zero_year(self):
        policies={p:dict(deductible_eur=10,limit_eur=100) for p in ('DE','FR')}
        r=aggregate([1,2],[dict(year_id=1,occurrence_id='storm-a',sampled_policy_ground_up_eur={'DE':80,'FR':50}),
                           dict(year_id=1,occurrence_id='storm-b',sampled_policy_ground_up_eur={'DE':30})],
                    policies,dict(attachment_eur=50,limit_eur=40))
        self.assertEqual(r['years'][0]['gross_annual_eur'],130)
        self.assertEqual(r['years'][0]['net_annual_eur'],90)
        self.assertEqual(r['years'][0]['gross_max_event_eur'],110)
        self.assertEqual(r['years'][1]['gross_annual_eur'],0)
        self.assertEqual(r['metrics']['gross']['sample_mean_annual_loss_eur'],65)
        ep=next(x for x in r['metrics']['gross']['empirical_ep'] if x['threshold_eur']==110)
        self.assertEqual(ep['AEP_strict'],.5);self.assertEqual(ep['OEP_strict'],0)

    def test_duplicate_occurrence_and_unknown_policy_rejected(self):
        event=dict(year_id=1,occurrence_id='a',sampled_policy_ground_up_eur={'DE':20})
        p={'DE':dict(deductible_eur=0,limit_eur=100)};t=dict(attachment_eur=0,limit_eur=0)
        with self.assertRaises(ValueError):aggregate([1],[event,event],p,t)
        with self.assertRaises(ValueError):aggregate([1],[event],{},t)
        with self.assertRaises(ValueError):aggregate([1,1],[],p,t)
