# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-only boundaries for NAIC insurer-group candidate review.

No legal parentage, regulator group ID, raw NAIC PDF copy, or CAT approval
may be inferred from textual insurer-directory group hints.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "research_runners/sql/worldwide_insurer_group_hint_review_readonly_v0.sql"
SOURCE = ROOT / "landscape/sources-global-insurer-registers-20261102.json"
NAIC = "us.naic.group-company-memberships.2025"


class InsurerGroupResearchBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = "\n".join(
            line for line in SQL_PATH.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("--")
        )
        cls.candidates = json.loads(SOURCE.read_text(encoding="utf-8"))["entries"]

    def test_group_hint_query_is_one_read_only_statement(self):
        self.assertEqual(self.sql.count(";"), 1)
        self.assertIn("FROM entity.organization_candidate", self.sql)
        self.assertIn("GROUP BY btrim(group_hint)", self.sql)
        self.assertIn("LIMIT 30;", self.sql)
        for verb in ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP",
                     "TRUNCATE", "CREATE", "GRANT", "COPY", "MERGE"):
            with self.subTest(operation=verb):
                self.assertIsNone(re.search(r"\b" + verb + r"\b", self.sql, re.I))

    def test_priority_is_triage_only_not_group_verification(self):
        self.assertIn("P1_MANUAL_IDENTITY_RECONCILIATION", self.sql)
        self.assertIn("P2_MULTI_CANDIDATE_REGULATOR_RESEARCH", self.sql)
        self.assertIn("false AS regulator_group_code_verified", self.sql)
        self.assertIn("false AS legal_parent_child_relationship_verified", self.sql)
        self.assertIn("false AS model_input_approved", self.sql)

    def test_naic_source_requires_separate_rights_admission(self):
        entries = [e for e in self.candidates if e["candidate_id"] == NAIC]
        self.assertEqual(len(entries), 1)
        item = entries[0]
        self.assertEqual(item["admission_status"], "not_admitted")
        self.assertEqual(item["rights_review_status"], "not_reviewed")
        self.assertIn("all_rights_reserved", item["access_class_hint"])
        self.assertIn("No copying bulk records", item["note"])
        self.assertIn("2025", item["temporal_scope"])
        self.assertIn("2026", item["temporal_scope"])


if __name__ == "__main__":
    unittest.main()
