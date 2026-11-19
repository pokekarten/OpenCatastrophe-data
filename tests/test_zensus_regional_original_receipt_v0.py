# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic miniature OOXML only: genuine Zensus source never embedded."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import hashlib
import sys
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research_runners"))
from zensus_regional_original_receipt_v0 import (
    inspect_original_package, download_original, OriginalReceiptError,
)


def mock_ooxml(sheets=None, content_types=True, worksheet=True):
    if sheets is None:
        sheets=["Erläuterungen zur Methodik", "Gebäude mit Wohnraum", "CSV_Gebaeude"]
    names="".join(
        '<sheet name="'+name+'" sheetId="'+str(i+1)+'"/>'
        for i,name in enumerate(sheets))
    wb=(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheets>'+names+'</sheets></workbook>'
    )
    out=BytesIO()
    with ZipFile(out,"w",compression=ZIP_DEFLATED) as z:
        if content_types: z.writestr("[Content_Types].xml","<Types/>")
        z.writestr("xl/workbook.xml",wb)
        if worksheet:z.writestr("xl/worksheets/sheet1.xml","<worksheet/>")
    return out.getvalue()


class ZensusExactOriginalReceiptTests(unittest.TestCase):
    def test_receipt_has_real_sha_sheets_and_explicit_blocks(self):
        raw=mock_ooxml()
        out=inspect_original_package(raw)
        self.assertEqual(out["original_file_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(out["original_file_bytes"],len(raw))
        self.assertEqual(out["original_worksheet_count"],3)
        self.assertTrue(out["methodology_named_worksheet_present"])
        self.assertEqual(out["csv_or_machine_readable_named_sheets"],["CSV_Gebaeude"])
        self.assertTrue(out["ooxml_package_structure_verified"])
        for field in ("original_numerical_cells_validated","kreis_ags_column_verified",
                      "building_population_column_verified",
                      "suppression_symbols_methodology_checked","district_2022_buildings_admitted",
                      "gdv_original_data_acquired","insurer_regional_risk_sites_observed",
                      "nextgen_cat_model_input_approved"):
            self.assertFalse(out[field],field)

    def test_same_bytes_reproducibly_sha(self):
        raw=mock_ooxml()
        self.assertEqual(inspect_original_package(raw),inspect_original_package(raw))

    def test_exact_official_publisher_url_mandatory(self):
        for url in ("http://www.destatis.de/filename.xlsx",
                    "https://www.destatis.de/other.xlsx",
                    "https://data.example.org/filename.xlsx"):
            with self.subTest(url=url),self.assertRaisesRegex(OriginalReceiptError,"exact"):
                inspect_original_package(mock_ooxml(),source_url=url)
            with self.subTest(download_url=url),self.assertRaisesRegex(OriginalReceiptError,"exact"):
                download_original(url)

    def test_non_zip_and_garbage_blocked(self):
        for raw in (b"not-ooxml",b"PKgarbage",b"",b"01234567890123456"):
            with self.subTest(raw=raw[:10]),self.assertRaises(OriginalReceiptError):
                inspect_original_package(raw)

    def test_missing_ooxml_components_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"missing original"):
            inspect_original_package(mock_ooxml(content_types=False))
        with self.assertRaisesRegex(OriginalReceiptError,"missing original"):
            inspect_original_package(mock_ooxml(worksheet=False))

    def test_duplicate_sheets_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"duplicate"):
            inspect_original_package(mock_ooxml(["Gebäude","Gebäude"]))

    def test_methodology_absent_cannot_be_claimed(self):
        out=inspect_original_package(mock_ooxml(["Data"]))
        self.assertFalse(out["methodology_named_worksheet_present"])

    def test_workbook_xml_is_required_and_parseable(self):
        buf=BytesIO()
        with ZipFile(buf,"w",compression=ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml","<Types/>")
            z.writestr("xl/workbook.xml","<not-workbook>")
            z.writestr("xl/worksheets/sheet1.xml","<worksheet/>")
        with self.assertRaisesRegex(OriginalReceiptError,"malformed"):
            inspect_original_package(buf.getvalue())

    def test_empty_sheets_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"lacks sheets|unavailable"):
            inspect_original_package(mock_ooxml([]))

    def test_source_file_is_not_repackaged_or_synthetically_rehashed(self):
        a=mock_ooxml(["CSV_1"])
        b=mock_ooxml(["CSV_2"])
        self.assertNotEqual(inspect_original_package(a)["original_file_sha256"],
                            inspect_original_package(b)["original_file_sha256"])


if __name__=="__main__":
    unittest.main()
