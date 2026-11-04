# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research source admission safeguards: no claim that agency or bank is insured."""
from pathlib import Path
import unittest
import tomllib
import copy
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research/observations/rva_distribution_bancassurance_public_awards_20261105_v0.toml"
BLOCKED=("actual_rva_insured_kreis_distribution_observed",
         "actual_rva_specific_building_sites_observed",
         "actual_rva_company_geo_tiv_observed",
         "bank_branch_to_rva_policy_conversion_observed",
         "agency_to_insured_building_conversion_observed",
         "public_award_full_object_schedule_and_coinsurance_share_verified",
         "rights_review_complete","cat_model_input_approved")
LOCAL_BLOCKED=("original_document_bytes_sha256_verified_this_turn",
               "actual_rva_solo_insured_policy_risk_locations_known",
               "actual_rva_solo_regional_market_share_known",
               "issuer_specific_claims_at_natural_peril_risk_site_known",
               "model_source_admitted_as_real_rva_company_location")

def load():
    return tomllib.loads(SOURCE.read_text(encoding="utf-8"))

def validate(c):
    if (c.get("schema_version")!="RVA_DISTRIBUTION_AFFINITY_AND_NAMED_AWARD_SOURCE_REGISTER_V0"
            or c.get("target_legal_entity")!="R+V Allgemeine Versicherung AG"
            or c.get("research_date")!="2026-11-05"):
        raise ValueError("wrong issuer source scope/date/schema")
    records=c.get("candidates",[])
    if c.get("candidate_count")!=28 or len(records)!=28:
        raise ValueError("source register length changed, needs review")
    ids=[r.get("id") for r in records]
    if len(set(ids))!=28 or any(not isinstance(k,str) or not k for k in ids):
        raise ValueError("source IDs must be unique and meaningful")
    if any(c.get(key) is not False for key in BLOCKED):
        raise ValueError("public source register falsely asserted insurer geography/TIV or approved rights")
    allowed={"P0","P1","P2"}
    for r in records:
        if any(r.get(key) is not False for key in LOCAL_BLOCKED):
            raise ValueError("individual source promoted to insurer risk or model without evidence")
        url=r.get("url","")
        parts=urlsplit(url)
        if parts.scheme!="https" or not parts.netloc or parts.fragment:
            raise ValueError("invalid public source HTTPS provenance")
        if r.get("research_priority") not in allowed:
            raise ValueError("unknown research action priority")
        for key in ("publisher","vintage","source_scope","geographic_grain",
                    "public_evidence","admission_blocker"):
            if len(r.get(key,""))<(2 if key=="publisher" else 4 if key=="vintage" else 8):
                raise ValueError("incomplete mandatory source field")
    return {r["id"]:r for r in records}

class DistributionAndPublicTenderEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.c=load()
        self.sources=validate(self.c)

    def test_28_new_unique_cross_domain_candidates(self):
        self.assertEqual(len(self.sources),28)
        self.assertGreaterEqual(sum(r["research_priority"]=="P0" for r in self.sources.values()),12)

    def test_all_sources_explicitly_not_rva_insured_sites(self):
        self.assertTrue(all(self.c[k] is False for k in BLOCKED))
        self.assertTrue(all(not any(r[k] for k in LOCAL_BLOCKED) for r in self.sources.values()))

    def test_2023_named_wbm_building_award_does_not_establish_asset_list(self):
        r=self.sources["wbm_residential_award2023"]
        self.assertEqual(r["source_scope"],"named_procurement_award_secondary_confirm")
        self.assertIn("783307-2023",r["public_evidence"])
        self.assertIn("unknown",r["admission_blocker"].lower())

    def test_2026_nine_commercial_coinsurance_is_separate_from_residential(self):
        x=self.sources["wbm_commercial_award2026"]
        self.assertIn("nine",x["public_evidence"])
        self.assertIn("HDI",x["public_evidence"])
        self.assertIn("Helvetia",x["public_evidence"])
        self.assertIn("Coinsurer",x["admission_blocker"])

    def test_motor_fleet_award_cannot_become_property_exposure(self):
        x=self.sources["rosenheim_fleet_negative"]
        self.assertIn("motor",x["geographic_grain"])
        self.assertIn("exclude",x["admission_blocker"])

    def test_bvr_members_do_not_become_2025_rva_policyholders(self):
        x=self.sources["bvr_2025_region"]
        self.assertEqual(x["source_scope"],"cooperative_banking_industry")
        self.assertIn("not all",x["admission_blocker"].lower())

    def test_partner_count_publisher_conflict_is_preserved(self):
        own=self.sources["ruv_group_network"]
        recrut=self.sources["ruv_sales_training"]
        self.assertIn("260",own["public_evidence"])
        self.assertIn("300",recrut["public_evidence"])
        self.assertIn("Different",recrut["admission_blocker"])

    def test_2025_farm_insurance_vs_2025_solo_residential_policy(self):
        agr=self.sources["ruv_agricultural_property"]
        self.assertIn("Separate",agr["admission_blocker"])
        br=self.sources["brandenburg_lbv_vvb"]
        self.assertEqual(br["source_scope"],"named_partner_agrarian")

    def test_bvg_corporate_inventory_dwellings_not_policy_sites(self):
        x=self.sources["wbm_2025_company_reports"]
        self.assertIn("Dwellings",x["admission_blocker"])
        self.assertIn("2023",x["admission_blocker"])

    def test_gdv_county_flood_industry_not_insurer(self):
        x=self.sources["gdv_county_flood_market"]
        self.assertEqual(x["source_scope"],"industry_peril_benchmark")
        self.assertIn("not carrier-specific",x["admission_blocker"].lower())

    def test_tampered_true_flags_rejected(self):
        for k in BLOCKED:
            with self.subTest(k=k):
                copy_c=copy.deepcopy(self.c);copy_c[k]=True
                with self.assertRaises(ValueError):
                    validate(copy_c)

    def test_tampered_issuer_or_missing_source_rejected(self):
        c=copy.deepcopy(self.c);c["target_legal_entity"]="R+V Gruppe"
        with self.assertRaises(ValueError):validate(c)
        c=copy.deepcopy(self.c);c["candidates"].pop()
        with self.assertRaises(ValueError):validate(c)

    def test_unlicensed_ftp_or_http_source_blocked(self):
        for p in ("http://example.org/a","ftp://example.org/a"):
            c=copy.deepcopy(self.c);c["candidates"][0]["url"]=p
            with self.assertRaises(ValueError):validate(c)

if __name__=="__main__":
    unittest.main()
