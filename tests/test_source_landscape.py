# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LANDSCAPE_DIR = ROOT / "landscape"
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


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_strict_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: landscape shard must be a JSON object")
    return payload


class SourceLandscapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = tuple(sorted(LANDSCAPE_DIR.glob("sources*.json")))
        cls.payloads = tuple((path, _load(path)) for path in cls.paths)
        cls.entries = tuple(
            (path, entry)
            for path, payload in cls.payloads
            for entry in payload["entries"]
        )

    def test_registry_shards_are_explicitly_non_admission(self) -> None:
        self.assertGreater(len(self.payloads), 0)
        for path, payload in self.payloads:
            with self.subTest(path=path.name):
                self.assertEqual(payload["schema_version"], "1.0.0")
                self.assertIn("Non-admission", payload["purpose"])
                self.assertRegex(payload["review_date"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertIsInstance(payload["entries"], list)
                self.assertGreater(len(payload["entries"]), 0)

    def test_candidate_ids_are_globally_unique_and_machine_addressable(self) -> None:
        ids = [entry["candidate_id"] for _, entry in self.entries]
        self.assertEqual(len(ids), len(set(ids)))
        for candidate_id in ids:
            with self.subTest(candidate_id=candidate_id):
                self.assertRegex(candidate_id, CANDIDATE_ID_RE)

    def test_every_candidate_has_bounded_required_fields(self) -> None:
        for path, entry in self.entries:
            with self.subTest(path=path.name, candidate_id=entry.get("candidate_id")):
                self.assertEqual(set(entry), REQUIRED_ENTRY_KEYS)
                self.assertTrue(entry["name"].strip())
                self.assertTrue(entry["provider"].strip())
                self.assertTrue(entry["categories"])
                self.assertTrue(entry["potential_roles"])
                self.assertTrue(entry["authoritative_url"].startswith("https://"))

    def test_landscape_never_implies_admission_or_completed_review(self) -> None:
        for path, entry in self.entries:
            with self.subTest(path=path.name, candidate_id=entry["candidate_id"]):
                self.assertEqual(entry["candidate_status"], "evidence_checked")
                self.assertEqual(entry["rights_review_status"], "not_reviewed")
                self.assertEqual(entry["scientific_review_status"], "not_reviewed")
                self.assertEqual(entry["admission_status"], "not_admitted")


if __name__ == "__main__":
    unittest.main()
