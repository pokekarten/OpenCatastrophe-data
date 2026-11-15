# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import copy
import unittest
from research_runners.wind_event_catalogue_completeness import audit

def fixture():
    return {'first_month':'2020-01','last_month':'2020-02','tracking_algorithm':'TRACK',
            'months':[{'month':'2020-01','tracking_algorithm':'TRACK','delivery_complete':True,
                       'source_sha256':'a'*64,'events':[]}]}

class CompletenessTest(unittest.TestCase):
    def test_missing_is_not_zero(self):
        r=audit(fixture())
        self.assertEqual(r['missing_months'],['2020-02'])
        self.assertEqual(r['explicit_zero_event_months'],['2020-01'])
        self.assertFalse(r['catalogue_claims_complete'])
    def test_duplicate_event_and_tracker_rejected(self):
        d=fixture();e=copy.deepcopy(d['months'][0]);e['month']='2020-02'
        d['months'].append(e)
        for m in d['months']:m['events']=[{'event_id':'same','footprint_verified':True}]
        with self.assertRaises(ValueError):audit(d)
        d['months'][1]['tracking_algorithm']='other'
        with self.assertRaises(ValueError):audit(d)
    def test_complete_claim_is_not_scientific_approval(self):
        d=fixture();d['last_month']='2020-01';r=audit(d)
        self.assertTrue(r['catalogue_claims_complete'])
        self.assertFalse(r['annual_risk_authorized'])
    def test_missing_footprint_blocks(self):
        d=fixture();d['last_month']='2020-01'
        d['months'][0]['events']=[{'event_id':'e','footprint_verified':False}]
        self.assertFalse(audit(d)['catalogue_claims_complete'])
