# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic T0 and rights-fail-closed checks for NCEI Storm Events 2024."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.build_source_access_inventory import build_inventory
from scripts.validate_source_access import SourceAccessError, validate_contract, validate_path
from research_runners.noaa_storm_events_relational_audit_v0 import HEADERS

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "access/noaa.ncei.storm-events.2024-three-tables.json"
SOURCE_ID = "noaa.ncei.storm-events"
ACCESS_ID = "noaa.ncei.storm-events.2024-three-tables"
PREFIX = "/pub/data/swdi/stormevents/csvfiles/"


class NOAA2024AccessTests(unittest.TestCase):
    def contract(self):
        return validate_path(PATH)

    def test_precise_three_original_table_identities(self):
        obj = self.contract()
        self.assertEqual(obj["access_id"], ACCESS_ID)
        self.assertEqual(obj["source_ids"], [SOURCE_ID])
        self.assertEqual(obj["interface_type"], "http_file")
        self.assertEqual(obj["service_root"], "https://www.ncei.noaa.gov")
        self.assertEqual(obj["request_contract"]["path_templates"], [
            PREFIX,
            *(PREFIX + "StormEvents_" + kind + "-ftp_v1.0_d2024_c20260728.csv.gz"
              for kind in ("details", "fatalities", "locations")),
        ])
        self.assertEqual(set(HEADERS), {"details", "fatalities", "locations"})
        self.assertEqual(obj["request_contract"]["allowed_operations"],
                         ["inspect_2024_three_table_index"])

    def test_no_implied_rights_or_model_inputs(self):
        obj = self.contract()
        self.assertEqual(obj["status"], "documented_only")
        self.assertEqual(obj["implementation_decision"], "document_only")
        self.assertEqual(obj["access_scope"], ["metadata", "catalogue"])
        self.assertEqual(obj["probe_contract"], {
            "mode": "none", "operation": None,
            "requires_credentials": False, "expected_evidence": [],
        })
        rights = obj["rights_and_policy"]
        self.assertEqual(rights["dataset_rights_status"], "not_reviewed")
        self.assertEqual(rights["api_terms_status"], "unknown")
        self.assertEqual(rights["commercial_automation_status"], "unknown")
        self.assertEqual(rights["redistribution_status"], "unknown")
        self.assertIn("3 parent-level fatality-count contradictions",
                      obj["response_contract"]["scientific_semantics"])
        self.assertIn("NOT policyholder insured losses",
                      obj["response_contract"]["scientific_semantics"])

    def test_negative_mutations_cannot_fake_rights_or_probe(self):
        baseline = self.contract()
        for mutate in (
            lambda d: d["rights_and_policy"].update({"commercial_automation_status": "allowed"}),
            lambda d: d["rights_and_policy"].update({"redistribution_status": "allowed"}),
            lambda d: d.update({"status": "verified_anonymous"}),
            lambda d: d["probe_contract"].update({"mode": "metadata_get",
                                                    "operation": "inspect_2024_three_table_index",
                                                    "expected_evidence": ["a pretend check"]}),
            lambda d: d["request_contract"]["path_templates"].append("/../private"),
        ):
            with self.subTest(mutation=str(mutate)):
                candidate = deepcopy(baseline)
                mutate(candidate)
                with self.assertRaises(SourceAccessError):
                    validate_contract(candidate)

    def test_historical_original_sha256_binding(self):
        """Bind three distinct historical compressed receipts; not a fresh T1/T3."""
        obj = self.contract()
        notes = obj["operational_constraints"]["mutability_notes"]
        report = (ROOT / "docs/research/executed-source-findings-20261103.md").read_text(
            encoding="utf-8")
        expected = (
            ("details", "12,693,243",
             "2070b83eccab041b36360ab73645b9a249c3eefc5b92b5b3fc0cbba4d9fcc09c"),
            ("fatalities", "13,057",
             "7113ce3232c98056867cf8d144df770e9e6b140cce40dff3ef46ff805ba17fdb"),
            ("locations", "983,723",
             "8847a6336e1af94000f7ecfb4a80c06bf0d5c1ac122fe39da5b2e379dc62c1b4"),
        )
        for kind, original_bytes, digest in expected:
            with self.subTest(table=kind):
                exact_name = f"StormEvents_{kind}-ftp_v1.0_d2024_c20260728.csv.gz"
                self.assertIn(f"{kind}={digest}", notes)
                self.assertIn(
                    f"| `{exact_name}` | {original_bytes} | `{digest}` |", report)
        self.assertIn("NOT freshly recomputed", notes)
        self.assertEqual(obj["probe_contract"]["mode"], "none")

    def test_existing_source_inventory_links_contract_not_admission(self):
        inventory = build_inventory()
        rows = {row["source_id"]: row for row in inventory["entries"]}
        self.assertIn(SOURCE_ID, rows)
        self.assertIn(ACCESS_ID, rows[SOURCE_ID]["contract_ids"])
        self.assertEqual(rows[SOURCE_ID]["operational_readiness"],
                         "contract_documentation_only")
        self.assertFalse(rows[SOURCE_ID]["live_data_availability_proven"])

    def test_existing_original_research_is_kept_as_narrative_evidence(self):
        review = (ROOT / "docs/research/executed-source-findings-20261103.md").read_text(
            encoding="utf-8")
        self.assertIn("69,801 detail rows", review)
        self.assertIn("three", review.lower())
        self.assertIn("StormEvents_details-ftp_v1.0_d2024_c20260728.csv.gz", review)
        self.assertIn("StormEvents_fatalities-ftp_v1.0_d2024_c20260728.csv.gz", review)
        self.assertIn("StormEvents_locations-ftp_v1.0_d2024_c20260728.csv.gz", review)


if __name__ == "__main__":
    unittest.main()
