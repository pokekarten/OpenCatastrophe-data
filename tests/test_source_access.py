# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.build_source_access_inventory as inventory_module
from scripts.build_source_access_inventory import (
    InventoryError,
    ROOT,
    _apply_contracts,
    build_inventory,
    classify_access,
    contract_files,
    landscape_files,
    manifest_files,
)
from scripts.validate_source_access import SourceAccessError, load_strict_json_bytes, validate_contract, validate_path


class SourceAccessInventoryTests(unittest.TestCase):
    def test_every_current_landscape_and_manifest_source_is_inventoried(self) -> None:
        inventory = build_inventory()
        expected_landscape = 0
        for path in landscape_files():
            payload = json.loads(path.read_text(encoding="utf-8"))
            expected_landscape += len(payload["entries"])
        expected_manifests = len(manifest_files())
        expected = expected_landscape + expected_manifests

        self.assertGreater(expected_landscape, 0)
        self.assertGreater(expected_manifests, 0)
        self.assertEqual(inventory["landscape_entry_count"], expected_landscape)
        self.assertEqual(inventory["manifest_entry_count"], expected_manifests)
        self.assertEqual(inventory["entry_count"], expected)
        self.assertEqual(len(inventory["entries"]), expected)
        keys = {
            (entry["record_type"], entry["source_id"], entry["source_registry_path"])
            for entry in inventory["entries"]
        }
        self.assertEqual(len(keys), expected)
        for entry in inventory["entries"]:
            self.assertIn(
                entry["rights_posture"],
                {"license_review_required", "known_restriction_requires_review", "source_rights_verified"},
            )
            self.assertNotEqual(entry["rights_posture"], "cleared")
            self.assertTrue(entry["next_action"].strip())
            self.assertIsInstance(entry["contract_ids"], list)
            if entry["record_type"] == "landscape_candidate":
                self.assertNotEqual(entry["automation_decision"], "build_adapter_now")

    def test_known_concrete_contracts_are_linked_to_admitted_sources(self) -> None:
        inventory = build_inventory()
        by_key = {(entry["record_type"], entry["source_id"]): entry for entry in inventory["entries"]}
        pegel = by_key[("admitted_manifest", "wsv.pegelonline.elbe-dresden-discharge.2020-2023")]
        dwd = by_key[("admitted_manifest", "dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03")]
        self.assertIn("wsv.pegelonline.rest-v2.dresden", pegel["contract_ids"])
        self.assertIn("dwd.cdc.extreme-wind.http-file", dwd["contract_ids"])
        self.assertEqual(pegel["api_status"], "concrete_contract_present")
        self.assertEqual(dwd["api_status"], "concrete_contract_present")

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

    def test_api_inference_is_token_based_not_substring_based(self) -> None:
        for hint in ("rapid_updates", "capital_model_download"):
            with self.subTest(hint=hint):
                result = classify_access(hint, ["hazard"], "source discovery")
                self.assertNotEqual(result["machine_access_class"], "api")

    def test_manifest_restriction_cannot_be_overwritten_by_contract(self) -> None:
        classification = {
            "machine_access_class": "api",
            "api_status": "documented_candidate",
            "authentication_posture": "anonymous_or_not_stated",
            "rights_posture": "known_restriction_requires_review",
            "license_or_terms_flags": ["commercial_use_restricted"],
            "automation_decision": "document_only",
            "next_action": "review",
        }
        contract = [{
            "access_id": "safe.example",
            "interface_type": "rest",
            "status": "probe_ready",
            "implementation_decision": "build_adapter_now",
        }]
        result = _apply_contracts(classification, contract, allow_contract_promotion=False)
        self.assertEqual(result["automation_decision"], "document_only")

    def test_multi_contract_source_has_order_independent_nonexecuting_aggregate(self) -> None:
        classification = {
            "machine_access_class": "api",
            "api_status": "documented_candidate",
            "authentication_posture": "anonymous_or_not_stated",
            "rights_posture": "source_rights_verified",
            "license_or_terms_flags": [],
            "automation_decision": "build_adapter_now",
            "next_action": "review",
        }
        build_now = {
            "access_id": "z.build",
            "interface_type": "rest",
            "status": "probe_ready",
            "implementation_decision": "build_adapter_now",
        }
        prohibited = {
            "access_id": "a.blocked",
            "interface_type": "web_portal",
            "status": "restricted_by_terms",
            "implementation_decision": "do_not_automate",
        }
        forward = _apply_contracts(classification, [build_now, prohibited], allow_contract_promotion=True)
        reverse = _apply_contracts(classification, [prohibited, build_now], allow_contract_promotion=True)
        for result in (forward, reverse):
            self.assertEqual(result["machine_access_class"], "multiple_reviewed_interfaces")
            self.assertEqual(result["api_status"], "multiple_concrete_contracts_present")
            self.assertEqual(result["automation_decision"], "do_not_automate")

    def test_build_inventory_rejects_invalid_contract_before_it_can_influence_output(self) -> None:
        pegel = json.loads((ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json").read_text(encoding="utf-8"))
        pegel["rights_and_policy"]["api_terms_status"] = "separate_unreviewed"
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            access_dir = Path(tmp)
            (access_dir / "invalid.json").write_text(json.dumps(pegel), encoding="utf-8")
            with mock.patch.object(inventory_module, "ACCESS_DIR", access_dir):
                with self.assertRaises(InventoryError):
                    build_inventory()

    def test_build_inventory_rejects_duplicate_access_ids(self) -> None:
        pegel = json.loads((ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            access_dir = Path(tmp)
            for name in ("one.json", "two.json"):
                (access_dir / name).write_text(json.dumps(pegel), encoding="utf-8")
            with mock.patch.object(inventory_module, "ACCESS_DIR", access_dir):
                with self.assertRaisesRegex(InventoryError, "duplicate source-access access_id"):
                    build_inventory()

    def test_build_inventory_rejects_dangling_source_reference(self) -> None:
        pegel = json.loads((ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json").read_text(encoding="utf-8"))
        pegel["source_ids"] = ["source.does.not.exist"]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            access_dir = Path(tmp)
            (access_dir / "dangling.json").write_text(json.dumps(pegel), encoding="utf-8")
            with mock.patch.object(inventory_module, "ACCESS_DIR", access_dir):
                with self.assertRaisesRegex(InventoryError, "unknown source_ids"):
                    build_inventory()


class SourceAccessContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pegel_path = ROOT / "access" / "wsv.pegelonline.rest-v2.dresden.json"
        self.pegel = json.loads(self.pegel_path.read_text(encoding="utf-8"))

    def test_all_checked_in_concrete_contracts_validate(self) -> None:
        paths = contract_files()
        self.assertGreaterEqual(len(paths), 2)
        for path in paths:
            validate_path(path)

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

    def test_secret_auth_mode_requires_symbolic_credential_reference(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["authentication"]["mode"] = "api_key"
        contract["authentication"]["credential_reference"] = None
        contract["probe_contract"]["requires_credentials"] = True
        with self.assertRaisesRegex(SourceAccessError, "symbolic credential reference"):
            validate_contract(contract)

    def test_arbitrary_url_cannot_be_smuggled_as_path_template(self) -> None:
        contract = copy.deepcopy(self.pegel)
        for path in (
            "https://attacker.example/data",
            "/safe\\..\\secret",
            "/safe/%2e%2e/secret",
            "/safe/%252e%252e/secret",
            "/safe/%3faccess_token=x",
        ):
            with self.subTest(path=path):
                mutated = copy.deepcopy(contract)
                mutated["request_contract"]["path_templates"] = [path]
                with self.assertRaises(SourceAccessError):
                    validate_contract(mutated)

    def test_percent_encoded_controls_and_malformed_escapes_fail_closed(self) -> None:
        for path in (
            "/safe/%0d%0aX-Test:1",
            "/safe/%00/secret",
            "/safe/%ZZ/secret",
        ):
            with self.subTest(path=path):
                contract = copy.deepcopy(self.pegel)
                contract["request_contract"]["path_templates"] = [path]
                with self.assertRaises(SourceAccessError):
                    validate_contract(contract)

    def test_local_private_and_secret_query_urls_fail_closed(self) -> None:
        host_cases = (
            "https://" + "local" + "host/data",
            "https://" + ".".join(("127", "0", "0", "1")) + "/data",
            "https://" + ".".join(("10", "0", "0", "1")) + "/data",
            "https://" + ".".join(("169", "254", "169", "254")) + "/latest/meta-data/",
            "https://example.invalid/data?access_token=not-a-real-token",
            "https://example.invalid/data?X-Amz-Signature=not-a-real-signature",
        )
        for url in host_cases:
            with self.subTest(url=url):
                contract = copy.deepcopy(self.pegel)
                contract["documentation_url"] = url
                with self.assertRaises(SourceAccessError):
                    validate_contract(contract)

    def test_unreviewed_rights_cannot_claim_allowed_reuse(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["rights_and_policy"]["dataset_rights_status"] = "not_reviewed"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_unreviewed_api_terms_cannot_remain_executable(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["rights_and_policy"]["api_terms_status"] = "separate_unreviewed"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_prohibited_automation_cannot_keep_probe_ready_build_now_state(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["rights_and_policy"]["commercial_automation_status"] = "prohibited"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_restricted_rights_require_nonexecuting_contract(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["rights_and_policy"]["dataset_rights_status"] = "restricted"
        contract["rights_and_policy"]["commercial_automation_status"] = "restricted"
        contract["rights_and_policy"]["redistribution_status"] = "unknown"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_anonymous_contract_cannot_reference_secret(self) -> None:
        contract = copy.deepcopy(self.pegel)
        contract["authentication"]["credential_reference"] = "PEGELONLINE_API_KEY"
        with self.assertRaises(SourceAccessError):
            validate_contract(contract)

    def test_ioc_contract_binds_current_v2_api_key_flow_without_enabling_automation(self) -> None:
        ioc = json.loads((ROOT / "access" / "ioc.vliz.slsmf.registered-api.documented.json").read_text(encoding="utf-8"))
        self.assertEqual(ioc["api_version"], "v2")
        self.assertEqual(ioc["authentication"]["mode"], "api_key")
        self.assertEqual(ioc["authentication"]["credential_reference"], "IOC_SLSMF_API_KEY")
        self.assertEqual(ioc["authentication"]["registration_url"], "https://ioc-sealevelmonitoring.org/api.php")
        self.assertEqual(ioc["status"], "restricted_by_terms")
        self.assertEqual(ioc["probe_contract"]["mode"], "none")
        self.assertEqual(ioc["implementation_decision"], "do_not_automate")
        validate_contract(ioc)

    def test_schema_is_closed_and_names_executable_authority(self) -> None:
        schema = json.loads((ROOT / "schemas" / "source-access-v1.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")
        self.assertIn("scripts/validate_source_access.py", schema["description"])
        self.assertTrue(schema["properties"]["request_contract"]["properties"]["path_templates"]["uniqueItems"])
        self.assertTrue(schema["allOf"])


if __name__ == "__main__":
    unittest.main()
