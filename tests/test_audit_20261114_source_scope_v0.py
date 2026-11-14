# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Guard audit-discovered source product scopes and pinned dependency documentation."""
from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

from scripts.build_source_access_inventory import build_inventory
from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
IDS = (
    "eu.jrc.eurocropsv2.gsa-parcels.publisher-catalogue",
    "global.geomermaids.gmwid.infrastructure.latest-open",
)


class AuditSourceScopeTests(unittest.TestCase):
    def test_acquisition_dependency_matches_inventory(self):
        req = (ROOT / "requirements-glofas-acquisition.txt").read_text(encoding="utf-8")
        match = re.search(r"(?m)^netCDF4==([0-9A-Za-z.]+)$", req)
        self.assertIsNotNone(match)
        inventory = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
        self.assertIn("netCDF4==" + match.group(1), inventory)
        self.assertIn("separate from bounded Oasis/CLIMK research workflows", inventory)

    def test_contracts_are_nonexecutable(self):
        for access_id in IDS:
            with self.subTest(access_id=access_id):
                contract = validate_path(ROOT / "access" / (access_id + ".json"))
                self.assertEqual(contract["status"], "documented_only")
                self.assertEqual(contract["implementation_decision"], "document_only")
                self.assertEqual(contract["probe_contract"]["mode"], "none")
                self.assertEqual(contract["rights_and_policy"]["commercial_automation_status"], "unknown")
                self.assertEqual(contract["access_scope"], ["metadata", "catalogue"])

    def test_restricted_nsta_data_stays_out(self):
        contract = json.loads((ROOT / "access" / (IDS[1] + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(contract["rights_and_policy"]["redistribution_status"], "restricted")
        self.assertNotIn("/gmwid/nsta/", contract["request_contract"]["path_templates"])
        self.assertIn("noncommercial", contract["rights_and_policy"]["notes"].lower())

    def test_exact_candidate_links_without_admission(self):
        inventory = build_inventory()
        rows = {item["source_id"]: item for item in inventory["entries"]}
        cases = {
            "eu.jrc.eurocropsv2.gsa-parcels": IDS[0],
            "global.geomermaids.gmwid.infrastructure": IDS[1],
        }
        for source_id, access_id in cases.items():
            with self.subTest(source=source_id):
                self.assertIn(access_id, rows[source_id]["contract_ids"])
                self.assertEqual(rows[source_id]["operational_readiness"], "contract_documentation_only")
                self.assertFalse(rows[source_id]["live_data_availability_proven"])

    def test_readme_separates_public_aggregates_from_admitted_data(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("published numerical aggregates", readme)
        self.assertIn("not synthetic insurer exposure", readme)
        self.assertTrue((ROOT / "research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml").is_file())


if __name__ == "__main__":
    unittest.main()
