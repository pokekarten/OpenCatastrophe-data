# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact-source, offline regression for 10k geocoded NRW model-admission gate.

Source physical polygons and fictitious insurer policy assignments remain
different concepts. This test NEVER fetches source data or admits CAT losses.
"""
from __future__ import annotations

from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "research_runners/sql/rva_solo_2025_neon_readiness_v0.sql"
SOURCE = ROOT / "research/observations/rva_nrw_hu22_original_full_10k_53kreis_oed_research_v0.toml"


class NRWGeocodedCohortGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.receipt = tomllib.loads(SOURCE.read_text(encoding="utf-8"))

    def test_exact_all_county_numbers_and_toy_tiv_match_source(self):
        section = self.sql.split("expected_nrw_10k_kreise(ags, n, tiv) AS (", 1)[1]
        section = section.split("nrw_county_completeness AS (", 1)[0]
        actual = {
            (ags, int(count), int(tiv))
            for ags, count, tiv in re.findall(
                r"\('([0-9]{5})',\s*([0-9]+),\s*([0-9]+)\)", section
            )
        }
        expected = {
            (x["ags"], x["fictional_contracts"], x["fictional_tiv_eur"])
            for x in self.receipt["kreis"]
        }
        self.assertEqual(len(actual), 53)
        self.assertEqual(len(expected), 53)
        self.assertEqual(actual, expected)
        self.assertEqual(sum(x[1] for x in actual), 10000)
        self.assertEqual(sum(x[2] for x in actual), 4826029500)
        self.assertTrue(all(x[0].startswith("05") for x in actual))

    def test_no_one_point_or_53_aggregate_can_pass_complete_10k(self):
        for marker in (
            "p.portfolio_type='synthetic'",
            "p.portfolio_key='RVA_LIKE_NRW_HU22_FULL_ORIGINAL_10K_53KREIS_GEO_STUDY'",
            "count(*)=53", "sum(c.n)=10000",
            "sum(c.unique_ids)=10000", "sum(c.unique_points)=10000",
            "sum(c.admitted)=10000", "sum(c.tiv)=4826029500::numeric",
            "c.n=e.n AND c.tiv=e.tiv",
            "u.unit_type='asset'", "u.building_count=1",
            "u.source_key=v.source_key",
            "ST_SRID(u.location)=4326", "ST_GeometryType(u.location)='ST_Point'",
            "BLOCKED_NRW_10K_ALL_KREISE_POLICY_TIV_AND_SOURCE_CONSERVATION",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.sql)

    def test_global_cross_kreis_identity_and_geometry_gates_not_weakened(self):
        # Local per-Kreis uniqueness alone cannot reject identical site IDs
        # or physical points reused in different Kreise: canonical main SQL
        # must also enforce version-global distinctness at 10k rows.
        section = self.sql.split("nrw_complete_10k AS (", 1)[1]
        section = section.split("audit AS (", 1)[0]
        for marker in (
            "count(*) FROM exposure.exposure_unit AS all_u",
            "count(DISTINCT all_u.external_unit_id)",
            "count(DISTINCT ST_AsBinary(all_u.location))",
            "all_u.portfolio_version_id=c.portfolio_version_id",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, section)
        self.assertEqual(
            section.count("all_u.portfolio_version_id=c.portfolio_version_id"),
            3,
        )

    def test_original_license_and_gfk_knowledge_stay_research_only(self):
        self.assertEqual(
            self.receipt["original_data_license"],
            "Datenlizenz Deutschland - Zero - Version 2.0",
        )
        self.assertFalse(self.receipt["2022_original_GFK_codebook_exact_vintage_reconciled"])
        self.assertFalse(self.receipt["real_RV_policy_geocodes_or_county_shares_observed"])
        self.assertFalse(self.receipt["science_CAT_model_input_admitted"])
        self.assertFalse(self.receipt["native_German_CAT_GUL_IL_RI_OEP_AEP_verified"])
        self.assertIn('"source_2022_GFK_codebook_verified":true', self.sql)
        self.assertIn("complete_source_admitted_10k_nrw_oed_versions", self.sql)
        self.assertIn("false::boolean AS annual_cat_ep_calibrated_by_these_sources", self.sql)

    def test_sql_remains_one_read_only_select(self):
        code = re.sub(r"--[^\n]*", "", self.sql).strip()
        self.assertTrue(code.upper().startswith("WITH\n"))
        for forbidden in (
            "INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE ",
            "GRANT ", "REVOKE ", "CREATE ",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, code.upper())


if __name__ == "__main__":
    unittest.main()
