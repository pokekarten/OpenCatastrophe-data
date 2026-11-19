# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed T0 boundary for EA Asset Management API, distinct from spatial AIMS."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/uk.ea.aims.asset-management-api.2026.json"
SOURCE_ID = "uk.ea.aims.asset-management-api.2026"


class EAAssetManagementT0Tests(unittest.TestCase):
    def test_existing_exact_source_documented_only(self):
        contract = validate_path(CONTRACT)
        self.assertEqual(contract["source_ids"], [SOURCE_ID])
        self.assertEqual(contract["status"], "documented_only")
        self.assertEqual(contract["interface_type"], "rest")
        self.assertEqual(contract["probe_contract"]["mode"], "none")
        self.assertEqual(contract["implementation_decision"], "document_only")
        self.assertEqual(contract["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertNotIn("SpatialFloodDefences", str(contract["request_contract"]["path_templates"]))

    def test_unreviewed_rights_cannot_be_claimed_as_approved(self):
        contract = validate_path(CONTRACT)
        changed = deepcopy(contract)
        changed["rights_and_policy"]["commercial_automation_status"] = "allowed"
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)
        changed = deepcopy(contract)
        changed["rights_and_policy"]["redistribution_status"] = "allowed"
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)

    def test_documented_only_must_not_activate_a_network_probe(self):
        changed = deepcopy(validate_path(CONTRACT))
        changed["probe_contract"].update(mode="metadata_get", operation="document_list_assets",
                                         expected_evidence=["transient original response SHA-256"])
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)

    def test_path_traversal_and_remote_host_not_allowed(self):
        changed = deepcopy(validate_path(CONTRACT))
        changed["request_contract"]["path_templates"] = ["/asset-management/../internal"]
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)
        changed = deepcopy(validate_path(CONTRACT))
        changed["service_root"] = "http://127.0.0.1"
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)


if __name__ == "__main__":
    unittest.main()
