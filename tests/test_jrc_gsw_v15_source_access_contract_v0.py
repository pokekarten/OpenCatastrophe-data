# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed checks for JRC GSW 1984-2024 v1.5 access readiness.

No network requests and no original provider bytes in this test.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "access" / "ec-jrc.global-surface-water.1984-2024.json"
EXACT_TILE = (
    "/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/occurrence/"
    "occurrence_10E_50N_v1_5_2024.tif"
)


class JRCGSWSourceAccessTests(unittest.TestCase):
    def setUp(self):
        self.contract = validate_path(PATH)

    def test_exact_original_source_and_fail_closed_metadata_contract(self):
        c = self.contract
        self.assertEqual(c["source_ids"], ["ec-jrc.global-surface-water.1984-2024"])
        self.assertEqual(c["status"], "documented_only")
        self.assertEqual(c["interface_type"], "object_store")
        self.assertEqual(c["service_root"], "https://s3.waw4-1.cloudferro.com")
        self.assertEqual(c["request_contract"]["path_templates"], [
            "/swift/v1/global-surface-water/", EXACT_TILE
        ])
        self.assertEqual(c["probe_contract"]["mode"], "none")
        self.assertIsNone(c["probe_contract"]["operation"])
        self.assertEqual(c["probe_contract"]["expected_evidence"], [])
        self.assertFalse(c["probe_contract"]["requires_credentials"])
        self.assertEqual(c["authentication"]["mode"], "none")
        self.assertEqual(c["implementation_decision"], "document_only")

    def test_dataset_use_not_conflated_with_api_and_redistribution(self):
        r = self.contract["rights_and_policy"]
        self.assertEqual(r["dataset_rights_status"], "verified")
        self.assertEqual(r["api_terms_status"], "separate_unreviewed")
        self.assertEqual(r["commercial_automation_status"], "unknown")
        self.assertEqual(r["redistribution_status"], "unknown")
        self.assertIsNone(r["terms_url"])
        self.assertIn("Source: EC JRC/Google", r["notes"])

    def test_publisher_correction_and_unfixed_recurrence_are_distinct(self):
        scientific = self.contract["response_contract"]["scientific_semantics"]
        mutable = self.contract["operational_constraints"]["mutability_notes"]
        self.assertIn("2026-11-10", scientific)
        self.assertIn("2026-11-10", mutable)
        self.assertIn("Monthly Recurrence", scientific)
        self.assertIn("unresolved", scientific)
        self.assertIn("Collection 1", scientific)
        self.assertIn("Collection 2", scientific)
        self.assertIn("not event flood hazard", scientific)

    def test_attempt_to_activate_before_api_terms_review_is_rejected(self):
        c = deepcopy(self.contract)
        c["status"] = "probe_ready"
        c["probe_contract"] = {
            "mode": "metadata_get",
            "operation": "preflight_original_v15_listing",
            "requires_credentials": False,
            "expected_evidence": ["A hypothetical provider checksum"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(c)

    def test_fake_automation_rights_without_terms_still_rejected(self):
        c = deepcopy(self.contract)
        c["rights_and_policy"]["commercial_automation_status"] = "allowed"
        c["status"] = "probe_ready"
        c["probe_contract"] = {
            "mode": "metadata_get",
            "operation": "preflight_original_v15_listing",
            "requires_credentials": False,
            "expected_evidence": ["A hypothetical provider checksum"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(c)

    def test_old_v14_or_unreviewed_host_never_whitelisted(self):
        routes = self.contract["request_contract"]["path_templates"]
        self.assertEqual(len(routes), 2)
        self.assertTrue(all("VER1-4" not in path and "v1_4" not in path for path in routes))
        self.assertTrue(all(path.startswith("/swift/v1/global-surface-water/") for path in routes))
        self.assertEqual(
            self.contract["operational_constraints"]["retry_policy"], "none"
        )


if __name__ == "__main__":
    unittest.main()
