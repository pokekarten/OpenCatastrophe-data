# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-canonical annual counts: no cross-threshold mixing or fake insurer model."""
import hashlib
import io
import csv
import math
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.c3s_wind_frequency_candidate_v0 import CalibrationError,fit_c3s_count_rate

COLUMNS=['year','region','threshold','storm_number','mean_wind_gust',
         'ssi','normalised_ssi','area_ratio','wind_gust_ratio','algorithm']


def source(rows):
    f=io.StringIO(newline='')
    w=csv.DictWriter(f,COLUMNS,lineterminator='\n')
    w.writeheader()
    for y,alg,threshold,count in rows:
        w.writerow({'year':y,'region':'DE','threshold':threshold,
                    'storm_number':count,'algorithm':alg})
    return f.getvalue().encode()


def rows_for_5years():
    counts=[0,1,2,0,2]
    return [(1950+i,a,'20',c if a=='TempestExtremes' else c+1)
            for i,c in enumerate(counts) for a in ('TempestExtremes','TRACK')]


def calculate(data=None,**kw):
    data=source(rows_for_5years()) if data is None else data
    args=dict(original_csv_bytes=data,expected_csv_sha256=hashlib.sha256(data).hexdigest(),
              region='DE',algorithm='TempestExtremes',threshold_mps='20',
              train_start=1950,train_end=1952,holdout_start=1953,holdout_end=1954)
    args.update(kw)
    return fit_c3s_count_rate(**args)


class C3SWindFrequencyCandidateTests(unittest.TestCase):
    def test_poisson_mle_and_actual_independent_holdout(self):
        x=calculate()
        self.assertEqual(x['train_annual_counts'],[0,1,2])
        self.assertEqual(x['holdout_annual_counts'],[0,2])
        self.assertEqual(x['train_count_total'],3)
        self.assertEqual(x['poisson_lambda_exact'],{'numerator':1,'denominator':1})
        self.assertAlmostEqual(x['poisson_probability_at_least_one_event'],1-math.exp(-1))
        self.assertAlmostEqual(x['holdout_mean_count'],1.)
        self.assertAlmostEqual(x['holdout_log_likelihood'], -2+2*math.log(1)-math.lgamma(3))
        self.assertEqual(x['automatic_nuts_join_permitted'],False)
        self.assertEqual(x['status'],'UNADMITTED_RESEARCH_COUNT_RATE_ONLY')

    def test_different_algorithms_are_separate_not_added(self):
        other=calculate(algorithm='TRACK')
        self.assertEqual(other['train_annual_counts'],[1,2,3])
        self.assertEqual(other['poisson_lambda_exact'],{'numerator':2,'denominator':1})
        self.assertNotEqual(other['selector_and_split_sha256'],calculate()['selector_and_split_sha256'])

    def test_missing_annual_zero_year_not_implicitly_filled(self):
        omitted=[row for row in rows_for_5years() if not (row[0]==1951 and row[1]=='TempestExtremes')]
        with self.assertRaisesRegex(CalibrationError,'incomplete annual'):
            calculate(data=source(omitted))

    def test_hash_and_wrong_threshold_fail_closed(self):
        for opts in ({'expected_csv_sha256':'0'*64},{'threshold_mps':'25'},
                     {'region':'FR'},{'algorithm':'NOT-A-SOURCE-TRACKER'}):
            with self.subTest(opts=opts),self.assertRaises(CalibrationError):
                calculate(**opts)

    def test_reject_overlap_horizon_and_nonconsecutive_splits(self):
        for opts in ({'train_end':1953,'holdout_start':1953},
                     {'train_start':1950,'train_end':1951,'holdout_start':1953},
                     {'train_start':1950,'train_end':1950},
                     {'holdout_end':1953}, {'train_start':True}):
            with self.subTest(opts=opts),self.assertRaises(CalibrationError):
                calculate(**opts)

    def test_poisson_zero_fit_positive_holdout_warning(self):
        original=source([(1950+i,'TRACK','25',n) for i,n in enumerate([0,0,1,0])])
        r=calculate(data=original,algorithm='TRACK',threshold_mps='25',
                    train_start=1950,train_end=1951,holdout_start=1952,holdout_end=1953)
        self.assertEqual(r['poisson_lambda_events_per_year'],0)
        self.assertTrue(r['zero_train_positive_holdout_failure'])
        self.assertIsNone(r['holdout_log_likelihood'])

    def test_nested_threshold_source_monotonicity_is_upstream_validated(self):
        # At a *higher* gust threshold, event count may not increase.
        original=source(rows_for_5years()+[(1950,'TempestExtremes','25',5)])
        with self.assertRaisesRegex(CalibrationError,'source parser rejected'):
            calculate(data=original)

    def test_reproduction_selector_and_digest(self):
        a=calculate();b=calculate()
        self.assertEqual(a,b)
        self.assertEqual(a['source_dataset'],'sis-european-wind-storm-reanalysis')
        self.assertEqual(len(a['selector_and_split_sha256']),64)


if __name__=='__main__':
    unittest.main()
