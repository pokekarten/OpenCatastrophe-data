# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Purely offline integrity of exact trusted DWD provider-replay ledger SQL."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SQLDIR = ROOT / "research_runners" / "sql"

class DWDStrictOriginalReceiptTests(unittest.TestCase):
    def test_no_existing_smoke_ledger_weakened(self):
        ddl=(SQLDIR / "insurance_source_strict_original_probe_v1_schema.sql").read_text()
        self.assertIn("research.source_strict_original_probe_receipt_v1", ddl)
        self.assertIn("original_provider_body_persisted = false", ddl)
        self.assertIn("insurer_model_input_approved = false", ddl)
        self.assertIn("github_ref = 'refs/heads/main'", ddl)
        self.assertNotIn("ALTER TABLE research.source_api_smoke_receipt_v0", ddl)
        self.assertNotIn("DROP TABLE", ddl)

    def test_both_exact_original_github_replays_pinned_and_nonadmitted(self):
        seed=(SQLDIR / "insurance_source_strict_original_probe_v1_seed.sql").read_text()
        self.assertIn("cf22ff485271d4d681a9b87f766440c2986bd13e", seed)
        self.assertIn("43480623017",seed)
        self.assertIn("132075848823",seed)
        self.assertIn("a3e02cb676b855390c0a9b69f41352c7c3dff74c7c25e2578727e8397f9d9b12",seed)
        self.assertIn("5dc4b6f0dac14f0a442103b78c16f647556bd870898aabff6d9f62aa4534f542",seed)
        self.assertIn("dwd.catrare.w3-eta.v2026.01",seed)
        self.assertIn("dwd.catrare.t5-eta.v2026.01",seed)
        self.assertEqual(seed.count("ON CONFLICT"),1)
        self.assertNotIn("COPY",seed)
        self.assertNotIn("UPDATE research",seed)

if __name__=="__main__":
    unittest.main()
