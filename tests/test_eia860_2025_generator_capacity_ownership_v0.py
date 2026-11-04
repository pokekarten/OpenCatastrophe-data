# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only nameplate MW / ownership S-J-W source cardinality regressions."""
from __future__ import annotations

from io import BytesIO
import json
import unittest
from zipfile import ZIP_DEFLATED,ZipFile

from research_runners import eia860_2025_generator_capacity_ownership_v0 as m
from tests.test_eia860_2025_generator_utility_owner_join_v0 import make_xlsx

HEAD=("Plant Code","Generator ID","Status","Utility ID",
      "Nameplate Capacity (MW)","Prime Mover","Energy Source 1","Ownership")
OWNER_HEAD=("Plant Code","Generator ID")

def source(gen=None,owners=None):
    if gen is None:
        gen={
            "Operable":[("599","GEN-1","OP","101","10.5","PV","SUN","S"),
                       ("599","GEN-2","OP","101","4.25","GT","NG","J"),
                       ("7318","GEN-3","SB","102","0.750","IC","DFO","S")],
            "Proposed":[("599","NEW1","P","101","50.00","PV","SUN","S")],
            "Retired and Canceled":[("599","OLD1","RE","101","3.0","GT","NG","W")]
        }
    if owners is None:
        owners=[("599","GEN-2"),("599","OLD1")]
    gen_file=make_xlsx([(tab,HEAD,gen.get(tab,[])) for tab in
                        ("Operable","Proposed","Retired and Canceled")])
    owner_file=make_xlsx([("Ownership",OWNER_HEAD,owners)])
    return gen_file,owner_file

