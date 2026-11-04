# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original EIA-860 2025 generator/utility workbook schema tests."""
from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import json
import unittest

from research_runners import eia860_2025_generator_utility_schema_v0 as m

NS=m.eia.NS
DOC=m.eia.DOC_REL
REL=m.eia.REL


def row(index, headers):
    cells = "".join(
        '<c r="%s%d" t="inlineStr"><is><t>%s</t></is></c>' %
        (chr(65+i), index, s)
        for i,s in enumerate(headers)
    )
    return f'<row r="{index}">{cells}</row>'


def xlsx(sheets, *, duplicate_relation=False, source_secret=False):
    buf=BytesIO()
    root=f'<workbook xmlns="{NS}" xmlns:r="{DOC}"><sheets>'
    relations=f'<Relationships xmlns="{REL}">'
    for i,(name,headers) in enumerate(sheets,1):
        root+=f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
        relid="rId1" if duplicate_relation else "rId"+str(i)
        relations+=f'<Relationship Id="{relid}" Type="{DOC}/worksheet" Target="worksheets/sheet{i}.xml"/>'
    root+='</sheets></workbook>'
    relations+='</Relationships>'
    with ZipFile(buf,"w",ZIP_DEFLATED) as out:
        out.writestr("xl/workbook.xml",root)
        out.writestr("xl/_rels/workbook.xml.rels",relations)
        for i,(name,headers) in enumerate(sheets,1):
            fake_value='SECRET OWNERSHIP COMPANY DO NOT EMIT' if source_secret else 'FIXTURE'
            sheet=(f'<worksheet xmlns="{NS}"><sheetData>'+
                   row(1,headers)+row(2,["599","GEN-X",fake_value])+
                   '</sheetData></worksheet>')
            out.writestr(f"xl/worksheets/sheet{i}.xml",sheet)
    return buf.getvalue()


def standard_generator():
    return xlsx([("Operable",["Plant Code","Generator ID","Utility ID"]),
                 ("Proposed",["Plant Code","Generator ID","Status"]),
                 ("Retired and Canceled",["Plant Code","Generator ID","Status"])])


class GeneratorSourceSchemaTests(unittest.TestCase):
    def test_three_status_tabs_are_not_collapsed(self):
        x=m.inspect_workbook(standard_generator(),scope="generator")
        self.assertEqual(x["worksheet_count"],3)
        self.assertEqual([v["name"] for v in x["worksheets"]],
                         ["Operable","Proposed","Retired and Canceled"])
        self.assertTrue(all(v["plant_code_and_generator_id_same_header_row"]==1
                            for v in x["worksheets"]))
        self.assertFalse(x["raw_generator_rows_or_owner_names_exported"])

    def test_utility_can_have_source_specific_sheet_title(self):
        x=m.inspect_workbook(xlsx([("Utility",["Utility ID","Utility Name"])]),scope="utility")
        self.assertEqual(x["worksheet_count"],1)
        self.assertIn("Utility ID",x["worksheets"][0]["fixed_allowlist_header_labels"])

    def test_source_generator_and_owner_ids_not_emitted(self):
        x=m.inspect_workbook(xlsx([
             ("Operable",["Plant Code","Generator ID","Utility Name"]),
             ("Proposed",["Plant Code","Generator ID"]),
             ("Retired and Canceled",["Plant Code","Generator ID"]),
        ],source_secret=True),scope="generator")
        rendered=json.dumps(x)
        self.assertNotIn("SECRET OWNERSHIP",rendered)
        self.assertNotIn("GEN-X",rendered)
        self.assertNotIn("599",rendered)

    def test_unknown_header_not_whitelisted(self):
        x=m.inspect_workbook(xlsx([("Utility",["Name of Our Company"])]),scope="utility")
        self.assertEqual(x["worksheets"][0]["fixed_allowlist_header_labels"],[])

    def test_wrong_reporting_scope_blocks_not_guessed(self):
        with self.assertRaisesRegex(m.GeneratorRosterBlocked,"reporting scope"):
            m.inspect_workbook(xlsx([("Operable",["Plant Code"])]),scope="generator")

    def test_bad_zip_is_blocked(self):
        for blob in (b"",b"not a ZIP",b"x"*(m.MAX_UTILITY_XLSX+1)):
            with self.subTest(bytes=len(blob)),self.assertRaises(m.GeneratorRosterBlocked):
                m.inspect_workbook(blob,scope="utility")

    def test_unknown_scope_blocks(self):
        with self.assertRaises(m.GeneratorRosterBlocked):
            m.inspect_workbook(standard_generator(),scope="latest")

    def test_external_title_and_duplicate_sheet_rejected(self):
        with self.assertRaises(m.GeneratorRosterBlocked):
            m.inspect_workbook(xlsx([("../BAD",["Plant Code"])]),scope="utility")
        with self.assertRaises(m.GeneratorRosterBlocked):
            m.inspect_workbook(xlsx([("Utility",[]),("Utility",[])]),scope="utility")

    def test_substituting_synthetic_outer_zip_must_fail_original_sha(self):
        with self.assertRaises(m.GeneratorRosterBlocked):
            m.inspect_original_zip(standard_generator())

    def test_pinned_source_product_filenames(self):
        self.assertEqual(m.GENERATOR_MEMBER,"3_1_Generator_Y2025.xlsx")
        self.assertEqual(m.UTILITY_MEMBER,"1___Utility_Y2025.xlsx")
        self.assertEqual(m.SOURCE_SHA,"2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba")


if __name__=="__main__":
    unittest.main()
