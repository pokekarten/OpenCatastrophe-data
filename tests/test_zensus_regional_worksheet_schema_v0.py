# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic OOXML table header; never commit any source Census cell."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research_runners"))
from zensus_regional_original_receipt_v0 import OriginalReceiptError
from zensus_regional_worksheet_schema_v0 import inspect_original_gwz_header


def example(*, sheet="CSV-Gebäude", target="worksheets/sheet1.xml",
            shared=True, broken_rel=False):
    out=BytesIO()
    wb=(
      '<?xml version="1.0" encoding="UTF-8"?>'
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
      '<sheets><sheet name="'+sheet+'" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels=(
      '<?xml version="1.0" encoding="UTF-8"?>'
      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      '<Relationship Id="rId1" Type="test" Target="'+
      ("worksheets/not_present.xml" if broken_rel else target)+'"/></Relationships>'
    )
    tag="s" if shared else "inlineStr"
    cell_a='<c r="A1" t="s"><v>0</v></c>' if shared else (
      '<c r="A1" t="inlineStr"><is><t>Kreis AGS</t></is></c>')
    xml=(
      '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
      '<sheetData><row r="1">'+cell_a+
      '<c r="B1" t="n"><v>99999</v></c>'
      '<c r="C1" t="s"><v>1</v></c></row>'
      '<row r="2"><c r="A2" t="e"><v>#N/A</v></c></row></sheetData></worksheet>'
    )
    with ZipFile(out,"w",compression=ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml","<Types/>")
        z.writestr("xl/workbook.xml",wb)
        z.writestr("xl/_rels/workbook.xml.rels",rels)
        z.writestr("xl/worksheets/sheet1.xml",xml)
        if shared:
            z.writestr("xl/sharedStrings.xml",
              '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<si><t>Kreis AGS</t></si><si><t>Gebäude mit Wohnraum</t></si></sst>')
    return out.getvalue()


class BoundedRealWorksheetPreflightTests(unittest.TestCase):
    def test_real_ooxml_sheet_rid_resolves_synthetic_header(self):
        out=inspect_original_gwz_header(example())
        self.assertEqual(out["sheet_exact_name"],"CSV-Gebäude")
        self.assertEqual(out["resolved_original_sheet_path"],"xl/worksheets/sheet1.xml")
        self.assertEqual(out["initial_rows_scanned"],2)
        self.assertEqual(out["initial_shared_string_cells_resolved"],2)
        self.assertEqual([x["text"] for x in out["bounded_nonnumeric_cell_headings"]],
                         ["Kreis AGS","Gebäude mit Wohnraum"])
        self.assertFalse(out["numerical_census_cells_exported"])
        self.assertFalse(out["nextgen_cat_model_input_approved"])

    def test_inline_string_without_shared_string_file(self):
        raw=example(shared=False)
        # C1 refers to one shared string even if A1 is inline -> intentionally blocked
        with self.assertRaisesRegex(OriginalReceiptError,"shared string table missing"):
            inspect_original_gwz_header(raw)

    def test_source_sheet_name_exact_and_not_guess(self):
        with self.assertRaisesRegex(OriginalReceiptError,"CSV-Gebäude worksheet"):
            inspect_original_gwz_header(example(sheet="Gebäude"))

    def test_rel_missing_blocks(self):
        with self.assertRaisesRegex(OriginalReceiptError,"unresolved worksheet"):
            inspect_original_gwz_header(example(broken_rel=True))

    def test_off_host_path_traversal_blocks(self):
        with self.assertRaisesRegex(OriginalReceiptError,"unsafe/unresolved worksheet path"):
            inspect_original_gwz_header(example(target="../../other.xml"))

    def test_original_headers_are_not_numerical_cells(self):
        out=inspect_original_gwz_header(example())
        text=" ".join(x["text"] for x in out["bounded_nonnumeric_cell_headings"])
        self.assertNotIn("99999",text)
        self.assertNotIn("#N/A",text)


if __name__=="__main__":
    unittest.main()
