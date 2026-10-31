# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only preflight regressions; no provider data or rights asserted."""
import csv
import hashlib
import io
import unittest

from research_runners.historical_cat_benchmark_csv_preflight_v0 import (
    HANZE_COLUMNS, EXPOSURE_COLUMNS, SourcePreflightError,
    inspect_hanze_v302, inspect_residential_v2025,
)

def csv_bytes(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def hanze_row(**kwargs):
    row = {c: "" for c in HANZE_COLUMNS}
    row.update(id="2000", country_code="DE", event_start_date_year="2025",
               start_date="2025-01-02", end_date="2025-01-04",
               admin_unit_year="2024", reference_year_eur="2025")
    row.update(kwargs)
    return row

def exposure_row(**kwargs):
    row = {c: "" for c in EXPOSURE_COLUMNS}
    row.update(IndicatorCode="B_COST", Indicator="building cost", Unit="EUR/m2",
               CountryCode="DE", Country="Germany", **{"2000":"10","2024":"0"})
    row.update(kwargs)
    return row

class HistoricalBenchmarkPreflightTest(unittest.TestCase):
    def test_hanze_missing_is_not_zero(self):
        blob = csv_bytes(HANZE_COLUMNS, [hanze_row(),
            hanze_row(id="2001", economic_loss_value_eur="0")])
        result = inspect_hanze_v302(blob, digest(blob))
        self.assertEqual((result["event_count"], result["economic_loss_present_count"],
                          result["economic_loss_missing_count"]), (2,1,1))
        self.assertFalse(result["insured_loss_calculated"])
        self.assertFalse(result["source_admitted"])

    def test_hanze_rejects_repeated_event_id(self):
        blob = csv_bytes(HANZE_COLUMNS, [hanze_row(), hanze_row()])
        with self.assertRaises(SourcePreflightError):
            inspect_hanze_v302(blob, digest(blob))

    def test_hanze_rejects_other_nuts_vintage(self):
        blob = csv_bytes(HANZE_COLUMNS, [hanze_row(admin_unit_year="2021")])
        with self.assertRaises(SourcePreflightError):
            inspect_hanze_v302(blob, digest(blob))

    def test_hanze_rejects_inverted_dates(self):
        blob = csv_bytes(HANZE_COLUMNS, [hanze_row(end_date="2025-01-01")])
        with self.assertRaises(SourcePreflightError):
            inspect_hanze_v302(blob, digest(blob))

    def test_hanze_rejects_wrong_price_reference(self):
        blob = csv_bytes(HANZE_COLUMNS, [hanze_row(
            economic_loss_value_eur="20", reference_year_eur="2024")])
        with self.assertRaises(SourcePreflightError):
            inspect_hanze_v302(blob, digest(blob))

    def test_hanze_rejects_nonfinite_economic_loss(self):
        blob = csv_bytes(HANZE_COLUMNS, [hanze_row(economic_loss_value_eur="NaN")])
        with self.assertRaises(SourcePreflightError):
            inspect_hanze_v302(blob, digest(blob))

    def test_residential_wide_years_zero_vs_missing(self):
        blob = csv_bytes(EXPOSURE_COLUMNS, [exposure_row()])
        result = inspect_residential_v2025(blob, digest(blob))
        self.assertEqual(result["indicator_country_row_count"], 1)
        self.assertEqual(result["numeric_cells_present"], 2)
        self.assertEqual(result["numeric_cells_missing"], 23)
        self.assertFalse(result["insured_tiv_calculated"])

    def test_residential_rejects_duplicate_indicators(self):
        blob = csv_bytes(EXPOSURE_COLUMNS, [exposure_row(), exposure_row()])
        with self.assertRaises(SourcePreflightError):
            inspect_residential_v2025(blob, digest(blob))

    def test_residential_rejects_negative(self):
        blob = csv_bytes(EXPOSURE_COLUMNS, [exposure_row(**{"2024":"-1"})])
        with self.assertRaises(SourcePreflightError):
            inspect_residential_v2025(blob, digest(blob))

    def test_both_reject_wrong_sha(self):
        for source, cols, row in (
            (inspect_hanze_v302, HANZE_COLUMNS, hanze_row()),
            (inspect_residential_v2025, EXPOSURE_COLUMNS, exposure_row()),
        ):
            with self.subTest(source=source):
                blob = csv_bytes(cols, [row])
                with self.assertRaises(SourcePreflightError):
                    source(blob, "0"*64)

    def test_both_reject_duplicated_header(self):
        for source, cols in ((inspect_hanze_v302, HANZE_COLUMNS),
                             (inspect_residential_v2025, EXPOSURE_COLUMNS)):
            with self.subTest(source=source):
                blob = (",".join(cols[:-1] + (cols[0],)) + "\n" + ","*(len(cols)-1) + "\n").encode()
                with self.assertRaises(SourcePreflightError):
                    source(blob, digest(blob))

    def test_both_reject_malformed_utf8(self):
        for source in (inspect_hanze_v302, inspect_residential_v2025):
            with self.subTest(source=source):
                blob = b"\xff\xfe"
                with self.assertRaises(SourcePreflightError):
                    source(blob, digest(blob))

    def test_both_reject_malformed_row_width(self):
        for source, cols in ((inspect_hanze_v302, HANZE_COLUMNS),
                             (inspect_residential_v2025, EXPOSURE_COLUMNS)):
            with self.subTest(source=source):
                blob = (",".join(cols) + "\na,b\n").encode()
                with self.assertRaises(SourcePreflightError):
                    source(blob, digest(blob))

if __name__ == "__main__":
    unittest.main()
