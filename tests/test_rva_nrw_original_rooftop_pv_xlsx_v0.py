# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-OOXML tests; do not fetch any provider XLSX here."""
import hashlib
import io
import unittest
import zipfile

from research_runners import rva_nrw_original_rooftop_pv_xlsx_v0 as m

CONTENT_TYPES = b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types" />'
WORKBOOK = (b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b'<sheets><sheet name="public aggregate" sheetId="1"/></sheets></workbook>')
SHEET_BEGIN = (b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
               b'<sheetData><row r="1"><c r="A1"><v>1</v></c>'
               b'<c r="B1"><v>2</v></c></row></sheetData>')
SHEET_END = b'</worksheet>'


def make_xlsx(*, extra=None, formula=False, two_columns=True):
    tail = b'<!--' + b'Z' * 1300 + b'-->'
    if not two_columns:
        sheet = (SHEET_BEGIN.replace(b'<c r="B1"><v>2</v></c>', b'') +
                 tail + SHEET_END)
    else:
        if formula:
            tail = b'<f>BAD()</f>' + tail
        sheet = SHEET_BEGIN + tail + SHEET_END
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("xl/workbook.xml", WORKBOOK)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        for path, payload in (extra or []):
            z.writestr(path, payload)
    payload = buf.getvalue()
    assert len(payload) < m.MAX_SOURCE_BYTES
    # Original Xlsx minimum is 1,024 bytes; synthetic tests can pad archive
    # with harmless bytes inside ZIP comment, still standard Zip.
    if len(payload) < 1024:
        out = io.BytesIO(payload)
        with zipfile.ZipFile(out, "a") as z:
            z.comment = b"Synthetic original package fixture only: " + b"Q" * (1100 - len(payload))
        payload = out.getvalue()
    assert len(payload) >= 1024
    return payload


class RvaNrwPvOriginalTests(unittest.TestCase):
    def test_parse_synthetic_aggregate_xlsx_only(self):
        blob = make_xlsx()
        got = m.parse_original(blob)
        self.assertEqual(got["original_sha256"], hashlib.sha256(blob).hexdigest())
        self.assertEqual(got["worksheet_count"], 1)
        self.assertEqual(got["worksheet_structure"][0]["occupied_row_elements"], 1)
        self.assertEqual(got["worksheet_structure"][0]["max_occupied_columns"], 2)
        self.assertEqual(got["source_geography"], "NRW_MUNICIPALITY_AGGREGATE")

    def test_no_insured_roof_or_installed_pv_claim(self):
        got = m.parse_original(make_xlsx())
        for key in ("insured_company_sites_observed", "pv_installed_units_observed",
                    "insurer_roof_pv_endorsement_observed", "actual_model_input_admitted",
                    "original_sha_pinned_in_source_code"):
            self.assertIs(got[key], False)

    def test_reject_zip_with_macro(self):
        with self.assertRaisesRegex(ValueError, "UNSAFE"):
            m.parse_original(make_xlsx(extra=[("xl/vbaProject.bin", b"malicious")]))

    def test_reject_zip_with_external_links(self):
        with self.assertRaisesRegex(ValueError, "UNSAFE"):
            m.parse_original(make_xlsx(extra=[("xl/externalLinks/externalLink1.xml", b"<link/>")]))

    def test_reject_formulas_even_in_public_xlsx(self):
        with self.assertRaisesRegex(ValueError, "FORMULAS"):
            m.parse_original(make_xlsx(formula=True))

    def test_reject_one_column_aggregate(self):
        with self.assertRaisesRegex(ValueError, "FEW_COLUMNS"):
            m.parse_original(make_xlsx(two_columns=False))

    def test_reject_malformed_xlsx(self):
        with self.assertRaisesRegex(ValueError, "BAD_STRUCTURE"):
            m.parse_original(b"not a real xlsx" * 150)

    def test_reject_bad_zip_file_size(self):
        with self.assertRaisesRegex(ValueError, "BAD_SIZE"):
            m.parse_original(b"a" * 70)

    def test_reject_invalid_nontype_bytes(self):
        with self.assertRaisesRegex(ValueError, "NOT_BYTES"):
            m.parse_original("not bytes")

    def test_reject_traversal_member(self):
        with self.assertRaisesRegex(ValueError, "UNSAFE"):
            m.parse_original(make_xlsx(extra=[("../secret.csv", b"never include")]))

    def test_reject_empty_worksheet(self):
        blob = make_xlsx()
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            files={p:z.read(p) for p in z.namelist()}
        files["xl/worksheets/sheet1.xml"]=(b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              b'<sheetData /></worksheet>')
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
            for k,v in files.items():z.writestr(k,v)
            z.comment=b"x"*1600
        with self.assertRaisesRegex(ValueError, "EMPTY_WORKSHEET"):
            m.parse_original(out.getvalue())


if __name__ == "__main__":
    unittest.main()
