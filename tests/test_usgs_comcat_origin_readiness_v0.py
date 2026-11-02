# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Regression contract for the read-only ComCat origin research preflight.

Live PostgreSQL proof is documented separately; no provider bytes or DB
credentials are required by this local source-structure regression.
"""
import re
import unittest
from pathlib import Path

SQL = (Path(__file__).resolve().parents[1] /
       "research_runners/sql/usgs_comcat_origin_readiness_v0.sql")


class USGSComCatOriginReadinessTests(unittest.TestCase):
    def test_read_only_single_statement_and_research_source(self):
        text = SQL.read_text(encoding="utf-8")
        executable = "\n".join(
            line for line in text.splitlines()
            if not line.lstrip().startswith("--")
        )
        self.assertEqual(executable.count(";"), 1)
        for forbidden in ("INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE",
                          "ALTER", "CREATE", "MERGE", "COPY", "GRANT"):
            with self.subTest(forbidden=forbidden):
                self.assertNotRegex(executable, r"\\b" + forbidden + r"\\b")
        self.assertIn("FROM research.usgs_comcat_origin_observation_v0", executable)

    def test_hash_identity_is_not_a_provider_url(self):
        sql = SQL.read_text(encoding="utf-8")
        self.assertIn("raw_response_sha256 IS NULL", sql)
        self.assertIn("raw_response_sha256 !~ '^[0-9a-f]{64}$'", sql)
        self.assertIn("raw_response_sha256 ~ '^[0-9a-f]{64}$'", sql)
        self.assertIn("original_response_sha_rows <> observations", sql)
        self.assertIn("count(DISTINCT usgs_event_id)", sql)
        self.assertIn("unique_event_ids <> observations", sql)

    def test_unexpected_admission_has_precedence_over_research_missing_hash(self):
        sql = SQL.read_text(encoding="utf-8")
        self.assertLess(
            sql.index("WHEN claimed_model_admissions > 0"),
            sql.index("WHEN missing_original_response_sha > 0"),
        )
        for status in ("MISSING_RESEARCH_ROWS",
                       "UNEXPECTED_ADMISSION_REQUIRES_REVIEW",
                       "RESEARCH_RECORD_QUALITY_BLOCKED",
                       "RESEARCH_ORIGINAL_BYTES_NOT_PINNED",
                       "RESEARCH_STRUCTURALLY_CHECKED_NOT_ADMITTED"):
            self.assertIn("'" + status + "'", sql)

    def test_no_scientific_or_model_admission_on_green_structural_check(self):
        sql = SQL.read_text(encoding="utf-8")
        for flag in ("complete_stochastic_event_catalogue_verified",
                     "hazard_intensity_footprints_verified",
                     "scientific_calibration_verified",
                     "insurer_loss_or_model_input_admitted"):
            self.assertIn("FALSE AS " + flag, sql)

    def test_quality_fields_present(self):
        sql = SQL.read_text(encoding="utf-8")
        for name in ("missing_event_ids", "missing_origin_times",
                     "suspect_magnitudes", "invalid_coordinates",
                     "depth_review_candidates", "missing_source_urls",
                     "unexpected_research_source_labels",
                     "claimed_model_admissions"):
            self.assertIn(name, sql)


if __name__ == "__main__":
    unittest.main()
