# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic generator-owner native XLSX schema inspection and privacy controls."""
from __future__ import annotations

from io import BytesIO
import json
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners import eia860_2025_original_owner_schema_v0 as w
from tests.test_eia860_annual_2025_original_zip_v0 import fake_xlsx, cell, M


def owner_fixture(*,name="Ownership",header=True):
    head='<row r="1">'+(
        cell("A",1,"Plant Code",text=True)+
        cell("B",1,"Generator ID",text=True)+
        cell("C",1,"Owner Name",text=True)+
        cell("D",1,"Percent Owned",text=True) if header
        else cell("A",1,"Random Field",text=True))+'</row>'
    data='<row r="2">'+(
        cell("A",2,"599")+cell("B",2,"X1",text=True)+
        cell("C",2,"SOURCE-PRIVATE-NAME",text=True)+
        cell("D",2,"40"))+'</row>'
    sheet='<worksheet xmlns="'+M+'"><sheetData>'+head+data+'</sheetData></worksheet>'
    return fake_xlsx(sheet_name=name,custom_sheet=sheet)


class OwnerSchemaMetadataTests(unittest.TestCase):
    def test_detects_header_only_with_no_source_row_leak(self):
        res=w.inspect_owner_workbook_member(owner_fixture())
        self.assertEqual(len(res),1)
        self.assertEqual(res[0]["sheet_name"],"Ownership")
        self.assertEqual(res[0]["candidate_plant_generator_or_owner_header_rows"],1)
        self.assertEqual(res[0]["rows_scanned_for_header_only"],2)
        self.assertIn("Percent Owned",res[0]["recognized_allowlisted_header_tokens"])
        self.assertFalse(res[0]["arbitrary_source_rows_or_values_emitted"])
        self.assertNotIn("SOURCE-PRIVATE-NAME",json.dumps(res))
        self.assertNotIn("X1",json.dumps(res))

    def test_worksheet_header_not_guessed_if_missing(self):
        res=w.inspect_owner_workbook_member(owner_fixture(header=False))
        self.assertEqual(res[0]["candidate_plant_generator_or_owner_header_rows"],0)
        self.assertNotIn("Random Field",json.dumps(res))

    def test_no_original_bytes_or_oversized_member(self):
        for raw in (b"",b"bad zip",b"x"*(w.MAX_OWNER_XLSX+1)):
            with self.subTest(length=len(raw)),self.assertRaises(w.OwnerSchemaBlocked):
                w.inspect_owner_workbook_member(raw)

    def test_rejects_unexpected_worksheet_title(self):
        with self.assertRaises(w.OwnerSchemaBlocked):
            w.inspect_owner_workbook_member(owner_fixture(name="../Private"))

    def test_rejects_missing_internal_workbook_relationship(self):
        b=BytesIO()
        with ZipFile(b,"w",ZIP_DEFLATED) as z:
            z.writestr("xl/workbook.xml",'<workbook xmlns="'+M+'"><sheets><sheet name="Owner" sheetId="1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
        with self.assertRaises(w.OwnerSchemaBlocked):
            w.inspect_owner_workbook_member(b.getvalue())

    def test_corrupt_source_outer_zip_never_softens_hash(self):
        with self.assertRaises(w.OwnerSchemaBlocked):
            w.inspect_owner_original_zip(b"not the pinned EIA-860 original ZIP")

    def test_source_contract_never_exports_ownership_values(self):
        self.assertEqual(w.OWNER_MEMBER,"4___Owner_Y2025.xlsx")
        self.assertEqual(w.eia.PINNED_ORIGINAL_SHA256,
                         "2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba")
        self.assertTrue(w.MAX_FIRST_ROWS <= 35)


if __name__=="__main__":
    unittest.main()
