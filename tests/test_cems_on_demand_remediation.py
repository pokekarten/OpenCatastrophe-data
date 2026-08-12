# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_manifest import assert_public_asset_allowed, load_manifest, validate_structure
from scripts.validate_source_access import load_strict_json_bytes, validate_contract


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "copernicus.cems.on-demand-mapping.json"
ACCESS = ROOT / "access" / "copernicus.cems.rapid-mapping.public-activations.json"


class CemsOnDemandRemediationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_manifest(MANIFEST)
        self.access = load_strict_json_bytes(ACCESS.read_bytes())

    def test_service_terms_uncertainty_keeps_api_nonexecuting(self) -> None:
        validate_contract(self.access)
        self.assertEqual(self.access["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(self.access["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(self.access["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertEqual(self.access["status"], "documented_only")
        self.assertEqual(self.access["probe_contract"]["mode"], "none")
        self.assertIsNone(self.access["probe_contract"]["operation"])
        self.assertEqual(self.access["probe_contract"]["expected_evidence"], [])
        self.assertEqual(self.access["implementation_decision"], "document_only")

    def test_manifest_preserves_mixed_provider_derived_semantics(self) -> None:
        validate_structure(self.manifest)
        assert_public_asset_allowed(self.manifest, "metadata")
        self.assertEqual(self.manifest["modelling_layer"], "other")

        intended_use = self.manifest["intended_use"].casefold()
        self.assertIn("provider-derived", intended_use)
        self.assertIn("not direct physical hazard-intensity observations", intended_use)
        self.assertIn("not", intended_use)
        self.assertNotIn("hazard-observation", intended_use)
        self.assertNotIn("observed event geometry", intended_use)

        variables = {item["name"]: item["description"] for item in self.manifest["variables_and_units"]}
        self.assertIn("provider-derived delineation and grading product metadata", variables)
        self.assertIn("exposure and consequence summary metadata", variables)
        self.assertIn("surveyed damage", variables["provider-derived delineation and grading product metadata"])
        self.assertIn("insured-loss observations", variables["exposure and consequence summary metadata"])

    def test_dataset_reuse_and_api_policy_are_not_collapsed(self) -> None:
        self.assertEqual(self.manifest["licensing"]["status"], "verified")
        self.assertEqual(self.manifest["licensing"]["commercial_use_status"], "allowed")
        self.assertEqual(self.access["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertNotEqual(
            self.access["rights_and_policy"]["commercial_automation_status"],
            self.manifest["licensing"]["commercial_use_status"],
        )

        serialized = json.dumps({"manifest": self.manifest, "access": self.access}, sort_keys=True)
        self.assertNotIn('"api_terms_status": "same_as_dataset"', serialized)


if __name__ == "__main__":
    unittest.main()
