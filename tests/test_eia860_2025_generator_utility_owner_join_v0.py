# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic original EIA generator/Owner/Utility key and reporting-scope tests."""
from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import json
import unittest
from xml.sax.saxutils import escape

from research_runners import eia860_2025_generator_utility_owner_join_v0 as m
from tests.test_eia860_2025_generator_utility_schema_v0 import NS,DOC,REL

GEN_HEADER=("Plant Code","Generator ID","Status","Utility ID","Utility Name")
UTIL_HEADER=("Utility ID","Utility Name")
OWN_HEADER=("Plant Code","Generator ID","Owner Name","Percent Owned")


def make_xlsx(sheets):
    buf=BytesIO()
    book='<workbook xmlns="'+NS+'" xmlns:r="'+DOC+'"><sheets>'
    links='<Relationships xmlns="'+REL+'">'
    for i,(name,headers,rows) in enumerate(sheets,1):
        book+=f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
        links+=f'<Relationship Id="rId{i}" Type="{DOC}/worksheet" Target="worksheets/sheet{i}.xml"/>'
    book+='</sheets></workbook>'
    links+='</Relationships>'
    with ZipFile(buf,'w',ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml',book)
        z.writestr('xl/_rels/workbook.xml.rels',links)
        for idx,(_,headers,rows) in enumerate(sheets,1):
            xml='<worksheet xmlns="'+NS+'"><sheetData>'
            for ridx,record in enumerate((headers,*rows),1):
                xml+=f'<row r="{ridx}">'
                for k,val in enumerate(record):
                    col=chr(65+k)
                    xml+=f'<c r="{col}{ridx}" t="inlineStr"><is><t>{escape(str(val))}</t></is></c>'
                xml+='</row>'
            xml+='</sheetData></worksheet>'
            z.writestr(f"xl/worksheets/sheet{idx}.xml",xml)
    return buf.getvalue()


def sample(gens=None,utilities=None,owners=None):
    if gens is None:
        gens={
            "Operable":[("599","G1","OP","123","Confidential Company"),
                       ("599","G2","SB","456","Second Confidential"),
                       ("7318","G3","OP","123","Confidential Company")],
            "Proposed":[("599","NEW","P","123","Confidential Company")],
            "Retired and Canceled":[("599","OLD","RE","123","Confidential Company")],
        }
    if utilities is None:
        utilities=[("123","Confidential Company"),("456","Second Confidential")]
    if owners is None:
        owners=[("599","G1","Private Investor A","40.0"),
                ("599","G1","Private Investor B","60.0"),
                ("7318","G3","Private Investor C","100.0")]
    generator=make_xlsx([(tab,GEN_HEADER,gens.get(tab,[])) for tab in
                         ("Operable","Proposed","Retired and Canceled")])
    util=make_xlsx([("Utility",UTIL_HEADER,utilities)])
    owner=make_xlsx([("Ownership",OWN_HEADER,owners)])
    return generator,util,owner


class OriginalGeneratorOperatorJoinTests(unittest.TestCase):
    def test_correct_original_grains_and_owner_schedule_key_join(self):
        r=m.inspect_members(*sample(),require_pinned=False)
        self.assertEqual(r["in_cohort_distinct_plant_generator_keys"],5)
        self.assertEqual(r["in_cohort_plant_ids_with_generator_rows"],2)
        self.assertEqual(r["in_cohort_generator_source_rows_by_sheet"],
                         {"Operable":3,"Proposed":1,"Retired and Canceled":1})
        self.assertEqual(r["owner_schedule_reported_rows_in_15_plants"],3)
        self.assertEqual(r["distinct_owner_schedule_generator_keys_in_15_plants"],2)
        self.assertEqual(r["owner_schedule_keys_present_in_original_generator_roster"],2)
        self.assertEqual(r["owner_schedule_keys_missing_from_generator_roster"],0)
        self.assertEqual(r["owner_schedule_generator_keys_by_original_tab"],
                         {"Operable":2,"Proposed":0,"Retired and Canceled":0})
        self.assertEqual(r["generator_keys_with_a_utility_id_in_original_utility_roster"],5)
        self.assertFalse(r["generator_keys_without_schedule4_are_confirmed_operator_owned"])
        self.assertFalse(r["insurer_portfolio_or_loss_model_admitted"] if "insurer_portfolio_or_loss_model_admitted" in r else r["insured_portfolio_or_loss_model_admitted"])
        txt=json.dumps(r)
        for forbidden in ("Private Investor","Confidential Company","G1","G2","G3"):
            self.assertNotIn(forbidden,txt)
        self.assertEqual(r["state"],"GENERATOR_OPERATOR_KEYS_RESEARCH_ONLY")

    def test_absent_schedule4_row_not_missing_generator_or_owner(self):
        r=m.inspect_members(*sample(owners=[]),require_pinned=False)
        self.assertEqual(r["in_cohort_distinct_plant_generator_keys"],5)
        self.assertEqual(r["distinct_owner_schedule_generator_keys_in_15_plants"],0)
        self.assertFalse(r["generator_keys_without_schedule4_are_confirmed_operator_owned"])

    def test_orphan_owner_key_is_held_for_review(self):
        r=m.inspect_members(*sample(owners=[("599","MISSING","Owner X","100")]),require_pinned=False)
        self.assertEqual(r["owner_schedule_keys_missing_from_generator_roster"],1)
        self.assertEqual(r["state"],"REVIEW_KEY_OR_SOURCE_STATUS")

    def test_same_generator_in_two_status_sheets_requires_review(self):
        gen={
            "Operable":[("599","GEN1","OP","123","X")],
            "Proposed":[("599","GEN1","P","123","X")],
            "Retired and Canceled":[],
        }
        r=m.inspect_members(*sample(gens=gen,owners=[]),require_pinned=False)
        self.assertEqual(r["in_cohort_generator_keys_in_multiple_sheets"],1)
        self.assertEqual(r["state"],"REVIEW_KEY_OR_SOURCE_STATUS")

    def test_same_generator_twice_in_one_tab_is_not_two_generators(self):
        gen={"Operable":[("599","GEN1","OP","123","X"),
                         ("599","GEN1","OP","123","X")],
             "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_members(*sample(gens=gen,owners=[]),require_pinned=False)
        self.assertEqual(r["in_cohort_distinct_plant_generator_keys"],1)
        self.assertEqual(r["in_cohort_duplicate_keys_within_sheet"],1)
        self.assertEqual(r["state"],"REVIEW_KEY_OR_SOURCE_STATUS")

    def test_unknown_status_is_not_logged_as_source_text(self):
        g={"Operable":[("599","GEN1","PRIVATELY NAMED SOURCE","123","X")],
           "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_members(*sample(gens=g,owners=[]),require_pinned=False)
        self.assertEqual(r["source_generator_rows_with_missing_or_unknown_status_by_sheet"]["Operable"],1)
        self.assertNotIn("PRIVATELY NAMED SOURCE",json.dumps(r))
        self.assertEqual(r["state"],"REVIEW_KEY_OR_SOURCE_STATUS")

    def test_utility_missing_and_unmatched_not_fabricated(self):
        g={"Operable":[("599","G1","OP","999","X"),
                       ("599","G2","OP","","X")],
           "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_members(*sample(gens=g,owners=[]),require_pinned=False)
        self.assertEqual(r["generator_keys_without_source_utility_id"],1)
        self.assertEqual(r["generator_keys_with_a_utility_id_in_original_utility_roster"],0)

    def test_native_sha_enforced_by_default(self):
        with self.assertRaisesRegex(m.GeneratorOperatorJoinBlocked,"source workbook SHA"):
            m.inspect_members(*sample())

    def test_non_canonical_original_outer_archive_cannot_be_used(self):
        with self.assertRaises(m.GeneratorOperatorJoinBlocked):
            m.inspect_pinned_original_zip(sample()[0])

    def test_exact_2025_cohort_is_distinct_source_supported_15(self):
        self.assertEqual(len(m.COHORT),15)
        self.assertEqual(m.GEN_SHA,"931e1ed0be2c6706794c196f158f779b5c8a32d08c61d748a823dfc25a3201a8")
        self.assertEqual(m.UTIL_SHA,"aa82abf7ecab6d202d44952e7ada2586f8a053dead3956d3eaca756bc8232db9")
        self.assertEqual(m.OWNER_SHA,"f0600c57b24f065017983e50a8a6561c8aa563382bb8862ad216448ca32d9383")


if __name__=="__main__":
    unittest.main()
