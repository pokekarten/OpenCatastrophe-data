# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Only synthetic data; original publisher bytes are never checked into Git."""

from __future__ import annotations

import csv
import io
import unittest
import zipfile
from xml.sax.saxutils import escape

from research_runners.cfdid_annual_coverage_preflight_v0 import (
    INDICATORS,
    PreflightError,
    parse_original_annual_workbook,
    reconcile_annual_coverage,
)

HEADERS = [
    "Event level", "Event ID", "Start year", "Start month", "Start day",
    "End year", "End month", "End day",
    "Direct economic losses (million CNY)",
    *[field for field, _, _ in INDICATORS],
]


def synthetic_csv(*, parent_1994: int = 40, include_child: bool = True,
                  missing_loss: bool = False) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=HEADERS)
    writer.writeheader()
    def add(level: str, eid: str, year: int, amount: str) -> None:
        row = {key: "" for key in HEADERS}
        row.update({
            "Event level": level, "Event ID": eid, "Start year": str(year),
            "Start month": "5", "Start day": "10",
            "Direct economic losses (million CNY)": amount,
        })
        row.update({field: amount for field, _, _ in INDICATORS})
        writer.writerow(row)
    add("L1", "1994-001", 1994, "" if missing_loss else str(parent_1994))
    if include_child:
        add("L2", "1994-001-01", 1994, "50")
    add("L1", "1995-001", 1995, "10")
    return stream.getvalue()


def synthetic_xlsx(*, years: tuple[int, ...] = (1994, 1995),
                   change_header: bool = False, formula: bool = False,
                   missing_last: bool = False, extra_cell: bool = False) -> bytes:
    xmlns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    headers = ["Year", *[item[1] for item in INDICATORS]]
    if change_header:
        headers[-1] = "Wrong metric"
    row_parts = []
    first = []
    for col, text in zip("ABCDEF", headers):
        first.append(f'<c r="{col}1" t="inlineStr"><is><t>{escape(text)}</t></is></c>')
    row_parts.append('<row r="1">' + "".join(first) + '</row>')
    for idx, year in enumerate(years, 2):
        cells = [f'<c r="A{idx}"><v>{year}</v></c>']
        for col in "BCDEF":
            if missing_last and idx == len(years) + 1 and col == "F":
                continue
            if formula and idx == 2 and col == "F":
                cells.append(f'<c r="{col}{idx}"><f>100</f><v>100</v></c>')
            else:
                cells.append(f'<c r="{col}{idx}"><v>100</v></c>')
        if extra_cell and idx == 2:
            cells.append(f'<c r="G2"><v>12</v></c>')
        row_parts.append(f'<row r="{idx}">' + "".join(cells) + '</row>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>' +
           f'<worksheet xmlns="{xmlns}"><sheetData>' + "".join(row_parts) +
           '</sheetData></worksheet>')
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", xml)
    return stream.getvalue()


class CFDIDAnnualCoverageTests(unittest.TestCase):
    def test_synthetic_l1_only_aggregate(self) -> None:
        result = reconcile_annual_coverage(
            synthetic_csv(), synthetic_xlsx(),
            strict_original=False, years=(1994, 1995),
        )
        self.assertEqual(result["years"], 2)
        self.assertTrue(result["nested_events_excluded"])
        self.assertEqual(result["l1_event_count"], 2)
        for item in result["indicators"].values():
            self.assertEqual(item["reported_l1_total"], "50")
            self.assertEqual(item["official_annual_total"], "200")
            self.assertEqual(item["coverage_percent"], "25.00")
            self.assertEqual(item["l1_nonmissing_reported_observations"], 2)

    def test_l1_missing_values_are_not_zero_observations(self) -> None:
        result = reconcile_annual_coverage(
            synthetic_csv(missing_loss=True), synthetic_xlsx(),
            strict_original=False, years=(1994, 1995),
        )
        for item in result["indicators"].values():
            self.assertEqual(item["l1_nonmissing_reported_observations"], 1)
            self.assertEqual(item["coverage_percent"], "5.00")

    def test_annual_over100_is_flagged_not_clipped(self) -> None:
        result = reconcile_annual_coverage(
            synthetic_csv(parent_1994=120), synthetic_xlsx(),
            strict_original=False, years=(1994, 1995),
        )
        for item in result["indicators"].values():
            self.assertEqual(item["years_over_100_percent"], [1994])
            self.assertEqual(item["coverage_percent"], "65.00")

    def test_wrong_original_header_fails_closed(self) -> None:
        with self.assertRaisesRegex(PreflightError, "headers"):
            parse_original_annual_workbook(synthetic_xlsx(change_header=True), years=(1994, 1995))

    def test_formula_cannot_use_stale_cache(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Formula"):
            parse_original_annual_workbook(synthetic_xlsx(formula=True), years=(1994, 1995))

    def test_missing_annual_value_fails_closed(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Missing or out-of-order"):
            parse_original_annual_workbook(synthetic_xlsx(missing_last=True), years=(1994, 1995))

    def test_populated_nonoriginal_column_fails_closed(self) -> None:
        with self.assertRaisesRegex(PreflightError, "Unexpected populated"):
            parse_original_annual_workbook(synthetic_xlsx(extra_cell=True), years=(1994, 1995))

    def test_incorrect_year_span_fails_closed(self) -> None:
        with self.assertRaisesRegex(PreflightError, "missing/extra"):
            parse_original_annual_workbook(synthetic_xlsx(), years=(1994,))

    def test_malformed_xlsx_fails_closed(self) -> None:
        with self.assertRaisesRegex(PreflightError, "malformed"):
            parse_original_annual_workbook(b"not an XLSX", years=(1994, 1995))

    def test_no_parent_event_missing_during_reconciliation(self) -> None:
        stream = synthetic_csv()
        stream = stream.replace("L1,1994-001,", "L1,1994-099,")
        with self.assertRaisesRegex(PreflightError, "Missing parents"):
            reconcile_annual_coverage(stream, synthetic_xlsx(), strict_original=False, years=(1994, 1995))


if __name__ == "__main__":
    unittest.main()
