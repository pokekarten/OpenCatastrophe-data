# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-only fail-closed guard for isolated Neon landscape metadata staging."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

SQL = (Path(__file__).resolve().parents[1] /
       "research_runners/sql/insurance_landscape_metadata_stage_readonly_verify_v0.sql")


class LandscapeMetadataStageReadOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SQL.read_text(encoding="utf-8")
        cls.sql = "\n".join(line for line in cls.original.splitlines()
                            if not line.lstrip().startswith("--"))

    def test_explicit_staging_branch_and_source_commit_pinned(self):
        self.assertIn("br-raspy-cell-ba5j7191", self.original)
        self.assertIn("d156e9e654652717179286caaa8cdf14636f9db2", self.sql)
        self.assertIn("classification='landscape_candidate'", self.sql)

    def test_single_readonly_statement_never_changes_neon(self):
        self.assertEqual(self.sql.count(";"), 1)
        self.assertTrue(self.sql.strip().startswith("WITH shards AS ("))
        for operation in ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP",
                          "TRUNCATE", "ALTER", "COPY", "MERGE", "GRANT"):
            with self.subTest(operation=operation):
                self.assertIsNone(re.search(r"\b" + operation + r"\b",
                                            self.sql, re.IGNORECASE))

    def test_no_source_or_model_approval_granted(self):
        for marker in ("unexpected_raw_admission", "nonstandard_rights",
                       "nonstandard_review", "malformed_provenance",
                       "FALSE AS automatic_production_sync_authorized",
                       "FALSE AS raw_provider_data_acquisition_authorized",
                       "FALSE AS cat_model_input_approved"):
            self.assertIn(marker, self.sql)

    def test_pinned_metadata_counters_and_git_identity_checked(self):
        for marker in ("staged_shards", "historical_shards",
                       "distinct_source_keys", "distinct_shard_paths",
                       "source_candidate_entry_count", "invalid_key",
                       "git_blob_sha !~", "git_commit_sha !~"):
            self.assertIn(marker, self.sql)


if __name__ == "__main__":
    unittest.main()
