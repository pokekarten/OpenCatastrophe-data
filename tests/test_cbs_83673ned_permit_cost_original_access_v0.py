# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed offline CBS 83673NED source rights and unit-contract tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "access" / "nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned.json"


class CBS83673PermitCostContractTests(unittest.TestCase):
    def setUp(self):
        self.c = validate_path(PATH)

    def test_documented_only_transport_without_fake_provider_execution(self):
        self.assertEqual(self.c["status"], "documented_only")
        self.assertEqual(self.c["interface_type"], "rest")
        self.assertEqual(self.c["probe_contract"]["mode"], "none")
        self.assertIsNone(self.c["probe_contract"]["operation"])
        self.assertEqual(self.c["probe_contract"]["expected_evidence"], [])
        self.assertEqual(self.c["implementation_decision"], "document_only")
        self.assertEqual(self.c["service_root"], "https://opendata.cbs.nl")
        self.assertEqual(self.c["authentication"]["mode"], "none")

    def test_exact_research_source_id_and_o_data_scope(self):
        self.assertEqual(
            self.c["source_ids"],
            ["nl.cbs.new-housing-permit-eur-per-m3-region-tenure.83673ned"],
        )
        self.assertEqual(self.c["access_id"], self.c["source_ids"][0])
        paths = self.c["request_contract"]["path_templates"]
        self.assertEqual(len(paths), 6)
        self.assertTrue(all(p.startswith("/ODataApi/OData/83673NED/") for p in paths))
        self.assertIn("/ODataApi/OData/83673NED/RegioS", paths)
        self.assertIn("/ODataApi/OData/83673NED/Eigendom", paths)
        self.assertIn("/ODataApi/OData/83673NED/TypedDataSet", paths)
        rules = self.c["request_contract"]["parameter_rules"]
        self.assertIn("2026VJ06", rules)
        self.assertIn("A028868", rules)
        self.assertIn("NL01%20%20", rules)
        self.assertIn("$top=10", rules)
        self.assertIn("No arbitrary URL", rules)

    def test_correct_native_units_and_vintage_are_mandatory(self):
        sci = self.c["response_contract"]["scientific_semantics"]
        self.assertIn("GemiddeldeBouwkostenPerM_2 means EUR per cubic metre", sci)
        self.assertIn("GemiddeldeBouwkostenPerM_3 means EUR per square metre", sci)
        self.assertIn("50000 EUR", sci)
        self.assertIn("12-month", sci)
        self.assertIn("provisional", sci)
        self.assertIn("488 EUR/m³", sci)
        self.assertIn("1473 EUR/m²", sci)
        self.assertIn("438 EUR/m³", sci)
        self.assertIn("1297 EUR/m²", sci)
        self.assertIn("not construction loss", sci)

    def test_product_use_and_api_automation_separated_from_model_admission(self):
        rights = self.c["rights_and_policy"]
        self.assertEqual(rights["dataset_rights_status"], "verified")
        self.assertEqual(rights["api_terms_status"], "separate_reviewed")
        self.assertEqual(rights["commercial_automation_status"], "allowed")
        self.assertIn("CC BY 4.0", rights["notes"])
        self.assertIn("not model-input admission", rights["notes"].lower())
        self.assertEqual(self.c["operational_constraints"]["retry_policy"], "none")

    def test_incorrect_early_activation_before_a_runner_is_blocked(self):
        c = deepcopy(self.c)
        c["status"] = "probe_ready"
        with self.assertRaises(SourceAccessError):
            validate_contract(c)

    def test_unreviewed_service_rights_cannot_create_live_probe(self):
        c = deepcopy(self.c)
        c["status"] = "probe_ready"
        c["rights_and_policy"]["commercial_automation_status"] = "unknown"
        c["probe_contract"] = {
            "mode": "metadata_get",
            "operation": "arbitrary_download",
            "requires_credentials": False,
            "expected_evidence": ["not-a-provider-receipt"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(c)


if __name__ == "__main__":
    unittest.main()
