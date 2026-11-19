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
    def test_reviewed_interface_is_frozen_to_metadata_without_features(self) -> None:
        source = validate_path(CONTRACT)
        self.assertEqual(source["access_id"], SOURCE_ID)
        self.assertEqual(source["source_ids"], [SOURCE_ID])
        self.assertEqual(source["interface_type"], "wfs")
        self.assertEqual(source["service_root"], "https://gdi.berlin.de")
        self.assertEqual(source["request_contract"]["path_templates"], ["/services/wfs/alkis_gebaeude"])
        self.assertEqual(source["request_contract"]["allowed_operations"], ["get_capabilities"])
        self.assertEqual(source["access_scope"], ["metadata"])
        self.assertEqual(source["status"], "probe_ready")
        self.assertEqual(source["implementation_decision"], "build_later")
        self.assertEqual(source["probe_contract"]["mode"], "metadata_get")
        self.assertEqual(source["probe_contract"]["operation"], "get_capabilities")
        self.assertFalse(source["probe_contract"]["requires_credentials"])
        self.assertEqual(source["rights_and_policy"]["api_terms_status"], "separate_reviewed")
        self.assertEqual(source["rights_and_policy"]["commercial_automation_status"], "allowed")

    def test_rights_downgrade_prevents_live_metadata_access(self) -> None:
        source = validate_path(CONTRACT)
        revoked = copy.deepcopy(source)
        revoked["rights_and_policy"]["api_terms_status"] = "unknown"
        revoked["rights_and_policy"]["commercial_automation_status"] = "unknown"
        with self.assertRaises(SourceAccessError):
            validate_contract(revoked)

    def test_derived_inventory_preserves_discovery_nonadmission_and_one_contract(self) -> None:
        rows = [
            row for row in build_inventory()["entries"]
            if row["record_type"] == "landscape_candidate" and row["source_id"] == SOURCE_ID
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["contract_ids"], [SOURCE_ID])
        self.assertEqual(row["operational_readiness"], "bounded_probe_defined_not_executed")
        self.assertEqual(row["automation_decision"], "document_only")
        self.assertFalse(row["live_data_availability_proven"])


if __name__ == "__main__":
    unittest.main()
