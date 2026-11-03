# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Non-admission and source-identity regression for ISIMIP3a historical TC rain."""
from __future__ import annotations

from pathlib import Path
import unittest

from research_runners.isimip3a_er11_maxrain_filelist_preflight_v0 import (
    DATASET_ID,
    FILELIST_URL,
    SOURCE_ID,
)
from scripts.render_public_views import render_landscape_markdown
from scripts.source_landscape_contract import load_landscape_shard

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "landscape/sources-isimip3a-tc-er11-maxrain-20261103.json"


class ISIMIP3aSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = load_landscape_shard(CANONICAL)
        cls.entry = cls.payload["entries"][0]

    def test_unique_exact_runner_product_identity(self) -> None:
        self.assertEqual(len(self.payload["entries"]), 1)
        self.assertEqual(self.entry["candidate_id"], SOURCE_ID)
        self.assertIn("ER11", self.entry["name"])
        self.assertIn("maxrain", self.entry["note"])
        self.assertIn(DATASET_ID, self.entry["note"])
        self.assertIn(FILELIST_URL, self.entry["note"])

    def test_no_commercial_or_model_admission(self) -> None:
        self.assertEqual(self.entry["rights_review_status"], "not_reviewed")
        self.assertEqual(self.entry["scientific_review_status"], "not_reviewed")
        self.assertEqual(self.entry["admission_status"], "not_admitted")
        self.assertIn("licence", self.entry["note"])
        self.assertIn("forbid sale", self.entry["note"].lower())

    def test_no_incorrect_hazard_role(self) -> None:
        self.assertIn("extreme_precipitation", self.entry["categories"])
        self.assertNotIn("wind_speed", self.entry["categories"])
        self.assertIn("not wind speed", self.entry["note"])
        self.assertIn("not count as independent", self.entry["note"])
        self.assertIn("1950–2021", self.entry["temporal_scope"])

    def test_markdown_is_exact_deterministic_projection(self) -> None:
        expected = render_landscape_markdown(CANONICAL, self.payload)
        self.assertEqual(CANONICAL.with_suffix(".md").read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
