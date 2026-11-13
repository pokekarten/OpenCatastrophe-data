# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed public PDOK metadata-only use-case rights decision."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RIGHTS = ROOT / "research_runners/sql/insurance_pdok_brp_metadata_rights_v0.sql"


class PDOKBRPRightsTests(unittest.TestCase):
    def test_exact_collection_scope_only(self):
        raw=RIGHTS.read_text(encoding="utf-8")
        self.assertIn("nl.rvo.brp-gewaspercelen.2025",raw)
        self.assertIn("current-live brpgewas Collection metadata GET",raw)
        self.assertIn("NOT immutable 2025 final parcel archive",raw)
        self.assertIn("ON CONFLICT (source_id, product_scope, use_case) DO NOTHING",raw)
        self.assertIn("DATE '2026-11-13'",raw)
        self.assertNotIn("ON CONFLICT DO UPDATE",raw)
        self.assertNotIn("UPDATE research",raw)
        self.assertNotIn("DELETE FROM",raw)

    def test_all_seven_decisions_keep_original_assets_unapproved(self):
        raw=RIGHTS.read_text(encoding="utf-8")
        for case in ("internal_research","commercial_cat_modelling","automated_api_access",
                     "internal_neon_metadata","internal_neon_source_sample",
                     "external_raw_redistribution","published_derived_results"):
            with self.subTest(case=case):
                self.assertIn("'"+case+"'",raw)
        self.assertEqual(raw.count("false, false)"),7)
        self.assertIn("'unknown'",raw)
        self.assertIn("'conditional'",raw)
        self.assertIn("public-domain *mark* is not a licence grant",raw)


if __name__=="__main__":
    unittest.main()
