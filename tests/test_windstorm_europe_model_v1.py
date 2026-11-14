# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import hashlib
from pathlib import Path
import tempfile
import unittest
from research_runners.windstorm_europe_model_v1 import execute
from tests.test_climk_building_hazard_join_v0 import cell

class IntegratedEuropeTests(unittest.TestCase):
    def test_class_specific_policy_aggregation_and_zero_year(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=b'wind speed,weak,strong\n0,0,0\n40,100,50\n'
            (root/'curve.csv').write_bytes(raw)
            spec=lambda c:dict(path='curve.csv',sha256=hashlib.sha256(raw).hexdigest(),kind='construction_percent_deterministic',column=c)
            c=dict(profile='windstorm-europe-research-v1',annual_schedule_basis='explicit_user_scenario_not_calibrated',seed=7,bounds=[5,45,16,56],
                   responses={'weak':spec('weak'),'strong':spec('strong')},
                   buildings=[dict(building_id='de',policy_id='joint',country='DE',dependence_group='de',response_id='weak',longitude=6.5,latitude=50.5,building_value_eur=100),
                              dict(building_id='fr',policy_id='joint',country='FR',dependence_group='fr',response_id='strong',longitude=7.5,latitude=50.5,building_value_eur=100)],
                   policies={'joint':dict(deductible_eur=10,limit_eur=200)},treaty=dict(attachment_eur=100,limit_eur=20),year_ids=[1,2],
                   occurrences=[dict(year_id=1,occurrence_id='storm',sample_id=0,storm_index=0)])
            loader=lambda i:dict(features=[cell(6,1,40),cell(7,2,40)],metadata={'storm_index':i})
            r=execute(c,root,loader)
            self.assertEqual(r['occurrences'][0]['gross_eur'],140)
            self.assertEqual(r['occurrences'][0]['net_eur'],120)
            self.assertEqual(r['metrics']['gross']['sample_mean_annual_loss_eur'],70)
            self.assertEqual(r['countries'],['DE','FR'])
            c['buildings'][1]['response_id']='unknown'
            with self.assertRaises(ValueError):execute(c,root,loader)
