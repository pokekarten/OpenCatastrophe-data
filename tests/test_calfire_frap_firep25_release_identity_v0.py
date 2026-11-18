# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline fail-closed checks for the April FRAP release vs mutable catalogue."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_source_access import SourceAccessError, validate_contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "us.calfire.frap.historical-fire-perimeters.firep25-1.json"


class CalFireFrapReleaseIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_source_release_cannot_be_substituted_with_latest_portal(self) -> None:
        contract = self.contract
        self.assertEqual(
            contract["source_ids"], ["us.calfire.frap.historical-fire-perimeters.firep25-1"]
        )
        self.assertIn("published April 2026", contract["api_version"])
        self.assertIn("2026-11-11", contract["api_version"])
        self.assertIn("NOT independently proven identical", contract["api_version"])
        self.assertEqual(contract["status"], "documented_only")
        self.assertEqual(contract["authentication"]["mode"], "none")
        self.assertEqual(contract["request_contract"]["path_templates"], ["/0"])
        self.assertEqual(contract["probe_contract"]["mode"], "none")
        self.assertEqual(contract["implementation_decision"], "document_only")
        self.assertEqual(contract["rights_and_policy"]["dataset_rights_status"], "not_reviewed")
        self.assertEqual(contract["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(contract["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertEqual(contract["rights_and_policy"]["redistribution_status"], "unknown")
        self.assertIn(
            "https://publish.data.ca.gov/dataset/california-fire-perimeters-1950",
            contract["evidence_urls"],
        )
        self.assertIn("12,097", contract["operational_constraints"]["mutability_notes"])
        validate_contract(contract)

    def test_unreviewed_release_cannot_gain_automation_by_status_only(self) -> None:
        for path, value in [
            (("status",), "probe_ready"),
            (("probe_contract", "mode"), "metadata_get"),
            (("implementation_decision",), "build_adapter_now"),
            (("rights_and_policy", "commercial_automation_status"), "allowed"),
        ]:
            with self.subTest(field=path):
                candidate = copy.deepcopy(self.contract)
                leaf = candidate
                for key in path[:-1]:
                    leaf = leaf[key]
                leaf[path[-1]] = value
                with self.assertRaises(SourceAccessError):
                    validate_contract(candidate)


if __name__ == "__main__":
    unittest.main()
