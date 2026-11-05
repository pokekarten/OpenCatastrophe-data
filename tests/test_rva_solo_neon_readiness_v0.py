# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline invariants for the read-only R+V SOLO/Neon reporting contract.

These tests guard source identity and accounting interpretation, NOT SQL runtime
semantics or a claim that source records are approved. The SQL was additionally
executed read-only against live Neon and must be replayed before promotion.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "research_runners/sql/rva_solo_2025_neon_readiness_v0.sql"
SFCR = ROOT / "research/observations/rva_solo_2025_public_sfcr_v0.toml"
HGB = ROOT / "research/observations/rva_solo_hgb_property_2019_2025_v0.toml"
LEI = ROOT / "research/observations/berlin_named_carrier_lei_temporal_preflight_20261105_v0.toml"
SOLO_LEI = "5299009UN4CBXZ336M65"
PARENT_LEI = "529900Z5KBA9KJP6EK09"


def lei_mod97(s: str) -> int:
    """ISO 17442 two-character checksum, independently of existing repo helper."""
    if not re.fullmatch(r"[A-Z0-9]{20}", s):
        return -1
    remainder = 0
    for char in s:
        expanded = str(ord(char) - 55) if "A" <= char <= "Z" else char
        for digit in expanded:
            remainder = (remainder * 10 + int(digit)) % 97
    return remainder


class RvaSoloNeonReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.sfcr = tomllib.loads(SFCR.read_text(encoding="utf-8"))
        cls.hgb = tomllib.loads(HGB.read_text(encoding="utf-8"))
        cls.lei = tomllib.loads(LEI.read_text(encoding="utf-8"))

    def test_independently_valid_solo_and_parent_lei(self) -> None:
        self.assertEqual(lei_mod97(SOLO_LEI), 1)
        self.assertEqual(lei_mod97(PARENT_LEI), 1)
        self.assertNotEqual(SOLO_LEI, PARENT_LEI)
        self.assertNotEqual(lei_mod97(SOLO_LEI[:-1] + "6"), 1)

    def test_solo_lei_is_already_research_evidenced_not_newly_invented(self) -> None:
        rows = [r for r in self.lei["source_carriers"]
                if r["reported_label"] == "R+V Allgemeine Versicherung AG"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["resolved_lei"], SOLO_LEI)
        self.assertEqual(rows[0]["resolved_legal_name"],
                         "R+V Allgemeine Versicherung Aktiengesellschaft")
        self.assertEqual(rows[0]["resolved_jurisdiction"], "DE")
        self.assertFalse(self.lei["original_regulator_or_gleif_http_json_hashed_in_this_preflight"])

    def test_sfcr_solo_2025_is_only_premium_not_tiv(self) -> None:
        profiles = [p for p in self.sfcr["profiles"] if p["profile_id"] == "RVA_DE_2025"]
        self.assertEqual(len(profiles), 1)
        p = profiles[0]
        self.assertEqual(p["entity"], "R+V Allgemeine Versicherung AG")
        self.assertEqual(p["entity_kind"], "solo_direct_insurer")
        self.assertEqual(p["report_year"], 2025)
        self.assertEqual(p["lob_measure"], "gross_written_premium_eur_million")
        premium = {row["code"]: Decimal(row["value"]) for row in p["lob_rows"]}
        self.assertEqual(premium["fire_and_other_property"], Decimal("2223.182"))
        self.assertEqual(Decimal(p["basis"]["denominator_eur_million"]), Decimal("5992.306"))

    def test_hgb_direct_building_premium_is_different_scope(self) -> None:
        year = next(row for row in self.hgb["years"] if row["year"] == 2025)
        self.assertEqual(year["connected_buildings_self_written"], 997710)
        self.assertEqual(year["fire_property_self_written"], 2125473)
        self.assertNotEqual(year["fire_property_self_written"], 2223182)
        self.assertEqual(self.hgb["cross_basis_2025"]["status"],
                         "non_equivalent_premium_classifications_reconciliation_not_established")

    def test_exact_year_end_contract_stock_not_geocoded_buildings(self) -> None:
        data = self.hgb["building_contract_observations"]
        last = next(row for row in data["years"] if row["year"] == 2025)
        self.assertEqual(last["contracts"], 1060546)
        self.assertEqual(last["source_report_year"], 2025)
        self.assertEqual(data["unit"], "contracts")
        self.assertFalse(data["company_insured_building_coordinates_observed"])
        self.assertFalse(data["company_geographic_contract_shares_observed"])
        self.assertIn("m.as_of_date = DATE '2025-12-31'", self.sql)

    def test_corporate_perimeter_breaks_2024_2025(self) -> None:
        years = {r["year"]: r for r in self.hgb["years"]}
        self.assertTrue(years[2024]["corporate_perimeter_break"])
        self.assertTrue(years[2025]["corporate_perimeter_break"])
        self.assertIn("Condor", years[2024]["merger_event"])
        self.assertIn("R+V Direktversicherung", years[2025]["merger_event"])
        self.assertIn("2025-01-01", years[2025]["merger_event"])

    def test_query_requires_exact_solo_leis_and_register_source(self) -> None:
        for term in (SOLO_LEI, PARENT_LEI, "o.legal_name IN",
                     "o.identity_status = 'verified'", "o.domicile_country = 'DE'",
                     "o.organization_type = 'insurer'", "i.identifier_scheme='GLEIF_LEI'",
                     "i.is_verified", "parent_lei_wrongly_on_solo_rows",
                     "exact_source_bound_solo_lei_rows", "registry.source_record",
                     "acpr.banque-france.fr"):
            with self.subTest(term=term):
                self.assertIn(term, self.sql)

    def test_query_separates_hgb_and_sfcr_without_premium_to_tiv(self) -> None:
        for term in ("2223182000", "1060546", "997710000",
                     "source_bound_exact_sfcr_property_gwp_rows",
                     "source_bound_exact_hgb_building_contract_rows",
                     "source_bound_exact_hgb_building_gwp_rows",
                     "company_geolocated_insured_tiv_observed_by_these_sources",
                     "annual_cat_ep_calibrated_by_these_sources"):
            with self.subTest(term=term):
                self.assertIn(term, self.sql)
        # Financial source receipts must carry an independently checked original
        # PDF and explicit metric-scope review, not merely a source-key join.
        self.assertEqual(self.sql.count("verified_original_financial_observation"), 3)
        self.assertEqual(self.sql.count("publisher_original_sha256_verified"), 3)
        self.assertEqual(self.sql.count("accounting_line_and_basis_verified"), 3)
        self.assertIn("false::boolean AS annual_cat_ep_calibrated_by_these_sources", self.sql)
        self.assertIn("false::boolean AS company_geolocated_insured_tiv_observed_by_these_sources", self.sql)

    def test_query_does_not_promote_reported_or_real_instead_of_synthetic(self) -> None:
        for term in ("company_linked_synthetic_portfolios",
                     "company_linked_reported_aggregate_portfolios",
                     "company_linked_real_restricted_portfolios",
                     "company_linked_exposure_units",
                     "RESEARCH_ONLY_NEEDS_HAZARD_VULNERABILITY_RIGHTS_AND_TREATY_REVIEW"):
            self.assertIn(term, self.sql)

    def test_query_is_one_read_only_select_not_db_mutation(self) -> None:
        code = re.sub(r"--[^\n]*", "", self.sql).strip()
        self.assertTrue(code.startswith("WITH\n"))
        self.assertEqual(code.count(";"), 1)
        self.assertTrue(code.endswith(";"))
        for verb in ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "TRUNCATE",
                     "CREATE", "COPY", "GRANT", "REVOKE", "CALL", "EXECUTE"):
            with self.subTest(verb=verb):
                self.assertIsNone(re.search(r"\b" + verb + r"\b", code, flags=re.I))


if __name__ == "__main__":
    unittest.main()
