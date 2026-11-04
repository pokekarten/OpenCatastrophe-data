# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline evidence-perimeter and solo policy-scale tests. No company exposure inferred."""

from decimal import Decimal
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
EVIDENCE = ROOT / "research/observations/rva_public_event_tariff_distribution_signals_v0.toml"

def read(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))

def validate(history, evidence):
    if history.get("entity") != "R+V Allgemeine Versicherung AG":
        raise ValueError("Changed target insurer")
    contract = history.get("building_contract_observations", {})
    years = contract.get("years", [])
    if ([x.get("year") for x in years] != [2023, 2024, 2025]
            or [x.get("contracts") for x in years] != [1036338, 1073802, 1060546]):
        raise ValueError("Not exact issuer year-end property policy series")
    if (contract.get("unit") != "contracts"
            or any(contract.get(k) is not False for k in (
                "company_insured_building_coordinates_observed",
                "company_natcat_covered_building_count_observed",
                "company_geographic_contract_shares_observed"))):
        raise ValueError("Contract count falsely promoted to geocoded insured building")
    if years[1].get("prior_year_condor_building_contracts") != 68847:
        raise ValueError("Missing separate merger stock context")
    if years[2].get("prior_year_direkt_building_contracts") != 0:
        raise ValueError("Direct insurer merger erroneously creates property stock")
    for x in years:
        if not x.get("source_url", "").startswith("https://www.ruv.de/"):
            raise ValueError("Insurer original HGB source URL required")
        if x["year"] in (2024,2025) and x.get("perimeter_break") is not True:
            raise ValueError("Merger scope break removed")
    claims = history.get("building_gross_claims_observations", {})
    if (claims.get("legal_entity") != history["entity"]
            or claims.get("basis") != "HGB_bruttoaufwendungen_fuer_versicherungsfaelle_self_written_connected_buildings"
            or claims.get("unit") != "EUR"
            or any(claims.get(k) is not False for k in (
                "observed_peril_split","observed_event_split","observed_net_natcat_loss"))):
        raise ValueError("All-cause gross claims promoted to solo peril loss")
    cy = claims.get("years", [])
    if [x["year"] for x in cy] != [2024, 2025]:
        raise ValueError("All-cause claim observation years")
    if ([Decimal(x["gross_claims_eur"]) for x in cy]
            != [Decimal("717388635.00"),Decimal("577492703.97")]):
        raise ValueError("Original issuer gross claim amount changed")
    if (evidence.get("target_legal_entity") != history["entity"]
            or evidence.get("schema_version") != "RVA_PUBLIC_EVENT_TARIFF_DISTRIBUTION_SIGNALS_V0"
            or any(evidence.get(k) is not False for k in (
                "company_insured_address_observed","company_regional_portfolio_shares_observed",
                "company_peril_specific_solo_loss_observed","company_treaty_structure_observed",
                "production_calibration_authorized"))):
        raise ValueError("Evidence advertised as real company portfolio")
    es = evidence.get("evidence", [])
    if len(es) < 10 or len({x.get("id") for x in es}) != len(es):
        raise ValueError("Missing/duplicate distinct source evidence")
    known_scopes = {"group_customer_population_mixed_entities",
                    "group_distribution_network_not_solo_property",
                    "solo_company_channel_description",
                    "group_marketing_not_insured_book_mix",
                    "public_blank_form_no_customer_records",
                    "published_standard_terms_not_policy_sales"}
    known_kinds = {"historical_group_cat_loss_context", "preliminary_group_event_loss_context",
                   "group_annual_peril_claims_context", "documented_local_group_claim_handling",
                   "group_sales_territory", "group_sales_footprint",
                   "solo_insurer_distribution_description", "issuer_residential_product",
                   "issuer_underwriting_field_dictionary", "issuer_agricultural_product",
                   "issuer_agricultural_policy_wording", "issuer_commercial_property_product"}
    for row in es:
        if (row.get("kind") not in known_kinds
                or row.get("scope") not in known_scopes
                or row.get("solo_geographic_exposure_admitted") is not False
                or row.get("solo_catastrophe_loss_calibration_admitted") is not False
                or not row.get("source", "").startswith("https://")
                or not row.get("blocked") or not row.get("use")):
            raise ValueError("Evidence lost scientific perimeter/provenance")
        if row["kind"] in ("group_annual_peril_claims_context", "preliminary_group_event_loss_context",
                           "historical_group_cat_loss_context"):
            if row["scope"] != "group_customer_population_mixed_entities":
                raise ValueError("Group press claims falsely promoted to solo loss")
            if "amount" not in row or row.get("qualifier") in (None, "exact"):
                raise ValueError("Source loss estimates are qualified, not exact")
            if "motor_amount" in row and Decimal(row["motor_amount"]) > Decimal(row["amount"]):
                raise ValueError("Motor cannot exceed total group hail loss")
    b = next(x for x in es if x["id"] == "ruv_bernd_flood_claims_report_20220707")
    if (b["flood_coverage_population"] != "affected_R+V_customers_in_flood_areas_2021"
            or b["flood_coverage_fraction"] != "0.75"
            or b["large_claim_threshold"] != "250000"
            or b["scope"] != "group_customer_population_mixed_entities"):
        raise ValueError("Selected flood region sample falsely generalized")
    h = next(x for x in es if x["id"] == "ruv_hail_2024_followup_20250521")
    if h.get("motor_amount") != "56" or h.get("motor_included") is not True:
        raise ValueError("Group hail auto claims mixed with building loss")
    return (years, es)

