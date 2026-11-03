# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""DataCite source contract must remain documentation-only and non-admitting."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access/storm.ibtracs.present-climate.v4.datacite.json"


class StormDataciteNonAdmissionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_fixed_metadata_only_doi_identity(self):
        x = self.data
        self.assertEqual(x["access_id"], "storm.ibtracs.present-climate.v4.datacite")
        self.assertEqual(x["source_ids"], ["storm.ibtracs.present-climate.v4"])
        self.assertEqual(x["service_root"], "https://api.datacite.org")
        self.assertEqual(x["request_contract"]["path_templates"],
                         ["/dois/10.4121/12706085.v4"])
        self.assertEqual(x["request_contract"]["allowed_operations"],
                         ["retrieve_fixed_v4_doi_metadata"])
        self.assertEqual(x["access_scope"], ["metadata", "catalogue"])

    def test_no_automatic_probe_or_download_enabled(self):
        x = self.data
        self.assertEqual(x["status"], "documented_only")
        self.assertEqual(x["implementation_decision"], "document_only")
        self.assertEqual(x["probe_contract"]["mode"], "none")
        self.assertIsNone(x["probe_contract"]["operation"])
        self.assertEqual(x["probe_contract"]["expected_evidence"], [])
        self.assertFalse(x["authentication"]["secret_in_repository"])
        self.assertEqual(x["authentication"]["mode"], "none")

    def test_future_metadata_request_must_be_bounded_and_separately_reviewed(self):
        limits = self.data["operational_constraints"]
        self.assertLessEqual(limits["max_probe_bytes"], 262144)
        self.assertLessEqual(limits["timeout_seconds"], 20)
        self.assertEqual(limits["retry_policy"], "none")
        self.assertIn("No live DataCite call is authorized", limits["rate_limit_notes"])
        self.assertIn("No 4TU file-list, download, or track-byte request is authorized",
                      self.data["request_contract"]["parameter_rules"])

    def test_dataset_rights_not_confused_with_api_or_model_approval(self):
        x = self.data
        rights = x["rights_and_policy"]
        self.assertEqual(rights["api_terms_status"], "unknown")
        self.assertEqual(rights["commercial_automation_status"], "unknown")
        self.assertEqual(rights["redistribution_status"], "unknown")
        self.assertIn("not", x["response_contract"]["scientific_semantics"].casefold())


if __name__ == "__main__":
    unittest.main()
