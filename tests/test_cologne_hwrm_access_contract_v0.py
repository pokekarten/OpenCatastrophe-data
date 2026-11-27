# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline binding of the official NRW WMS metadata-only access contract.

This is NOT an acquisition or source-admission test. It fails if the exact
repository-reviewed service metadata/rights boundary and the fixed metadata
probe silently drift apart.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "de.nrw.lanuk.hwrm-hw-gefahrenkarte.wms.2026.json"
RUNNER = ROOT / "research_runners" / "cologne_hwrm_service_probe_v0.py"
spec = importlib.util.spec_from_file_location("cologne_hwrm_service_probe_v0", RUNNER)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class NRWOfficialWmsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exact_metadata_operation_not_raster_acquisition(self):
        access = self.contract
        self.assertEqual(access["source_ids"], ["de.nrw.lanuk.hwrm-hqhaeufig-flood.2026"])
        self.assertEqual(access["interface_type"], "wms")
        self.assertEqual(access["access_scope"], ["metadata"])
        self.assertEqual(access["request_contract"]["allowed_operations"], ["get_capabilities"])
        self.assertEqual(access["probe_contract"]["mode"], "metadata_get")
        self.assertEqual(access["probe_contract"]["operation"], "get_capabilities")
        self.assertFalse(access["probe_contract"]["requires_credentials"])
        self.assertEqual(access["authentication"]["mode"], "none")
        self.assertEqual(access["implementation_decision"], "build_later")
        self.assertEqual(access["service_root"], "https://www.wms.nrw.de")
        self.assertEqual(
            access["request_contract"]["path_templates"],
            ["/umwelt/wasser/HW_Gefahrenkarte"],
        )
        self.assertTrue(probe.CAPABILITIES_URL.startswith(
            access["service_root"] + access["request_contract"]["path_templates"][0] + "?"
        ))
        self.assertEqual(
            probe.CAPABILITIES_URL.split("?", 1)[1],
            "REQUEST=GetCapabilities&SERVICE=WMS",
        )

    def test_original_wms_terms_digest_and_attribution_not_silent_drift(self):
        access = self.contract
        self.assertEqual(access["api_version"], "OGC WMS " + probe.REVIEWED_WMS_VERSION)
        self.assertEqual(access["rights_and_policy"]["api_terms_status"], "same_as_dataset")
        self.assertEqual(
            access["rights_and_policy"]["terms_url"],
            "https://www.govdata.de/dl-de/by-2-0",
        )
        self.assertEqual(access["rights_and_policy"]["redistribution_status"], "unknown")
        self.assertEqual(access["probe_contract"]["expected_evidence"][3][:8], "Original")
        self.assertIn(
            probe.REVIEWED_WMS_SERVICE_TERMS_SHA256,
            access["response_contract"]["format"],
        )
        self.assertIn(
            probe.REVIEWED_WMS_SERVICE_TERMS_SHA256,
            access["rights_and_policy"]["notes"],
        )
        self.assertIn(
            probe.REVIEWED_WMS_SERVICE_TERMS_SHA256,
            access["notes"],
        )
        self.assertIn("Land NRW", access["rights_and_policy"]["notes"])
        self.assertIn("DL-DE Zero 2.0", access["rights_and_policy"]["notes"])
        self.assertIn("dl-de/by-2-0", access["rights_and_policy"]["notes"])
        self.assertNotEqual(
            probe.REVIEWED_WMS_SERVICE_TERMS_SHA256,
            "b5d72228b7c3c926c9765e79be3ee516237fa2a31054578e57e4ea2cbb4e095e",
        )

    def test_protocol_limits_match_fixed_probe(self):
        ops = self.contract["operational_constraints"]
        self.assertEqual(ops["timeout_seconds"], 20)
        self.assertEqual(ops["max_probe_bytes"], probe.MAX_RESPONSE_BYTES)
        self.assertEqual(ops["retry_policy"], "none")
        self.assertEqual(self.contract["status"], "verified_anonymous")
        self.assertNotIn("get_map", self.contract["request_contract"]["allowed_operations"])
        self.assertNotIn("bulk", self.contract["access_scope"])
        self.assertNotIn("sample", self.contract["access_scope"])

    def test_original_xml_receipt_is_not_a_scientific_admission(self):
        self.assertIn("not_admitted", self.contract["probe_contract"]["expected_evidence"][4])
        self.assertIn("wms_capabilities", self.contract["response_contract"]["format"].lower())
        self.assertIn("no model admission", self.contract["response_contract"]["scientific_semantics"].lower())


if __name__ == "__main__":
    unittest.main()
