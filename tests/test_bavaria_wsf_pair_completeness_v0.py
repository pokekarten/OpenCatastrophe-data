# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline guard for explicit two-window WSF/BVV source-completeness verdict."""
from pathlib import Path
import unittest

SQL = (Path(__file__).resolve().parents[1]
       / "research_runners/sql/bavaria_hu_by_wsf2019_original_pair_readiness_v0.sql"
       ).read_text(encoding="utf-8")


class WSFPairCompletenessContractTests(unittest.TestCase):
    def test_all_expected_windows_survive_failed_checks(self):
        self.assertIn("FROM expected e\n LEFT JOIN checked c", SQL)
        self.assertIn("ON c.bvv_sample_id=e.bvv_sample_id", SQL)
        self.assertIn("AND c.wsf_sample_id=e.wsf_sample_id", SQL)
        self.assertIn("(c.bvv_sample_id IS NOT NULL) AS window_receipt_pass", SQL)
        self.assertIn("count(*) FILTER (WHERE window_receipt_pass)", SQL)
        self.assertIn("coverage.expected_rows", SQL.replace("expected_window_count", "expected_rows"))
        self.assertIn("coverage.passed_window_count=2", SQL)
        self.assertIn("AS both_source_windows_verified", SQL)
        self.assertNotIn("FROM checked ORDER BY bvv_sample_id", SQL)

    def test_missing_receipts_never_emit_guessed_loss_or_admission(self):
        self.assertIn("c.stored_iou", SQL)
        self.assertIn("c.stored_wsf_coverage", SQL)
        self.assertIn("false AS historical_same_year_ground_truth_verified", SQL)
        self.assertIn("false AS insurer_tiv_available", SQL)
        self.assertIn("false AS cat_model_input_approved", SQL)
        self.assertIn("2019 WSF settlement class versus later-vintage BVV footprints", SQL)


if __name__ == "__main__":
    unittest.main()
