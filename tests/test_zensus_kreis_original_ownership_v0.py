# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Hermetic original source owner-type safeguards using 400 fictional Kreise."""
from io import BytesIO
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from zensus_kreis_original_ownership_v0 import extract_original_kreis_ownership,OWNER_CODES,OriginalReceiptError  # noqa: E402
from tests.test_zensus_kreis_original_age_cohorts_v0 import fake_source,baseline  # noqa: E402

M="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

def fixture(*,edit=None,header=None):
    raw=fake_source()
    target=BytesIO()
    with ZipFile(BytesIO(raw)) as z,ZipFile(target,"w",compression=ZIP_DEFLATED) as out:
        for fname in z.namelist():
            data=z.read(fname)
            if fname=="xl/worksheets/sheet1.xml":
                root=ET.fromstring(data)
                for r in root.findall(".//"+M+"row"):
                    k=int(r.attrib["r"])
                    for i in range(8):
                        col=chr(84+i) if i<7 else "AA"
                        label=OWNER_CODES[i] if header is None or i!=header[0] else header[1]
                        if k==1 or edit is not None and k==2 and i==edit[0] and isinstance(edit[1],str):
                            c=ET.SubElement(r,M+"c",{"r":f"{col}{k}","t":"inlineStr"})
                            el=ET.SubElement(ET.SubElement(c,M+"is"),M+"t")
                            el.text=label if k==1 else edit[1]
                        else:
                            v=edit[1] if edit is not None and k==2 and i==edit[0] else 125
                            c=ET.SubElement(r,M+"c",{"r":f"{col}{k}","t":"n"})
                            ET.SubElement(c,M+"v").text=str(v)
                data=ET.tostring(root,encoding="utf-8")
            out.writestr(fname,data)
    return target.getvalue()

class OriginalOwnershipKreisTests(unittest.TestCase):
    def test_400_synthetic_counties_eight_categories_conserved(self):
        r,rows=extract_original_kreis_ownership(fixture(),baseline(),require_original_sha=False)
        self.assertEqual(len(rows),400)
        self.assertEqual(r["county_count"],400)
        self.assertEqual(r["source_ownership_codes"],list(OWNER_CODES))
        self.assertEqual(r["available_owner_category_2022_counts"][OWNER_CODES[0]],50000)
        self.assertEqual(r["numeric_counties_per_ownership_category"][OWNER_CODES[7]],400)
        self.assertEqual(r["complete_counties_all_8_ownership_categories"],400)
        self.assertEqual(r["signed_county_ownership_sum_minus_total"],0)
        self.assertFalse(r["rva_2025_company_ownership_distribution_observed"])
        self.assertFalse(r["census_building_owner_equals_insurer_policyholder"])
        self.assertEqual(rows[0]["ags"],"01001")

    def test_sha_required_for_real_source(self):
        with self.assertRaisesRegex(OriginalReceiptError,"source edition SHA"):
            extract_original_kreis_ownership(fixture(),baseline())

    def test_wrong_original_header_fails(self):
        with self.assertRaisesRegex(OriginalReceiptError,"header/column order"):
            extract_original_kreis_ownership(fixture(header=(7,"EIGENTUM__OTHER")),baseline(),require_original_sha=False)

    def test_suppressed_owner_is_null_not_zero(self):
        r,rows=extract_original_kreis_ownership(fixture(edit=(1,"/")),baseline(),require_original_sha=False)
        self.assertIsNone(rows[0]["ownership_categories_2022"][1])
        self.assertFalse(rows[0]["ownership_fully_numeric"])
        self.assertEqual(r["numeric_counties_per_ownership_category"][OWNER_CODES[1]],399)
        self.assertEqual(r["unavailable_counties_per_category"][OWNER_CODES[1]],1)
        self.assertEqual(r["complete_counties_all_8_ownership_categories"],399)

    def test_missing_other_owner_does_not_change_primary_total(self):
        r,rows=extract_original_kreis_ownership(fixture(edit=(6,"...")),baseline(),require_original_sha=False)
        self.assertEqual(rows[0]["buildings_with_residential_use_2022"],1000)
        self.assertIsNone(rows[0]["ownership_categories_2022"][6])
        self.assertEqual(r["buildings_with_residential_use_2022_count"],400000)

    def test_category_overage_beyond_tolerance_fails(self):
        with self.assertRaisesRegex(OriginalReceiptError,"outside Cell-Key tolerance"):
            extract_original_kreis_ownership(fixture(edit=(4,1011)),baseline(),require_original_sha=False)

    def test_primary_count_must_equal_original_building_baseline(self):
        b=baseline()
        b["01001"]+=1
        with self.assertRaisesRegex(OriginalReceiptError,"total not same"):
            extract_original_kreis_ownership(fixture(),b,require_original_sha=False)

    def test_nonadditive_published_ownership_kept_verbatim(self):
        r,rows=extract_original_kreis_ownership(fixture(edit=(2,129)),baseline(),require_original_sha=False)
        self.assertEqual(rows[0]["ownership_categories_2022"][2],129)
        self.assertEqual(rows[0]["original_owner_category_sum_minus_total"],4)
        self.assertEqual(r["max_abs_county_ownership_sum_minus_total"],4)
        self.assertEqual(r["signed_county_ownership_sum_minus_total"],4)

    def test_original_source_receipt_deterministic(self):
        a,ra=extract_original_kreis_ownership(fixture(),baseline(),require_original_sha=False)
        b,rb=extract_original_kreis_ownership(fixture(),baseline(),require_original_sha=False)
        self.assertEqual(a["source_values_canonical_sha256"],b["source_values_canonical_sha256"])
        self.assertEqual(ra,rb)

    def test_duplicate_kreis_rejected(self):
        raw=fixture()
        out=BytesIO()
        with ZipFile(BytesIO(raw)) as z,ZipFile(out,"w",compression=ZIP_DEFLATED) as target:
            for f in z.namelist():
                b=z.read(f)
                if f=="xl/worksheets/sheet1.xml":
                    b=b.replace(b"01002",b"01001",1)
                target.writestr(f,b)
        with self.assertRaisesRegex(OriginalReceiptError,"duplicate"):
            extract_original_kreis_ownership(out.getvalue(),baseline(),require_original_sha=False)

if __name__=="__main__":
    unittest.main()
