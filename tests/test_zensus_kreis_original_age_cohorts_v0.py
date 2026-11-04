# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic 400-Kreis original-sheet age extraction tests; no Census raw rows."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from zensus_kreis_original_age_cohorts_v0 import (
    inspect_original_age_cohorts,BANDS,CODES,OriginalReceiptError,
    read_pinned_baseline
)
from tests.test_zensus_kreis_original_numeric_receipt_v0 import build

M="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

def fake_source(*,age_edit=None,header_edit=None,duplicate=False,other_level=False):
    original=build(duplicate=duplicate,other_level=other_level)
    out=BytesIO()
    with ZipFile(BytesIO(original)) as zin, ZipFile(out,"w",compression=ZIP_DEFLATED) as zout:
        for name in zin.namelist():
            data=zin.read(name)
            if name=="xl/worksheets/sheet1.xml":
                root=ET.fromstring(data)
                for r in root.findall(".//"+M+"row"):
                    number=int(r.attrib["r"])
                    for ix in range(10):
                        col=chr(74+ix)
                        key=(header_edit[1] if header_edit and number==1 and ix==header_edit[0]
                             else CODES[ix])
                        if number==1:
                            cell=ET.SubElement(r,M+"c",{"r":f"{col}{number}","t":"inlineStr"})
                            text=ET.SubElement(ET.SubElement(cell,M+"is"),M+"t")
                            text.text=key
                        else:
                            value=(age_edit[1] if age_edit and number==2 and ix==age_edit[0]
                                   else 100)
                            if isinstance(value,str):
                                cell=ET.SubElement(r,M+"c",{"r":f"{col}{number}","t":"inlineStr"})
                                text=ET.SubElement(ET.SubElement(cell,M+"is"),M+"t")
                                text.text=value
                            else:
                                cell=ET.SubElement(r,M+"c",{"r":f"{col}{number}","t":"n"})
                                text=ET.SubElement(cell,M+"v")
                                text.text=str(value)
                data=ET.tostring(root,encoding="utf-8")
                data=data.replace(b"15.05.2022",b"20220515")
            zout.writestr(name,data)
    return out.getvalue()

def baseline():
    return {f"{n//25+1:02}{n%25+1:03}":1000 for n in range(400)}

class OriginalBaujahrDecadeCohorts(unittest.TestCase):
    def test_all_400_fake_kreise_with_ten_verified_age_headers(self):
        receipt,rows=inspect_original_age_cohorts(fake_source(),baseline(),require_original_sha=False)
        self.assertEqual(receipt["county_count"],400)
        self.assertEqual(receipt["source_age_columns"],list(CODES))
        self.assertEqual(receipt["age_band_labels_official_order"],list(BANDS))
        self.assertEqual(receipt["original_date_verified"],"20220515")
        self.assertEqual(receipt["counties_all_ten_age_bands_numeric"],400)
        self.assertEqual(receipt["age_numeric_coverage_by_column"][CODES[0]],400)
        self.assertEqual(receipt["complete_county_max_abs_age_sum_minus_total"],0)
        self.assertEqual(receipt["building_total_original"],400000)
        self.assertFalse(receipt["insurer_risk_locations_or_values_observed"])
        self.assertFalse(receipt["rva_2025_age_book_admitted"])
        self.assertEqual(len(rows[0]["age_bands_2022"]),10)

    def test_unmodified_original_sha_required(self):
        with self.assertRaisesRegex(OriginalReceiptError,"edition changed"):
            inspect_original_age_cohorts(fake_source(),baseline())

    def test_wrong_schema_fails(self):
        with self.assertRaisesRegex(OriginalReceiptError,"source columns changed"):
            inspect_original_age_cohorts(fake_source(header_edit=(5,"BAD")),baseline(),require_original_sha=False)

    def test_suppressed_age_cell_is_null_not_zero(self):
        receipt,rows=inspect_original_age_cohorts(fake_source(age_edit=(5,"/")),baseline(),require_original_sha=False)
        self.assertIsNone(rows[0]["age_bands_2022"][5])
        self.assertFalse(rows[0]["all_age_bands_numeric"])
        self.assertEqual(receipt["age_numeric_coverage_by_column"][CODES[5]],399)
        self.assertEqual(receipt["age_unavailable_count_by_column"][CODES[5]],1)
        self.assertEqual(receipt["counties_all_ten_age_bands_numeric"],399)

    def test_negative_age_cell_is_not_a_count(self):
        receipt,rows=inspect_original_age_cohorts(fake_source(age_edit=(0,-1)),baseline(),require_original_sha=False)
        self.assertIsNone(rows[0]["age_bands_2022"][0])
        self.assertEqual(receipt["age_numeric_coverage_by_column"][CODES[0]],399)

    def test_age_cell_cannot_exceed_buildings_beyond_ckm_tolerance(self):
        with self.assertRaisesRegex(OriginalReceiptError,"outside physical"):
            inspect_original_age_cohorts(fake_source(age_edit=(2,1011)),baseline(),require_original_sha=False)

    def test_duplicate_county_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"duplicate"):
            inspect_original_age_cohorts(fake_source(duplicate=True),baseline(),require_original_sha=False)

    def test_inconsistent_admin_level_blocked(self):
        with self.assertRaisesRegex(OriginalReceiptError,"unexpected administrative"):
            inspect_original_age_cohorts(fake_source(other_level=True),baseline(),require_original_sha=False)

    def test_missing_county_or_bad_original_baseline_blocked(self):
        b=baseline()
        b.pop("01001")
        with self.assertRaisesRegex(OriginalReceiptError,"unfamiliar|incomplete"):
            inspect_original_age_cohorts(fake_source(),b,require_original_sha=False)

    def test_unadditive_ckm_age_sum_is_preserved_as_source_value(self):
        receipt,rows=inspect_original_age_cohorts(fake_source(age_edit=(0,103)),baseline(),require_original_sha=False)
        self.assertEqual(rows[0]["complete_age_band_sum_minus_buildings"],3)
        self.assertEqual(receipt["complete_county_age_sum_delta_total"],3)
        self.assertEqual(receipt["complete_county_max_abs_age_sum_minus_total"],3)

    def test_age_order_and_original_canonical_mapping_reproducible(self):
        a,ra=inspect_original_age_cohorts(fake_source(),baseline(),require_original_sha=False)
        b,rb=inspect_original_age_cohorts(fake_source(),baseline(),require_original_sha=False)
        self.assertEqual(a["source_400_county_age_canonical_sha256"],b["source_400_county_age_canonical_sha256"])
        self.assertEqual(ra,rb)
        self.assertEqual(ra[0]["ags"],"01001")
        self.assertEqual(ra[-1]["ags"],"16025")

    def test_original_400_county_building_baseline_reads_correctly(self):
        real=ROOT/"research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"
        c=read_pinned_baseline(real.read_bytes())
        self.assertEqual(len(c),400)
        self.assertEqual(sum(c.values()),19957288)

if __name__=="__main__":
    unittest.main()
