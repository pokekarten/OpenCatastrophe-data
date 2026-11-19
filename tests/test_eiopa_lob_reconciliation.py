# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.eiopa_lob_reconciliation import reconcile

def rows(values):
    return [{'Event ID':'e','Country':'DE','LoB':k,'Insured loss (EUR)':v} for k,v in values]

class ReconciliationTest(unittest.TestCase):
    def test_alternative_total(self):
        r=reconcile(rows([('RES','0.1'),('COM','0.2'),('ALL','0.3')]))[0]
        self.assertTrue(r['all_equals_components_within_cent'])
        self.assertFalse(r['denominator_match_verified'])
    def test_disagreement_visible(self):
        self.assertFalse(reconcile(rows([('RES',1),('ALL',2)]))[0]['all_equals_components_within_cent'])
    def test_duplicate_and_overlap_rejected(self):
        for values in [[('ALL',1),('ALL',1)],[('RES+COM',1),('RES',1)]]:
            with self.assertRaises(ValueError):reconcile(rows(values))
    def test_invalid_loss_rejected(self):
        for value in ['NaN','Infinity',-1]:
            with self.assertRaises(ValueError):reconcile(rows([('ALL',value)]))
