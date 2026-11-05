# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, generated XLSX only; never fetch, embed or reveal HANZE original."""
from __future__ import annotations

from hashlib import md5, sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from xml.sax.saxutils import escape
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_runners.hanze_windstorm_original_xlsx_acquisition_v0 import OriginalHanzeError
from research_runners.hanze_windstorm_original_workbook_audit_v0 import (
    HEADERS, CONTRACT, _excel_date, audit_workbook,
)

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
COLS = tuple(chr(65 + n) for n in range(20))


def fixture(*, duplicate_id=False, malformed_header=False, formula=False,
            date1904=False, malicious_dtd=False, missing_econ=False) -> bytes:
    """Minimal Office XLSX with original header semantics and adversarial rows."""
    values = []
    def strid(text):
        text = str(text)
        if text not in values:
            values.append(text)
        return values.index(text)

    def cell(col, n, value=None, *, numeric=False, blank=False, with_formula=False):
        if blank:
            return f'<c r="{col}{n}" s="1"/>'
        if with_formula:
            return f'<c r="{col}{n}"><f>SUM(1,2)</f><v>3</v></c>'
        if numeric:
            return f'<c r="{col}{n}"><v>{value}</v></c>'
        return f'<c r="{col}{n}" t="s"><v>{strid(value)}</v></c>'

    hdr = list(HEADERS)
    if malformed_header:
        hdr[15] = "Losses (2020 euro) in millions"  # source's typo matters
    rows = ['<row r="1">' + "".join(cell(c, 1, h) for c, h in zip(COLS, hdr)) + '</row>']
    cases = [
        {"A": "20001", "B": "DE", "C": "2007", "D": "Germany",
         "E": "2007-01-18", "F": "2007-01-19", "G": "windstorm",
         "H": "Kyrill", "P": "100.00", "S": "Modelled economic loss from CDS",
         "T": "Provider candidate"},
        {"A": "20001" if duplicate_id else "20002", "B": "FR", "C": "2007",
         "D": "France", "E": "2007-01-18", "F": "2007-01-18",
         "G": "windstorm", "H": "Kyrill", "T": "Published source note"},
        {"A": "20003", "B": "ES", "C": "2014", "D": "Spain",
         "E": "42768", "F": "41672", "G": "windstorm",
         "H": "OTHER", "P": "300", "T": "Candidate"},
        {"A": "20004", "B": "RO", "C": "2019", "D": "Romania",
         "E": "43641", "F": "2019-06-25", "G": "windstorm",
         "H": "OTHER", "T": "Source 4"},
    ]
    if missing_econ:
        del cases[0]["P"]
    for i, fields in enumerate(cases, start=2):
        cols = []
        for col in COLS:
            if col in fields:
                cols.append(cell(col, i, fields[col],
                                 numeric=col in ("P",) or
                                 col in ("E", "F") and fields[col].isdigit(),
                                 with_formula=formula and i == 2 and col == "P"))
            elif col == "P":
                cols.append(cell(col, i, blank=True))
        rows.append(f'<row r="{i}">' + "".join(cols) + "</row>")
    ref_columns = ("No.", "Name", "URL", "Type")
    refrows = '<row r="1">' + "".join(cell(c, 1, h)
            for c, h in zip(COLS, ref_columns)) + '</row>'
    refrows += '<row r="2">' + "".join(cell(c, 2, x)
            for c, x in zip(COLS, ("1", "Source X", "https://example.org", "Report"))) + '</row>'
    shared = '<sst xmlns="' + NS + '">' + "".join(
        "<si><t>" + escape(v) + "</t></si>" for v in values
    ) + "</sst>"
    workbook = ('<workbook xmlns="' + NS + '"><workbookPr date1904="' +
                ("1" if date1904 else "0") + '"/></workbook>')
    pre = f'<worksheet xmlns="{NS}"><sheetData>'
    impact = pre + "".join(rows) + "</sheetData></worksheet>"
    sources = pre + refrows + "</sheetData></worksheet>"
    if malicious_dtd:
        impact = '<!DOCTYPE worksheet [<!ENTITY x "blocked-test-only">]>' + impact
    buf = BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", '<Types/>')
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/sharedStrings.xml", shared)
        z.writestr("xl/worksheets/sheet1.xml", impact)
        z.writestr("xl/worksheets/sheet2.xml", sources)
    return buf.getvalue()


def report(data):
    return audit_workbook(
        data, expected_size=len(data),
        expected_md5=md5(data).hexdigest(),
        expected_sha256=sha256(data).hexdigest(),
    )


