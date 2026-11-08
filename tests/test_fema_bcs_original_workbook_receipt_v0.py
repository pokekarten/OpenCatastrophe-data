# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hermetic synthetic OOXML tests; no FEMA workbook or network access."""
import hashlib
import io
import unittest
import zipfile
from unittest import mock

from research_runners import fema_bcs_original_workbook_receipt_v0 as m

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
CORE = {
    "[Content_Types].xml": b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types" />',
    "xl/workbook.xml": f'<workbook xmlns="{NS}" xmlns:r="{REL}"><workbookPr date1904="0"/><sheets><sheet name="SYNTHETIC NO FEMA" sheetId="1" r:id="rId1"/></sheets></workbook>'.encode(),
    "xl/_rels/workbook.xml.rels": f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="{REL}/worksheet"/></Relationships>'.encode(),
    "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{NS}"><sheetData><row r="1"><c r="A1"><v>1</v></c><c r="B1"><v>2</v></c></row></sheetData></worksheet>'.encode(),
}


def fake(**changes):
    files = {**CORE, **changes}
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for path, data in files.items():
            z.writestr(path, data)
        z.comment = b"SYNTHETIC SOURCE CONTRACT ONLY " + b"x" * 1500
    return output.getvalue()


class OriginalFemaReceiptTests(unittest.TestCase):
    def test_verified_synthetic_workbook_structure(self):
        raw = fake()
        result = m.inspect_original(raw)
        self.assertEqual(result["original_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["original_bytes"], len(raw))
        self.assertEqual(result["worksheets"][0]["sheet_name"], "SYNTHETIC NO FEMA")
        self.assertEqual(result["worksheets"][0]["row_element_count"], 1)
        self.assertEqual(result["worksheets"][0]["first_row_cell_references"], ["A1", "B1"])
        for key in ("source_cell_values_emitted", "source_rights_reviewed",
                    "original_source_admitted", "aep_or_oep_calculated",
                    "prior_hash_pin_verified"):
            self.assertIs(result[key], False)

    def test_hash_pin_explicit_and_checked(self):
        raw = fake()
        good = hashlib.sha256(raw).hexdigest()
        self.assertTrue(m.inspect_original(raw, expected_sha256=good)["prior_hash_pin_verified"])
        for wrong in ("0" * 64, "bad", "A" * 64):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(m.OriginalFEMASourceError, "SHA-256"):
                m.inspect_original(raw, expected_sha256=wrong)

    def test_cannot_read_unbounded_or_non_xlsx(self):
        for raw in (b"z" * 64, "not bytes", None, b"z" * 2048):
            with self.subTest(value=type(raw).__name__), self.assertRaises(m.OriginalFEMASourceError):
                m.inspect_original(raw)

    def test_external_relationship_disallowed(self):
        hostile = CORE["xl/_rels/workbook.xml.rels"].replace(
            b'Target="worksheets/sheet1.xml"',
            b'Target="https://example.com/sheet.xml" TargetMode="External"')
        with self.assertRaisesRegex(m.OriginalFEMASourceError, "external"):
            m.inspect_original(fake(**{"xl/_rels/workbook.xml.rels": hostile}))

    def test_traversal_relationship_disallowed(self):
        bad = CORE["xl/_rels/workbook.xml.rels"].replace(b"worksheets/sheet1.xml", b"../../passwd")
        with self.assertRaisesRegex(m.OriginalFEMASourceError, "relationship"):
            m.inspect_original(fake(**{"xl/_rels/workbook.xml.rels": bad}))

    def test_macro_and_external_links_disallowed(self):
        for name in ("xl/vbaProject.bin", "xl/externalLinks/externalLink1.xml",
                     "xl/connections.xml", "../evil.txt"):
            with self.subTest(name=name), self.assertRaises(m.OriginalFEMASourceError):
                m.inspect_original(fake(**{name: b"danger"}))

    def test_duplicate_zip_entry_disallowed(self):
        data = io.BytesIO(fake())
        import warnings
        with zipfile.ZipFile(data, "a") as z, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            z.writestr("xl/workbook.xml", CORE["xl/workbook.xml"])
        with self.assertRaisesRegex(m.OriginalFEMASourceError, "duplicate"):
            m.inspect_original(data.getvalue())

    def test_formula_count_metadata_no_evaluation(self):
        formula = CORE["xl/worksheets/sheet1.xml"].replace(
            b"<v>2</v>", b"<f>SUM(1,1)</f><v>2</v>")
        result = m.inspect_original(fake(**{"xl/worksheets/sheet1.xml": formula}))
        self.assertEqual(result["worksheets"][0]["formula_element_count"], 1)
        self.assertIs(result["source_cell_values_emitted"], False)

    def test_sheet_cell_values_not_in_output(self):
        sheet = CORE["xl/worksheets/sheet1.xml"].replace(b"<v>1</v>", b"<v>987654321</v>")
        result = m.inspect_original(fake(**{"xl/worksheets/sheet1.xml": sheet}))
        self.assertNotIn("987654321", str(result))

    def test_bad_cell_reference_fail_closed(self):
        sheet = CORE["xl/worksheets/sheet1.xml"].replace(b'r="A1"', b'r="../../../secret"')
        with self.assertRaisesRegex(m.OriginalFEMASourceError, "cell reference"):
            m.inspect_original(fake(**{"xl/worksheets/sheet1.xml": sheet}))

    def test_missing_package_member(self):
        data = {k:v for k,v in CORE.items() if k != "xl/_rels/workbook.xml.rels"}
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            for k,v in data.items():
                z.writestr(k,v)
            z.comment = b"A" * 1500
        with self.assertRaisesRegex(m.OriginalFEMASourceError, "relationships missing"):
            m.inspect_original(output.getvalue())

    def test_zip_expansion_budget(self):
        oversize = zipfile.ZipInfo("xl/huge.xml")
        oversize.file_size = m.MAX_SINGLE_XML_BYTES + 1
        archive = mock.Mock()
        archive.infolist.return_value = [oversize, zipfile.ZipInfo("a"), zipfile.ZipInfo("b")]
        with self.assertRaises(m.OriginalFEMASourceError):
            m._validated_zip(archive)

    def test_official_fetch_rejects_unreviewed_redirect(self):
        class Response:
            headers = {"Content-Length": "1500"}
            def geturl(self): return "https://evil.example/original.xlsx"
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self, n): return b""
        def opener(req, timeout): return Response()
        with self.assertRaisesRegex(m.OriginalFEMASourceError, "redirected"):
            m.fetch_official(opener=opener)


if __name__ == "__main__":
    unittest.main()
