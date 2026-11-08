# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Negative and positive tests use completely invented data, never insurer rows."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))  # repository: tests/ imports research_runners, see below
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research_runners'))
from twia_synthetic_microzones_v0 import (
    SCENARIOS, MEASURES, SyntheticAllocationError,
    allocate_two_priors, apportion_integer,
)
from twia_liability_2025_reconciliation_v0 import COUNTIES, CLASSES


def synthetic_rows():
    return [{
        'county': county, 'policy_class': cls,
        'policies_in_force': 3,
        'risks_in_force': 4 if cls == 'Commercial' else 3,
        'direct_liability_usd': 101,
        'indirect_liability_usd': 5,
        'ytd_written_premium_usd': 9,
    } for county in COUNTIES for cls in CLASSES]


def audit():
    return {
        'reconciled_at_normalized_grain': True,
        'report_as_of': '2025-12-31', 'mode': 'synthetic',
        'normalization_county_sha256': 'a' * 64,
        'normalization_class_sha256': 'b' * 64,
    }


class SyntheticTWIAZoneTests(unittest.TestCase):
    def test_two_independent_worlds_and_exact_45x3_cells(self):
        pkg = allocate_two_priors(synthetic_rows(), source_audit=audit())
        self.assertEqual(pkg['scenario_count'], 2)
        self.assertEqual([s['scenario'] for s in pkg['scenarios']], ['distributed', 'concentrated'])
        self.assertTrue(pkg['scenarios_are_distinct'])
        self.assertTrue(pkg['worlds_are_mutually_exclusive'])
        self.assertEqual([len(s['cells']) for s in pkg['scenarios']], [135, 135])
        self.assertFalse(pkg['oasis_oed_ready'])
        self.assertFalse(pkg['model_input_approved'])
        self.assertFalse(pkg['synthetic_zones_are_geospatial'])
        self.assertFalse(pkg['exposure_is_observed_insured_tiv'])

    def test_every_county_class_conserves_all_five_metrics_each_world(self):
        rows = synthetic_rows()
        package = allocate_two_priors(rows, source_audit=audit())
        for scenario in package['scenarios']:
            for r in rows:
                cells = [c for c in scenario['cells'] if c['county'] == r['county'] and c['policy_class'] == r['policy_class']]
                self.assertEqual(len(cells), 3)
                for m in MEASURES:
                    self.assertEqual(sum(c[m] for c in cells), r[m])
                for c in cells:
                    self.assertGreaterEqual(c['risks_in_force'], c['policies_in_force'])
                    if c['risks_in_force'] == 0:
                        self.assertEqual(c['direct_liability_usd'], 0)

    def test_large_integer_precision_no_float_rounding(self):
        v = 10**17 + 29
        for weights in SCENARIOS.values():
            split = apportion_integer(v, weights)
            self.assertEqual(sum(split), v)
            self.assertTrue(all(isinstance(x, int) for x in split))

    def test_tiny_residual_conservation(self):
        self.assertEqual(apportion_integer(1, (1, 1, 1)), [1, 0, 0])
        self.assertEqual(apportion_integer(2, (1, 1, 1)), [1, 1, 0])

    def test_zero_amount_with_zero_weights(self):
        self.assertEqual(apportion_integer(0, (0, 0, 0)), [0, 0, 0])

    def test_positive_amount_zero_weights_fails(self):
        with self.assertRaises(SyntheticAllocationError):
            apportion_integer(4, (0, 0, 0))

    def test_bool_float_negative_bad_weights_fails(self):
        for bad in ((1, True, 1), (1, -1, 1), (1, 1.1, 1)):
            with self.subTest(bad=bad), self.assertRaises(SyntheticAllocationError):
                apportion_integer(5, bad)

    def test_bool_or_float_amount_fails(self):
        for bad in (-1, 5.0, True):
            with self.subTest(bad), self.assertRaises(SyntheticAllocationError):
                apportion_integer(bad, (1, 2, 3))

    def test_duplicate_class_fails(self):
        rows = synthetic_rows()
        rows[1] = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(SyntheticAllocationError, 'duplicate'):
            allocate_two_priors(rows, source_audit=audit())

    def test_missing_class_fails(self):
        with self.assertRaisesRegex(SyntheticAllocationError, '45'):
            allocate_two_priors(synthetic_rows()[:-1], source_audit=audit())

    def test_unknown_county_fails(self):
        rows = synthetic_rows()
        rows[0]['county'] = 'Not a county'
        with self.assertRaisesRegex(SyntheticAllocationError, 'invalid'):
            allocate_two_priors(rows, source_audit=audit())

    def test_risks_less_than_policies_fails(self):
        rows = synthetic_rows()
        rows[0]['risks_in_force'] = 2
        with self.assertRaisesRegex(SyntheticAllocationError, 'smaller'):
            allocate_two_priors(rows, source_audit=audit())

    def test_direct_liability_without_risk_fails(self):
        rows = synthetic_rows()
        rows[0]['risks_in_force'] = rows[0]['policies_in_force'] = 0
        with self.assertRaisesRegex(SyntheticAllocationError, 'zero reported risks'):
            allocate_two_priors(rows, source_audit=audit())

    def test_negative_and_missing_marginals_fail(self):
        for value in (-1, None, 0.5, True):
            rows = synthetic_rows()
            rows[0]['indirect_liability_usd'] = value
            with self.subTest(value=value), self.assertRaisesRegex(SyntheticAllocationError, 'nonnegative integer'):
                allocate_two_priors(rows, source_audit=audit())

    def test_failed_reconciliation_cannot_allocate(self):
        a = audit()
        a['reconciled_at_normalized_grain'] = False
        with self.assertRaisesRegex(SyntheticAllocationError, 'did not reconcile'):
            allocate_two_priors(synthetic_rows(), source_audit=a)

    def test_wrong_vintage_cannot_allocate(self):
        a = audit()
        a['report_as_of'] = '2025-09-30'
        with self.assertRaisesRegex(SyntheticAllocationError, 'vintage'):
            allocate_two_priors(synthetic_rows(), source_audit=a)

    def test_missing_sha_cannot_allocate(self):
        a = audit()
        a['normalization_county_sha256'] = 'not-original-digest'
        with self.assertRaisesRegex(SyntheticAllocationError, 'digest'):
            allocate_two_priors(synthetic_rows(), source_audit=a)

    def test_deterministic_for_reordered_input(self):
        rows = synthetic_rows()
        a = allocate_two_priors(rows, source_audit=audit())
        b = allocate_two_priors(list(reversed(rows)), source_audit=audit())
        self.assertEqual(a, b)

    def test_zero_policies_with_historical_written_premiums(self):
        rows = synthetic_rows()
        for row in rows:
            row['policies_in_force'] = 0
            row['risks_in_force'] = 0
            row['direct_liability_usd'] = 0
        package = allocate_two_priors(rows, source_audit=audit())
        for scenario in package['scenarios']:
            self.assertEqual(sum(x['risks_in_force'] for x in scenario['cells']), 0)
            self.assertEqual(sum(x['ytd_written_premium_usd'] for x in scenario['cells']), 9*45)


