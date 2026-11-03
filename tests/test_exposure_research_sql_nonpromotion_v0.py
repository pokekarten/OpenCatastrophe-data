# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only Florida/Texas view and validation SQL boundary tests.

The result of a reproducible staged-data QA view must never imply insurer
ZIP-level TIV, legal entity identity, or CAT model approval.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "research_runners" / "sql"
FL = SQL / "fl_oir_company_exposure_readiness_v0.sql"
TX = SQL / "tx_market_policy_stock_quality_v0.sql"
INVARIANTS = SQL / "exposure_research_invariants_v0.sql"


def stripped_sql(path: Path) -> str:
    return "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    ).strip()


class ExposuresResearchNoPromotionTests(unittest.TestCase):
    def test_fl_view_is_only_validation_branch_research(self):
        source = FL.read_text(encoding="utf-8")
        sql = stripped_sql(FL)
        self.assertIn("validation-schema-20261031", source)
        self.assertTrue(sql.startswith("CREATE OR REPLACE VIEW research.fl_oir_company_exposure_readiness_v0 AS"))
        self.assertIn("false::boolean AS model_input_approved", sql)
        self.assertIn("'statewide_company_by_reported_policy_type'", sql)
        for gate in (
            "BLOCKED_REPORTING_UNIVERSE_UNKNOWN",
            "BLOCKED_RIGHTS_REVIEW",
            "BLOCKED_NO_CARRIER_ZIP_EXPOSURE",
            "BLOCKED_NO_BUILDING_TIV",
            "BLOCKED_COVERAGE_AND_MODEL_VALIDATION",
        ):
            self.assertIn(gate, sql)

    def test_texas_market_not_insurer_location_valuations(self):
        source = TX.read_text(encoding="utf-8")
        sql = stripped_sql(TX)
        self.assertIn("validation-schema-20261031", source)
        self.assertTrue(sql.startswith("CREATE OR REPLACE VIEW research.tx_market_policy_stock_quality_v0 AS"))
        self.assertIn("false::boolean AS model_input_approved", sql)
        self.assertIn("'market_zip5_by_policy_type_not_company_specific'", sql)
        self.assertIn("BLOCKED_ORIGINAL_SOURCE_PROVENANCE", sql)
        self.assertIn("BLOCKED_NO_CARRIER_ZIP_IDENTITY", sql)
        self.assertIn("BLOCKED_NO_INSURED_TIV", sql)

    def test_both_views_deny_unreviewed_write_operations(self):
        for path in (FL, TX):
            with self.subTest(path=path.name):
                sql = stripped_sql(path)
                self.assertEqual(sql.count(";"), 1)
                for operation in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
                                  "CREATE TABLE", "TRUNCATE", "COPY", "GRANT"):
                    self.assertIsNone(re.search(r"\b" + operation + r"\b", sql, re.I))

    def test_original_source_invariants_are_one_read_only_query(self):
        sql = stripped_sql(INVARIANTS)
        self.assertTrue(sql.startswith("WITH checks AS ("))
        self.assertTrue(sql.endswith("ORDER BY check_id;"))
        self.assertEqual(sql.count(";"), 1)
        self.assertEqual(sql.count("UNION ALL"), 10)
        self.assertIn("fl_no_model_promotion", sql)
        self.assertIn("fl_never_confuse_reporting_universe", sql)
        self.assertIn("tx_no_carrier_or_tiv_inference", sql)
        for operation in ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP",
                          "ALTER", "TRUNCATE", "MERGE", "COPY"):
            self.assertIsNone(re.search(r"\b" + operation + r"\b", sql, re.I))


if __name__ == "__main__":
    unittest.main()
