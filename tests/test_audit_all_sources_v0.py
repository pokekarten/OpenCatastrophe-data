# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, offline coverage checks for the full canonical source register."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.audit_all_sources_v0 import SourceAuditError, build_report, markdown_summary
from scripts.build_source_access_inventory import build_inventory, canonical_bytes
from scripts.probe_fixed_public_sources_v0 import PROBES


class AllSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = build_inventory()
        cls.report = build_report()

    def test_every_landscape_and_manifest_record_is_accounted_for(self):
        report = self.report
        inv = self.inventory
        self.assertEqual(report["total_source_records"], inv["entry_count"])
        self.assertEqual(len(report["records"]), inv["entry_count"])
        self.assertEqual(
            report["landscape_candidates"] + report["admitted_manifests"],
            report["total_source_records"],
        )
        self.assertEqual(sum(report["readiness_counts"].values()), report["total_source_records"])
        self.assertEqual(report["validated_access_contracts"], len(inv["access_contract_files"]))
        self.assertEqual(
            report["records_with_exact_contract"],
            sum(bool(entry["contract_ids"]) for entry in inv["entries"]),
        )

    def test_no_rights_or_live_status_are_invented(self):
        self.assertFalse(self.report["live_provider_access_verified_by_this_report"])
        self.assertFalse(self.report["rights_or_scientific_admission_granted_by_this_report"])
        for row in self.report["records"]:
            with self.subTest(source=row["source_id"]):
                self.assertFalse(row["live_probe_verified_this_audit"])
                self.assertFalse(row["scientific_model_use_approved_this_audit"])
                self.assertTrue(row["next_action"])
                self.assertTrue(row["readiness"])
                self.assertTrue(row["rights"])

    def test_fixed_live_probe_set_is_registered(self):
        ids = {row["source_id"] for row in self.report["records"]}
        self.assertEqual(self.report["fixed_public_live_probe_ids"], sorted(PROBES))
        self.assertTrue(set(PROBES).issubset(ids))

    def test_summary_and_json_are_deterministic(self):
        self.assertEqual(canonical_bytes(self.report), canonical_bytes(build_report()))
        markdown = markdown_summary(self.report)
        self.assertIn(str(self.report["total_source_records"]), markdown)
        self.assertIn("No external provider payloads", markdown)

    def test_missing_records_fail_closed(self):
        fake = {
            "entries": [], "entry_count": 1, "landscape_entry_count": 1,
            "manifest_entry_count": 0, "access_contract_files": [],
        }
        with patch("scripts.audit_all_sources_v0.build_inventory", return_value=fake):
            with self.assertRaisesRegex(SourceAuditError, "omitted"):
                build_report()


if __name__ == "__main__":
    unittest.main()
