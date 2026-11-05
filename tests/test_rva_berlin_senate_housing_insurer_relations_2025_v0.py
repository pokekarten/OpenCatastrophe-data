# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Primary Berlin Senate 2025 company-building insurance relationships.

A company-level insurance policy is neither a person nor an individually
geocoded insured building. Six public corporation facts are safe as metadata.
"""
from pathlib import Path
import copy
import tomllib
import unittest

SOURCE=Path(__file__).resolve().parents[1]/"research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml"
RVA="R+V Allgemeine Versicherung AG"
POS={"degewo AG","GESOBAU AG","WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"}
NEG={"Gewobag Wohnungsbau-Aktiengesellschaft Berlin",
     "HOWOGE Wohnungsbaugesellschaft mbH",
     "STADT UND LAND Wohnbauten-Gesellschaft mbH"}
FALSE_FLAGS=(
    "source_original_document_sha256_verified",
    "wbm_pure_commercial_2025_rva_carrier_identified_by_this_senate_answer",
    "degewo_rva_coinsurance_fraction_observed",
    "insured_policies_for_either_rva_company_count_observed",
    "number_of_insured_properties_observed",
    "corporate_owner_dwelling_count_equal_insured_properties",
    "rva_specific_storm_hail_claims_observed",
    "company_tiv_or_coverage_deductibles_at_site_observed",
    "named_competitor_means_exclusive_no_rva_insurance_any_time",
    "company_2026_renewal_or_current_carrier_observed",
    "natcat_OEP_AEP_or_RI_terms_observed",
    "model_real_rva_exposure_site_admitted",
)
CORP_FALSE=(
    "risk_addresses_known","insured_building_count_known","covered_property_tiv_known",
    "carrier_2026_still_current_confirmed",
    "individual_building_is_separate_insurance_contract",
)

def load():
    return tomllib.loads(SOURCE.read_text(encoding="utf-8"))

def validate(d):
    if (d.get("schema_version")!="BERLIN_SENATE_2025_PUBLIC_HOUSING_BUILDING_INSURER_RELATIONSHIPS_V0"
        or d.get("source_document_number")!="Drucksache 19/22033"
        or d.get("source_official_url")!="https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf"
        or d.get("source_issuing_authority")!="Senatsverwaltung fuer Stadtentwicklung Bauen und Wohnen Berlin"
        or d.get("source_statement_date")!="2025-04-01"
        or d.get("source_page_pdf_zero_based_for_relationships")!=2
        or d.get("source_question_ids")!=[2,3,4,10]
        or d.get("risk_geography")!="Berlin public housing entities; no verified insured site-level or administrative district footprints"):
        raise ValueError("original Berlin 2025 senate source attribution changed")
    if len(d.get("housing_companies",[]))!=6 or d.get("public_named_berlin_housing_entities")!=6:
        raise ValueError("Berlin housing company count changed")
    if any(d.get(flag) is not False for flag in FALSE_FLAGS):
        raise ValueError("company relationships unlawfully promoted to insured risk lists")
    if (d.get("source_relationships_observed_as_of_2025") is not True
        or d.get("source_relationships_derived_from_public_company_submissions") is not True
        or d.get("policy_structure")!="building_insurance_overarching_blanket_company_contract_not_one_policy_per_building"
        or d.get("wbm_separate_commercial_master_policy") is not True
        or d.get("confirmed_rva_named_housing_company_count")!=3
        or d.get("no_rva_named_other_insurer_company_count")!=3
        or d.get("cover_summary_is_not_per_object_schedule") is not True):
        raise ValueError("unreconciled official Senate insurer, policy or cover semantics")
    if d.get("market_coverage_terms_across_lwu")!=["fire","tap_water","storm_hail","elemental","vandalism"]:
        raise ValueError("published 2025 peril cover blocks changed")
    rows=d["housing_companies"]
    names={r.get("legal_name") for r in rows}
    if names!=POS|NEG or len(names)!=6:raise ValueError("company legal identity mismatch")
    rmap={r["legal_name"]:r for r in rows}
    for key,r in rmap.items():
        insured=key in POS
        if (r.get("rva_allgemeine_explicitly_named") is not insured
            or (RVA in r.get("named_insurers",[]))!=insured
            or r.get("other_insurer_comparator") is insured
            or r.get("carrier_observation_date")!="2025-04-01"
            or r.get("source_question_number")!=2
            or any(r.get(f) is not False for f in CORP_FALSE)):
            raise ValueError("falsely attributed issuer/direct 2025 contract or unknown site")
    if len(rmap["degewo AG"]["named_insurers"])!=2:
        raise ValueError("degewo Allianz co-insurance missing")
    if rmap["degewo AG"]["insurance_relation_type"]!="named_member_of_coinsurance_consortium":
        raise ValueError("degewo carrier not full insured quota")
    if any(len(r["named_insurers"])<1 for r in rows):
        raise ValueError("missing comparator insurer record")
    return rmap

class SenatePrimary2025InsuranceRelationship(unittest.TestCase):
    def setUp(self):self.d=load()
    def test_six_company_primary_named_source(self):
        self.assertEqual(len(validate(self.d)),6)
        self.assertEqual(self.d["source_statement_date"],"2025-04-01")
    def test_three_explicit_rva_and_three_comparators(self):
        m=validate(self.d)
        self.assertEqual({k for k,v in m.items() if v["rva_allgemeine_explicitly_named"]},POS)
        self.assertEqual({k for k,v in m.items() if not v["rva_allgemeine_explicitly_named"]},NEG)
    def test_degewo_insurance_consortium_not_exclusive(self):
        m=validate(self.d)
        self.assertEqual(set(m["degewo AG"]["named_insurers"]),{RVA,"Allianz AG"})
        self.assertFalse(self.d["degewo_rva_coinsurance_fraction_observed"])
    def test_wbm_gsobau_real_named_counterparties_not_insured_sites(self):
        m=validate(self.d)
        for n in ("GESOBAU AG","WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"):
            self.assertEqual(m[n]["named_insurers"],[RVA])
            self.assertFalse(m[n]["risk_addresses_known"])
    def test_wbm_commercial_separate_and_unknown_insurer(self):
        validate(self.d)
        self.assertTrue(self.d["wbm_separate_commercial_master_policy"])
        self.assertFalse(self.d["wbm_pure_commercial_2025_rva_carrier_identified_by_this_senate_answer"])
    def test_general_perils_not_site_specific_terms(self):
        validate(self.d)
        self.assertEqual(len(self.d["market_coverage_terms_across_lwu"]),5)
        self.assertTrue(self.d["cover_summary_is_not_per_object_schedule"])
    def test_no_dwelling_count_or_location_promotion(self):
        validate(self.d)
        self.assertTrue(all(not self.d[x] for x in FALSE_FLAGS))
        self.assertTrue(all(not r[x] for r in self.d["housing_companies"] for x in CORP_FALSE))
    def test_no_2026_renewal_claim(self):
        m=validate(self.d)
        self.assertTrue(all(not r["carrier_2026_still_current_confirmed"] for r in m.values()))
    def test_tamper_positive_as_competitor_blocked(self):
        d=copy.deepcopy(self.d)
        x=next(x for x in d["housing_companies"] if x["legal_name"]=="GESOBAU AG")
        x["rva_allgemeine_explicitly_named"]=False
        with self.assertRaises(ValueError):validate(d)
    def test_tamper_degewo_as_full_exclusive_blocked(self):
        d=copy.deepcopy(self.d)
        x=next(x for x in d["housing_companies"] if x["legal_name"]=="degewo AG")
        x["named_insurers"]=[RVA]
        with self.assertRaises(ValueError):validate(d)
    def test_tamper_current_2026_insurance_blocked(self):
        d=copy.deepcopy(self.d);d["company_2026_renewal_or_current_carrier_observed"]=True
        with self.assertRaises(ValueError):validate(d)
    def test_tamper_false_risk_address_blocked(self):
        d=copy.deepcopy(self.d)
        d["housing_companies"][0]["risk_addresses_known"]=True
        with self.assertRaises(ValueError):validate(d)
    def test_missing_named_competitor_blocked(self):
        d=copy.deepcopy(self.d);d["housing_companies"].pop()
        with self.assertRaises(ValueError):validate(d)

if __name__=="__main__":
    unittest.main()