class PublicRvaPerimeterTests(unittest.TestCase):
    def setUp(self):
        self.h = read(HISTORY)
        self.e = read(EVIDENCE)
    def test_original_series_and_14_secondary_signals(self):
        y, es = validate(self.h, self.e)
        self.assertEqual(len(y), 3)
        self.assertEqual(len(es), 14)
    def test_2025_exact_contract_count_and_2024_previous(self):
        y, _ = validate(self.h, self.e)
        self.assertEqual(y[2]["contracts"]-y[1]["contracts"], -13256)
    def test_wrong_legal_entity_blocked(self):
        self.h["entity"] = "R+V Versicherung AG"
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_incorrect_contract_or_year_blocked(self):
        self.h["building_contract_observations"]["years"][2]["contracts"] = 1100000
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_claims_cannot_become_event_loss(self):
        self.h["building_gross_claims_observations"]["observed_event_split"] = True
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_2024_condor_inherited_stock_is_not_organic_growth(self):
        self.h["building_contract_observations"]["years"][1]["prior_year_condor_building_contracts"] = 0
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_group_claims_cannot_be_relabelled_solo(self):
        self.e["evidence"][0]["scope"] = "solo_company_channel_description"
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_motor_portion_cannot_exceed_hail_claims(self):
        next(x for x in self.e["evidence"] if x["id"] == "ruv_hail_2024_followup_20250521")["motor_amount"] = "98"
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_conditional_bernd_coverage_not_unconditional(self):
        self.e["evidence"][0]["flood_coverage_population"] = "all_R+V_Germany_property_policies"
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_agencies_cannot_be_used_as_company_regional_shares(self):
        self.e["company_regional_portfolio_shares_observed"] = True
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_documented_product_terms_not_confirmed_policy_sales(self):
        self.e["evidence"][-1]["solo_catastrophe_loss_calibration_admitted"] = True
        with self.assertRaises(ValueError): validate(self.h, self.e)
    def test_missing_source_and_duplicate_claim_blocked(self):
        self.e["evidence"][1]["id"] = self.e["evidence"][0]["id"]
        with self.assertRaises(ValueError): validate(self.h, self.e)

if __name__ == "__main__":
    unittest.main()