class FullHANZEOriginalWorkbookAudit(unittest.TestCase):
    def test_original_source_has_strict_known_metadata(self):
        from research_runners import hanze_windstorm_original_workbook_audit_v0 as mod
        self.assertEqual(mod.EXPECTED_SOURCE_ROWS, 1_358)
        self.assertEqual(mod.EXPECTED_SOURCE_REFERENCES, 815)
        self.assertEqual(mod.EXPECTED_SOURCE_CODES, 33)
        self.assertEqual(mod.EXPECTED_SOURCE_MODELLED_CDS, 299)
        self.assertEqual(mod.EXPECTED_SOURCE_MISSING_ECONOMIC_LOSS, 638)
        self.assertEqual(mod.EXPECTED_SOURCE_KYRILL, 12)
        self.assertEqual(mod.EXPECTED_SOURCE_KYRILL_CDS, 4)

    def test_all_rows_dates_missing_losses_and_source_circularity(self):
        r = report(fixture())
        self.assertEqual(r["contract"], CONTRACT)
        self.assertEqual(r["original_impact_country_rows"], 4)
        self.assertEqual(r["unique_publisher_country_row_ids"], 4)
        self.assertEqual(r["country_code_count"], 4)
        self.assertEqual(r["original_reference_worksheet_rows"], 1)
        self.assertEqual(r["economic_loss_2020_eur_million_present"], 2)
        self.assertEqual(r["economic_loss_2020_eur_million_missing"], 2)
        self.assertEqual(r["nominal_economic_loss_value_present"], 0)
        self.assertEqual(r["explicit_publisher_modelled_cds_loss_rows"], 1)
        self.assertEqual(r["rows_with_excel_date_serials"], 2)
        self.assertEqual(r["year_differs_from_normalized_start_year"], 1)
        self.assertEqual(r["source_year_min"], 2007)
        self.assertEqual(r["source_year_max"], 2019)
        self.assertEqual(r["unresolved_date_rows"], [{
            "source_id": "20003", "problem": "END_BEFORE_START",
            "normalized_start": "2017-02-02", "normalized_end": "2014-02-02",
        }])
        self.assertEqual(r["named_kyrill_country_rows"], 2)
        self.assertEqual(
            {x["country_code"]: x["publisher_modelled_cds_loss"]
             for x in r["kyrill_candidates"]},
            {"DE": True, "FR": False},
        )
        self.assertEqual(
            {x["country_code"]: x["economic_loss_value_present"]
             for x in r["kyrill_candidates"]},
            {"DE": True, "FR": False},
        )
        self.assertFalse(r["published_loss_equals_observed_claim"])
        self.assertFalse(r["modelled_loss_eligible_for_independent_empirical_holdout"])
        self.assertFalse(r["other_loss_rows_independently_verified"])
        self.assertFalse(r["yearly_country_rows_are_independent_physical_storms"])
        self.assertIsNone(r["annual_event_frequency"])
        self.assertIsNone(r["annual_AEP"])
        self.assertIsNone(r["annual_OEP"])

    def test_excel_serials_and_bad_dates_are_distinct(self):
        self.assertEqual(_excel_date("31263"), "1985-08-04")
        self.assertEqual(_excel_date("31296"), "1985-09-06")
        self.assertEqual(_excel_date("43641"), "2019-06-25")
        self.assertEqual(_excel_date("42768"), "2017-02-02")
        self.assertEqual(_excel_date("41672"), "2014-02-02")
        self.assertEqual(_excel_date("2007-01-18"), "2007-01-18")
        for bad in (None, "", "notadate", "1900-02-29", "60", "-2", "NaN"):
            with self.subTest(bad=bad):
                self.assertIsNone(_excel_date(bad))

    def test_blank_selfclosing_cell_never_inherits_next_source_note(self):
        r = report(fixture())
        fr = next(x for x in r["kyrill_candidates"] if x["country_code"] == "FR")
        self.assertFalse(fr["economic_loss_value_present"])
        self.assertEqual(r["economic_loss_2020_eur_million_missing"], 2)
        r2 = report(fixture(missing_econ=True))
        self.assertEqual(r2["economic_loss_2020_eur_million_present"], 1)
        self.assertEqual(r2["economic_loss_2020_eur_million_missing"], 3)

    def test_provider_identity_never_inferred_from_synthetic_zip(self):
        with self.assertRaisesRegex(OriginalHanzeError, "original source"):
            audit_workbook(fixture())

    def test_duplicate_id_and_source_header_schema_rejected(self):
        with self.assertRaisesRegex(OriginalHanzeError, "duplicate"):
            report(fixture(duplicate_id=True))
        with self.assertRaisesRegex(OriginalHanzeError, "schema drift"):
            report(fixture(malformed_header=True))

    def test_excel_1904_date_mode_and_formula_rejected(self):
        with self.assertRaisesRegex(OriginalHanzeError, "1904"):
            report(fixture(date1904=True))
        with self.assertRaisesRegex(OriginalHanzeError, "formulas prohibited"):
            report(fixture(formula=True))

    def test_malicious_xml_dtd_rejected_without_expansion(self):
        with self.assertRaisesRegex(OriginalHanzeError, "DTD"):
            report(fixture(malicious_dtd=True))

    def test_original_producer_evidence_has_no_annual_or_insured_admission(self):
        out = report(fixture())
        for key in ("annual_AAL", "annual_AEP", "annual_OEP",
                    "annual_event_frequency"):
            self.assertIsNone(out[key])
        for key in ("original_data_rights_admitted", "source_rows_promoted_to_cat",
                    "c3s_climk_native_event_ids_joined"):
            self.assertFalse(out[key])


if __name__ == "__main__":
    unittest.main()
