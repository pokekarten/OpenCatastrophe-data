# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANDSCAPE = ROOT / "landscape/sources.json"
CANDIDATE_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
REQUIRED_ENTRY_KEYS = {
    "candidate_id",
    "name",
    "provider",
    "categories",
    "spatial_scope",
    "temporal_scope",
    "resolution_or_granularity",
    "potential_roles",
    "authoritative_url",
    "access_class_hint",
    "candidate_status",
    "rights_review_status",
    "scientific_review_status",
    "admission_status",
    "note",
}


class SourceLandscapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(LANDSCAPE.read_text(encoding="utf-8"))
        cls.entries = cls.payload["entries"]

    def test_registry_header_is_explicitly_non_admission(self) -> None:
        self.assertEqual(self.payload["schema_version"], "1.0.0")
        self.assertIn("Non-admission", self.payload["purpose"])
        self.assertRegex(self.payload["review_date"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertGreater(len(self.entries), 0)

    def test_candidate_ids_are_unique_and_machine_addressable(self) -> None:
        ids = [entry["candidate_id"] for entry in self.entries]
        self.assertEqual(len(ids), len(set(ids)))
        for candidate_id in ids:
            with self.subTest(candidate_id=candidate_id):
                self.assertRegex(candidate_id, CANDIDATE_ID_RE)

    def test_every_candidate_has_bounded_required_fields(self) -> None:
        for entry in self.entries:
            with self.subTest(candidate_id=entry.get("candidate_id")):
                self.assertEqual(set(entry), REQUIRED_ENTRY_KEYS)
                self.assertTrue(entry["name"].strip())
                self.assertTrue(entry["provider"].strip())
                self.assertTrue(entry["categories"])
                self.assertTrue(entry["potential_roles"])
                self.assertTrue(entry["authoritative_url"].startswith("https://"))

    def test_landscape_never_implies_admission_or_completed_review(self) -> None:
        for entry in self.entries:
            with self.subTest(candidate_id=entry["candidate_id"]):
                self.assertEqual(entry["candidate_status"], "evidence_checked")
                self.assertEqual(entry["rights_review_status"], "not_reviewed")
                self.assertEqual(entry["scientific_review_status"], "not_reviewed")
                self.assertEqual(entry["admission_status"], "not_admitted")


if __name__ == "__main__":
    unittest.main()
