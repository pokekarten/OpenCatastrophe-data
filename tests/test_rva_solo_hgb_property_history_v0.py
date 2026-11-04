# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Public, independent HGB history audit: no hidden portfolio or NatCat reconstruction."""
import copy
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
SFCR = ROOT / "research/observations/rva_solo_2025_public_sfcr_v0.toml"


def load():
    return tomllib.loads(SOURCE.read_text(encoding="utf-8"))


def validate(d):
    if (d.get("entity") != "R+V Allgemeine Versicherung AG"
            or d.get("entity_kind") != "solo_direct_insurer"
            or d.get("accounting_basis") != "HGB_Gebuchte_Bruttobeitraege"
            or d.get("premium_unit") != "thousand_eur"
            or d.get("fire_property_scope") != "self_written_direct_business"):
        raise ValueError("Legal entity, accounting or underwriting scope changed")
    if any(d.get(k) is not False for k in (
            "exposure_site_count_observed", "company_insured_tiv_observed",
            "company_geo_exposure_observed", "company_natcat_claims_observed")):
        raise ValueError("Accounting data falsely promoted to observed insurer exposure")
    rows = d.get("years", [])
    if [x["year"] for x in rows] != list(range(2019, 2026)):
        raise ValueError("History lacks a year, or duplicates/out-of-order")
    for r in rows:
        sub = sum(r[k] for k in ("fire_self_written",
                 "household_contents_self_written", "connected_buildings_self_written",
                 "other_property_self_written"))
        if any(r[k] < 0 for k in ("fire_self_written",
                 "household_contents_self_written", "connected_buildings_self_written",
                 "other_property_self_written", "total_accepted_reinsurance_gwp")):
            raise ValueError("Premium measure unexpectedly negative")
        if abs(sub - r["fire_property_self_written"]) > 1:
            raise ValueError("Property line totals do not reconcile to issuer")
        if abs(r["total_self_written_company_gwp"] +
               r["total_accepted_reinsurance_gwp"] -
               r["total_solo_company_gwp"]) > 1:
            raise ValueError("Solo company direct/accepted scope does not reconcile")
        if r["source_scope"] != "issuer_HGB_annual_report" or not r["source_url"].startswith("https://www.ruv.de/"):
            raise ValueError("An original issuer evidence URL is required")
        if r["comparative_from_next_report"] != (r["source_report_year"] != r["year"]):
            raise ValueError("Prior-year comparative source provenance inconsistent")
        if r["corporate_perimeter_break"] != (r["year"] in (2024, 2025)):
            raise ValueError("Merger/perimeter discontinuity lost")
    c = d["cross_basis_2025"]
    if (c["hgb_direct_fire_property_thousand_eur"] != rows[-1]["fire_property_self_written"]
            or c["status"] != "non_equivalent_premium_classifications_reconciliation_not_established"):
        raise ValueError("HGB/Solvency basis incorrectly reconciled")
    return rows


class RvaSoloHgbHistoryTests(unittest.TestCase):
    def test_source_is_valid_and_conserves_reported_splits(self):
        self.assertEqual(len(validate(load())), 7)

    def test_hgb_and_solveny_ii_are_explicitly_different(self):
        d = load()
        sfcr = tomllib.loads(SFCR.read_text(encoding="utf-8"))
        sol = sfcr["profiles"][0]
        self.assertEqual(d["cross_basis_2025"]["solvency_ii_fire_other_property_thousand_eur"], 2223182)
        self.assertEqual(sol["lob_rows"][0]["code"], "fire_and_other_property")
        self.assertEqual(sol["lob_rows"][0]["value"], "2223.182")
        self.assertNotEqual(d["years"][-1]["fire_property_self_written"], 2223182)

    def test_building_contract_count_does_not_become_locations(self):
        d = load()
        o = d["additional_issuer_observations_2025"]
        self.assertEqual(o["building_contracts_approx_million"], "1.1")
        self.assertIn("not_risk_locations", o["building_contract_status"])
        self.assertFalse(d["exposure_site_count_observed"])

    def test_company_geography_is_not_building_geography(self):
        d = load()
        o = d["additional_issuer_observations_2025"]
        self.assertEqual(sum(o[k] for k in (
            "company_domestic_gwp_thousand_eur_sfcr_basis",
            "company_austria_gwp_thousand_eur_sfcr_basis",
            "company_italy_gwp_thousand_eur_sfcr_basis")), 5992305)
        self.assertIn("whole-company", o["geography_warning"])
        self.assertFalse(d["company_geo_exposure_observed"])

    def test_detects_wrong_solo_entity_and_scope(self):
        for k, v in (("entity", "R+V Gruppe"), ("entity_kind", "group"),
                     ("fire_property_scope", "gross_reinsurance_inward"),
                     ("premium_unit", "million_eur")):
            d = load()
            d[k] = v
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate(d)

    def test_detects_missing_year_and_double_year(self):
        d = load()
        d["years"].pop(2)
        with self.assertRaises(ValueError):
            validate(d)
        d = load()
        d["years"][2]["year"] = 2020
        with self.assertRaises(ValueError):
            validate(d)

    def test_detects_broken_property_splits_and_company_totals(self):
        for k in ("connected_buildings_self_written", "total_accepted_reinsurance_gwp"):
            d = load()
            d["years"][-1][k] += 2
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate(d)

    def test_detects_missing_merger_discontinuity(self):
        for year in (2024, 2025):
            d = load()
            d["years"][year - 2019]["corporate_perimeter_break"] = False
            with self.subTest(year=year), self.assertRaises(ValueError):
                validate(d)

    def test_rejects_claimed_real_exposure(self):
        for k in ("exposure_site_count_observed", "company_insured_tiv_observed",
                  "company_geo_exposure_observed", "company_natcat_claims_observed"):
            d = load()
            d[k] = True
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate(d)

    def test_rejects_unreconciled_hgb_sfcr_basis_claim(self):
        d = load()
        d["cross_basis_2025"]["status"] = "fully_equivalent"
        with self.assertRaises(ValueError):
            validate(d)


if __name__ == "__main__":
    unittest.main()
