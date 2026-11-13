# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline HU-BY exact product rights and research-vs-model firewall."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "access" / "de.bayern.hausumringe.json"


class BVVHubyRightsContractTests(unittest.TestCase):
    def setUp(self):
        self.c = validate_path(PATH)

    def test_exact_bavarian_state_product_not_national_hu_de(self):
        self.assertEqual(self.c["access_id"], "de.bayern.hausumringe")
        self.assertEqual(self.c["source_ids"], ["de.bayern.hausumringe"])
        self.assertEqual(self.c["interface_type"], "http_file")
        self.assertEqual(self.c["service_root"], "https://geodaten.bayern.de")
        self.assertEqual(
            self.c["request_contract"]["path_templates"],
            ["/odd/m/3/daten/hausumringe/bezirk/data/091_Oberbayern_Hausumringe.zip"],
        )
        self.assertNotIn("HU-DE", self.c["request_contract"]["path_templates"][0])

    def test_verified_data_license_but_separately_unreviewed_service_terms(self):
        rights = self.c["rights_and_policy"]
        self.assertEqual(rights["dataset_rights_status"], "verified")
        self.assertEqual(rights["api_terms_status"], "separate_unreviewed")
        self.assertEqual(rights["commercial_automation_status"], "unknown")
        self.assertEqual(rights["redistribution_status"], "allowed")
        self.assertIn("CC BY 4.0", rights["notes"])
        self.assertIn("Bayerische Vermessungsverwaltung", rights["notes"])
        self.assertIn("modification", rights["notes"])
        self.assertIn("no new live calls authorized", self.c["operational_constraints"]["rate_limit_notes"])

    def test_no_duplicate_full_zip_source_download_approved(self):
        self.assertEqual(self.c["status"], "documented_only")
        self.assertEqual(self.c["implementation_decision"], "document_only")
        self.assertEqual(self.c["probe_contract"]["mode"], "none")
        self.assertIsNone(self.c["probe_contract"]["operation"])
        self.assertEqual(self.c["probe_contract"]["expected_evidence"], [])
        self.assertEqual(self.c["operational_constraints"]["retry_policy"], "none")
        self.assertEqual(self.c["operational_constraints"]["max_probe_bytes"], 8 * 1024 * 1024)
        self.assertIn("no new provider GET/HEAD/Range", self.c["request_contract"]["parameter_rules"])

    def test_existing_trusted_shp_member_is_not_whole_zip_or_2020_truth(self):
        evidence = self.c["response_contract"]["format"]
        self.assertIn("2703736", evidence)
        self.assertIn("501212696", evidence)
        self.assertIn("166172236", evidence)
        self.assertIn(
            "977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c",
            evidence,
        )
        self.assertIn("Full source ZIP SHA256 NOT verified", evidence)
        self.assertIn("43471636096", evidence)
        science = self.c["response_contract"]["scientific_semantics"]
        self.assertIn("not 2020 historical survey truth", science)
        self.assertIn("not individually insured buildings", science)
        self.assertIn("Risk model scientific calibration", science)

    def test_cannot_turn_on_probe_without_separate_api_review(self):
        c = deepcopy(self.c)
        c["status"] = "probe_ready"
        c["probe_contract"] = {
            "mode": "provider_specific",
            "operation": "preflight_original_shp_crc_and_member_sha",
            "requires_credentials": False,
            "expected_evidence": ["bounded original bytes and sha"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(c)

    def test_contract_cannot_silently_claim_automation_permission(self):
        c = deepcopy(self.c)
        c["rights_and_policy"]["commercial_automation_status"] = "allowed"
        c["implementation_decision"] = "build_adapter_now"
        with self.assertRaises(SourceAccessError):
            validate_contract(c)

    def test_attribution_and_source_scope_not_model_approval(self):
        self.assertEqual(self.c["probe_contract"]["expected_evidence"], [])
        self.assertIn("model input approval", self.c["notes"].lower())
        self.assertIn("No raw building geographies distributed", self.c["rights_and_policy"]["notes"])
        self.assertIn("not GHSL E2020 historic survey truth", self.c["notes"])


if __name__ == "__main__":
    unittest.main()