class SyntheticTWIAIntegratedCSVTests(unittest.TestCase):
    """Uses the actual merged source checker, not a test stub."""

    def test_real_source_checker_to_alternative_worlds_with_fictional_csv(self):
        import csv
        from tempfile import TemporaryDirectory
        from twia_liability_2025_reconciliation_v0 import COUNTY_FIELDS, CLASS_FIELDS
        from twia_synthetic_microzones_v0 import allocate_from_csv

        with TemporaryDirectory() as td:
            county_path = Path(td) / "county.csv"
            classes_path = Path(td) / "classes.csv"
            class_rows = []
            county_rows = []
            for county in COUNTIES:
                total_p = total_direct = total_premium = 0
                for policy_class in CLASSES:
                    n = 3 if policy_class == "Commercial" else 2
                    direct = 101 * n
                    premium = 9 * n
                    class_rows.append({
                        "record_kind": "county_class",
                        "report_as_of": "2025-12-31", "county": county,
                        "policy_class": policy_class,
                        "policies_in_force": str(n),
                        "risks_in_force": str(n + 1 if policy_class == "Commercial" else n),
                        "direct_liability_usd": str(direct),
                        "indirect_liability_usd": "7",
                        "ytd_written_premium_usd": str(premium),
                    })
                    total_p += n
                    total_direct += direct
                    total_premium += premium
                county_rows.append({
                    "record_kind": "county", "report_as_of": "2025-12-31",
                    "county": county, "policies_in_force": str(total_p),
                    "direct_liability_usd": str(total_direct),
                    "ytd_written_premium_usd": str(total_premium),
                })
            for out, header, rows in [
                (county_path, COUNTY_FIELDS, county_rows),
                (classes_path, CLASS_FIELDS, class_rows),
            ]:
                with out.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=header)
                    writer.writeheader()
                    writer.writerows(rows)
            package = allocate_from_csv(county_path, classes_path, mode="synthetic")
            self.assertTrue(package["source_marginals_conserved"])
            self.assertEqual(len(package["scenarios"]), 2)
            self.assertEqual(len(package["scenarios"][0]["cells"]), 135)
            self.assertEqual(package["source_control_mode"], "synthetic")
            self.assertFalse(package["original_provider_bytes_verified"])
            self.assertFalse(package["model_input_approved"])

    def test_real_source_checker_rejects_fictional_csv_in_published_mode(self):
        """Even internally consistent invented data fail TWIA external 2025 totals."""
        from tempfile import TemporaryDirectory
        import csv
        from twia_liability_2025_reconciliation_v0 import COUNTY_FIELDS, CLASS_FIELDS
        from twia_synthetic_microzones_v0 import allocate_from_csv
        with TemporaryDirectory() as td:
            county_path, class_path = Path(td) / "county.csv", Path(td) / "class.csv"
            for out, cols, records in [
                (county_path, COUNTY_FIELDS, [
                    {"record_kind": "county", "report_as_of": "2025-12-31", "county": county,
                     "policies_in_force": "3", "direct_liability_usd": "300",
                     "ytd_written_premium_usd": "30"}
                    for county in COUNTIES
                ]),
                (class_path, CLASS_FIELDS, [
                    {"record_kind": "county_class", "report_as_of": "2025-12-31",
                     "county": county, "policy_class": cls,
                     "policies_in_force": "1", "risks_in_force": "1",
                     "direct_liability_usd": "100", "indirect_liability_usd": "0",
                     "ytd_written_premium_usd": "10"}
                    for county in COUNTIES for cls in CLASSES
                ]),
            ]:
                with out.open("w", encoding="utf-8", newline="") as stream:
                    writer=csv.DictWriter(stream, fieldnames=cols)
                    writer.writeheader()
                    writer.writerows(records)
            with self.assertRaisesRegex(SyntheticAllocationError, "reconciliation failed"):
                allocate_from_csv(county_path, class_path, mode="published-2025")


if __name__ == '__main__':
    unittest.main()
