# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only EIA Schedule 4 generator-level owner share audit."""
from __future__ import annotations

import json
import unittest
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners import eia860_2025_owner_shares_cohort_v0 as m
from tests.test_eia860_annual_2025_original_zip_v0 import fake_xlsx,cell,M


def fixture(rows=None):
    if rows is None:
        rows=[("599","GEN1","TEST OWNER A","40.00"),("599","GEN1","TEST OWNER B","60.00")]
    header='<row r="1">'+''.join(cell(c,1,n,text=True) for c,n in [
        ("A","Plant Code"),("B","Generator ID"),("C","Owner Name"),
        ("D","Percent Owned")])+'</row>'
    records=[]
    for i,(plant,gen,owner,pct) in enumerate(rows,2):
        records.append(f'<row r="{i}">'+
                       cell("A",i,plant)+cell("B",i,gen,text=True)+
                       cell("C",i,owner,text=True)+cell("D",i,pct,text=True)+
                       "</row>")
    sheet='<worksheet xmlns="'+M+'"><sheetData>'+header+''.join(records)+'</sheetData></worksheet>'
    return fake_xlsx(sheet_name="Ownership",custom_sheet=sheet)


def percent_format_fixture():
    """Synthetic native OOXML 0.4 + 0.6 cells styled as 40% + 60%."""
    raw=fixture(rows=[("599","G1","TEST OWNER A","0.4"),
                      ("599","G1","TEST OWNER B","0.6")])
    src=BytesIO(raw)
    output=BytesIO()
    with ZipFile(src) as read, ZipFile(output,"w",ZIP_DEFLATED) as write:
        for path in read.namelist():
            part=read.read(path)
            if path=="xl/worksheets/sheet1.xml":
                xml=part.decode("utf-8")
                for row,pct in ((2,"0.4"),(3,"0.6")):
                    existing=(f'<c r="D{row}" t="inlineStr"><is><t>{pct}</t></is></c>')
                    assert existing in xml
                    xml=xml.replace(existing,f'<c r="D{row}" s="1"><v>{pct}</v></c>')
                part=xml.encode("utf-8")
            write.writestr(path,part)
        write.writestr("xl/styles.xml",
            ('<styleSheet xmlns="'+M+'"><cellXfs count="2">'+
             '<xf numFmtId="0"/><xf numFmtId="10"/></cellXfs></styleSheet>').encode())
    return output.getvalue()


class OriginalOwnerShareTests(unittest.TestCase):
    def test_generator_shares_not_plant_insurance_allocation(self):
        r=m.inspect_owner_worksheet(fixture())
        self.assertEqual(r["delaware_owner_schedule_rows"],2)
        self.assertEqual(r["delaware_distinct_generators_with_owner_schedule_rows"],1)
        self.assertEqual(r["delaware_generators_owner_sum_100_within_0_05_percentage_points"],1)
        self.assertEqual(r["state"],"EIA_OWNER_GENERATOR_COACH_RESEARCH_ONLY")
        self.assertFalse(r["source_owner_name_or_address_emitted"])
        self.assertFalse(r["insurer_policies_or_tiv_inferred"])
        self.assertFalse(r["unreported_generators_are_operator_owned_proven"])
        self.assertNotIn("TEST OWNER A",json.dumps(r))

    def test_native_xlsx_percentage_style_scales_fraction_to_100_percent(self):
        r=m.inspect_owner_worksheet(percent_format_fixture())
        self.assertEqual(r["delaware_generators_owner_sum_100_within_0_05_percentage_points"],1)
        self.assertEqual(r["delaware_generators_owner_sum_below_99_95_pct"],0)
        self.assertEqual(r["delaware_owner_rows_with_native_percent_format"],2)
        self.assertEqual(r["delaware_percent_owned_style_number_format_ids"],{"1":"10"})
        self.assertEqual(r["state"],"EIA_OWNER_GENERATOR_COACH_RESEARCH_ONLY")

    def test_unstyled_fraction_must_not_be_misrepresented_as_100_percent(self):
        r=m.inspect_owner_worksheet(fixture(rows=[
            ("599","G1","OWNER A","0.4"),("599","G1","OWNER B","0.6")]))
        self.assertEqual(r["delaware_generators_owner_sum_below_99_95_pct"],1)
        self.assertEqual(r["delaware_owner_rows_with_native_percent_format"],0)

    def test_not_in_cohort_does_not_create_delaware_owner(self):
        r=m.inspect_owner_worksheet(fixture(rows=[("3136","GEN1","OTHER","100")]))
        self.assertEqual(r["delaware_owner_schedule_rows"],0)
        self.assertEqual(r["delaware_plant_ids_with_explicit_owner_schedule_rows"],0)
        self.assertEqual(r["delaware_distinct_generators_with_owner_schedule_rows"],0)

    def test_generators_are_distinct_even_at_same_plant(self):
        r=m.inspect_owner_worksheet(fixture(rows=[
            ("599","A","A OWNER","100"),("599","B","B OWNER","100")]))
        self.assertEqual(r["delaware_plant_ids_with_explicit_owner_schedule_rows"],1)
        self.assertEqual(r["delaware_distinct_generators_with_owner_schedule_rows"],2)

    def test_under_and_over_ownership_are_reviewed(self):
        for shares,target in [(["40"],"delaware_generators_owner_sum_below_99_95_pct"),
                              (["60","60"],"delaware_generators_owner_sum_above_100_05_pct")]:
            rows=[("599","X"+str(i),"A"+str(i),pct) for i,pct in enumerate(shares)]
            # Same generator so we detect a total > 100, not unrelated units.
            rows=[(p,"GEN1",o,pct) for p,_,o,pct in rows]
            r=m.inspect_owner_worksheet(fixture(rows=rows))
            self.assertEqual(r[target],1)
            self.assertEqual(r["state"],"REVIEW_OWNER_SHARE_ANOMALIES")

    def test_invalid_share_does_not_impute_ownership(self):
        r=m.inspect_owner_worksheet(fixture(rows=[("599","A","OWNER","n/a")]))
        self.assertEqual(r["delaware_owner_rows_with_unparsed_share"],1)
        self.assertEqual(r["delaware_generators_ownership_unverifiable_due_to_bad_rows"],1)

    def test_duplicate_generator_owner_name_is_not_silent(self):
        r=m.inspect_owner_worksheet(fixture(rows=[
            ("599","A","OWNER","40"),("599","A","OWNER","60")]))
        self.assertEqual(r["delaware_repeated_generator_owner_name_rows"],1)
        self.assertEqual(r["delaware_generators_ownership_unverifiable_due_to_bad_rows"],1)

    def test_blank_owner_name_is_unverified(self):
        r=m.inspect_owner_worksheet(fixture(rows=[("599","A","","100")]))
        self.assertEqual(r["delaware_owner_rows_with_empty_or_invalid_owner_name"],1)

    def test_wrong_original_owner_hash_is_rejected(self):
        with self.assertRaisesRegex(m.OwnerShareBlocked,"checksum differs"):
            m.inspect_owner_worksheet(fixture(),require_original_member_sha=True)

    def test_missing_header_or_empty_bytes_blocks(self):
        with self.assertRaises(m.OwnerShareBlocked):
            m.inspect_owner_worksheet(b"")

    def test_bad_generator_id_blocks_in_cohort(self):
        with self.assertRaises(m.OwnerShareBlocked):
            m.inspect_owner_worksheet(fixture(rows=[("599","BAD ID","OWNER","100")]))


if __name__=="__main__":
    unittest.main()
