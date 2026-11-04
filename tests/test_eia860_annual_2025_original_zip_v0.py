# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only original EIA annual XLSX/ZIP parsing and source non-admission."""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
import unittest
from xml.sax.saxutils import escape

from research_runners import eia860_annual_2025_original_zip_v0 as w

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"


def cell(col, row, value, *, text=False):
    if text:
        return f'<c r="{col}{row}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
    return f'<c r="{col}{row}"><v>{escape(str(value))}</v></c>'


def fake_xlsx(rows=None, *, sheet_name="Plant", custom_sheet=None, shared=False):
    if rows is None:
        rows = [("599", "DE", "Synthetic Dover"), ("591", "DE", "Synthetic Wilmington"),
                ("3136", "PA", "Synthetic separate PA")]
    if not shared:
        sheet_rows = ['<row r="1">' +
                      cell("A",1,"Plant Code",text=True) +
                      cell("B",1,"State",text=True) +
                      cell("C",1,"Plant Name",text=True) + '</row>']
        for index,(code,st,name) in enumerate(rows, 2):
            sheet_rows.append(f'<row r="{index}">' +
                              cell("A",index,code) + cell("B",index,st,text=True) +
                              cell("C",index,name,text=True) + '</row>')
        shared_xml = None
    else:
        strings=["Plant Code","State","Plant Name","DE","PA","Synthetic"]
        shared_xml = ('<sst xmlns="'+M+'">'+
                      "".join('<si><t>'+s+'</t></si>' for s in strings)+'</sst>')
        sheet_rows=['<row r="1">'+
                    '<c r="A1" t="s"><v>0</v></c>'+
                    '<c r="B1" t="s"><v>1</v></c>'+
                    '<c r="C1" t="s"><v>2</v></c></row>']
        for index, (code,st,_) in enumerate(rows,2):
            sheet_rows.append(f'<row r="{index}">'+cell("A",index,code)+
                              f'<c r="B{index}" t="s"><v>{3 if st=="DE" else 4}</v></c>'+
                              f'<c r="C{index}" t="s"><v>5</v></c></row>')
    worksheet=custom_sheet or ('<worksheet xmlns="'+M+'"><sheetData>'+
                    "".join(sheet_rows)+'</sheetData></worksheet>')
    workbook='<workbook xmlns="'+M+'" xmlns:r="'+R+'"><sheets><sheet name="'+sheet_name+'" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels='<Relationships xmlns="'+P+'"><Relationship Id="rId1" Type="'+R+'/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    blob=BytesIO()
    with ZipFile(blob,"w",compression=ZIP_DEFLATED) as outer:
        outer.writestr("xl/workbook.xml",workbook)
        outer.writestr("xl/_rels/workbook.xml.rels",rels)
        outer.writestr("xl/worksheets/sheet1.xml",worksheet)
        if shared_xml is not None:
            outer.writestr("xl/sharedStrings.xml",shared_xml)
    return blob.getvalue()


def fake_archive(xlsx=None, *, add=None):
    if xlsx is None:
        xlsx=fake_xlsx()
    blob=BytesIO()
    with ZipFile(blob,"w",compression=ZIP_DEFLATED) as outer:
        outer.writestr(w.PLANT_MEMBER,xlsx)
        outer.writestr("LayoutY2025.xlsx",b"test-only-layout-not-an-eia-file")
        if add:
            for name,payload in add:
                outer.writestr(name,payload)
    return blob.getvalue()


def run(data=None, **kwargs):
    return w.check_original_archive(fake_archive() if data is None else data,**kwargs)


