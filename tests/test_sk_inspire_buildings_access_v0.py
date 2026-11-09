# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded source and licensing regression for GKÚ Slovakia INSPIRE Buildings."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from scripts.build_source_access_inventory import build_inventory
from scripts.structured_public_views import render_structured_markdown
from scripts.validate_source_access import (
    SourceAccessError, load_strict_json_bytes, validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "access/sk.gku.inspire-buildings.gpkg.json"
SOURCE = "sk.gku.inspire-hvd-buildings.2026"


class SlovakINSPIREBuildingsAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = validate_contract(load_strict_json_bytes(PATH.read_bytes()))

    def test_fixed_official_buildings_product_no_unreviewed_network(self):
        c = self.contract
        self.assertEqual(c["source_ids"], [SOURCE])
        self.assertEqual(c["status"], "documented_only")
        self.assertEqual(c["interface_type"], "http_file")
        self.assertEqual(c["service_root"], "https://opendata.skgeodesy.sk")
        self.assertEqual(c["request_contract"]["path_templates"], [
            "/static/INSPIRE/Buildings/inspire_bu_gpkg.zip"
        ])
        self.assertEqual(c["probe_contract"]["mode"], "none")
        self.assertEqual(c["implementation_decision"], "document_only")
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "unknown")

    def test_cannot_promote_probe_or_adapter_from_dataset_licence_alone(self):
        active = deepcopy(self.contract)
        active["status"] = "probe_ready"
        active["probe_contract"] = {
            "mode": "head",
            "operation": "fetch_fixed_buildings_gpkg_zip",
            "requires_credentials": False,
            "expected_evidence": ["bounded HEAD receipt"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(active)
        adapter = deepcopy(self.contract)
        adapter["implementation_decision"] = "build_adapter_now"
        with self.assertRaises(SourceAccessError):
            validate_contract(adapter)

    def test_source_remains_discovery_only_in_derived_inventory(self):
        entries = [x for x in build_inventory()["entries"]
                   if x["record_type"] == "landscape_candidate"
                   and x["source_id"] == SOURCE]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["contract_ids"], ["sk.gku.inspire-buildings.gpkg"])
        self.assertEqual(entries[0]["operational_readiness"],
                         "contract_documentation_only")
        self.assertNotEqual(entries[0]["automation_decision"], "build_adapter_now")

    def test_generated_human_view_is_exact(self):
        payload = load_strict_json_bytes(PATH.read_bytes())
        self.assertEqual(PATH.with_suffix(".md").read_text(encoding="utf-8"),
                         render_structured_markdown(PATH, payload, kind="access"))


if __name__ == "__main__":
    unittest.main()
