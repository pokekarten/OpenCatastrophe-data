# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline regression guards for the OpenFEMA NFIP penetration v1 T0 boundary."""

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, validate_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "fema.openfema.nfip-residential-penetration-rates.v1.json"
SOURCE_ID = "fema.openfema.nfip-residential-penetration-rates.v1"


class NfipPenetrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_documented_only_contract_is_schema_valid(self) -> None:
        validated = validate_contract(self.contract)
        self.assertEqual(validated["source_ids"], [SOURCE_ID])
        self.assertEqual(validated["api_version"].split(";")[0], "OpenFEMA NFIP Residential Penetration Rates v1")
        self.assertEqual(validated["request_contract"]["path_templates"], [
            "/api/open/v1/NfipResidentialPenetrationRates"
        ])

    def test_current_rights_do_not_grant_live_probing_or_model_use(self) -> None:
        rights = self.contract["rights_and_policy"]
        self.assertEqual(self.contract["status"], "documented_only")
        self.assertEqual(rights["dataset_rights_status"], "not_reviewed")
        self.assertEqual(rights["api_terms_status"], "separate_reviewed")
        self.assertEqual(rights["commercial_automation_status"], "restricted")
        self.assertEqual(rights["redistribution_status"], "unknown")
        self.assertEqual(self.contract["implementation_decision"], "document_only")
        self.assertEqual(self.contract["probe_contract"]["mode"], "none")
        self.assertIsNone(self.contract["probe_contract"]["operation"])

    def test_cannot_activate_probe_while_documented_only(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["probe_contract"].update(
            mode="metadata_get",
            operation="nfip_residential_penetration_rates_v1_documented_get",
            expected_evidence=["bounded test"],
        )
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)

    def test_unreviewed_dataset_rights_cannot_claim_commercial_automation(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["rights_and_policy"]["commercial_automation_status"] = "allowed"
        with self.assertRaises(SourceAccessError):
            validate_contract(changed)


if __name__ == "__main__":
    unittest.main()
