# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hermetic 400-Kreis original-structure negatives; no official dataset rows inside tests."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from zensus_regional_original_receipt_v0 import OriginalReceiptError  # noqa: E402
from zensus_kreis_original_numeric_receipt_v0 import inspect_original_kreis_building_counts  # noqa: E402

COLUMNS=("Berichtszeitpunkt","_RS","Name","Regionalebene",
         "GEBAEUDEART_SYS_1","GEBAEUDEART_SYS_11",
         "GEBAEUDEART_SYS_111","GEBAEUDEART_SYS_112",
         "GEBAEUDEART_SYS_12")

def build(*,edit=None,make_rows=400,duplicate=False,other_level=False,missing_state=False):
    rows=[list(COLUMNS)]
    # Synthetic 25 different Kreis-like AGS keys for each of 16 states.
    for n in range(make_rows):
        st=n//25+1
        code=f"{st:02}{n%25+1:03}"
        if missing_state and st==16:\n            code=f"01{n%25+26:03}"
        if duplicate and n==1:
            code="01001"
        row=["15.05.2022",code,f"Fiktiv Kreis {n+1}",
             "Stadtkreis/kreisfreie Stadt/Landkreis",1000,900,880,20,100]
        if other_level and n==1:
            row[3]="Gemeinde"
        if edit is not None and n==0:
            row[edit[0]]=edit[1]
        rows.append(row)
    # Non-Kreis hierarchical parent must never be added as a district.
    rows.append(["15.05.2022","01","Fiktiv Land","Land",999999,99999,99999,0,100])
    content=['<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>']
    for i,r in enumerate(rows,start=1):
        content.append(f'<row r="{i}">')
        for j,val in enumerate(r):
            col=chr(65+j)
            if isinstance(val,str):
                content.append(f'<c r="{col}{i}" t="inlineStr"><is><t>{escape(val)}</t></is></c>')
            else:
                content.append(f'<c r="{col}{i}" t="n"><v>{val}</v></c>')
        content.append('</row>')
    content.append('</sheetData></worksheet>')
    wb=('<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="CSV-Gebäude" sheetId="1" r:id="rId1"/></sheets></workbook>')
    rel=('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
    buffer=BytesIO()
    with ZipFile(buffer,"w",compression=ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml","<Types/>")
        z.writestr("xl/workbook.xml",wb)
        z.writestr("xl/_rels/workbook.xml.rels",rel)
        z.writestr("xl/worksheets/sheet1.xml","".join(content))
    return buffer.getvalue()

class OriginalKreisNumericReceiptTests(unittest.TestCase):
    def test_stream_400_synthetic_rows_and_exclude_land(self):
        r,rows=inspect_original_kreis_building_counts(build(),require_original_sha=False)
        self.assertEqual(r["kreis_count"],400)
        self.assertEqual(len(rows),400)
        self.assertEqual(r["land_codes_present"],[f"{n:02}" for n in range(1,17)])
        self.assertEqual(r["kreis_count_sum_by_field"]["gebaeude_mit_wohnraum"],400000)
        self.assertEqual(r["kreis_count_sum_by_field"]["wohngebaeude"],360000)
        self.assertEqual(r["kreis_count_sum_by_field"]["sonstiges_gebaeude_mit_wohnraum"],40000)
        self.assertEqual(r["sum_count_nonadditivity_hierarchy_abs"],0)
        self.assertEqual(r["original_reported_dates"],{"15.05.2022":400})
        self.assertFalse(r["insurer_spatial_contracts_observed"])
        self.assertFalse(r["oasis_model_input_admitted"])

    def test_original_sha_pinned_and_synthetic_denied(self):
        with self.assertRaisesRegex(OriginalReceiptError,"SHA256 changed"):
            inspect_original_kreis_building_counts(build())

    def test_header_schema_prevents_misaligned_value(self):
        with self.assertRaisesRegex(OriginalReceiptError,"column schema changed"):
            inspect_original_kreis_building_counts(build_with_header_mutation(),require_original_sha=False)

    def test_publisher_suppression_marker_is_not_zero(self):
        for bad in ("/","...","-","x","","0.5",None):
            value="" if bad is None else bad
            with self.subTest(value=value),self.assertRaisesRegex(OriginalReceiptError,"missing/suppressed"):
                inspect_original_kreis_building_counts(build(edit=(4,value)),require_original_sha=False)

    def test_duplicate_kreis_ags_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"duplicated"):
            inspect_original_kreis_building_counts(build(duplicate=True),require_original_sha=False)

    def test_kreis_label_filter_fails_partial_count(self):
        with self.assertRaisesRegex(OriginalReceiptError,"missing Kreis rows|conflicting region type"):
            inspect_original_kreis_building_counts(build(other_level=True),require_original_sha=False)

    def test_invalid_negative_building_count_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"missing/suppressed"):
            inspect_original_kreis_building_counts(build(edit=(4,-1)),require_original_sha=False)

    def test_cannot_invert_building_type_hierarchy(self):
        with self.assertRaisesRegex(OriginalReceiptError,"hierarchy impossible"):
            inspect_original_kreis_building_counts(build(edit=(4,30)),require_original_sha=False)

    def test_too_few_kreise_not_admitted(self):
        with self.assertRaisesRegex(OriginalReceiptError,"missing Kreis rows"):
            inspect_original_kreis_building_counts(build(make_rows=375),require_original_sha=False)

    def test_all_16_states_required(self):
        with self.assertRaisesRegex(OriginalReceiptError,"missing Kreis rows or Länder"):
            inspect_original_kreis_building_counts(build(missing_state=True),require_original_sha=False)

    def test_stable_deterministic_count_receipt(self):
        first,rows=inspect_original_kreis_building_counts(build(),require_original_sha=False)
        second,other=inspect_original_kreis_building_counts(build(),require_original_sha=False)
        self.assertEqual(first["kreis_numeric_mapping_sha256"],second["kreis_numeric_mapping_sha256"])
        self.assertEqual(rows,other)
        self.assertEqual(rows[0]["kreis_ags_2022"],"01001")

    def test_total_land_must_not_be_summed(self):
        r,_=inspect_original_kreis_building_counts(build(),require_original_sha=False)
        self.assertNotEqual(r["kreis_count_sum_by_field"]["gebaeude_mit_wohnraum"],1399999)


def build_with_header_mutation():
    source=build()
    # Build one fixture with a changed original header (zero data change).
    from io import BytesIO
    buf=BytesIO()
    with ZipFile(BytesIO(source)) as z, ZipFile(buf,"w",compression=ZIP_DEFLATED) as out:
        for name in z.namelist():
            original=z.read(name)
            if name=="xl/worksheets/sheet1.xml":
                original=original.replace(b"GEBAEUDEART_SYS_1",b"Dwellings",1)
            out.writestr(name,original)
    return buf.getvalue()

if __name__=="__main__":
    unittest.main()
