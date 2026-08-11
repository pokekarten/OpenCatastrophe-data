# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.build_source_access_inventory as inventory


class SourceAccessInventoryFailClosedTests(unittest.TestCase):
    def build_synthetic_inventory(self) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            landscape_dir = root / "landscape"
            manifest_dir = root / "manifests"
            access_dir = root / "access"
            landscape_dir.mkdir()
            manifest_dir.mkdir()
            access_dir.mkdir()

            landscape = {
                "review_date": "2026-08-11",
                "entries": [
                    {
                        "candidate_id": "essl.eswd.synthetic",
                        "provider": "ESSL",
                        "authoritative_url": "https://example.org/eswd",
                        "access_class_hint": "public api subset by agreement",
                        "categories": ["api"],
                        "note": "Commercial use not allowed; access and reuse require agreement.",
                        "rights_review_status": "not_reviewed",
                    }
                ],
            }
            (landscape_dir / "sources-test.json").write_text(
                json.dumps(landscape), encoding="utf-8"
            )

            manifest = {
                "dataset_id": "verified.api.synthetic",
                "provider": "Synthetic Provider",
                "canonical_source": "https://example.org/data",
                "access_class": "public api",
                "modelling_layer": "hazard",
                "intended_use": "Synthetic test only.",
                "licensing": {
                    "status": "verified",
                    "commercial_use_status": "allowed",
                    "notes": "Dataset rights only; API terms are not represented here.",
                },
                "redistribution": {"status": "allowed"},
                "review": {"notes": "No concrete source-access contract exists."},
            }
            (manifest_dir / "verified.api.synthetic.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            with (
                patch.object(inventory, "ROOT", root),
                patch.object(inventory, "LANDSCAPE_DIR", landscape_dir),
                patch.object(inventory, "MANIFEST_DIR", manifest_dir),
                patch.object(inventory, "ACCESS_DIR", access_dir),
                patch.object(inventory, "DEFAULT_OUTPUT", access_dir / "source-access-inventory.json"),
            ):
                return inventory.build_inventory()

    def test_landscape_known_restriction_is_preserved(self) -> None:
        payload = self.build_synthetic_inventory()
        entry = next(
            item for item in payload["entries"]
            if item["source_id"] == "essl.eswd.synthetic"
        )
        self.assertEqual(entry["rights_posture"], "known_restriction_requires_review")
        self.assertEqual(entry["automation_decision"], "document_only")
        self.assertTrue(entry["license_or_terms_flags"])

    def test_verified_manifest_without_access_contract_cannot_build_now(self) -> None:
        payload = self.build_synthetic_inventory()
        entry = next(
            item for item in payload["entries"]
            if item["source_id"] == "verified.api.synthetic"
        )
        self.assertEqual(entry["rights_posture"], "source_rights_verified")
        self.assertEqual(entry["machine_access_class"], "api")
        self.assertEqual(entry["contract_ids"], [])
        self.assertEqual(entry["automation_decision"], "build_later")
        self.assertIn("source-access contract", entry["next_action"])


if __name__ == "__main__":
    unittest.main()
