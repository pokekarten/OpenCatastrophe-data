# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.windstorm_europe_damage_samples_v0 import sample_policy_losses,uniform
from research_runners.windstorm_europe_financial_years_v0 import aggregate

class DamageSamplesTests(unittest.TestCase):
    def test_reordering_seed_and_marginal_response(self):
        sites=[dict(building_id=str(i),policy_id=str(i),dependence_group=str(i),building_value_eur=100,gust_mps=30) for i in range(2)]
        curve=[(20,0,0),(40,1,1)]
        kwargs=dict(seed=7,sample_id=2,occurrence_id='kyrill')
        self.assertEqual(sample_policy_losses(sites,curve,**kwargs),sample_policy_losses(list(reversed(sites)),curve,**kwargs))
        self.assertNotEqual(uniform(7,2,'kyrill','0'),uniform(8,2,'kyrill','0'))
        mean=sum(sample_policy_losses(sites[:1],curve,seed=7,sample_id=i,occurrence_id='kyrill')['0'] for i in range(10000))/10000
        self.assertAlmostEqual(mean,25,delta=1)

    def test_shared_group_and_policy_financial_bridge(self):
        sites=[dict(building_id=str(i),policy_id='joint',dependence_group='shared',building_value_eur=100,gust_mps=40) for i in range(2)]
        losses=sample_policy_losses(sites,[(0,0,0),(40,1,.5)],seed=1,sample_id=0,occurrence_id='storm')
        self.assertEqual(losses,{'joint':100})
        r=aggregate([1,2],[dict(year_id=1,occurrence_id='storm',sampled_policy_ground_up_eur=losses)],
                    {'joint':dict(deductible_eur=10,limit_eur=200)},dict(attachment_eur=50,limit_eur=20))
        self.assertEqual(r['occurrences'][0]['gross_eur'],90)
        self.assertEqual(r['occurrences'][0]['net_eur'],70)

    def test_missing_group_and_extrapolation_rejected(self):
        site=dict(building_id='a',policy_id='a',dependence_group='',building_value_eur=100,gust_mps=20)
        with self.assertRaises(ValueError):sample_policy_losses([site],[(0,0,0),(40,1,1)],seed=1,sample_id=0,occurrence_id='a')
        site['dependence_group']='a';site['gust_mps']=41
        with self.assertRaises(ValueError):sample_policy_losses([site],[(0,0,0),(40,1,1)],seed=1,sample_id=0,occurrence_id='a')
