# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic USDA RMA COL ZIP provenance and 30-field scientific-schema tests."""
from __future__ import annotations

from io import BytesIO
import unittest
import zipfile

from scripts.usda_rma_cause_loss_zip_preflight_v0 import (
    ZIP_NAME, Blocked, inspect_zip,
)


def row(**changes):
    # Synthetic fields, in exact official 2026-05-28 one-based order.
    cells = [
        "2025", "48", "TX", "201", "Synth County",
        "0041", "Synth Crop", "01", "APH", "A", "01",
        "04", "Synthetic Hail", "06", "JUN", "2025",
        "10", "2", "150.00", "0", "100000",
        "10000", "4000", "6000", "0", "0", "0",
        "25.00", "3500", "0.35",
    ]
    for key, value in changes.items():
        cells[int(key[1:])] = value
    return "|".join(cells).encode("utf-8") + b"\r\n"


def zipped(contents=None, *, entry="colsom2025.txt", another=None):
    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        if contents is not None:
            z.writestr(entry, contents)
        if another is not None:
            z.writestr("second.dat", another)
    return out.getvalue()


class OriginalZipPreflightTests(unittest.TestCase):
    def test_two_rows_are_provenance_only_not_model_admitted(self):
        second = row(f28="-250", f13="07", f14="JUL", f15="2024",
                     f16="", f17="")
        receipt = inspect_zip(zipped(row() + second))
        self.assertEqual(receipt["rows"], 2)
        self.assertEqual(receipt["distinct_loss_months"], 2)
        self.assertEqual(receipt["distinct_states"], 1)
        self.assertEqual(receipt["negative_indemnity_rows"], 1)
        self.assertEqual(receipt["rows_with_missing_policy_counts"], 1)
        self.assertEqual(len(receipt["original_local_archive_sha256"]), 64)
        self.assertFalse(receipt["source_original_http_response_authenticated"])
        self.assertFalse(receipt["source_rights_and_automation_reviewed"])
        self.assertFalse(receipt["cat_model_input_approved"])
        self.assertFalse(receipt["external_database_import_performed"])
        self.assertNotIn("Synth County", repr(receipt))

    def test_year_of_loss_not_assumed_equal_commodity_year(self):
        result = inspect_zip(zipped(row(f15="2024")))
        self.assertEqual(result["commodity_year"], 2025)

    def test_wrong_commodity_year_blocked(self):
        with self.assertRaisesRegex(Blocked, "commodity/policy year"):
            inspect_zip(zipped(row(f0="2024")))

    def test_year_of_loss_outside_review_window_blocked(self):
        with self.assertRaisesRegex(Blocked, "year of loss"):
            inspect_zip(zipped(row(f15="1988")))

    def test_wrong_number_of_pipe_fields_blocked(self):
        with self.assertRaisesRegex(Blocked, "30 pipe"):
            inspect_zip(zipped(row().replace(b"|0.35", b"")))

    def test_header_is_not_a_record(self):
        with self.assertRaisesRegex(Blocked, "coded field"):
            inspect_zip(zipped(row(f0="Commodity Year Identifier")))

    def test_unknown_coverage_is_not_cat_class(self):
        with self.assertRaisesRegex(Blocked, "coverage"):
            inspect_zip(zipped(row(f9="X")))

    def test_invalid_month_or_state_blocked(self):
        with self.assertRaisesRegex(Blocked, "month"):
            inspect_zip(zipped(row(f13="13")))
        with self.assertRaisesRegex(Blocked, "state abbreviation"):
            inspect_zip(zipped(row(f2="??")))

    def test_nonfinite_and_negative_unsigned_dollars_blocked(self):
        for cell in ("NaN", "-100", "INF", "1e30"):
            with self.subTest(cell=cell), self.assertRaisesRegex(Blocked, "numeric"):
                inspect_zip(zipped(row(f21=cell)))

    def test_ambiguous_data_members_require_exact_selection(self):
        binary = zipped(row(), another=row())
        with self.assertRaisesRegex(Blocked, "ambiguous"):
            inspect_zip(binary)
        self.assertEqual(inspect_zip(binary, member="second.dat")["rows"], 1)

    def test_path_traversal_and_encrypted_container_blocked(self):
        with self.assertRaisesRegex(Blocked, "unsafe ZIP"):
            inspect_zip(zipped(row(), entry="../escape.txt"))
        with self.assertRaisesRegex(Blocked, "ZIP data member"):
            inspect_zip(zipped(row()), member="../escape.txt")

    def test_wrong_zip_or_year_or_empty_data_blocked(self):
        with self.assertRaisesRegex(Blocked, "invalid original ZIP"):
            inspect_zip(b"not a ZIP container")
        with self.assertRaisesRegex(Blocked, "exact 2025"):
            inspect_zip(zipped(row()), year=2026)
        with self.assertRaisesRegex(Blocked, "no source records"):
            inspect_zip(zipped(b""))

    def test_broken_line_and_missing_source_values_blocked(self):
        with self.assertRaisesRegex(Blocked, "missing geography"):
            inspect_zip(zipped(row(f12="")))
        with self.assertRaisesRegex(Blocked, "invalid coded field"):
            inspect_zip(zipped(row(f11="A")))


if __name__ == "__main__":
    unittest.main()
