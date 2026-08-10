# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.build_source_access_inventory import ROOT, build_inventory, classify_access, source_files
from scripts.validate_source_access import SourceAccessError, load_strict_json_bytes, validate_contract, validate_path


class SourceAccessInventoryTests(unittest.TestCase):
    def test_every_current_landscape_source_is_inventoried(self) -> None:
        inventory = build_inventory()
        expected = 0
        for path in source_files():
            payload = json.loads(path.read_text(encoding="utf-8"))
            expected += len(payload["entries"])
        self.assertGreater(expected, 0)
        self.assertEqual(inventory["entry_count"], expected)
        self.assertEqual(len(inventory["entries"]), expected)
        self.assertEqual(
            len({entry["source_id"] for entry in inventory["entries"]}),
            expected,
        )
        for entry in inventory["entries"]:
            self.assertIn(
                entry["rights_posture"],
                {"license_review_required", "known_restriction_requires_review"},
            )
            self.assertNotEqual(entry["rights_posture"], "cleared")
            self.assertTrue(entry["next_action"].strip())

    def test_api_download_and_restricted_hints_classify_differently(self) -> None:
        public_api = classify_access("public_api_and_download", ["api"], "public service")
        self.assertEqual(public_api["machine_access_class"], "api")
        self.assertEqual(public_api["automation_decision"], "build_adapter_now")

        bulk = classify_access("public_download", ["climate"], "stable files")
        self.assertEqual(bulk["machine_access_class"], "bulk_or_file")
        self.assertEqual(bulk["automation_decision"], "build_later")

        restricted = classify_access(
            "public_subset_noncommercial_with_broader_access_by_agreement",
            ["event_catalogue"],
            "Commercial use not allowed; broader access by agreement.",
        )
        self.assertEqual(restricted["rights_posture"], "known_restriction_requires_review")
        self.assertEqual(restricted["automation_decision"], "document_only")
        self.assertIn("commercial_use_restriction", restricted["license_or_terms_flags"])


class SourceAccessContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pegel_path = ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json"
        self.dwd_path = ROOT / "access" / "dwd.cdc.extreme-wind.http-file.json"
        self.pegel = json.loads(self.pegel_path.read_text(encoding="utf-8"))

    def test_concrete_contracts_validate(self) -> None:
        validate_path(self.pegel_path)
        validate_path(self.dwd_path)

    def test_duplicate_json_keys_fail_closed(self) -> None:
        with self.assertRaises(SourceAccessError):
            load_strict_json_bytes(b'{"schema_version":"1.0.0","schema_version":"1.0.0"}')

    def test_real_or_unstructured_credential_reference_is_rejected(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["authentication"]["mode"] = "api_key"
        contract["authentication"]["credential_reference"] = "actual-secret-value"
        contract["probe_contract"]["requires_credentials"] = True
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_arbitrary_url_cannot_be_smuggled_as_path_template(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["request_contract"]["path_templates"] = ["https://attacker.example/data"]
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_unreviewed_rights_cannot_claim_allowed_reuse(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["rights_and_policy"]["dataset_rights_status"] = "not_reviewed"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_anonymous_contract_cannot_reference_secret(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["authentication"]["credential_reference"] = "PEGELONLINE_API_KEY"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_schema_is_closed(self) -> None:
        schema = json.loads((ROOT / "schemas" / "source-access-v1.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
