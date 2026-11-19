# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline fail-closed check for the French hourly climate dataset's two transports."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, validate_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "access" / "fr.meteofrance.hourly-climate-stations.openlicence-v2.json"


class MeteoFranceHourlyAccessSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_public_catalogue_not_registered_climatologie_api(self) -> None:
        contract = self.contract
        self.assertEqual(contract["source_ids"], ["fr.meteofrance.hourly-climate-stations.openlicence-v2"])
        self.assertEqual(contract["service_root"], "https://www.data.gouv.fr")
        self.assertEqual(contract["request_contract"]["path_templates"], [
            "/api/1/datasets/donnees-climatologiques-de-base-horaires/"
        ])
        self.assertEqual(contract["authentication"]["mode"], "none")
        self.assertEqual(contract["status"], "documented_only")
        self.assertEqual(contract["probe_contract"]["mode"], "none")
        self.assertEqual(contract["implementation_decision"], "document_only")
        self.assertEqual(contract["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(contract["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertIn(
            "https://www.data.gouv.fr/dataservices/api-donnees-climatologiques",
            contract["evidence_urls"],
        )
        self.assertIn("100 requests/minute", contract["operational_constraints"]["rate_limit_notes"])
        self.assertIn("NOT a rate allowance", contract["operational_constraints"]["rate_limit_notes"])
        self.assertIn("NOT an allowed host", contract["request_contract"]["parameter_rules"])
        validate_contract(contract)

    def test_unreviewed_terms_cannot_be_promoted_to_live_access(self) -> None:
        contract = self.contract
        modifications = [
            (("status",), "probe_ready"),
            (("rights_and_policy", "commercial_automation_status"), "allowed"),
            (("probe_contract", "mode"), "metadata_get"),
            (("implementation_decision",), "build_adapter_now"),
        ]
        for path, value in modifications:
            with self.subTest(field=path):
                candidate = copy.deepcopy(contract)
                node = candidate
                for key in path[:-1]:
                    node = node[key]
                node[path[-1]] = value
                with self.assertRaises(SourceAccessError):
                    validate_contract(candidate)


if __name__ == "__main__":
    unittest.main()
