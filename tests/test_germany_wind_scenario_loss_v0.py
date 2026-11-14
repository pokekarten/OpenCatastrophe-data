# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.germany_wind_scenario_loss_v0 import damage_ratio,calculate
from tests.test_climk_building_hazard_join_v0 import cell

class WindScenarioTests(unittest.TestCase):
    def test_separate_interpolation_before_product(self):
        self.assertAlmostEqual(damage_ratio(30,[(20,0,0),(40,1,1)]),0.25)
        for gust in (19,41,float('nan')):
            with self.assertRaises(ValueError): damage_ratio(gust,[(20,0,0),(40,1,1)])

    def test_multicell_loss_conserves_values_and_blocks_missing(self):
        hazard={'features':[cell(6,1,30),cell(7,2,40)],'metadata':{}}
        portfolio=[dict(building_id='a',longitude=6.5,latitude=50.5,building_value_eur=100),
                   dict(building_id='b',longitude=7.5,latitude=50.5,building_value_eur=200)]
        r=calculate(hazard,portfolio,[(20,0,0),(40,1,1)])
        self.assertEqual(r['expected_ground_up_loss_eur'],225)
        self.assertEqual(r['building_value_eur'],300)
        self.assertEqual(len(r['cell_aggregates']),2)
        hazard['features'][1]=cell(7,2,None)
        with self.assertRaises(ValueError): calculate(hazard,portfolio,[(20,0,0),(40,1,1)])
