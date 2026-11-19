# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from copy import deepcopy
from research_runners.windstorm_europe_year_blocks_v1 import resample_config

class YearBlocksTests(unittest.TestCase):
    def test_full_blocks_zero_years_reproducibility_and_order(self):
        c=dict(year_ids=[2001,2002],occurrences=[dict(year_id=2001,occurrence_id=n,storm_index=i,sample_id=0) for i,n in enumerate(('a','b'))])
        out,receipt=resample_config(c,1000,7)
        again=deepcopy(c);again['year_ids'].reverse();again['occurrences'].reverse()
        self.assertEqual((out,receipt),resample_config(again,1000,7))
        for row in receipt['mapping']:
            events=[e['occurrence_id'] for e in out['occurrences'] if e['year_id']==row['simulation_year']]
            self.assertEqual(events,['a','b'] if row['source_year']==2001 else [])
        selected=sum(r['source_year']==2001 for r in receipt['mapping'])
        self.assertTrue(400<selected<600)
        self.assertFalse(receipt['annual_frequency_calibrated'])
        self.assertEqual(c['year_ids'],[2001,2002])
        self.assertNotEqual(receipt['mapping'],resample_config(c,1000,8)[1]['mapping'])

    def test_invalid_unsampled_event_is_rejected_before_random_selection(self):
        for bad in [dict(storm_index=True,sample_id=0),dict(storm_index=50,sample_id=0),
                    dict(storm_index=0,sample_id=-1),dict(storm_index=0,sample_id=True)]:
            c=dict(year_ids=[1,2],occurrences=[dict(year_id=2,occurrence_id='bad',**bad)])
            # Many seeds select empty year 1. Validation must never depend on
            # whether source year 2 happens to appear in the one-year draw.
            for seed in range(20):
                with self.subTest(bad=bad,seed=seed),self.assertRaises(ValueError):
                    resample_config(c,1,seed)
        c=dict(year_ids=[1,2],occurrences=[dict(year_id=y,occurrence_id='same',storm_index=y,sample_id=0) for y in (1,2)])
        with self.assertRaises(ValueError):resample_config(c,1,7)

    def test_invalid_source_measure_and_unknown_year(self):
        for c in [dict(year_ids=[1,1],occurrences=[]),dict(year_ids=[1],occurrences=[dict(year_id=2,occurrence_id='a')])]:
            with self.assertRaises(ValueError):resample_config(c,10,7)
