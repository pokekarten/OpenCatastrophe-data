# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed official station and best-track access/rights scope tests."""
from __future__ import annotations

from pathlib import Path
import unittest

from scripts.build_source_access_inventory import build_inventory
from scripts.validate_source_access import validate_path, validate_contract, SourceAccessError

ROOT = Path(__file__).resolve().parents[1]

CASES = {
    "fr.meteofrance.hourly-climate-stations.openlicence-v2": ("documented_only", "none", "verified"),
    "nl.knmi.kdp.hourly-validated-edr.v1": ("blocked_credentials", "api_key", "unknown"),
    "uk.metoffice.midas-open-hourly.v202607": ("blocked_registration", "provider_account", "verified"),
    "eu.ecad.meteogate.nonblended-stations.2026": ("restricted_by_terms", "none", "restricted"),
    "us.noaa.nhc.hurdat2.atlantic.2026-09": ("documented_only", "none", "unknown"),
}


class OfficialEuropeWindAndNHCSourceAccessTests(unittest.TestCase):
    def _contract(self, source_id: str):
        return validate_path(ROOT / "access" / (source_id + ".json"))

    def test_exact_five_candidates_link_to_five_valid_contracts(self):
        rows = {row["source_id"]: row for row in build_inventory()["entries"]}
        self.assertEqual(len(CASES), 5)
        for source_id, expected in CASES.items():
            with self.subTest(source_id=source_id):
                self.assertIn(source_id, rows)
                self.assertIn(source_id, rows[source_id]["contract_ids"])
                self.assertFalse(rows[source_id]["live_data_availability_proven"])
                contract = self._contract(source_id)
                self.assertEqual(contract["source_ids"], [source_id])
                self.assertEqual((contract["status"], contract["authentication"]["mode"],
                                  contract["rights_and_policy"]["dataset_rights_status"]), expected)
                self.assertEqual(contract["probe_contract"]["mode"], "none")
                self.assertIsNone(contract["probe_contract"]["operation"])
                self.assertFalse(contract["authentication"]["secret_in_repository"])
                self.assertNotEqual(contract["implementation_decision"], "build_adapter_now")

    def test_european_station_product_rights_do_not_bleed_across_providers(self):
        france = self._contract("fr.meteofrance.hourly-climate-stations.openlicence-v2")
        knmi = self._contract("nl.knmi.kdp.hourly-validated-edr.v1")
        uk = self._contract("uk.metoffice.midas-open-hourly.v202607")
        ecad = self._contract("eu.ecad.meteogate.nonblended-stations.2026")
        self.assertEqual(france["request_contract"]["path_templates"],
                         ["/api/1/datasets/donnees-climatologiques-de-base-horaires/"])
        self.assertTrue(france["service_root"].endswith("data.gouv.fr"))
        self.assertEqual(knmi["authentication"]["credential_reference"], "KNMI_EDR_API_KEY")
        self.assertIn("/edr/v1/collections/hourly-in-situ-meteorological-observations-validated",
                      knmi["request_contract"]["path_templates"])
        self.assertIn("d04207b551674c07801b7d4e6d883e50", uk["api_version"])
        self.assertEqual(ecad["rights_and_policy"]["commercial_automation_status"], "prohibited")
        self.assertEqual(ecad["implementation_decision"], "do_not_automate")
        self.assertEqual(ecad["rights_and_policy"]["redistribution_status"], "restricted")
        self.assertIn("ECAD_datapolicy.pdf", ecad["rights_and_policy"]["terms_url"])

    def test_noaa_track_is_not_european_windfield_or_independent_ibtracs(self):
        source = self._contract("us.noaa.nhc.hurdat2.atlantic.2026-09")
        self.assertEqual(source["request_contract"]["path_templates"], ["/data/", "/data/hurdat/"])
        self.assertIn("IBTrACS", source["response_contract"]["scientific_semantics"])
        self.assertIn("not independent", source["response_contract"]["scientific_semantics"])
        self.assertEqual(source["rights_and_policy"]["commercial_automation_status"], "unknown")

    def test_contracts_cannot_be_silently_promoted(self):
        import copy
        for source_id in CASES:
            with self.subTest(source=source_id):
                c = copy.deepcopy(self._contract(source_id))
                c["probe_contract"] = {
                    "mode": "metadata_get",
                    "operation": c["request_contract"]["allowed_operations"][0],
                    "requires_credentials": c["authentication"]["mode"] != "none",
                    "expected_evidence": ["original provider response SHA256"],
                }
                c["status"] = "probe_ready"
                with self.assertRaises(SourceAccessError):
                    validate_contract(c)


if __name__ == "__main__":
    unittest.main()
