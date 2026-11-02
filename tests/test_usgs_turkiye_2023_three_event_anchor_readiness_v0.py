# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only three-physical-earthquake anchor readiness regression."""
import re
from pathlib import Path
import unittest

SQL_PATH = (Path(__file__).resolve().parents[1]
            / "research_runners/sql/usgs_turkiye_2023_three_event_anchor_readiness_v0.sql")
SQL = SQL_PATH.read_text(encoding="utf-8")
QUERY = "\n".join(line for line in SQL.splitlines()
                  if not line.lstrip().startswith("--"))


class TurkiyeSequenceResearchTests(unittest.TestCase):
    def test_query_is_read_only_exactly_one_statement(self):
        self.assertEqual(QUERY.count(";"), 1)
        for operation in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
                          "CREATE", "TRUNCATE", "MERGE", "COPY", "GRANT"):
            with self.subTest(operation=operation):
                self.assertNotRegex(QUERY, r"\b" + operation + r"\b")

    def test_three_distinct_usgs_physical_event_anchors(self):
        for event_id in ("us6000jllz", "us6000jlm1", "us6000jlqa"):
            self.assertEqual(QUERY.count("'" + event_id + "'"), 1)
        self.assertIn("VALUES", QUERY)
        self.assertIn("count(DISTINCT expected_id)", QUERY)
        self.assertIn("count(DISTINCT usgs_event_id)", QUERY)
        self.assertIn("MISSING_OR_DUPLICATE_ANCHOR_ROWS", QUERY)

    def test_uses_exact_cat_only_research_rows(self):
        self.assertIn("FROM expected_anchors e", QUERY)
        self.assertIn("LEFT JOIN research.usgs_comcat_origin_observation_v0 s", QUERY)
        self.assertIn("s.usgs_event_id = e.usgs_event_id", QUERY)
        self.assertIn("DATE '2023-02-06'", QUERY)
        self.assertIn("origin_time_utc IS NULL", QUERY)

    def test_absent_original_bytes_fail_closed(self):
        for marker in ("raw_response_sha256 IS NULL", "raw_response_sha256 !~",
                       "raw_response_sha256 ~", "sha_shaped_rows <> selected_expected_anchors",
                       "ORIGINAL_USGS_RESPONSE_BYTES_NOT_PINNED"):
            with self.subTest(marker=marker):
                self.assertIn(marker, QUERY)
        self.assertLess(QUERY.index("WHEN unexpected_model_admissions > 0"),
                        QUERY.index("WHEN missing_original_response_sha > 0"))

    def test_access_contract_is_independent_rights_gate(self):
        for marker in ("registry.source_record", "'access_contract'",
                       "'usgs.anss.comcat'",
                       "'access/usgs.anss.comcat.json'",
                       "source_raw_admission_flags",
                       "RAW_ACCESS_NOT_ADMITTED"):
            with self.subTest(marker=marker):
                self.assertIn(marker, QUERY)

    def test_contractual_occurrence_and_loss_never_auto_admitted(self):
        for forbidden_promotion in (
            "physical_event_family_crosswalk_verified",
            "single_contractual_occurrence_verified",
            "historic_product_vintages_verified",
            "hazard_ground_motion_verified",
            "insurance_portfolio_loss_verified",
            "annual_cat_capital_metric_justified",
        ):
            with self.subTest(flag=forbidden_promotion):
                self.assertIn("FALSE AS " + forbidden_promotion, QUERY)

    def test_only_three_anchors_not_full_historical_catalogue(self):
        self.assertIn("NOT the full aftershock", SQL)
        self.assertNotIn("SUM(magnitude)", QUERY)
        self.assertNotIn("physical_event_id =", QUERY)


if __name__ == "__main__":
    unittest.main()
