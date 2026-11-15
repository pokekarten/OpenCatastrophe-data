# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only TWIA schema/conservation tests; no provider dataset rows."""
from __future__ import annotations
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from twia_liability_2025_reconciliation_v0 import (
    CLASSES, COUNTIES, COUNTY_FIELDS, CLASS_FIELDS, TWIAReconciliationError, reconcile,
)


class TWIATests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.county = Path(self.tmp.name) / "county.csv"
        self.classes = Path(self.tmp.name) / "classes.csv"
        self.detail = []
        for county in COUNTIES:
            for cls in CLASSES:
                # Made-up small amounts; never original TWIA county numbers.
                n = 2 if cls == "Commercial" else 1
                self.detail.append(dict(
                    record_kind="county_class", report_as_of="2025-12-31", county=county,
                    policy_class=cls, policies_in_force=str(n),
                    risks_in_force=str(n+2 if cls=="Commercial" else n),
                    direct_liability_usd=str(n*100),
                    indirect_liability_usd="10", ytd_written_premium_usd=str(n*3),
                ))
        self._rebuild_counties()
        self.write()

    def _rebuild_counties(self):
        self.summary = []
        for county in COUNTIES:
            rows=[r for r in self.detail if r['county']==county]
            self.summary.append(dict(record_kind="county", report_as_of="2025-12-31",county=county,
                policies_in_force=str(sum(int(r['policies_in_force']) for r in rows)),
                direct_liability_usd=str(sum(int(r['direct_liability_usd']) for r in rows)),
                ytd_written_premium_usd=str(sum(int(r['ytd_written_premium_usd']) for r in rows))))

    def write(self):
        for path,fieldnames,rows in ((self.county, COUNTY_FIELDS,self.summary),(self.classes, CLASS_FIELDS,self.detail)):
            with path.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=fieldnames)
                w.writeheader();w.writerows(rows)

    def test_valid_synthetic_15_counties_and_45_classes(self):
        r=reconcile(self.county,self.classes)
        self.assertTrue(r['reconciled_at_normalized_grain'])
        self.assertEqual((r['county_rows'],r['county_class_rows']),(15,45))
        self.assertFalse(r['original_provider_bytes_verified'])
        self.assertFalse(r['model_input_approved'])
        self.assertEqual(r['total_risks_in_force']-r['total_policies_in_force'],30)

    def test_published_mode_does_not_accept_fake_consistent_rows(self):
        r=reconcile(self.county,self.classes,mode='published-2025')
        self.assertFalse(r['reconciled_at_normalized_grain'])
        self.assertEqual(len(r['published_class_control_mismatches']),3)
        self.assertTrue(r['published_grand_total_mismatch'])

    def test_mismatched_county_detected(self):
        self.summary[0]['direct_liability_usd']='1'
        self.write()
        r=reconcile(self.county,self.classes)
        self.assertEqual(r['county_mismatches'],[COUNTIES[0]])
        self.assertFalse(r['reconciled_at_normalized_grain'])

    def test_wrong_county_blocked(self):
        self.detail[0]['county']='Unknown'
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'unknown TWIA county'):
            reconcile(self.county,self.classes)

    def test_wrong_county_vintage_rejected(self):
        self.summary[0]['report_as_of']='2025-09-30'
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'snapshot'):
            reconcile(self.county,self.classes)

    def test_duplicate_class_blocked(self):
        self.detail[1]['policy_class']='Commercial'
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'duplicate'):
            reconcile(self.county,self.classes)

    def test_missing_class_blocked(self):
        self.detail.pop()
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'incomplete'):
            reconcile(self.county,self.classes)

    def test_garbage_and_negative_and_suppressed_rejected(self):
        for bad in ('-1','1.0','NaN','','1,000',' 2','2.30','N/A'):
            with self.subTest(value=bad):
                self.detail[0]['policies_in_force']=bad
                self.write()
                with self.assertRaises(TWIAReconciliationError):
                    reconcile(self.county,self.classes)

    def test_risks_smaller_than_policies_rejected(self):
        self.detail[0]['risks_in_force']='1'
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'risk count'):
            reconcile(self.county,self.classes)

    def test_residential_risks_cannot_diverge(self):
        row=next(r for r in self.detail if r['policy_class']=='Residential')
        row['risks_in_force']='2'
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'1 risk'):
            reconcile(self.county,self.classes)

    def test_indirect_liability_not_included_in_direct(self):
        r=reconcile(self.county,self.classes)
        self.assertEqual(r['total_direct_liability_usd'],6000)
        self.assertEqual(r['total_indirect_liability_usd'],450)

    def test_missing_column_blocked(self):
        self.summary[0]['unexpected']='data'
        with self.county.open('w',encoding='utf-8',newline='') as f:
            fields=COUNTY_FIELDS+('unexpected',)
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader();writer.writerows(self.summary)
        with self.assertRaisesRegex(TWIAReconciliationError,'header'):
            reconcile(self.county,self.classes)

    def test_published_control_matching_does_not_verify_original_pdf(self):
        # Deliberately fabricated per-county allocations matching published class
        # grand totals: no geographic truth can be inferred from aggregates.
        from twia_liability_2025_reconciliation_v0 import PUBLISHED_CLASSES, METRICS
        for cls in CLASSES:
            controls=PUBLISHED_CLASSES[cls]
            rows=[r for r in self.detail if r["policy_class"]==cls]
            for i,field in enumerate(METRICS):
                q,rem=divmod(controls[i],len(rows))
                for j,row in enumerate(rows):
                    row[field]=str(q+(j < rem))
        self._rebuild_counties()
        self.write()
        r=reconcile(self.county,self.classes,mode='published-2025')
        self.assertTrue(r['reconciled_at_normalized_grain'])
        self.assertEqual(r['total_risks_in_force'],293466)
        self.assertFalse(r['original_provider_bytes_verified'])
        self.assertFalse(r['model_input_approved'])
        self.assertFalse(r['observed_insured_building_positions'])

    def test_indirect_liability_never_added_to_direct(self):
        self.detail[0]['indirect_liability_usd'] = '999999'
        self.write()
        r=reconcile(self.county,self.classes)
        self.assertTrue(r['reconciled_at_normalized_grain'])
        self.assertEqual(r['total_direct_liability_usd'],6000)
        self.assertEqual(r['total_indirect_liability_usd'],1000439)

    def test_partial_harris_stays_explicit(self):
        r=reconcile(self.county,self.classes)
        self.assertIn('part of Harris County',r['scope'])

    def test_invalid_class_blocked(self):
        self.detail[0]['policy_class']='Hotel'
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,'unknown TWIA liability-report class'):
            reconcile(self.county,self.classes)

    def test_overlong_value_blocked(self):
        self.detail[0]['direct_liability_usd']='1'*100
        self.write()
        with self.assertRaisesRegex(TWIAReconciliationError,"nonnegative integer"):
            reconcile(self.county,self.classes,mode='published-2025')


if __name__=='__main__': unittest.main()
