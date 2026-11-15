# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests. No insurer, postal or licensed source bytes committed."""

import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from fl_mir_zip_reconciliation_v0 import (
    BASE_FIELDS, ZIP_FIELDS, ExposureReconciliationError, reconcile
)


class MIRZipReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / "state.csv"
        self.zip = Path(self.tmp.name) / "zip.csv"
        self.state_rows = [{
            "report_as_of": "2025-12-31",
            "scope_token": "same-explicit-export-criteria-v1",
            "naic_code": "01234",
            "reported_policy_type": "Synthetic owner-occupied",
            "policies_in_force": "3",
            "wind_structure_exposure_usd": "300.00",
        }]
        self.zip_rows = [
            {
                **self.state_rows[0], "county_key": "synthetic-north",
                "zip5": "01234", "policies_in_force": "1",
                "wind_structure_exposure_usd": "100.00",
            },
            {
                **self.state_rows[0], "county_key": "synthetic-south",
                "zip5": "01234", "policies_in_force": "2",
                "wind_structure_exposure_usd": "200.00",
            },
        ]
        self.write()

    def file(self, path, headers, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def write(self):
        self.file(self.state, BASE_FIELDS, self.state_rows)
        self.file(self.zip, ZIP_FIELDS, self.zip_rows)

    def test_same_zip_in_two_counties_conserves_without_dedup(self):
        result = reconcile(self.state, self.zip)
        self.assertTrue(result["reconciled_at_normalized_grain"])
        self.assertEqual(result["county_zip_rows"], 2)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["original_provider_bytes_verified"])
        self.assertFalse(result["individual_building_tiv_observed"])

    def test_changed_wind_exposure_fails(self):
        self.zip_rows[1]["wind_structure_exposure_usd"] = "199.98"
        self.write()
        result = reconcile(self.state, self.zip)
        self.assertEqual(result["wind_structure_exposure_mismatches"], 1)
        self.assertFalse(result["reconciled_at_normalized_grain"])

    def test_one_cent_rounding_tolerance(self):
        self.zip_rows[1]["wind_structure_exposure_usd"] = "199.99"
        self.write()
        self.assertTrue(reconcile(self.state, self.zip)["reconciled_at_normalized_grain"])

    def test_policy_count_fails(self):
        self.zip_rows[0]["policies_in_force"] = "2"
        self.write()
        self.assertEqual(reconcile(self.state, self.zip)["policy_count_mismatches"], 1)

    def test_extra_carrier_lob_detected(self):
        self.zip_rows[1]["naic_code"] = "54321"
        self.write()
        result = reconcile(self.state, self.zip)
        self.assertEqual(
            (result["statewide_keys_missing_in_zip"], result["zip_keys_missing_in_statewide"]),
            (0, 1),
        )

    def test_other_month_rejected(self):
        self.zip_rows[1]["report_as_of"] = "2025-11-30"
        self.write()
        with self.assertRaisesRegex(ExposureReconciliationError, "one report date"):
            reconcile(self.state, self.zip)

    def test_different_scope_rejected(self):
        for row in self.zip_rows:
            row["scope_token"] = "other-selection"
        self.write()
        with self.assertRaisesRegex(ExposureReconciliationError, "selection scope differ"):
            reconcile(self.state, self.zip)

    def test_no_count_suppression_or_negative_values(self):
        for value in ("-1", "NA", "1.0", ""):
            with self.subTest(value=value):
                self.zip_rows[0]["policies_in_force"] = value
                self.write()
                with self.assertRaises(ExposureReconciliationError):
                    reconcile(self.state, self.zip)

    def test_nonfinite_or_overprecise_money(self):
        for value in ("NaN", "Infinity", "-1", "2.345"):
            with self.subTest(value=value):
                self.zip_rows[0]["wind_structure_exposure_usd"] = value
                self.write()
                with self.assertRaises(ExposureReconciliationError):
                    reconcile(self.state, self.zip)

    def test_duplicate_county_zip_row_rejected(self):
        self.zip_rows.append(dict(self.zip_rows[0]))
        self.write()
        with self.assertRaisesRegex(ExposureReconciliationError, "duplicate normalized grain"):
            reconcile(self.state, self.zip)

    def test_leading_zero_zip_preserved(self):
        self.zip_rows[0]["zip5"] = "1234"
        self.write()
        with self.assertRaisesRegex(ExposureReconciliationError, "zip5 must"):
            reconcile(self.state, self.zip)

    def test_no_empty_data(self):
        self.zip_rows = []
        self.write()
        with self.assertRaisesRegex(ExposureReconciliationError, "no observations"):
            reconcile(self.state, self.zip)

    def test_duplicate_company_summary_rejected(self):
        self.state_rows.append(dict(self.state_rows[0]))
        self.write()
        with self.assertRaisesRegex(ExposureReconciliationError, "duplicate normalized grain"):
            reconcile(self.state, self.zip)


if __name__ == "__main__":
    unittest.main()
