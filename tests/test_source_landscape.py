# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.source_landscape_contract import (
    CANDIDATE_ID_RE,
    ENTRY_KEYS,
    load_landscape,
    load_landscape_shards,
)


class SourceLandscapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.shards = load_landscape_shards()
        cls.entries = load_landscape()

    def test_current_registry_is_valid_and_non_empty(self) -> None:
        self.assertGreater(len(self.shards), 0)
        self.assertGreater(len(self.entries), 0)
        self.assertEqual(
            len(self.entries),
            sum(len(payload["entries"]) for _path, payload in self.shards),
        )

    def test_candidate_ids_are_globally_unique_machine_addresses(self) -> None:
        ids = [entry["candidate_id"] for entry in self.entries]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))
        for candidate_id in ids:
            with self.subTest(candidate_id=candidate_id):
                self.assertRegex(candidate_id, CANDIDATE_ID_RE)

    def test_current_entries_expose_the_versioned_public_surface(self) -> None:
        for entry in self.entries:
            with self.subTest(candidate_id=entry["candidate_id"]):
                self.assertEqual(set(entry), ENTRY_KEYS)
                self.assertTrue(entry["categories"])
                self.assertTrue(entry["potential_roles"])

    def test_landscape_never_implies_admission_or_completed_review(self) -> None:
        for entry in self.entries:
            with self.subTest(candidate_id=entry["candidate_id"]):
                self.assertEqual(entry["candidate_status"], "evidence_checked")
                self.assertEqual(entry["rights_review_status"], "not_reviewed")
                self.assertEqual(entry["scientific_review_status"], "not_reviewed")
                self.assertEqual(entry["admission_status"], "not_admitted")


if __name__ == "__main__":
    unittest.main()
