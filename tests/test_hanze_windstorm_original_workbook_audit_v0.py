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
    kyrill_country_source_candidate, EXPECTED_KYRILL_COUNTRY_ID_PAIRS,
)

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
COLS = tuple(chr(65 + n) for n in range(20))


def fixture(*, duplicate_id=False, malformed_header=False, formula=False,
            date1904=False, malicious_dtd=False, missing_econ=False,
            invalid_econ=None) -> bytes:
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
    if invalid_econ is not None:
        cases[2]["P"] = invalid_econ
    for i, fields in enumerate(cases, start=2):
        cols = []
        for col in COLS:
            if col in fields:
                cols.append(cell(col, i, fields[col],
                                 numeric=(col == "P" and invalid_econ is None) or
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
        self.assertEqual(mod.EXPECTED_SOURCE_NUMERIC_ECONOMIC_LOSS, 687)
        self.assertEqual(mod.EXPECTED_SOURCE_NONNUMERIC_ECONOMIC_LOSS, 33)
        self.assertEqual(mod.EXPECTED_SOURCE_ORIGIN_MATRIX, {
            "explicit_publisher_CDS_modelled": {
                "numeric": 278, "non_numeric": 21, "blank": 0,
            },
            "not_flagged_CDS_independence_unverified": {
                "numeric": 409, "non_numeric": 12, "blank": 638,
            },
        })
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
        self.assertEqual(r["economic_loss_2020_eur_million_numeric"], 2)
        self.assertEqual(r["economic_loss_2020_eur_million_non_numeric"], 0)
        self.assertEqual(r["economic_loss_by_publisher_CDS_flag_and_numeric_class"], {
            "explicit_publisher_CDS_modelled": {"numeric": 1, "non_numeric": 0, "blank": 0},
            "not_flagged_CDS_independence_unverified": {"numeric": 1, "non_numeric": 0, "blank": 2},
        })
        self.assertFalse(r["not_flagged_CDS_means_independently_observed"])
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

    def test_kyrill_source_country_candidacy_never_becomes_physical_event(self):
        source = report(fixture())
        group = source["kyrill_source_country_review_candidate"]
        self.assertEqual(group["country_codes"], ["DE", "FR"])
        self.assertEqual(group["review_day_intersection_start"], "2007-01-18")
        self.assertEqual(group["review_day_intersection_end"], "2007-01-18")
        self.assertEqual(group["country_report_rows"], 2)
        self.assertEqual(group["country_codes_explicitly_modelled_cds"], ["DE"])
        self.assertEqual(group["country_codes_without_economic_loss_value"], ["FR"])
        self.assertEqual(group["country_codes_not_explicitly_modelled_cds"], ["FR"])
        self.assertEqual(group["source_country_id_pairs"], [
            {"country_code": "DE", "publisher_row_id": "20001"},
            {"country_code": "FR", "publisher_row_id": "20002"},
        ])
        self.assertFalse(group["other_country_rows_independently_observed"])
        self.assertIsNone(group["published_cross_country_parent_storm_id"])
        self.assertIsNone(group["native_c3s_climk_oasis_parent_id"])
        self.assertIsNone(group["independent_physical_hazard_occurrences"])
        for metric in ("annual_event_frequency", "annual_AAL", "annual_AEP", "annual_OEP"):
            self.assertIsNone(group[metric])
        self.assertFalse(group["scientific_or_rights_admitted"])

    def test_all_twelve_original_country_identifiers_are_only_review_candidates(self):
        self.assertEqual(len(EXPECTED_KYRILL_COUNTRY_ID_PAIRS), 12)
        rows = []
        modelled = {"AT", "IE", "LU", "PL"}
        for code, sid in EXPECTED_KYRILL_COUNTRY_ID_PAIRS:
            rows.append({
                "source_id": sid, "country_code": code,
                "date_start": "2007-01-17" if code in ("DK", "IE", "NL", "CH", "UK")
                              else "2007-01-18",
                "date_end": "2007-01-19" if code in ("DE", "DK", "IE", "PL", "UK")
                            else "2007-01-18",
                "publisher_modelled_cds_loss": code in modelled,
                "economic_loss_value_present": True,
            })
        result = kyrill_country_source_candidate(rows)
        self.assertEqual(result["review_day_intersection_start"], "2007-01-18")
        self.assertEqual(result["review_day_intersection_end"], "2007-01-18")
        self.assertEqual(result["country_report_rows"], 12)
        self.assertEqual(result["country_codes_explicitly_modelled_cds"],
                         ["AT", "IE", "LU", "PL"])
        self.assertEqual(
            [(x["country_code"], x["publisher_row_id"])
             for x in result["source_country_id_pairs"]],
            list(EXPECTED_KYRILL_COUNTRY_ID_PAIRS))
        self.assertIsNone(result["independent_physical_hazard_occurrences"])

    def test_kyrill_cross_country_group_rejects_duplicate_and_inconsistent_horizon(self):
        cases = [
            {"source_id":"20001", "country_code":"DE",
             "date_start":"2007-01-18", "date_end":"2007-01-19",
             "publisher_modelled_cds_loss":False,
             "economic_loss_value_present":True},
            {"source_id":"20002", "country_code":"FR",
             "date_start":"2007-01-18", "date_end":"2007-01-18",
             "publisher_modelled_cds_loss":False,
             "economic_loss_value_present":True},
        ]
        self.assertEqual(kyrill_country_source_candidate(cases)["country_report_rows"],2)
        trials = [
            [cases[0], cases[0]],
            [cases[0], {**cases[1], "source_id":cases[0]["source_id"]}],
            [cases[0], {**cases[1], "country_code":cases[0]["country_code"]}],
            [cases[0], {**cases[1], "date_start":"2007-01-20",
                        "date_end":"2007-01-20"}],
            [cases[0], {**cases[1], "date_start":"2007-01-21",
                        "date_end":"2007-01-20"}],
            [cases[0], {**cases[1], "date_start":"2008-01-18",
                        "date_end":"2008-01-18"}],
            [cases[0], {**cases[1], "date_start":"2007-99-99"}],
            [cases[0], {**cases[1], "publisher_modelled_cds_loss":1}],
            [cases[0], {**cases[1], "economic_loss_value_present":"unknown"}],
            [cases[0], {**cases[1], "country_code":"D3"}],
            [cases[0], {**cases[1], "source_id":True}],
        ]
        for index, candidate in enumerate(trials):
            with self.subTest(index=index),self.assertRaises(OriginalHanzeError):
                kyrill_country_source_candidate(candidate)
        for candidate in ([], None, "Kyrill", [{}] * 34):
            with self.subTest(candidate_type=type(candidate).__name__),self.assertRaises(OriginalHanzeError):
                kyrill_country_source_candidate(candidate)

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

    def test_source_non_numeric_economic_loss_not_silently_zero_or_observed(self):
        for value in ("not reported", "n/a", "NaN", "Infinity", "-100"):
            with self.subTest(value=value):
                receipt = report(fixture(invalid_econ=value))
                self.assertEqual(receipt["economic_loss_2020_eur_million_present"], 2)
                self.assertEqual(receipt["economic_loss_2020_eur_million_missing"], 2)
                self.assertEqual(receipt["economic_loss_2020_eur_million_numeric"], 1)
                self.assertEqual(receipt["economic_loss_2020_eur_million_non_numeric"], 1)
                self.assertEqual(receipt["economic_loss_by_publisher_CDS_flag_and_numeric_class"], {
                    "explicit_publisher_CDS_modelled": {"numeric": 1, "non_numeric": 0, "blank": 0},
                    "not_flagged_CDS_independence_unverified": {"numeric": 0, "non_numeric": 1, "blank": 2},
                })
                self.assertEqual(receipt["economic_loss_2020_eur_million_non_numeric_source_rows"], [
                    {"source_id": "20003", "country_code": "ES",
                     "problem": "NON_NUMERIC_OR_INVALID_PUBLISHED_ECONOMIC_LOSS"}])
                self.assertFalse(receipt["economic_loss_non_numeric_rows_admitted_as_claims"])
                self.assertFalse(receipt["published_loss_equals_observed_claim"])
                self.assertIsNone(receipt["annual_AAL"])
                self.assertIsNone(receipt["annual_AEP"])
                self.assertIsNone(receipt["annual_OEP"])

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