class EIA860AnnualOriginalTests(unittest.TestCase):
    def test_official_archive_shape_is_research_only(self):
        x=run()
        self.assertEqual(x["original_2025_plant_inventory_records"],3)
        self.assertEqual(x["delaware_ids_present_in_eia_2025_with_state_DE"],2)
        self.assertEqual(x["delaware_ids_absent_from_eia_2025_plant_sheet"],13)
        self.assertEqual(x["delaware_ids_present_with_state_mismatch"],0)
        self.assertTrue(x["separate_pa_oris_3136_present_in_eia_2025"])
        self.assertTrue(x["separate_pa_oris_3136_state_PA"])
        self.assertEqual(x["state"],"ANNUAL_2025_PLANT_ID_COVERAGE_RESEARCH_ONLY")
        self.assertFalse(x["source_byte_sha_pinned_before_download"])
        for k in ("gem_plant_join_confirmed","source_rights_or_model_admission_granted",
                  "eia_owner_row_proves_policyholder_or_insurer",
                  "epa_frs_link_proves_physical_site_coordinates",
                  "eia_plant_is_an_individual_generator_or_building"):
            self.assertFalse(x[k])
        self.assertNotIn("Synthetic",str(x))

    def test_supplied_sha_is_checked(self):
        raw=fake_archive()
        exact=sha256(raw).hexdigest()
        self.assertTrue(run(raw,expected_sha256=exact)["source_byte_sha_pinned_before_download"])
        with self.assertRaisesRegex(w.EIA860ProofBlocked,"SHA-256 mismatch"):
            run(raw,expected_sha256="0"*64)
        with self.assertRaises(w.EIA860ProofBlocked):
            run(raw,expected_sha256="wrong")

    def test_multiple_rows_are_not_generators(self):
        x=run(fake_archive(fake_xlsx(rows=[("599","DE","A"),("7318","DE","B"),
                   ("7153","DE","C"),("3136","PA","D")])))
        self.assertEqual(x["original_2025_plant_inventory_records"],4)
        self.assertEqual(x["delaware_ids_present_in_eia_2025_with_state_DE"],3)
        self.assertFalse(x["eia_plant_is_an_individual_generator_or_building"])

    def test_wrong_state_requires_review(self):
        x=run(fake_archive(fake_xlsx(rows=[("599","PA","synthetic")])) )
        self.assertEqual(x["delaware_ids_present_with_state_mismatch"],1)
        self.assertEqual(x["state"],"REVIEW_STATE_MISMATCH")

    def test_one_absent_planted_is_not_no_physical_plant(self):
        x=run(fake_archive(fake_xlsx(rows=[("3136","PA","historical")])) )
        self.assertEqual(x["delaware_ids_absent_from_eia_2025_plant_sheet"],15)
        self.assertEqual(x["state"],"ANNUAL_2025_PLANT_ID_COVERAGE_RESEARCH_ONLY")
        self.assertFalse(x["historical_2025_membership_is_current_2026_operating_status"])

    def test_shared_strings_are_parsed(self):
        x=run(fake_archive(fake_xlsx(shared=True)))
        self.assertEqual(x["delaware_ids_present_in_eia_2025_with_state_DE"],2)

    def test_duplicate_plant_id_after_normalization_blocks(self):
        data=fake_archive(fake_xlsx(rows=[("599","DE","One"),("000599","DE","Two")]))
        with self.assertRaisesRegex(w.EIA860ProofBlocked,"duplicate annual"):
            run(data)

    def test_invalid_code_and_state_block(self):
        for invalid in [("0","DE","A"),("AB","DE","A"),("599","delaware","A"),
                        ("599","","A")]:
            with self.subTest(invalid=invalid),self.assertRaises(w.EIA860ProofBlocked):
                run(fake_archive(fake_xlsx(rows=[invalid])))

    def test_no_plant_sheet_is_not_silently_guessed(self):
        with self.assertRaisesRegex(w.EIA860ProofBlocked,"Plant worksheet"):
            run(fake_archive(fake_xlsx(sheet_name="2025 Summary")))

    def test_unknown_header_fails_closed(self):
        x='<worksheet xmlns="'+M+'"><sheetData><row r="1">'+cell("A",1,"ORIS",text=True)+'</row></sheetData></worksheet>'
        with self.assertRaises(w.EIA860ProofBlocked):
            run(fake_archive(fake_xlsx(custom_sheet=x)))

    def test_wrong_zip_member_and_invalid_zip_fail(self):
        with self.assertRaises(w.EIA860ProofBlocked):
            run(b"not a zip")
        data=BytesIO()
        with ZipFile(data,"w") as z:
            z.writestr("2___Plant_Y2024.xlsx",fake_xlsx())
        with self.assertRaises(w.EIA860ProofBlocked):
            run(data.getvalue())

    def test_zip_path_traversal_rejected(self):
        data=fake_archive(add=[("../forbidden.txt",b"synthetic")])
        with self.assertRaisesRegex(w.EIA860ProofBlocked,"unsafe"):
            run(data)

    def test_bad_worksheet_xml_rejected(self):
        data=fake_archive(fake_xlsx(custom_sheet="<broken>"))
        with self.assertRaises(w.EIA860ProofBlocked):
            run(data)

    def test_source_row_order_does_not_change_coverage(self):
        a=[("599","DE","One"),("3136","PA","Two"),("591","DE","Three")]
        r1=run(fake_archive(fake_xlsx(rows=a)))
        r2=run(fake_archive(fake_xlsx(rows=list(reversed(a)))))
        self.assertNotEqual(r1["source_zip_body_sha256"],r2["source_zip_body_sha256"])
        for k in ("delaware_ids_present_in_eia_2025_with_state_DE",
                  "delaware_ids_absent_from_eia_2025_plant_sheet",
                  "separate_pa_oris_3136_present_in_eia_2025"):
            self.assertEqual(r1[k],r2[k])

    def test_blank_original_bytes_rejected(self):
        with self.assertRaises(w.EIA860ProofBlocked):
            run(b"")
        with self.assertRaises(w.EIA860ProofBlocked):
            run(b"x"*(w.MAX_ORIGINAL_BYTES+1))


if __name__=="__main__":
    unittest.main()
