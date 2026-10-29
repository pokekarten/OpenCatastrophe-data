# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import copy
import unittest
from research_runners.regional_exposure_hazard_join_v0 import InputError, join


def example():
    return {
        'exposures': [
            {'record_id': 'SYNTH-EX-1', 'dataset_id': 'SYNTHETIC-NOT-EIOPA',
             'as_of_date': '2020-12-31', 'nuts_version': '2021', 'nuts2': 'DE21',
             'peril': 'windstorm', 'occupancy': 'residential',
             'sum_insured_eur': 1000000, 'market_scope': 'insurance_sample_not_full_market'},
            {'record_id': 'SYNTH-EX-2', 'dataset_id': 'SYNTHETIC-NOT-EIOPA',
             'as_of_date': '2020-12-31', 'nuts_version': '2021', 'nuts2': 'DE21',
             'peril': 'windstorm', 'occupancy': 'commercial_including_industrial',
             'sum_insured_eur': 800000, 'market_scope': 'insurance_sample_not_full_market'},
        ],
        'hazards': [
            {'record_id': 'SYNTH-HZ-1', 'dataset_id': 'SYNTHETIC-NOT-C3S',
             'event_id': 'SYNTH-2021-001', 'event_date': '2021-02-01',
             'nuts_version': '2021', 'nuts2': 'DE21',
             'peril': 'extratropical_windstorm', 'gust_mps': 30,
             'aggregation': 'max_of_footprint_grid_cells'},
        ],
    }


class JoinTests(unittest.TestCase):
    def test_exact_join_preserves_coverage(self):
        result=join(example())
        self.assertEqual(len(result['matched']),2)
        self.assertEqual([r['sum_insured_eur'] for r in result['matched']],[800000,1000000])
        self.assertEqual(result['unmatched_hazards'],[])
        self.assertFalse(result['economic_or_insured_losses_calculated'])
    def test_reproducible(self):
        self.assertEqual(join(example()),join(copy.deepcopy(example())))
    def test_temporal_leakage_blocked(self):
        data=example();data['hazards'][0]['event_date']='2020-02-09'
        result=join(data)
        self.assertEqual(result['matched'],[])
        self.assertEqual(len(result['unmatched_hazards']),2)
        self.assertEqual({r['reason'] for r in result['unmatched_hazards']},{'exposure_snapshot_after_event_temporal_leakage'})
    def test_unknown_version_no_join(self):
        data=example();data['hazards'][0]['nuts_version']='2016'
        self.assertEqual(join(data)['matched'],[])
        self.assertEqual(join(data)['unmatched_hazards'][0]['reason'],'no_exact_nuts2_version_and_region')
    def test_unknown_region_no_join(self):
        data=example();data['hazards'][0]['nuts2']='FR10'
        self.assertEqual(join(data)['matched'],[])
    def test_duplicates_exposure_rejected(self):
        data=example();data['exposures'].append(copy.deepcopy(data['exposures'][0]))
        with self.assertRaises(InputError):join(data)
    def test_duplicate_aggregating_key_rejected(self):
        data=example();data['exposures'][1]['occupancy']='residential'
        with self.assertRaises(InputError):join(data)
    def test_duplicate_event_region_rejected(self):
        data=example();data['hazards'].append(copy.deepcopy(data['hazards'][0]))
        with self.assertRaises(InputError):join(data)
    def test_bad_numeric_rejected(self):
        for n in (float('nan'),float('inf'),-2,True,'100'):
            data=example();data['exposures'][0]['sum_insured_eur']=n
            with self.subTest(n=n),self.assertRaises(InputError):join(data)
    def test_unsupported_peril_rejected(self):
        data=example();data['hazards'][0]['peril']='convective_storm'
        with self.assertRaises(InputError):join(data)
    def test_unsupported_market_scope_rejected(self):
        data=example();data['exposures'][0]['market_scope']='full_market'
        with self.assertRaises(InputError):join(data)
    def test_no_silent_grid_to_region(self):
        data=example();data['hazards'][0]['aggregation']='raw_grid_point'
        with self.assertRaises(InputError):join(data)
    def test_unverified_nuts_version_rejected(self):
        data=example();data['exposures'][0]['nuts_version']='unknown'
        with self.assertRaises(InputError):join(data)
    def test_mismatched_lob_rejected(self):
        data=example();data['exposures'][0]['occupancy']='motor'
        with self.assertRaises(InputError):join(data)
    def test_extra_field_rejected(self):
        data=example();data['exposures'][0]['insurer']='RealCo'
        with self.assertRaises(InputError):join(data)

if __name__=='__main__':unittest.main()