class NativeNameplateOwnerTests(unittest.TestCase):
    def test_live_like_complete_synthetic_source_cohort(self):
        r=m.inspect_original_members(*source(),require_pinned=False)
        self.assertEqual(r["original_gen_keys"],5)
        self.assertEqual(r["by_reporting_tab_nameplate_mw_not_tiv"],
                         {"Operable":"15.500","Proposed":"50.000","Retired and Canceled":"3.000"})
        self.assertEqual(r["by_exact_2025_source_status_nameplate_mw_not_tiv"],
                         {"OP":"14.750","P":"50.000","RE":"3.000","SB":"0.750"})
        self.assertEqual(r["by_reporting_tab_prime_mover_family_nameplate_mw_not_tiv"]["Operable"],
                         {"gas_turbine":"4.250","internal_combustion":"0.750",
                          "solar_pv":"10.500"})
        self.assertEqual(r["by_reporting_tab_ownership_code_S_J_W"]["Operable"],
                         {"S":2,"J":1,"W":0})
        self.assertEqual(r["owner_schedule_gen_keys_by_original_ownership_code"],
                         {"S":0,"J":1,"W":1})
        self.assertEqual(r["original_generators_J_or_W_without_owner_schedule"],0)
        self.assertEqual(r["original_generators_S_with_owner_schedule"],0)
        self.assertEqual(r["by_reporting_tab_prime_mover_equipment_families"]["Operable"],
                         {"gas_turbine":1,"internal_combustion":1,"solar_pv":1})
        self.assertEqual(r["state"],"SOURCE_CAPACITY_OWNERSHIP_RESEARCH_ONLY")
        self.assertFalse(r["generator_capacity_is_replacement_cost_tiv"])
        self.assertFalse(r["generator_equals_one_insured_asset"])
        self.assertFalse(r["insurer_portfolio_or_treaty_admitted"])
        self.assertFalse(r["source_2025_status_equals_2026_operational_status"])
        self.assertFalse(r["raw_generator_owner_ids_and_names_emitted"])
        payload=json.dumps(r)
        self.assertNotIn("GEN-1",payload)
        self.assertNotIn("GEN-2",payload)
        self.assertNotIn("599",payload)

    def test_single_ownership_with_owner_schedule_requires_review(self):
        r=m.inspect_original_members(*source(owners=[("599","GEN-1"),("599","GEN-2"),
                                                 ("599","OLD1")]),require_pinned=False)
        self.assertEqual(r["original_generators_S_with_owner_schedule"],1)
        self.assertEqual(r["state"],"REVIEW_SOURCE_OWNERSHIP_CAPACITY")

    def test_jointly_owned_missing_owner_schedule_requires_review(self):
        r=m.inspect_original_members(*source(owners=[("599","OLD1")]),require_pinned=False)
        self.assertEqual(r["original_generators_J_or_W_without_owner_schedule"],1)
        self.assertEqual(r["state"],"REVIEW_SOURCE_OWNERSHIP_CAPACITY")

    def test_missing_nameplate_marked_not_imputed(self):
        g={"Operable":[("599","G1","OP","123","","PV","SUN","S")],
           "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_original_members(*source(gen=g,owners=[]),require_pinned=False)
        self.assertEqual(r["by_reporting_tab_nameplate_missing_or_invalid"]["Operable"],1)
        self.assertEqual(r["by_reporting_tab_nameplate_mw_not_tiv"]["Operable"],"0.000")
        self.assertEqual(r["state"],"REVIEW_SOURCE_OWNERSHIP_CAPACITY")

    def test_capacity_units_not_converted_to_dollars(self):
        self.assertEqual(str(m._frozen_mw("0.4")),"0.4")
        self.assertEqual(str(m._frozen_mw("1234.5678")),"1234.5678")
        self.assertIsNone(m._frozen_mw("1,234"))
        self.assertIsNone(m._frozen_mw("123 MW"))
        self.assertIsNone(m._frozen_mw("-10"))
        self.assertIsNone(m._frozen_mw("n/a"))
        self.assertIsNone(m._frozen_mw("50001"))
        self.assertIsNone(m._frozen_mw("NaN"))

    def test_source_name_not_emitted_as_prime_mover(self):
        g={"Operable":[("599","G1","OP","123","0.5","PRIVATE CUSTOMER NAME","SUN","S")],
           "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_original_members(*source(gen=g,owners=[]),require_pinned=False)
        self.assertEqual(r["unmapped_prime_mover_by_tab"]["Operable"],1)
        self.assertNotIn("PRIVATE CUSTOMER",json.dumps(r))
        self.assertEqual(r["state"],"REVIEW_SOURCE_OWNERSHIP_CAPACITY")

    def test_duplicate_generator_key_fails_no_multiplication(self):
        g={"Operable":[("599","G1","OP","123","1","GT","NG","S"),
                       ("599","G1","OP","123","1","GT","NG","S")],
           "Proposed":[],"Retired and Canceled":[]}
        with self.assertRaisesRegex(m.NativeCapacityBlocked,"duplicate generator"):
            m.inspect_original_members(*source(gen=g,owners=[]),require_pinned=False)

    def test_original_generator_and_owner_sha_fails_closed(self):
        with self.assertRaisesRegex(m.NativeCapacityBlocked,"member hash mismatch"):
            m.inspect_original_members(*source(),require_pinned=True)

    def test_original_zip_requires_exact_full_archive_hash(self):
        with self.assertRaises(m.NativeCapacityBlocked):
            m.inspect_pinned_original_zip(source()[0])

    def test_unknown_ownership_code_flagged_without_echoing(self):
        g={"Operable":[("599","G1","OP","123","1.5","PV","SUN","INTERNAL NAME")],
           "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_original_members(*source(gen=g,owners=[]),require_pinned=False)
        self.assertEqual(r["ownership_code_missing_or_unknown_by_tab"]["Operable"],1)
        self.assertNotIn("INTERNAL NAME",json.dumps(r))
        self.assertEqual(r["state"],"REVIEW_SOURCE_OWNERSHIP_CAPACITY")

    def test_unkeyed_source_footer_ignored_not_a_generator(self):
        g={"Operable":[("599","G1","OP","123","1.5","PV","SUN","S"),
                       ("Footnote","","","","","","","")],
           "Proposed":[],"Retired and Canceled":[]}
        r=m.inspect_original_members(*source(gen=g,owners=[]),require_pinned=False)
        self.assertEqual(r["original_gen_keys"],1)
        self.assertEqual(r["excluded_source_unkeyed_rows_by_tab"]["Operable"],1)
        self.assertEqual(r["by_reporting_tab_nameplate_mw_not_tiv"]["Operable"],"1.500")

if __name__ == "__main__":
    unittest.main()
