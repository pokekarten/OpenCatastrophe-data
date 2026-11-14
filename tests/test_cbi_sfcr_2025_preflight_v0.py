# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic tests only: never fetch or include a genuine SFCR row."""

import csv
import io
import tempfile
import unittest
from pathlib import Path

from research_runners.cbi_sfcr_2025_preflight_v0 import (
    EXPECTED_HEADER, PreflightError, inspect_csv, inspect_file, main,
)


def fake_row(**overrides):
    data = dict(zip(EXPECTED_HEADER, [
        "30/06/2025", "SYNTHETIC TEST INSURER", "123456",
        "5493001KJTIIGC8Y1R12", "Insurance Company Non-Life", "2025",
        "S.02.01.02", "Assets Test", "Solvency II value", "Test asset",
        "Solvency II value", "R0500", "C0010", "R0500 - Test asset",
        "C0010 - Solvency II value", "-100.5", "-0.1005", "-100.5",
    ]))
    data.update(overrides)
    return data


def csv_text(rows, header=EXPECTED_HEADER):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(header), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


class IrishSFCRPreflightTests(unittest.TestCase):
    def test_synthetic_two_dates_and_templates_are_aggregate_only(self):
        second = fake_row(ReportingDate="31/12/2025", InstitutionNumber="654321",
                          LEICode="", templates="S.05.01.02", row_code="R0020")
        result = inspect_csv(io.StringIO(csv_text([fake_row(), second])))
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["distinct_institution_numbers"], 2)
        self.assertEqual(result["distinct_reporting_dates"], 2)
        self.assertEqual(result["rows_with_missing_lei"], 1)
        self.assertEqual(result["qrt_template_row_counts"]["S.05.01.02"], 1)
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["insured_tiv_or_cat_loss_inferred"])
        self.assertNotIn("SYNTHETIC TEST INSURER", str(result))

    def test_negative_numeric_and_missing_numeric_allowed(self):
        result = inspect_csv(io.StringIO(csv_text([fake_row(Local_value_or_percentage_value="")])))
        self.assertEqual(result["populated_numeric_field_counts"]["Euro_value_or_percentage_value"], 1)
        self.assertNotIn("Local_value_or_percentage_value", result["populated_numeric_field_counts"])

    def test_empty_rows_blocked(self):
        with self.assertRaises(PreflightError):
            inspect_csv(io.StringIO(csv_text([])))

    def test_wrong_year_and_date_blocked(self):
        for value in ["31/02/2025", "1/2/2025", "30/06/2024", "30/06/2026", "2025-06-30"]:
            with self.subTest(value=value), self.assertRaises(PreflightError):
                inspect_csv(io.StringIO(csv_text([fake_row(ReportingDate=value)])))
        with self.assertRaises(PreflightError):
            inspect_csv(io.StringIO(csv_text([fake_row(year_end="2024")])))

    def test_header_extra_missing_and_swapped_blocked(self):
        variants = [
            list(EXPECTED_HEADER)[1:],
            list(EXPECTED_HEADER) + ["NEW"],
            list(reversed(EXPECTED_HEADER)),
        ]
        for header in variants:
            with self.subTest(header=header), self.assertRaises(PreflightError):
                inspect_csv(io.StringIO(csv_text([fake_row()], header=header)))

    def test_row_extra_columns_blocked(self):
        raw = csv_text([fake_row()]) + "30/06/2025,extra\n"
        with self.assertRaises(PreflightError):
            inspect_csv(io.StringIO(raw))
        raw = csv_text([fake_row()]) + "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18\n"
        with self.assertRaises(PreflightError):
            inspect_csv(io.StringIO(raw))

    def test_bad_institution_and_lei_blocked(self):
        for override in [
            {"InstitutionName": ""}, {"InstitutionNumber": ""},
            {"InstitutionNumber": "1.0"}, {"LEICode": "INVALID"},
        ]:
            with self.subTest(override=override), self.assertRaises(PreflightError):
                inspect_csv(io.StringIO(csv_text([fake_row(**override)])))

    def test_bad_codes_blocked(self):
        for override in [{"templates": "S.02.01"}, {"row_code": "P0500"},
                         {"col_code": "X0010"}]:
            with self.subTest(override=override), self.assertRaises(PreflightError):
                inspect_csv(io.StringIO(csv_text([fake_row(**override)])))

    def test_bad_numeric_fields_blocked(self):
        for bad in ["NaN", "Infinity", "1e999999", "not a number", "5,000"]:
            with self.subTest(bad=bad), self.assertRaises(PreflightError):
                inspect_csv(io.StringIO(csv_text([fake_row(Euro_value_or_percentage_value=bad)])))

    def test_aggregate_hash_and_reject_source_inside_repo(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.csv"
            path.write_text(csv_text([fake_row()]), encoding="utf-8")
            out = inspect_file(path)
            self.assertEqual(len(out["source_byte_sha256"]), 64)
            self.assertEqual(out["source_byte_count"], path.stat().st_size)
            self.assertFalse(out["rights_cleared"])
            self.assertEqual(main(["--csv", str(path)]), 0)

    def test_bounded_file_limit(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oversized.csv"
            with path.open("wb") as out:
                out.truncate(24 * 1024 * 1024 + 1)
            with self.assertRaises(PreflightError):
                inspect_file(path)


if __name__ == "__main__":
    unittest.main()
