# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed parity of the two independently used 10k SQL exposure gates.

Both SQL entry points MUST source identical exact synthetic OED/version,
geometry, taxonomy, and deterministic CAT event/loss CTEs; only the final
read-only result projection may differ. This test does not validate real CAT.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "research_runners/sql/neon_synthetic_gul_10k_v0.sql"
RECEIPT = ROOT / "research_runners/sql/neon_synthetic_gul_10k_row_receipts_v0.sql"


def common_sql_ctes(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # Each file has only one unindented final SELECT after the WITH CTEs.
    # Keep this deliberately strict: if that assumption changes, fail rather
    # than comparing truncated text or accidentally hiding an extra statement.
    marker = "\nSELECT"
    if text.count(marker) != 1 or not text.endswith(";\n"):
        raise ValueError(f"SQL query layout not uniquely canonical: {path.name}")
    prefix, final = text.rsplit(marker, 1)
    if not prefix.startswith("-- SPDX-FileCopyrightText:"):
        raise ValueError("missing SPDX notice")
    if "asserted_fixture=1" not in prefix or "years AS (" not in prefix:
        raise ValueError("missing mandatory guarded 10k CTE")
    if not final.strip().endswith(";"):
        raise ValueError("final SQL projection missing semicolon")
    return prefix


class Neon10kSqlGateParity(unittest.TestCase):
    def test_exact_complete_cte_identity(self):
        self.assertEqual(common_sql_ctes(SUMMARY), common_sql_ctes(RECEIPT))

    def test_geographic_and_value_basis_are_common(self):
        cte = common_sql_ctes(SUMMARY)
        for requirement in (
            "p.country_code='DE'",
            "p.peril_scope=ARRAY['windstorm','flood']::text[]",
            "pv.as_of_date=DATE '2026-11-01'",
            "pv.assumption_metadata ->> 'real_buildings'='false'",
            "e.insured_value_currency='EUR'",
            "e.value_basis='invented_smoke_test_value_not_insured_observation'",
            "a.occupancy_code IS DISTINCT FROM e.expected_occupancy",
            "a.construction_code IS DISTINCT FROM e.expected_construction",
            "ST_AsEWKB(a.location) IS DISTINCT FROM ST_AsEWKB(e.expected_location)",
            "all_unit_count=12 AND n=12 AND unique_ids=12",
            "mismatches=0",
            "1 / (CASE WHEN",
        ):
            with self.subTest(required=requirement):
                self.assertIn(requirement, cte)

    def test_final_projection_is_deliberately_different(self):
        summary = SUMMARY.read_text(encoding="utf-8")
        receipts = RECEIPT.read_text(encoding="utf-8")
        self.assertIn("AS aep995_loss_eur", summary)
        self.assertIn("AS event_asset_exact_md5", receipts)
        self.assertNotEqual(summary, receipts)

    def test_mismatched_contract_gate_is_rejected(self):
        # This challenges the equality rule independently of PostgreSQL.
        summary = common_sql_ctes(SUMMARY)
        changed = summary.replace(
            "a.occupancy_code IS DISTINCT FROM e.expected_occupancy",
            "a.occupancy_code IS NOT DISTINCT FROM e.expected_occupancy",
        )
        self.assertNotEqual(changed, common_sql_ctes(RECEIPT))


if __name__ == "__main__":
    unittest.main()
