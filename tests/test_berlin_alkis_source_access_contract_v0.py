# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed static Berlin ALKIS building WFS source contract tests."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.build_source_access_inventory import build_inventory
from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "de.berlin.alkis-gebaeude.wfs.json"
SOURCE_ID = "de.berlin.alkis-gebaeude.wfs"


class BerlinAlkisSourceContractTests(unittest.TestCase):
    def test_reviewed_interface_and_source_identity_are_frozen_but_nonexecuting(self) -> None:
        source = validate_path(CONTRACT)
        self.assertEqual(source["access_id"], SOURCE_ID)
        self.assertEqual(source["source_ids"], [SOURCE_ID])
        self.assertEqual(source["interface_type"], "wfs")
        self.assertEqual(source["service_root"], "https://gdi.berlin.de")
        self.assertEqual(source["request_contract"]["path_templates"], ["/services/wfs/alkis_gebaeude"])
        self.assertEqual(source["status"], "documented_only")
        self.assertEqual(source["implementation_decision"], "document_only")
        self.assertEqual(source["probe_contract"]["mode"], "none")
        self.assertEqual(source["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(source["rights_and_policy"]["commercial_automation_status"], "unknown")

    def test_adapter_promotion_and_probe_enablement_fail_without_terms_review(self) -> None:
        source = validate_path(CONTRACT)
        enabled = copy.deepcopy(source)
        enabled["implementation_decision"] = "build_adapter_now"
        with self.assertRaises(SourceAccessError):
            validate_contract(enabled)
        enabled = copy.deepcopy(source)
        enabled["status"] = "probe_ready"
        enabled["probe_contract"] = {
            "mode": "metadata_get",
            "operation": "get_capabilities",
            "requires_credentials": False,
            "expected_evidence": ["response digest"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(enabled)

    def test_derived_inventory_preserves_discovery_nonadmission_and_one_contract(self) -> None:
        rows = [
            row for row in build_inventory()["entries"]
            if row["record_type"] == "landscape_candidate" and row["source_id"] == SOURCE_ID
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["contract_ids"], [SOURCE_ID])
        self.assertEqual(row["operational_readiness"], "contract_documentation_only")
        self.assertEqual(row["automation_decision"], "document_only")


if __name__ == "__main__":
    unittest.main()
